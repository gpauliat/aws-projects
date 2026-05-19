# ---------------------------------------------------------------------------
# WAF — IP-based access restriction
# ---------------------------------------------------------------------------

# Provider for us-east-1 (required for CloudFront WAF WebACL)
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

# ---------------------------------------------------------------------------
# IP Set for CloudFront (CLOUDFRONT scope — must be in us-east-1)
# ---------------------------------------------------------------------------

resource "aws_wafv2_ip_set" "allowed_ip_cloudfront" {
  provider           = aws.us_east_1
  name               = "${var.project_name}-allowed-ip-cloudfront"
  scope              = "CLOUDFRONT"
  ip_address_version = "IPV4"
  addresses          = [var.allowed_ip]

  tags = {
    Name = "${var.project_name}-allowed-ip-cloudfront"
  }
}

# ---------------------------------------------------------------------------
# Web ACL for CloudFront (CLOUDFRONT scope — must be in us-east-1)
# ---------------------------------------------------------------------------

resource "aws_wafv2_web_acl" "cloudfront" {
  provider    = aws.us_east_1
  name        = "${var.project_name}-cloudfront-ip-restrict"
  scope       = "CLOUDFRONT"
  description = "Allow only the specified IP address to access the frontend"

  default_action {
    block {}
  }

  rule {
    name     = "allow-specific-ip"
    priority = 1

    action {
      allow {}
    }

    statement {
      ip_set_reference_statement {
        arn = aws_wafv2_ip_set.allowed_ip_cloudfront.arn
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.project_name}-cloudfront-allowed-ip"
    }
  }

  visibility_config {
    sampled_requests_enabled   = true
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.project_name}-cloudfront-waf"
  }

  tags = {
    Name = "${var.project_name}-cloudfront-ip-restrict"
  }
}

# ---------------------------------------------------------------------------
# IP Set for API Gateway (REGIONAL scope)
# ---------------------------------------------------------------------------

resource "aws_wafv2_ip_set" "allowed_ip_regional" {
  name               = "${var.project_name}-allowed-ip-regional"
  scope              = "REGIONAL"
  ip_address_version = "IPV4"
  addresses          = [var.allowed_ip]

  tags = {
    Name = "${var.project_name}-allowed-ip-regional"
  }
}

# ---------------------------------------------------------------------------
# Web ACL for API Gateway (REGIONAL scope)
# ---------------------------------------------------------------------------

resource "aws_wafv2_web_acl" "api_gateway" {
  name        = "${var.project_name}-apigw-ip-restrict"
  scope       = "REGIONAL"
  description = "Allow only the specified IP address to access the API"

  default_action {
    block {}
  }

  rule {
    name     = "allow-specific-ip"
    priority = 1

    action {
      allow {}
    }

    statement {
      ip_set_reference_statement {
        arn = aws_wafv2_ip_set.allowed_ip_regional.arn
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.project_name}-apigw-allowed-ip"
    }
  }

  visibility_config {
    sampled_requests_enabled   = true
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.project_name}-apigw-waf"
  }

  tags = {
    Name = "${var.project_name}-apigw-ip-restrict"
  }
}

# ---------------------------------------------------------------------------
# Associate WAF Web ACL with API Gateway Stage
# ---------------------------------------------------------------------------

resource "aws_wafv2_web_acl_association" "api_gateway" {
  resource_arn = aws_api_gateway_stage.main.arn
  web_acl_arn  = aws_wafv2_web_acl.api_gateway.arn
}
