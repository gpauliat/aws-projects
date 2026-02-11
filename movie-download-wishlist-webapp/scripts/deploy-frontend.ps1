# Frontend Deployment Script for Movie Download Wishlist (PowerShell)
# This script deploys the frontend to S3 and invalidates CloudFront cache

# Exit on error
$ErrorActionPreference = "Stop"

# Function to print colored output
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

# Check if AWS CLI is installed
try {
    $null = Get-Command aws -ErrorAction Stop
} catch {
    Write-Error-Custom "AWS CLI is not installed. Please install it first."
    exit 1
}

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$FrontendDir = Join-Path $ProjectRoot "frontend"
$TerraformDir = Join-Path $ProjectRoot "terraform"

Write-Info "Starting frontend deployment..."

# Check if frontend directory exists
if (-not (Test-Path $FrontendDir)) {
    Write-Error-Custom "Frontend directory not found at $FrontendDir"
    exit 1
}

# Check if terraform directory exists
if (-not (Test-Path $TerraformDir)) {
    Write-Error-Custom "Terraform directory not found at $TerraformDir"
    exit 1
}

# Get S3 bucket name and CloudFront distribution ID from Terraform outputs
Write-Info "Getting deployment configuration from Terraform..."
Push-Location $TerraformDir

try {
    $S3Bucket = terraform output -raw s3_frontend_bucket_name 2>$null
    $CloudFrontId = terraform output -raw cloudfront_distribution_id 2>$null
    $CloudFrontUrl = terraform output -raw cloudfront_distribution_url 2>$null
} catch {
    Write-Error-Custom "Could not get Terraform outputs. Make sure you have run 'terraform apply' first."
    Pop-Location
    exit 1
}

Pop-Location

if ([string]::IsNullOrEmpty($S3Bucket) -or [string]::IsNullOrEmpty($CloudFrontId)) {
    Write-Error-Custom "Could not get Terraform outputs. Make sure you have run 'terraform apply' first."
    exit 1
}

Write-Info "S3 Bucket: $S3Bucket"
Write-Info "CloudFront Distribution ID: $CloudFrontId"

# Sync frontend files to S3
Write-Info "Syncing frontend files to S3..."
aws s3 sync $FrontendDir "s3://$S3Bucket" `
    --exclude "README.md" `
    --exclude ".git*" `
    --exclude "*.sh" `
    --exclude "*.ps1" `
    --delete `
    --cache-control "public, max-age=3600"

if ($LASTEXITCODE -ne 0) {
    Write-Error-Custom "Failed to sync frontend files to S3"
    exit 1
}

Write-Info "Frontend files synced successfully!"

# Set specific cache control for HTML files (shorter cache)
Write-Info "Setting cache control for HTML files..."
$IndexPath = Join-Path $FrontendDir "index.html"
aws s3 cp $IndexPath "s3://$S3Bucket/index.html" `
    --cache-control "public, max-age=300" `
    --content-type "text/html"

# Invalidate CloudFront cache
Write-Info "Invalidating CloudFront cache..."
$InvalidationOutput = aws cloudfront create-invalidation `
    --distribution-id $CloudFrontId `
    --paths "/*" `
    --query 'Invalidation.Id' `
    --output text

if ($LASTEXITCODE -ne 0) {
    Write-Error-Custom "Failed to create CloudFront invalidation"
    exit 1
}

$InvalidationId = $InvalidationOutput
Write-Info "CloudFront invalidation created: $InvalidationId"
Write-Info "Waiting for invalidation to complete (this may take a few minutes)..."

aws cloudfront wait invalidation-completed `
    --distribution-id $CloudFrontId `
    --id $InvalidationId

if ($LASTEXITCODE -eq 0) {
    Write-Info "CloudFront cache invalidated successfully!"
} else {
    Write-Warning-Custom "Invalidation is in progress. It may take a few minutes to complete."
}

# Print deployment URL
Write-Host ""
Write-Info "=========================================="
Write-Info "Deployment completed successfully!"
Write-Info "=========================================="
Write-Info "Frontend URL: $CloudFrontUrl"
Write-Info "=========================================="
Write-Host ""
Write-Warning-Custom "Remember to update the configuration in app.js with:"
Write-Warning-Custom "  - User Pool ID"
Write-Warning-Custom "  - Client ID"
Write-Warning-Custom "  - API Gateway endpoint"
Write-Host ""
