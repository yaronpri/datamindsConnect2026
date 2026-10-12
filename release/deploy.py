"""Deploy the items committed in the parentY folder to a target workspace with fabric-cicd.

Phase 1 publishes every supported item type with bulk publish (one bulkImportDefinitions call per dependency batch).
Phase 2 publishes PaginatedReport with the standard per-item API, because paginated reports do not yet support
service principal identities for Git integration and the bulk import API (PrincipalTypeNotSupported).

Environment variables: TENANT_ID, CLIENT_ID, CLIENT_SECRET, TARGET_WORKSPACE, ENVIRONMENT.
"""

import os
from pathlib import Path

from azure.identity import ClientSecretCredential
from fabric_cicd import FabricWorkspace, append_feature_flag, change_log_level, constants, publish_all_items

ROOT = Path(__file__).resolve().parent.parent

BULK_ITEM_TYPES = ["Lakehouse", "VariableLibrary", "Notebook", "SemanticModel"]
STANDARD_ITEM_TYPES = ["PaginatedReport"]

if os.environ.get("SYSTEM_DEBUG", "").lower() == "true":
    change_log_level()

credential = ClientSecretCredential(
    tenant_id=os.environ["TENANT_ID"],
    client_id=os.environ["CLIENT_ID"],
    client_secret=os.environ["CLIENT_SECRET"],
)


def workspace_for(item_types):
    return FabricWorkspace(
        workspace_name=os.environ["TARGET_WORKSPACE"],
        environment=os.environ.get("ENVIRONMENT", "TEST"),
        repository_directory=str(ROOT / "parentY"),
        parameter_file_path=str(ROOT / "release" / "parameter.yml"),
        item_type_in_scope=item_types,
        token_credential=credential,
    )


# Phase 1: bulk publish
append_feature_flag("enable_experimental_features")
append_feature_flag("enable_bulk_publish")
publish_all_items(workspace_for(BULK_ITEM_TYPES))

# Phase 2: standard publish.
# NOTE: this second pass exists only because PaginatedReport does not yet support service principal
# identities for Git integration and the bulk import API (PrincipalTypeNotSupported). Once it does,
# add "PaginatedReport" to BULK_ITEM_TYPES and remove this phase.
# A new FabricWorkspace re-reads the target workspace, so
# $items.SemanticModel.sm_demo.$id resolves to the model deployed in phase 1.
constants.FEATURE_FLAG.discard("enable_bulk_publish")
publish_all_items(workspace_for(STANDARD_ITEM_TYPES))
