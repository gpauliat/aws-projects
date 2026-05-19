variable "aws_region" {}
variable "project_name" {}
variable "environment" {}
variable "cognito_callback_urls" {}
variable "cognito_logout_urls" {}
variable "allowed_ip" {
  description = "The IP address allowed to access the application (CIDR notation, e.g. 203.0.113.50/32)"
  type        = string
}
