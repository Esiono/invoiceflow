variable "region" {
  type    = string
  default = "us-west-2"
}

variable "alert_email" {
  type        = string
  description = "Where budget alerts go."
  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.alert_email))
    error_message = "alert_email must be a valid email address."
  }
}

variable "monthly_budget_usd" {
  type    = string
  default = "25"
}

variable "owner" {
  type    = string
  default = "esiono"
}
