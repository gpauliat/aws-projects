#!/bin/bash

# Frontend Deployment Script for Movie Download Wishlist
# This script deploys the frontend to S3 and invalidates CloudFront cache

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"

print_info "Starting frontend deployment..."

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    print_error "Frontend directory not found at $FRONTEND_DIR"
    exit 1
fi

# Check if terraform directory exists
if [ ! -d "$TERRAFORM_DIR" ]; then
    print_error "Terraform directory not found at $TERRAFORM_DIR"
    exit 1
fi

# Get S3 bucket name and CloudFront distribution ID from Terraform outputs
print_info "Getting deployment configuration from Terraform..."
cd "$TERRAFORM_DIR"

S3_BUCKET=$(terraform output -raw s3_frontend_bucket_name 2>/dev/null)
CLOUDFRONT_ID=$(terraform output -raw cloudfront_distribution_id 2>/dev/null)
CLOUDFRONT_URL=$(terraform output -raw cloudfront_distribution_url 2>/dev/null)

if [ -z "$S3_BUCKET" ] || [ -z "$CLOUDFRONT_ID" ]; then
    print_error "Could not get Terraform outputs. Make sure you have run 'terraform apply' first."
    exit 1
fi

print_info "S3 Bucket: $S3_BUCKET"
print_info "CloudFront Distribution ID: $CLOUDFRONT_ID"

# Sync frontend files to S3
print_info "Syncing frontend files to S3..."
aws s3 sync "$FRONTEND_DIR" "s3://$S3_BUCKET" \
    --exclude "README.md" \
    --exclude ".git*" \
    --exclude "*.sh" \
    --delete \
    --cache-control "public, max-age=3600"

if [ $? -eq 0 ]; then
    print_info "Frontend files synced successfully!"
else
    print_error "Failed to sync frontend files to S3"
    exit 1
fi

# Set specific cache control for HTML files (shorter cache)
print_info "Setting cache control for HTML files..."
aws s3 cp "$FRONTEND_DIR/index.html" "s3://$S3_BUCKET/index.html" \
    --cache-control "public, max-age=300" \
    --content-type "text/html"

# Invalidate CloudFront cache
print_info "Invalidating CloudFront cache..."
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id "$CLOUDFRONT_ID" \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

if [ $? -eq 0 ]; then
    print_info "CloudFront invalidation created: $INVALIDATION_ID"
    print_info "Waiting for invalidation to complete (this may take a few minutes)..."
    
    aws cloudfront wait invalidation-completed \
        --distribution-id "$CLOUDFRONT_ID" \
        --id "$INVALIDATION_ID"
    
    if [ $? -eq 0 ]; then
        print_info "CloudFront cache invalidated successfully!"
    else
        print_warning "Invalidation is in progress. It may take a few minutes to complete."
    fi
else
    print_error "Failed to create CloudFront invalidation"
    exit 1
fi

# Print deployment URL
echo ""
print_info "=========================================="
print_info "Deployment completed successfully!"
print_info "=========================================="
print_info "Frontend URL: $CLOUDFRONT_URL"
print_info "=========================================="
echo ""
print_warning "Remember to update the configuration in app.js with:"
print_warning "  - User Pool ID"
print_warning "  - Client ID"
print_warning "  - API Gateway endpoint"
echo ""
