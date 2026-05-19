data aws_iam_policy_document assume_role { 
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

data aws_iam_policy_document lambda_policy {
  statement {
    sid    = "AllowPolly"
    effect = "Allow"
    actions = ["polly:*"]
    resources = ["*"]
  }

  statement {
    sid    = "AllowS3Access"
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:ListBucket"
    ]
    resources = [
      "${aws_s3_bucket.text_to_speech_bucket.arn}/*",
      aws_s3_bucket.text_to_speech_bucket.arn
    ]
  }

  statement {
    sid    = "AllowSNSPublish"
    effect = "Allow"
    actions = ["sns:Publish"]
    resources = [aws_sns_topic.sns-topic-polly.arn]
  }

  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["${aws_cloudwatch_log_group.lambda_logs.arn}:*"]
  }
}

resource aws_iam_policy lambda_policy {
  name   = "gautier_lambda_policy"
  policy = data.aws_iam_policy_document.lambda_policy.json
}

resource aws_iam_role iam_for_lambda {
  name               = "gautier_iam_for_lambda"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource aws_iam_role_policy_attachment lambda_policy_attachment {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

resource aws_cloudwatch_log_group lambda_logs {
  name              = "/aws/lambda/${var.lambda_name}"
  retention_in_days = 7
}

data archive_file lambda {
  type        = "zip"
  source_file = "lambda_function.py"
  output_path = "lambda_function_payload.zip"
}



resource aws_lambda_function text_to_speech_lambda {
  # If the file is not in the current working directory you will need to include a
  # path.module in the filename.
  filename      = data.archive_file.lambda.output_path
  function_name = var.lambda_name
  role          = aws_iam_role.iam_for_lambda.arn
  handler       = "lambda_function.lambda_handler"

  source_code_hash = data.archive_file.lambda.output_base64sha256

  runtime = "python3.11"
  timeout = 3*60 # in seconds

  environment {
    variables = {
      output_folder = "audio"
      sns_topic_arn = aws_sns_topic.sns-topic-polly.arn
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]
}