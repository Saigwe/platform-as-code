variable "name" {
  description = "Warehouse name"
  type        = string
}

variable "size" {
  description = "Warehouse size"
  type        = string

  validation {
    condition     = contains(["XSMALL", "SMALL", "MEDIUM", "LARGE"], var.size)
    error_message = "Use XSMALL to LARGE. Bigger sizes need a FinOps review and a module change."
  }
}

variable "auto_suspend_seconds" {
  description = "Idle seconds before the warehouse suspends"
  type        = number

  validation {
    condition     = var.auto_suspend_seconds >= 60 && var.auto_suspend_seconds <= 600
    error_message = "Auto-suspend must be between 60 and 600 seconds."
  }
}

variable "monthly_credit_quota" {
  description = "Credits per month before the warehouse is suspended"
  type        = number
}

variable "usage_roles" {
  description = "Roles granted USAGE and OPERATE on the warehouse"
  type        = list(string)
}
