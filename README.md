# Fabric CI/CD end to end with Terraform, fabric-cicd, and Azure DevOps Pipelines

Sample that takes a Microsoft Fabric project from an empty tenant to a tag-based release, using three Azure DevOps pipelines that all authenticate as a service principal:

| Stage | Folder | Pipeline | What it does |
|-------|--------|----------|--------------|
| 1. Infrastructure | `infra/` | Terraform: Plan, Approve, Apply | Capacity, workspaces `parentY`, `test-parentY`, `prod-parentY`, and the Git connection of `parentY` to the `parentY/` folder |
| 2. Seed items | `items/` | Manual run | Creates demo items in `parentY` with fabric-cicd: lakehouse, notebook, variable library, Direct Lake semantic model, paginated report |
| 3. Release | `release/` | Triggered by a tag on `main` | Deploys the items committed in `parentY/` to `test-parentY` with fabric-cicd bulk publish and dynamic replacement variables |

```
parentY workspace --(commit from workspace)--> parentY/ folder on main --(git tag v1.0.0)--> test-parentY workspace
```

## Repository layout

```
infra/
  azure-pipelines.yml   Pipeline definition (Plan / Approve / Apply)
  provider.tf           Providers (azurerm, fabric, time) and azurerm state backend
  variables.tf          Input variables
  main.tf               Capacity, workspaces, role assignment, Git connection
  outputs.tf            Capacity id and workspace ids
  terraform.tfvars      Environment settings: edit this
  backend.hcl           Terraform state location: edit this
items/
  azure-pipelines.yml   Seeds the demo items into parentY (run once)
  deploy.py             fabric-cicd publish, runs the notebook, refreshes the model
  workspace/            Item definitions with placeholder IDs, plus parameter.yml
release/
  azure-pipelines.yml   Tag-triggered release to test-parentY
  deploy.py             fabric-cicd bulk publish of parentY/
  parameter.yml         Dynamic replacement variables (no hard-coded IDs)
parentY/                Git folder of the parentY workspace (filled by Fabric when you commit)
```

## What the infrastructure stage creates

1. A resource group and a **Fabric capacity** in Azure (the service principal is set as capacity admin).
2. Three workspaces on that capacity: `<name>`, `test-<name>`, and `prod-<name>`. The service principal creates them, so it is **Admin** on each.
3. A user added as **Contributor** on the main `<name>` workspace.
4. An Azure DevOps **source control connection** (service principal credentials) and a **Git connection** of the main workspace to a folder in an Azure DevOps repo.

The pipeline runs in three stages: **Plan**, **Approve** (manual), **Apply**. The plan is shown on the run Summary tab; the Apply stage applies exactly the reviewed plan. If the plan has no changes, Approve and Apply are skipped.

## Prerequisites

**Service principal** (app registration with a client secret):

- **Contributor** (or Owner) on the Azure subscription, to create the resource group and capacity, register the `Microsoft.Fabric` resource provider, and read the state storage account key.
- Added to the **Azure DevOps organization** with access to the target repository, so the Fabric Git connection can authenticate.

**Fabric tenant settings** (Fabric admin portal), enabled for the service principal or a security group that contains it:

- Service principals can use Fabric APIs.
- Service principals can create workspaces, connections, and deployment pipelines.
- Users can synchronize workspace items with their Git repositories.

**Azure:**

- Fabric capacity **quota** in the chosen region. Check it with:
  ```bash
  az rest --method get --url "https://management.azure.com/subscriptions/<subscription-id>/providers/Microsoft.Fabric/locations/<region>/usages?api-version=2023-11-01"
  ```
  A region with a limit of 0 fails with a regional quota error.
- An existing **storage account and container** for the Terraform state. The storage account must be reachable from the pipeline agent (Microsoft-hosted agents need public network access).

**Azure DevOps:**

- The target folder (`/parentY`) exists in the repository and branch (this repository includes it).
- Microsoft-hosted agent parallelism (or change `pool` to a self-hosted pool).

## Setup

1. Copy this repository (all folders) into a repository in your Azure DevOps project.
2. Edit `infra/terraform.tfvars` with your region, names, contributor user object id, and Azure DevOps organization / project / repository / folder.
3. Edit `infra/backend.hcl` with the state storage resource group, account, container, and blob name.
4. Create a pipeline from `infra/azure-pipelines.yml` (Pipelines > New pipeline > Azure Repos Git > Existing YAML file).
5. In the pipeline, add a variable **`CLIENT_SECRET`**: mark it **secret** and **"Let users override this value when running this pipeline"**.

## Run

### 1. Infrastructure

1. Select **Run pipeline** and fill in the parameters: **Tenant ID**, **Service principal client ID**, **Azure subscription ID**. Set `CLIENT_SECRET` under Variables if it is not stored.
2. When the **Plan** stage finishes, review the plan on the run **Summary** tab.
3. On the **Approve** stage, select **Review**, then **Resume** to apply or **Reject** to stop. Pending approvals time out (reject) after 24 hours.

### 2. Seed the demo items

1. Create a pipeline from `items/azure-pipelines.yml` and add the secret variable **`CLIENT_SECRET`**.
2. Run it with **Tenant ID**, **Service principal client ID**, and **Target workspace name** (`parentY`). It publishes the items, runs `nb_demo` to create `dbo.sales`, and refreshes `sm_demo`.
3. In the `parentY` workspace, open **Source control** and **Commit** the new items. Fabric writes them to the `parentY/` folder.

### 3. Release with a tag

1. Create a pipeline from `release/azure-pipelines.yml`. Add the variables **`TENANT_ID`**, **`CLIENT_ID`**, and secret **`CLIENT_SECRET`**, then **Save** the pipeline.
2. Create a tag on `main`, from Git (`git tag v1.0.0 && git push origin v1.0.0`) or in the portal (**Repos > Tags > New tag**).
3. The pipeline verifies the tag is on `main` and deploys `parentY/` to `test-parentY`. In `vl_demo`, `workspace_name` becomes `test-parentY`.
4. In `test-parentY`, run `nb_demo` and refresh `sm_demo` so `rpt_demo` shows data.

See `release/README.md` for the parameterization details.

## Notes

- **Bulk publish and paginated reports:** paginated reports do not yet support service principals for Git integration and the bulk import API (`PrincipalTypeNotSupported`). `release/deploy.py` therefore publishes `rpt_demo` in a second, standard pass. This is a temporary workaround; remove the second pass once paginated reports support it.
- **Renaming parentY:** the name appears in `infra/terraform.tfvars` (`main_workspace_name`, `ado_directory`), the `parentY/` folder, `release/parameter.yml` (`$workspace.parentY...`), `release/deploy.py` (source folder), `release/azure-pipelines.yml` (`TARGET_WORKSPACE`), and the `vl_demo` default value in `items/`.
- **Feature branch flow:** if the workspace is connected to a branch other than `main` (for example `dev`), merge it to `main` with a pull request before tagging.
- **Experimental features:** bulk publish needs fabric-cicd 1.4.0 or later and the `enable_experimental_features` and `enable_bulk_publish` feature flags.

- **Secret in the plan artifact:** the plan file stores input variable values, including the client secret, in plain text. Anyone with read access to the pipeline artifacts can read it. For production use, restrict artifact access or pass credentials to the providers through environment variables instead of Terraform variables.
- **Workspace admin:** no explicit Admin role assignment is made for the service principal; the workspace creator is Admin automatically, and a duplicate assignment would fail.
- **Capacity lookup:** after creating the capacity, Terraform waits 60 seconds before looking it up in Fabric, so the new capacity is visible.
- **Changing region:** `location` changes force the resource group and capacity to be recreated.
