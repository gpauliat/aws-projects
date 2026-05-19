import json
import boto3
import os
import sys
import logging
from contextlib import closing

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(json.dumps(event, indent = 4))
    output_folder = os.environ['output_folder']
    if not output_folder.endswith('/'):
        output_folder += '/'
    
    file_in = event["Records"][0]["s3"]["object"]["key"] #get the file name

    bucket_name = event["Records"][0]["s3"]["bucket"]["name"] #get the bucket name

    s3 = boto3.client('s3')

    polly_client = boto3.client('polly')
      
    text = s3.get_object(Bucket=bucket_name, Key=file_in)['Body'].read().decode('utf-8')
    
    file_out = file_in.split('/')[-1] #removes the prefix (textes/)

    file_out = file_out.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('.txt', '')
    file_out = file_out + '.mp3'

    response = polly_client.synthesize_speech(VoiceId='Joanna',
                                            LanguageCode='en-US',
                                            OutputFormat='mp3',
                                            TextType='text',
                                            Text = text)


    # Access the audio stream from the response
    if "AudioStream" in response:
        # Note: Closing the stream is important because the service throttles on the
        # number of parallel connections. Here we are using contextlib.closing to
        # ensure the close method of the stream object will be called automatically
        # at the end of the with statement's scope.
        with closing(response["AudioStream"]) as stream:
            output = os.path.join('/tmp', file_out)
            try:
                # Open a file for writing the output as a binary stream
                with open(output, "wb") as file:
                    file.write(stream.read())
            except IOError as error:
                # Could not write to file, exit gracefully
                print(error)
                sys.exit(-1)
    else:
        # The response didn't contain audio data, exit gracefully
        print("Could not stream audio")
        sys.exit(-1)

    s3.upload_file('/tmp/' + file_out, bucket_name,  output_folder + file_out )

    # Send SNS notification
    sns = boto3.client('sns')
    topic_arn = os.environ['sns_topic_arn']
    
    sns.publish(
        TopicArn=topic_arn,
        Message=f"Audio file {file_out} has been successfully generated from {file_in}",
        Subject="Text-to-Speech Conversion Complete"
    )

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
