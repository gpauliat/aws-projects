# Integration Tests

## Overview

The integration tests in `test_integration_e2e.py` validate the complete Movie Download Wishlist application against deployed AWS infrastructure.

## Prerequisites

1. **Deployed Infrastructure**: Ensure all AWS resources are deployed via Terraform
2. **Python Dependencies**: Install required packages:
   ```bash
   pip install -r lambda/requirements.txt
   ```
3. **AWS Credentials**: Configure AWS credentials with access to the deployed resources

## Running the Tests

### Option 1: Using PowerShell Script (Windows)

```powershell
# Set execution policy if needed (run as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run the test script
.\lambda\tests\run_integration_tests.ps1
```

### Option 2: Manual Configuration (Cross-platform)

#### On Windows (PowerShell):
```powershell
cd terraform
$env:AWS_REGION = terraform output -raw aws_region
$env:USER_POOL_ID = terraform output -raw cognito_user_pool_id
$env:CLIENT_ID = terraform output -raw cognito_user_pool_client_id
$env:API_ENDPOINT = terraform output -raw api_gateway_invoke_url
$env:MOVIES_TABLE_NAME = terraform output -raw dynamodb_movies_table_name
$env:INTERESTS_TABLE_NAME = terraform output -raw dynamodb_interests_table_name
cd ..

pytest lambda/tests/test_integration_e2e.py -v
```

#### On Linux/Mac (Bash):
```bash
cd terraform
export AWS_REGION=$(terraform output -raw aws_region)
export USER_POOL_ID=$(terraform output -raw cognito_user_pool_id)
export CLIENT_ID=$(terraform output -raw cognito_user_pool_client_id)
export API_ENDPOINT=$(terraform output -raw api_gateway_invoke_url)
export MOVIES_TABLE_NAME=$(terraform output -raw dynamodb_movies_table_name)
export INTERESTS_TABLE_NAME=$(terraform output -raw dynamodb_interests_table_name)
cd ..

pytest lambda/tests/test_integration_e2e.py -v
```

Or source the bash script:
```bash
source lambda/tests/integration_test_config.sh
pytest lambda/tests/test_integration_e2e.py -v
```

## Test Coverage

The integration tests cover:

### 1. Complete User Flow (TestEndToEndUserFlow)
- User authentication
- Adding movies
- Marking movies as downloaded
- Adding/removing interest
- Deleting movies

### 2. Multi-User Scenarios (TestMultiUserScenarios)
- Multiple users interacting with the same movie
- Concurrent status updates
- Interest tracking across users

### 3. Data Consistency (TestDataConsistency)
- Referential integrity (deleting movies removes interests)
- Input validation (empty titles rejected)
- Invalid status transitions rejected

### 4. Authentication (TestAuthenticationFlow)
- Unauthenticated access denied
- Invalid tokens rejected
- Valid authentication grants access

## Test Data Cleanup

The tests automatically:
- Create temporary test users in Cognito
- Clean up test data before and after each test
- Delete test users after test completion

## Troubleshooting

### Authentication Errors
- Verify Cognito User Pool and Client IDs are correct
- Check AWS credentials have permissions to create/delete Cognito users

### API Errors
- Verify API Gateway endpoint is correct and deployed
- Check Lambda functions are deployed and have correct permissions
- Review CloudWatch logs for Lambda function errors

### DynamoDB Errors
- Verify table names are correct
- Check AWS credentials have DynamoDB read/write permissions
- Ensure tables exist and are in ACTIVE state

