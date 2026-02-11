#!/bin/bash
# Configuration for integration tests
# Source this file before running integration tests: source lambda/tests/integration_test_config.sh

# Get values from Terraform outputs
cd terraform

export AWS_REGION=$(terraform output -raw aws_region)
export USER_POOL_ID=$(terraform output -raw cognito_user_pool_id)
export CLIENT_ID=$(terraform output -raw cognito_user_pool_client_id)
export API_ENDPOINT=$(terraform output -raw api_gateway_invoke_url)
export MOVIES_TABLE_NAME=$(terraform output -raw dynamodb_movies_table_name)
export INTERESTS_TABLE_NAME=$(terraform output -raw dynamodb_interests_table_name)

cd ..

echo "Integration test environment configured:"
echo "  AWS_REGION: $AWS_REGION"
echo "  USER_POOL_ID: $USER_POOL_ID"
echo "  CLIENT_ID: $CLIENT_ID"
echo "  API_ENDPOINT: $API_ENDPOINT"
echo "  MOVIES_TABLE_NAME: $MOVIES_TABLE_NAME"
echo "  INTERESTS_TABLE_NAME: $INTERESTS_TABLE_NAME"
echo ""
echo "Run tests with: pytest lambda/tests/test_integration_e2e.py -v"
