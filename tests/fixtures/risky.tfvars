environment         = "dev"
data_retention_days = 1

warehouses = {
  TRANSFORM = {
    size                 = "XLARGE"
    auto_suspend_seconds = 3600
    monthly_credit_quota = 900
    users                = ["TRANSFORMER", "ACCOUNTADMIN"]
  }
}
