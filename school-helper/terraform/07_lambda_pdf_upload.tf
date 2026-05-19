# PDF Upload Lambda

data "archive_file" "pdf_upload" {
  type        = "zip"
  source_file = "${path.module}/lambdas/pdf_upload/lambda_function.py"
  output_path = "${path.module}/.build/pdf_upload.zip"
}

resource "aws_lambda_function" "pdf_upload" {
  function_name    = "${var.project_name}-pdf-upload"
  role             = aws_iam_role.pdf_upload.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.11"
  timeout          = 60
  filename         = data.archive_file.pdf_upload.output_path
  source_code_hash = data.archive_file.pdf_upload.output_base64sha256

  environment {
    variables = {
      S3_BUCKET_NAME      = aws_s3_bucket.pdf_storage.id
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.pdfs.name
      MAX_FILE_SIZE       = "52428800"
    }
  }

  depends_on = [
    aws_iam_role_policy.pdf_upload,
    aws_cloudwatch_log_group.pdf_upload,
  ]

  tags = {
    Name = "${var.project_name}-pdf-upload"
  }
}
