variable "aws_region" {}
variable "authorized_ips" {}


variable "az" {
    type        = string
    description = "Availability zone"
    validation {
    condition     = contains(["a", "b", "c"], var.az)
    error_message = "Valid values for az are a, b and c"
  }  
}

variable "lambda_name" {}
variable "email_adresses" {}