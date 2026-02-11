# Essential outputs for application configuration

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = aws_cognito_user_pool.main.id
}

output "cognito_user_pool_client_id" {
  description = "Cognito User Pool Client ID"
  value       = aws_cognito_user_pool_client.main.id
}

output "api_gateway_invoke_url" {
  description = "API Gateway invoke URL"
  value       = "${aws_api_gateway_stage.main.invoke_url}"
}