variable "environment" {
  description = "Environment name, used as a prefix for every object"
  type        = string

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "The environment must be dev or prod."
  }
}

variable "terraform_role" {
  description = "Role Terraform runs as. Created once by an admin with only the privileges it needs, never ACCOUNTADMIN"
  type        = string
  default     = "TERRAFORM_ADMIN"
}

variable "data_retention_days" {
  description = "Time Travel retention for the analytics database"
  type        = number
  default     = 1
}

variable "warehouses" {
  description = "One warehouse per workload, each with its own monthly credit cap and the roles allowed to use it"

  type = map(object({
    size                 = string
    auto_suspend_seconds = number
    monthly_credit_quota = number
    users                = list(string)
  }))
}
