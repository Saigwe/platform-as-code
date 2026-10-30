environment         = "dev"
data_retention_days = 1

warehouses = {
  TRANSFORM = {
    size                 = "XSMALL"
    auto_suspend_seconds = 60
    monthly_credit_quota = 60
    users                = ["TRANSFORMER"]
  }
  REPORTING = {
    size                 = "XSMALL"
    auto_suspend_seconds = 60
    monthly_credit_quota = 30
    users                = ["REPORTER"]
  }
  LOADING = {
    size                 = "XSMALL"
    auto_suspend_seconds = 60
    monthly_credit_quota = 30
    users                = ["LOADER"]
  }
}
