terraform {
  required_version = ">= 1.6"

  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 1.0"
    }
  }

  # State lives in a remote backend, configured per environment with -backend-config.
  backend "s3" {}
}

# Credentials come from SNOWFLAKE_* environment variables (key-pair auth in CI).
provider "snowflake" {
  role = var.terraform_role
}
