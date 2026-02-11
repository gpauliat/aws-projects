resource "aws_sns_topic" "sns-topic-polly" {
  name = "gautier-text-to-speech"
}

resource "aws_sns_topic_subscription" "email_subscription" {
    count = length(var.email_adresses)
    topic_arn = aws_sns_topic.sns-topic-polly.arn
    protocol  = "email"
    endpoint  = var.email_adresses[count.index]
}

