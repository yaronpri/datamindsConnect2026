"""Deploy the demo items in items/workspace to a Fabric workspace with fabric-cicd.

Phase 1: Variable library, lakehouse, notebook.
Then:    Run the notebook (creates dbo.sales in lh_demo) and sync the lakehouse SQL analytics endpoint.
Phase 2: Direct Lake semantic model and paginated report, then refresh (frame) the semantic model.

Environment variables: TENANT_ID, CLIENT_ID, CLIENT_SECRET, WORKSPACE_NAME.
"""

import os
import sys
import time
from pathlib import Path

import requests
from azure.identity import ClientSecretCredential
from fabric_cicd import FabricWorkspace, change_log_level, publish_all_items

FABRIC_API = "https://api.fabric.microsoft.com/v1"
PBI_API = "https://api.powerbi.com/v1.0/myorg"
REPO_DIR = str(Path(__file__).parent / "workspace")

NOTEBOOK = "nb_demo"
LAKEHOUSE = "lh_demo"
SEMANTIC_MODEL = "sm_demo"


def log(msg: str) -> None:
    print(f"[deploy] {msg}", flush=True)


credential = ClientSecretCredential(
    tenant_id=os.environ["TENANT_ID"],
    client_id=os.environ["CLIENT_ID"],
    client_secret=os.environ["CLIENT_SECRET"],
)
workspace_name = os.environ["WORKSPACE_NAME"]

if os.environ.get("SYSTEM_DEBUG", "").lower() == "true":
    change_log_level()


def headers(scope: str) -> dict:
    return {"Authorization": f"Bearer {credential.get_token(scope).token}"}


def fabric(method: str, path: str, **kwargs) -> requests.Response:
    url = path if path.startswith("http") else f"{FABRIC_API}{path}"
    resp = requests.request(method, url, headers=headers("https://api.fabric.microsoft.com/.default"), timeout=60, **kwargs)
    if resp.status_code >= 400:
        sys.exit(f"Fabric API {method} {url} failed: {resp.status_code} {resp.text}")
    return resp


def wait_for(url: str, done: set, failed: set, timeout_s: int, what: str) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        time.sleep(15)
        status = fabric("GET", url).json().get("status", "")
        log(f"{what}: {status}")
        if status in done:
            return
        if status in failed:
            sys.exit(f"{what} ended with status {status}")
    sys.exit(f"{what} timed out after {timeout_s}s")


def deploy(item_types: list) -> FabricWorkspace:
    log(f"Publishing {item_types} to '{workspace_name}'")
    ws = FabricWorkspace(
        workspace_name=workspace_name,
        environment="DEV",
        repository_directory=REPO_DIR,
        item_type_in_scope=item_types,
        token_credential=credential,
    )
    publish_all_items(ws)
    return ws


def find_item(ws_id: str, item_type: str, name: str) -> dict:
    items = fabric("GET", f"/workspaces/{ws_id}/items?type={item_type}").json()["value"]
    for item in items:
        if item["displayName"] == name:
            return item
    sys.exit(f"{item_type} '{name}' not found in workspace")


# Phase 1
ws = deploy(["VariableLibrary", "Lakehouse", "Notebook"])
ws_id = ws.workspace_id

# Run the notebook so the Direct Lake model has a table to bind to
nb = find_item(ws_id, "Notebook", NOTEBOOK)
log(f"Running notebook {NOTEBOOK}")
resp = fabric("POST", f"/workspaces/{ws_id}/items/{nb['id']}/jobs/instances?jobType=RunNotebook")
wait_for(resp.headers["Location"], {"Completed"}, {"Failed", "Cancelled", "Deduped"}, 40 * 60, "Notebook run")

# Make the new table visible in the lakehouse SQL analytics endpoint
lh = fabric("GET", f"/workspaces/{ws_id}/lakehouses/{find_item(ws_id, 'Lakehouse', LAKEHOUSE)['id']}").json()
sql_id = lh["properties"]["sqlEndpointProperties"]["id"]
log("Refreshing SQL analytics endpoint metadata")
resp = fabric("POST", f"/workspaces/{ws_id}/sqlEndpoints/{sql_id}/refreshMetadata", json={})
if resp.status_code == 202:
    wait_for(resp.headers["Location"], {"Succeeded"}, {"Failed"}, 10 * 60, "SQL endpoint sync")

# Phase 2
deploy(["SemanticModel", "PaginatedReport"])

# Frame the Direct Lake model so the report has data
sm = find_item(ws_id, "SemanticModel", SEMANTIC_MODEL)
pbi_headers = headers("https://analysis.windows.net/powerbi/api/.default")
log(f"Refreshing semantic model {SEMANTIC_MODEL}")
resp = requests.post(f"{PBI_API}/groups/{ws_id}/datasets/{sm['id']}/refreshes", headers=pbi_headers, json={"type": "full"}, timeout=60)
if resp.status_code >= 400:
    sys.exit(f"Semantic model refresh request failed: {resp.status_code} {resp.text}")
deadline = time.time() + 10 * 60
while time.time() < deadline:
    time.sleep(10)
    last = requests.get(f"{PBI_API}/groups/{ws_id}/datasets/{sm['id']}/refreshes?$top=1", headers=pbi_headers, timeout=60).json()["value"][0]
    log(f"Semantic model refresh: {last['status']}")
    if last["status"] == "Completed":
        break
    if last["status"] in ("Failed", "Disabled", "Cancelled"):
        sys.exit(f"Semantic model refresh failed: {last.get('serviceExceptionJson', '')}")
else:
    sys.exit("Semantic model refresh timed out")

log("Done")
