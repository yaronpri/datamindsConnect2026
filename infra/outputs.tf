output "capacity_id" {
  value = data.fabric_capacity.capacity.id
}

output "workspace_ids" {
  value = { for k, ws in fabric_workspace.ws : ws.display_name => ws.id }
}
