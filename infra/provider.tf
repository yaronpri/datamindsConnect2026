terraform {
  required_version = ">= 1.8, < 2.0"

  # Remote state in Azure Storage. Values come from backend.hcl at init time:
  #   terraform init -backend-config=backend.hcl
  # Auth uses ARM_CLIENT_ID / ARM_CLIENT_SECRET / ARM_TENANT_ID / ARM_SUBSCRIPTION_ID.
  backend "azurerm" {}

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.9"
    }
    fabric = {
      source  = "microsoft/fabric"
      version = "~> 1.14"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.13"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id
  client_id       = var.client_id
  client_secret   = var.client_secret
}

provider "fabric" {
  tenant_id     = var.tenant_id
  client_id     = var.client_id
  client_secret = var.client_secret
  preview       = true
}
