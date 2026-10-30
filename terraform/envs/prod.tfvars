environment         = "prod"
data_retention_days = 7

warehouses = {
  TRANSFORM = {
    size                 = "MEDIUM"
    auto_suspend_seconds = 60
    monthly_credit_quota = 300
    users                = ["TRANSFORMER"]
  }
  REPORTING = {
    size                 = "SMALL"
    auto_suspend_seconds = 300
    monthly_credit_quota = 250
    users                = ["REPORTER"]
  }
  LOADING = {
    size                 = "XSMALL"
    auto_suspend_seconds = 60
    monthly_credit_quota = 120
    users                = ["LOADER"]
  }
}
