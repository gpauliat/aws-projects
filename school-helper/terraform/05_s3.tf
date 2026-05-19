# S3 Buckets

# PDF storage bucket
resource "aws_s3_bucket" "pdf_storage" {
  bucket_prefix = "${var.project_name}-pdfs-"

  tags = {
    Name = "${var.project_name}-pdf-storage"
  }
}

resource "aws_s3_bucket_cors_configuration" "pdf_storage" {
  bucket = aws_s3_bucket.pdf_storage.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["PUT", "GET"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3600
  }
}

resource "aws_s3_object" "pdfs_folder" {
  bucket = aws_s3_bucket.pdf_storage.id
  key    = "pdfs/"
}

# Frontend hosting bucket
resource "aws_s3_bucket" "frontend" {
  bucket_prefix = "${var.project_name}-frontend-"

  tags = {
    Name = "${var.project_name}-frontend"
  }
}

resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_cloudfront_origin_access_identity" "frontend" {
  comment = "${var.project_name} frontend OAI"
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  policy = data.aws_iam_policy_document.frontend_bucket_policy.json
}

data "aws_iam_policy_document" "frontend_bucket_policy" {
  statement {
    sid    = "AllowCloudFrontAccess"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = [aws_cloudfront_origin_access_identity.frontend.iam_arn]
    }

    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.frontend.arn}/*"]
  }
}
