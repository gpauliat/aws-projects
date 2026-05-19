# Knowledge Base Sync Lambda

data "archive_file" "kb_sync" {
  type        = "zip"
  source_file = "${path.module}/lambdas/kb_sync/lambda_function.py"
  output_path = "${path.module}/.build/kb_sync.zip"
}

resource "aws_lambda_function" "kb_sync" {
  function_name    = "${var.project_name}-kb-sync"
  role             = aws_iam_role.kb_sync.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.11"
  timeout          = 300
  filename         = data.archive_file.kb_sync.output_path
  source_code_hash = data.archive_file.kb_sync.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.pdfs.name
      KNOWLEDGE_BASE_ID   = aws_bedrockagent_knowledge_base.this.id
      DATA_SOURCE_ID      = aws_bedrockagent_data_source.pdfs.data_source_id
    }
  }

  depends_on = [
    aws_iam_role_policy.kb_sync,
    aws_cloudwatch_log_group.kb_sync,
  ]

  tags = {
    Name = "${var.project_name}-kb-sync"
  }
}

# Allow S3 to invoke the Lambda function
resource "aws_lambda_permission" "kb_sync_s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.kb_sync.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.pdf_storage.arn
}

# Trigger Lambda on PDF uploads to the pdfs/ prefix
resource "aws_s3_bucket_notification" "pdf_upload_trigger" {
  bucket = aws_s3_bucket.pdf_storage.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.kb_sync.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "pdfs/"
    filter_suffix       = ".pdf"
  }

  depends_on = [aws_lambda_permission.kb_sync_s3]
}
