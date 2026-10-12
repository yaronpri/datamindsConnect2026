data "azurerm_client_config" "current" {}

# ---------- Azure: resource group + Fabric capacity ----------
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}

resource "azurerm_fabric_capacity" "capacity" {
  name                = var.capacity_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location

  # The pipeline service principal (object id) becomes capacity admin,
  # so it can assign workspaces to this capacity.
  administration_members = [data.azurerm_client_config.current.object_id]

  sku {
    name = var.capacity_sku
    tier = "Fabric"
  }
}

# Give Fabric a moment to see the new capacity before looking it up.
resource "time_sleep" "wait_for_capacity" {
  depends_on      = [azurerm_fabric_capacity.capacity]
  create_duration = "60s"
}

data "fabric_capacity" "capacity" {
  display_name = azurerm_fabric_capacity.capacity.name
  depends_on   = [time_sleep.wait_for_capacity]
}

# ---------- Fabric: workspaces ----------
# The service principal creates the workspaces, so it is automatically Admin on each.
locals {
  workspaces = {
    main = var.main_workspace_name
    test = "test-${var.main_workspace_name}"
    prod = "prod-${var.main_workspace_name}"
  }
}

resource "fabric_workspace" "ws" {
  for_each     = local.workspaces
  display_name = each.value
  description  = "Created by Terraform (${each.key})"
  capacity_id  = data.fabric_capacity.capacity.id
}

resource "fabric_workspace_role_assignment" "main_contributor" {
  workspace_id = fabric_workspace.ws["main"].id
  principal = {
    id   = var.contributor_user_id
    type = "User"
  }
  role = "Contributor"
}

# ---------- Git: connect main workspace to Azure DevOps ----------
resource "fabric_connection" "ado" {
  display_name      = "ado-${lower(var.main_workspace_name)}-conn"
  connectivity_type = "ShareableCloud"
  privacy_level     = "Organizational"
  connection_details = {
    type            = "AzureDevOpsSourceControl"
    creation_method = "AzureDevOpsSourceControl.Contents"
    parameters = [
      {
        name  = "url"
        value = "https://dev.azure.com/${var.ado_organization}/${var.ado_project}/_git/${var.ado_repository}/"
      }
    ]
  }
  credential_details = {
    credential_type      = "ServicePrincipal"
    skip_test_connection = false
    service_principal_credentials = {
      tenant_id                = var.tenant_id
      client_id                = var.client_id
      client_secret_wo         = var.client_secret
      client_secret_wo_version = 1
    }
  }
}

resource "fabric_workspace_git" "main" {
  workspace_id            = fabric_workspace.ws["main"].id
  initialization_strategy = "PreferRemote"
  git_provider_details = {
    git_provider_type = "AzureDevOps"
    organization_name = var.ado_organization
    project_name      = var.ado_project
    repository_name   = var.ado_repository
    branch_name       = var.ado_branch
    directory_name    = var.ado_directory
  }
  git_credentials = {
    source        = "ConfiguredConnection"
    connection_id = fabric_connection.ado.id
  }
}
