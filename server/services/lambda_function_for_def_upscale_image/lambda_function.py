import json
import logging
import os
import requests
import boto3
from uuid import uuid4

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Boto3 clients
secretsmanager_client = boto3.client('secretsmanager')
s3_client = boto3.client('s3')
dynamodb_client = boto3.resource('dynamodb')

# DynamoDB table name
TABLE_NAME = os.environ.get('TABLE_NAME', 'ImageProcessingQueue')

# S3 bucket name and target folder
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'draft-images-bucket')
TARGET_FOLDER = os.environ.get('TARGET_FOLDER', 'image_2x')

# Step Functions state machine ARN
STATE_MACHINE_ARN = os.environ.get('arn:aws:states:us-east-1:905418180959:stateMachine:MyStateMachine-nsbofpjm5')

# Function to get the API key from AWS Secrets Manager
def get_secret():
    secret_name = os.environ.get('UPSCALER_SECRET_NAME', 'Upscaler')
    try:
        response = secretsmanager_client.get_secret_value(SecretId=secret_name)
        secret_dict = json.loads(response['SecretString'])
        return secret_dict['apiKey']  # Return the API key
    except Exception as e:
        logger.error(f"Error fetching secret: {secret_name} - {e}")
        raise e

def upload_to_s3(bucket, key, image_content):
    # Upload image to S3
    s3_client.put_object(Body=image_content, Bucket=bucket, Key=key, ContentType='image/png')

def update_dynamodb(job_id, update_info):
    table = dynamodb_client.Table(TABLE_NAME)
    table.update_item(
        Key={'jobId': job_id},
        UpdateExpression='SET ' + ', '.join(f"{k} = :{k}" for k in update_info),
        ExpressionAttributeValues={f":{k}": v for k, v in update_info.items()},
        ReturnValues="UPDATED_NEW"
    )

def upscale_image(api_key, image_url):
    url = "https://ai-picture-upscaler.p.rapidapi.com/supersize-image"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "ai-picture-upscaler.p.rapidapi.com"
    }
    payload = {
        "sizeFactor": "2",
        "imageStyle": "default",
        "noiseCancellationFactor": "0"
    }
    files = {'image': requests.get(image_url).content}
    response = requests.post(url, data=payload, files=files, headers=headers)
    return response

def start_step_function_execution(job_id, upscaled_key):
    # Start a new execution of the Step Functions state machine
    input_payload = json.dumps({
        'jobId': job_id,
        'upscaledImageKey': upscaled_key
    })
    response = stepfunctions_client.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=job_id,  # Using the job ID as the execution name
        input=input_payload
    )
    return response

def lambda_handler(event, context):
    # Retrieve the API key from AWS Secrets Manager
    api_key = get_secret()

    # Generate a unique jobId
    job_id = str(uuid4())

    # Assuming the 'filename' is passed in the event, which includes the original extension
    original_filename = event['filename']
    
    # Add "2x" suffix to the original filename (before the extension)
    base_filename, file_extension = os.path.splitext(original_filename)
    upscaled_filename = f"{base_filename}2x{file_extension}"

    # Define the key for the upscaled image in the S3 bucket
    upscaled_key = os.path.join(TARGET_FOLDER, upscaled_filename)

    # Assuming the image URL is passed in the event
    image_url = event['image_url']

    # Insert a new item into the DynamoDB table with the initial job status
    dynamodb_client.Table(TABLE_NAME).put_item(
        Item={
            'jobId': job_id,
            'filename': original_filename,
            'status': 'UPSCALING',
            'originalImageUrl': image_url,
            'upscaledImageUrl': '',  # Will be updated after upscaling
            'processedImageUrl': ''  # Will be updated after background removal
        }
    )

    # Call the upscaling API
    response = upscale_image(api_key, image_url)
    if response.status_code == 200:
        # The content could be saved back to S3 or processed further as needed
        upload_to_s3(BUCKET_NAME, upscaled_key, response.content)

        # Update the DynamoDB table with the upscaled image URL and status
        update_dynamodb(
            job_id,
            {
                'upscaledImageUrl': f"s3://{BUCKET_NAME}/{upscaled_key}",
                'status': 'UPSCALED'
            }
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f"Upscaled image saved to {upscaled_key} successfully",
                'jobId': job_id  # Return the jobId for tracking
                'stepFunctionExecutionArn': sf_response['executionArn']
            })
        }
    else:
        # Log the error and return a 500 error response
        logger.error(f"Failed to upscale image. Status code: {response.status_code}, Response: {response.text}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to upscale image'})
        }
