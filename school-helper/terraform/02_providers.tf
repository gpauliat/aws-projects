provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Owner = "gautier"
      Environment = var.environment
    }
  }
}
