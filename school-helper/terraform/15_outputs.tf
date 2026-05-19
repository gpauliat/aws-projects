# Output Values

output "api_gateway_url" {
  description = "The invoke URL for the Quiz Generator REST API"
  value       = aws_api_gateway_stage.main.invoke_url
}

output "cloudfront_domain_name" {
  description = "The CloudFront distribution domain name for the frontend SPA"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "cognito_user_pool_id" {
  description = "The ID of the Cognito user pool for authentication"
  value       = aws_cognito_user_pool.main.id
}

output "cognito_client_id" {
  description = "The ID of the Cognito user pool client"
  value       = aws_cognito_user_pool_client.main.id
}

output "pdf_storage_bucket" {
  description = "The name of the S3 bucket used for PDF file storage"
  value       = aws_s3_bucket.pdf_storage.id
}

output "frontend_bucket" {
  description = "The name of the S3 bucket used for frontend static hosting"
  value       = aws_s3_bucket.frontend.id
}
