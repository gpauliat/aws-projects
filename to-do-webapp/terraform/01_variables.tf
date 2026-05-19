# Variables for To Do List infrastructure

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "eu-west-3" #Paris
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "to-do-list"
}