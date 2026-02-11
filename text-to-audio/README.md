# Text-to-Speech AWS Infrastructure

This project provides an automated text-to-speech conversion system using AWS services. Upload a text file to S3, and it automatically converts it to audio using Amazon Polly, stores the result, and sends you an email notification.

## Architecture Overview

The infrastructure consists of the following AWS components:

- **S3 Bucket**: Storage for input text files and output audio files
- **Lambda Function**: Processes text files and converts them to speech
- **Amazon Polly**: AWS text-to-speech service
- **SNS Topic**: Sends email notifications when conversion is complete
- **CloudWatch Logs**: Monitors Lambda function execution

## How It Works

1. **Upload**: You upload a `.txt` file to the `text/` folder in the S3 bucket
2. **Trigger**: S3 automatically triggers the Lambda function when a new text file is detected
3. **Convert**: Lambda reads the text file and uses Amazon Polly to synthesize speech
4. **Store**: The generated MP3 audio file is saved to the `audio/` folder in the same S3 bucket
5. **Notify**: An SNS notification is sent to subscribed email addresses confirming the conversion

## Workflow Diagram

```
┌─────────────┐
│  Upload     │
│  .txt file  │
│  to text/   │
└──────┬──────┘
       │
       v
┌─────────────────┐
│   S3 Bucket     │
│   (text/)       │
└──────┬──────────┘
       │ Event Notification
       v
┌─────────────────┐
│ Lambda Function │
│  - Read text    │
│  - Call Polly   │
│  - Save audio   │
└──────┬──────────┘
       │
       ├─────────────────┐
       │                 │
       v                 v
┌─────────────┐   ┌─────────────┐
│  S3 Bucket  │   │ SNS Topic   │
│  (audio/)   │   │ Email Alert │
│  .mp3 file  │   └─────────────┘
└─────────────┘
```

## Prerequisites

- AWS Account
- Terraform installed
- AWS CLI configured with appropriate credentials

## Deployment

1. Navigate to the `terraform/` directory:
   ```bash
   cd terraform
   ```

2. Initialize Terraform:
   ```bash
   terraform init
   ```

3. Configure your variables in `terraform.tfvars`:
   - Set your email addresses for notifications
   - Adjust other variables as needed

4. Deploy the infrastructure:
   ```bash
   terraform apply
   ```

5. Confirm your email subscription by clicking the link in the confirmation email sent by AWS SNS

## Usage

1. Upload a text file to the S3 bucket's `text/` folder:
   - Via AWS Console
   - Using AWS CLI: `aws s3 cp myfile.txt s3://your-bucket-name/text/`

2. Wait for the Lambda function to process the file (usually takes a few seconds)

3. Check your email for the completion notification

4. Download the audio file from the `audio/` folder in the S3 bucket

## File Naming

The Lambda function automatically processes filenames:
- Converts to lowercase
- Replaces spaces with underscores
- Removes parentheses
- Changes extension from `.txt` to `.mp3`

Example: `My Story (Draft).txt` → `my_story_draft.mp3`

## Voice Configuration

The current setup uses:
- **Voice**: Joanna (female, US English)
- **Language**: en-US
- **Format**: MP3

To change the voice, modify the `VoiceId` and `LanguageCode` parameters in `lambda_function.py`.

## Cleanup

To destroy all resources and avoid AWS charges:

```bash
cd terraform
terraform destroy
```

## Cost Considerations

- **S3**: Storage costs for text and audio files
- **Lambda**: Free tier includes 1M requests/month
- **Amazon Polly**: Pay per character converted
- **SNS**: First 1,000 email notifications free per month

## Troubleshooting

- Check CloudWatch Logs for Lambda execution details
- Ensure your text files are in UTF-8 encoding
- Verify SNS email subscription is confirmed
- Check IAM permissions if Lambda fails to access services
