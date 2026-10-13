# ---------- Passed by the pipeline (do not put these in terraform.tfvars) ----------
variable "tenant_id" {
  description = "Entra tenant id of the service principal."
  type        = string
}

variable "client_id" {
  description = "Service principal (app) client id."
  type        = string
}

variable "client_secret" {
  description = "Service principal client secret."
  type        = string
  sensitive   = true
}

variable "subscription_id" {
  description = "Azure subscription where the Fabric capacity is created."
  type        = string
}

# ---------- Set in terraform.tfvars ----------
variable "location" {
  description = "Azure region for the resource group and capacity. Must have Fabric capacity quota."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group for the Fabric capacity (created by Terraform)."
  type        = string
}

variable "capacity_name" {
  description = "Fabric capacity name (lowercase letters and digits only, 3-63 chars)."
  type        = string
}

variable "capacity_sku" {
  description = "Fabric capacity SKU, for example F2."
  type        = string
  default     = "F2"
}

variable "main_workspace_name" {
  description = "Main (Git connected) workspace name. test-<name> and prod-<name> are created too."
  type        = string
}

variable "contributor_user_id" {
  description = "Entra object id of the user added as Contributor on the main workspace."
  type        = string
}

variable "ado_organization" {
  description = "Azure DevOps organization name."
  type        = string
}

variable "ado_project" {
  description = "Azure DevOps project name."
  type        = string
}

variable "ado_repository" {
  description = "Azure DevOps repository name."
  type        = string
}

variable "ado_branch" {
  description = "Branch the main workspace is connected to."
  type        = string
  default     = "main"
}

variable "ado_directory" {
  description = "Repository folder the main workspace is connected to, for example /sales-analytics."
  type        = string
}
