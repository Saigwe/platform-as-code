locals {
  prefix = upper(var.environment)
  roles  = toset(flatten([for w in values(var.warehouses) : w.users]))
}

# Functional roles (TRANSFORMER, REPORTER, LOADER), rolled up to SYSADMIN so admins keep visibility.
resource "snowflake_account_role" "functional" {
  for_each = local.roles

  name    = "${local.prefix}_${each.key}"
  comment = "Managed by Terraform"
}

resource "snowflake_grant_account_role" "to_sysadmin" {
  for_each = local.roles

  role_name        = snowflake_account_role.functional[each.key].name
  parent_role_name = "SYSADMIN"
}

resource "snowflake_database" "analytics" {
  name                        = "${local.prefix}_ANALYTICS"
  data_retention_time_in_days = var.data_retention_days
  comment                     = "Managed by Terraform"
}

resource "snowflake_schema" "layer" {
  for_each = toset(["RAW", "STAGING", "MARTS"])

  database = snowflake_database.analytics.name
  name     = each.key
}

resource "snowflake_grant_privileges_to_account_role" "database_usage" {
  for_each = local.roles

  account_role_name = snowflake_account_role.functional[each.key].name
  privileges        = ["USAGE"]

  on_account_object {
    object_type = "DATABASE"
    object_name = snowflake_database.analytics.name
  }
}

# Every warehouse is created through the module, so none can exist without a resource monitor.
module "warehouse" {
  source   = "./modules/warehouse"
  for_each = var.warehouses

  name                 = "${local.prefix}_${each.key}_WH"
  size                 = each.value.size
  auto_suspend_seconds = each.value.auto_suspend_seconds
  monthly_credit_quota = each.value.monthly_credit_quota
  usage_roles          = [for r in each.value.users : snowflake_account_role.functional[r].name]
}
