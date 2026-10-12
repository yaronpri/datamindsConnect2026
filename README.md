# Fabric environment with Terraform and Azure DevOps Pipelines

Sample Azure DevOps pipeline that uses Terraform to stand up a Microsoft Fabric environment, authenticating as a service principal.

What it creates:

1. A resource group and a **Fabric capacity** in Azure (the service principal is set as capacity admin).
2. Three workspaces on that capacity: `<name>`, `test-<name>`, and `prod-<name>`. The service principal creates them, so it is **Admin** on each.
3. A user added as **Contributor** on the main `<name>` workspace.
4. An Azure DevOps **source control connection** (service principal credentials) and a **Git connection** of the main workspace to a folder in an Azure DevOps repo.

The pipeline runs in three stages: **Plan**, **Approve** (manual), **Apply**. The plan is shown on the run Summary tab; the Apply stage applies exactly the reviewed plan. If the plan has no changes, Approve and Apply are skipped.

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
```

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

- The target folder (for example `/my-workspace`) exists in the repository and branch.
- Microsoft-hosted agent parallelism (or change `pool` to a self-hosted pool).

## Setup

1. Copy the `infra` folder into a repository in your Azure DevOps project.
2. Edit `infra/terraform.tfvars` with your region, names, contributor user object id, and Azure DevOps organization / project / repository / folder.
3. Edit `infra/backend.hcl` with the state storage resource group, account, container, and blob name.
4. Create a pipeline from `infra/azure-pipelines.yml` (Pipelines > New pipeline > Azure Repos Git > Existing YAML file).
5. In the pipeline, add a variable **`CLIENT_SECRET`**: mark it **secret** and **"Let users override this value when running this pipeline"**.

## Run

1. Select **Run pipeline** and fill in the parameters: **Tenant ID**, **Service principal client ID**, **Azure subscription ID**. Set `CLIENT_SECRET` under Variables if it is not stored.
2. When the **Plan** stage finishes, review the plan on the run **Summary** tab.
3. On the **Approve** stage, select **Review**, then **Resume** to apply or **Reject** to stop. Pending approvals time out (reject) after 24 hours.

## Notes

- **Secret in the plan artifact:** the plan file stores input variable values, including the client secret, in plain text. Anyone with read access to the pipeline artifacts can read it. For production use, restrict artifact access or pass credentials to the providers through environment variables instead of Terraform variables.
- **Workspace admin:** no explicit Admin role assignment is made for the service principal; the workspace creator is Admin automatically, and a duplicate assignment would fail.
- **Capacity lookup:** after creating the capacity, Terraform waits 60 seconds before looking it up in Fabric, so the new capacity is visible.
- **Changing region:** `location` changes force the resource group and capacity to be recreated.
