import json
import logging
import os
import requests
import boto3
from io import BytesIO

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Boto3 clients
secretsmanager_client = boto3.client('secretsmanager')
s3_client = boto3.client('s3')

# S3 bucket name and target folder
BUCKET_NAME = 'draft-images-bucket'
TARGET_FOLDER = 'image_2x'

# Function to get the API key from AWS Secrets Manager
def get_secret():
    secret_name = 'Upscaler'
    try:
        response = secretsmanager_client.get_secret_value(SecretId=secret_name)
        secret_dict = json.loads(response['SecretString'])
        return secret_dict['apiKey']  # Return the API key
    except Exception as e:
        logger.error(f"Error fetching secret: '{secret_name}' - {e}")
        raise e

def upload_to_s3(bucket, key, image_content):
    # Upload image to S3
    s3_client.put_object(Body=image_content, Bucket=bucket, Key=key, ContentType='image/png')

def lambda_handler(event, context):
    # Retrieve the API key from AWS Secrets Manager
    api_key = get_secret()

    # Assuming the 'filename' is passed in the event, which includes the original extension
    original_filename = event['filename']
    
    # Add "2x" suffix to the original filename (before the extension)
    base_filename, file_extension = os.path.splitext(original_filename)
    upscaled_filename = f"{base_filename}2x{file_extension}"

    # Define the key for the original and upscaled images in the S3 bucket
    original_key = os.path.join(FOLDER_NAME, original_filename)
    upscaled_key = os.path.join(TARGET_FOLDER, upscaled_filename)

    # Assuming the image URL is passed in the event
    image_url = event['image_url']
    response = requests.get(image_url)
    if response.status_code == 200:
        # The content could be saved back to S3 or processed further as needed
        upload_to_s3(BUCKET_NAME, upscaled_key, response.content)

        return {
            'statusCode': 200,
            'body': json.dumps({'message': f"Upscaled image saved to {upscaled_key} successfully"})
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to download image'})
        }

