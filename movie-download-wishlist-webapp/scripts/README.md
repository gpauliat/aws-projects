# Deployment Scripts

This directory contains deployment scripts for the Movie Download Wishlist application.

## Scripts

### deploy-frontend.sh (Linux/Mac)
Bash script to deploy the frontend to S3 and invalidate CloudFront cache.

**Usage:**
```bash
chmod +x scripts/deploy-frontend.sh
./scripts/deploy-frontend.sh
```

### deploy-frontend.ps1 (Windows)
PowerShell script to deploy the frontend to S3 and invalidate CloudFront cache.

**Usage:**
```powershell
.\scripts\deploy-frontend.ps1
```

## Prerequisites

1. **AWS CLI installed and configured**
   ```bash
   aws --version
   aws configure
   ```

2. **Terraform infrastructure deployed**
   ```bash
   cd terraform
   terraform init
   terraform apply
   ```

3. **AWS credentials configured**
   - The scripts use your default AWS CLI credentials
   - Ensure you have permissions for S3 and CloudFront operations

## What the Scripts Do

1. **Get Configuration**: Retrieves S3 bucket name and CloudFront distribution ID from Terraform outputs
2. **Sync Files**: Uploads all frontend files to S3 bucket
3. **Set Cache Control**: Configures appropriate cache headers for different file types
4. **Invalidate Cache**: Creates CloudFront invalidation to clear cached content
5. **Wait for Completion**: Waits for the invalidation to complete
6. **Display URL**: Shows the CloudFront URL where the application is accessible

## Configuration

Before deploying, make sure to update `frontend/app.js` with the correct values:

```javascript
const CONFIG = {
    region: 'eu-west-3',
    userPoolId: 'YOUR_USER_POOL_ID',  // From: terraform output cognito_user_pool_id
    clientId: 'YOUR_CLIENT_ID',        // From: terraform output cognito_user_pool_client_id
    apiEndpoint: 'YOUR_API_ENDPOINT'   // From: terraform output api_gateway_invoke_url
};
```

Get these values by running:
```bash
cd terraform
terraform output cognito_user_pool_id
terraform output cognito_user_pool_client_id
terraform output api_gateway_invoke_url
```

## Deployment Process

### First-Time Deployment

1. Deploy infrastructure:
   ```bash
   cd terraform
   terraform init
   terraform apply
   ```

2. Get configuration values:
   ```bash
   terraform output
   ```

3. Update `frontend/app.js` with the configuration values

4. Deploy frontend:
   ```bash
   # Linux/Mac
   ./scripts/deploy-frontend.sh
   
   # Windows
   .\scripts\deploy-frontend.ps1
   ```

5. Access your application at the CloudFront URL displayed

### Subsequent Deployments

After making changes to the frontend:

```bash
# Linux/Mac
./scripts/deploy-frontend.sh

# Windows
.\scripts\deploy-frontend.ps1
```

## Cache Control

The scripts set different cache control headers:

- **HTML files**: `max-age=300` (5 minutes) - Allows quick updates
- **Other files** (CSS, JS): `max-age=3600` (1 hour) - Better performance

## CloudFront Invalidation

The scripts create a CloudFront invalidation for `/*` (all files). This ensures users get the latest version immediately.

**Note**: AWS allows 1,000 free invalidation paths per month. After that, there's a small charge per path.

## Troubleshooting

### AWS CLI Not Found
Install AWS CLI:
- **Linux/Mac**: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
- **Windows**: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

### Permission Denied (Linux/Mac)
Make the script executable:
```bash
chmod +x scripts/deploy-frontend.sh
```

### Terraform Outputs Not Found
Make sure you've run `terraform apply` first:
```bash
cd terraform
terraform apply
```

### AWS Credentials Not Configured
Configure AWS CLI:
```bash
aws configure
```

### Invalidation Takes Too Long
CloudFront invalidations can take 5-15 minutes. The script waits for completion, but you can cancel (Ctrl+C) and the invalidation will continue in the background.

## Manual Deployment (Alternative)

If you prefer to deploy manually:

1. **Upload to S3:**
   ```bash
   aws s3 sync frontend/ s3://YOUR-BUCKET-NAME --delete
   ```

2. **Invalidate CloudFront:**
   ```bash
   aws cloudfront create-invalidation --distribution-id YOUR-DISTRIBUTION-ID --paths "/*"
   ```

## Security Notes

- The S3 bucket is private and only accessible via CloudFront
- CloudFront enforces HTTPS (HTTP redirects to HTTPS)
- All API calls require authentication via Cognito JWT tokens
- CORS is configured in API Gateway to only allow requests from your domain

## Performance

- CloudFront caches content at edge locations worldwide
- First request to a location may be slower (cache miss)
- Subsequent requests are served from edge cache (very fast)
- Cache invalidation ensures users get updates quickly
