# Resets monthly. Alerts at 75% and 90%, suspends once running queries finish at 100%, and cancels them at 110%.
resource "snowflake_resource_monitor" "this" {
  name                      = "${var.name}_MONITOR"
  credit_quota              = var.monthly_credit_quota
  notify_triggers           = [75, 90]
  suspend_trigger           = 100
  suspend_immediate_trigger = 110
}

resource "snowflake_warehouse" "this" {
  name                = var.name
  warehouse_size      = var.size
  auto_suspend        = var.auto_suspend_seconds
  auto_resume         = "true"
  initially_suspended = true
  resource_monitor    = snowflake_resource_monitor.this.name
  comment             = "Managed by Terraform"
}

resource "snowflake_grant_privileges_to_account_role" "usage" {
  for_each = toset(var.usage_roles)

  account_role_name = each.value
  privileges        = ["USAGE", "OPERATE"]

  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.this.name
  }
}
