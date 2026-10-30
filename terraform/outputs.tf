output "warehouses" {
  description = "Warehouse name for each workload"
  value       = { for k, m in module.warehouse : k => m.warehouse_name }
}

output "monthly_credit_cap" {
  description = "Total credits the environment can spend in a month before warehouses are suspended"
  value       = sum([for w in values(var.warehouses) : w.monthly_credit_quota])
}
