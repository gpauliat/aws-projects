# Script to run integration tests with proper configuration
# Usage: .\lambda\tests\run_integration_tests.ps1

Write-Host "Configuring integration test environment..." -ForegroundColor Cyan

# Get values from Terraform outputs
Push-Location terraform

try {
    $env:AWS_REGION = terraform output -raw aws_region
    $env:USER_POOL_ID = terraform output -raw cognito_user_pool_id
    $env:CLIENT_ID = terraform output -raw cognito_user_pool_client_id
    $env:API_ENDPOINT = terraform output -raw api_gateway_invoke_url
    $env:MOVIES_TABLE_NAME = terraform output -raw dynamodb_movies_table_name
    $env:INTERESTS_TABLE_NAME = terraform output -raw dynamodb_interests_table_name
    
    Pop-Location
    
    Write-Host "`nEnvironment configured:" -ForegroundColor Green
    Write-Host "  AWS_REGION: $env:AWS_REGION"
    Write-Host "  USER_POOL_ID: $env:USER_POOL_ID"
    Write-Host "  CLIENT_ID: $env:CLIENT_ID"
    Write-Host "  API_ENDPOINT: $env:API_ENDPOINT"
    Write-Host "  MOVIES_TABLE_NAME: $env:MOVIES_TABLE_NAME"
    Write-Host "  INTERESTS_TABLE_NAME: $env:INTERESTS_TABLE_NAME"
    Write-Host ""
    
    Write-Host "Running integration tests..." -ForegroundColor Cyan
    pytest lambda/tests/test_integration_e2e.py -v
    
} catch {
    Pop-Location
    Write-Host "Error: Failed to get Terraform outputs. Make sure infrastructure is deployed." -ForegroundColor Red
    exit 1
}
