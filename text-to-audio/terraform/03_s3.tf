resource aws_s3_bucket text_to_speech_bucket {
  bucket_prefix = "text-to-speech-bucket"
  
  tags = {
    Name        = "My bucket"
    Environment = "Dev"
  }
}

resource "aws_s3_object" "text_folder" {
  bucket = aws_s3_bucket.text_to_speech_bucket.id
  key    = "text/" # Création du dossier text
}

resource "aws_s3_object" "audio_folder" {
  bucket = aws_s3_bucket.text_to_speech_bucket.id
  key    = "audio/" # Création du dossier audio
}


# resource aws_s3_bucket_policy text_to_speech_bucket_policy {
#   bucket = aws_s3_bucket.text_to_speech_bucket.bucket
#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Effect    = "Allow"
#         Principal = "*"
#         Action    = "s3:GetObject"
#         Resource  = aws_s3_bucket.text_to_speech_bucket.arn
#         Condition = {
#           IpAddress = {
#             "aws:SourceIp" = var.authorized_ips
#           }
#         }
#       }
#     ]
#   })
# }


resource "aws_lambda_permission" "allow_s3_invoke" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.text_to_speech_lambda.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.text_to_speech_bucket.arn
}

resource aws_s3_bucket_notification text_to_speech_bucket_notification {
  bucket = aws_s3_bucket.text_to_speech_bucket.bucket
  depends_on = [aws_lambda_permission.allow_s3_invoke]

  lambda_function {
    lambda_function_arn = aws_lambda_function.text_to_speech_lambda.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "text/"
    filter_suffix       = ".txt"
  }
}


