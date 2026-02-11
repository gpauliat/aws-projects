# Terraform and Provider Configuration

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }

  # Remote state backend configuration
  # Useful for: team collaboration, state locking, backup protection, CI/CD, and working from multiple machines
  # Uncomment and configure after creating the S3 bucket and DynamoDB table
  # backend "s3" {
  #   bucket         = "movie-wishlist-terraform-state"
  #   key            = "terraform.tfstate"
  #   region         = "eu-west-3"
  #   dynamodb_table = "movie-wishlist-terraform-locks"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = merge(
      {
        Project     = var.project_name
        Environment = var.environment
        ManagedBy   = "Terraform"
      },
      var.tags
    )
  }
}
