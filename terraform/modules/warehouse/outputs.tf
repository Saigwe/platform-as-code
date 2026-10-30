output "warehouse_name" {
  description = "Warehouse name"
  value       = snowflake_warehouse.this.name
}

output "resource_monitor_name" {
  description = "Resource monitor attached to the warehouse"
  value       = snowflake_resource_monitor.this.name
}
