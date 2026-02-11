# Movie Download Wishlist - Terraform Infrastructure

This directory contains the Terraform infrastructure as code for the Movie Download Wishlist application.

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured with appropriate credentials
- AWS account with permissions to create resources

## File Structure

- `01_variables.tf` - Variable definitions
- `02_providers.tf` - Terraform and AWS provider configuration
- `terraform.tfvars` - Variable values (customize for your deployment)
- `outputs.tf` - Output definitions
- `03_cognito.tf` - Cognito User Pool and Identity Pool (to be created)
- `04_dynamodb.tf` - DynamoDB tables (to be created)
- `05_iam.tf` - IAM roles and policies (to be created)
- `06_lambda.tf` - Lambda functions (to be created)
- `07_api_gateway.tf` - API Gateway configuration (to be created)
- `08_s3_cloudfront.tf` - S3 and CloudFront for frontend (to be created)

## Getting Started

### 1. Initialize Terraform

```bash
cd terraform
terraform init
```

### 2. Configure Variables

Edit `terraform.tfvars` to set your desired configuration:
- AWS region
- Environment (dev/test/prod)
- Password policies
- Resource sizing

### 3. Plan Infrastructure

```bash
terraform plan
```

### 4. Apply Infrastructure

```bash
terraform apply
```

## Workspaces

Use Terraform workspaces to manage multiple environments:

```bash
# Create and switch to dev workspace
terraform workspace new dev
terraform workspace select dev

# Create and switch to prod workspace
terraform workspace new prod
terraform workspace select prod
```

## Remote State (Optional)

To enable remote state storage with S3 backend:

1. Create an S3 bucket for state storage
2. Create a DynamoDB table for state locking
3. Uncomment the backend configuration in `02_providers.tf`
4. Run `terraform init -migrate-state`

## Outputs

After applying, view outputs with:

```bash
terraform output
```

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning:** This will delete all resources including data in DynamoDB tables.
