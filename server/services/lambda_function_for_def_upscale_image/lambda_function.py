import json
import logging
import os
import requests
import boto3

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Boto3 clients
secretsmanager_client = boto3.client('secretsmanager')
s3_client = boto3.client('s3')

# S3 bucket name and folder
BUCKET_NAME = 'draft-images-bucket'
FOLDER_NAME = 'image_original'

# AWS Lambda supports /tmp for temporary storage
UPLOAD_FOLDER = '/tmp/image_original'

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

def upscale_image(filename, api_key):
    url = "https://ai-picture-upscaler.p.rapidapi.com/supersize-image"

    # Ensure the directory exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # Full path for the image to be saved locally in Lambda's /tmp directory
    local_image_path = os.path.join(UPLOAD_FOLDER, filename)

    # Download the image from S3 to Lambda's temporary storage
    s3_client.download_file(BUCKET_NAME, os.path.join(FOLDER_NAME, filename), local_image_path)

    # Read the original image and prepare the request data
    with open(local_image_path, 'rb') as f:
        files = {"image": f}
        payload = {
            "sizeFactor": "2",
            "imageStyle": "default",
            "noiseCancellationFactor": "0"
        }
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "ai-picture-upscaler.p.rapidapi.com"
        }

        # Make the POST request to the upscaling API
        response = requests.post(url, data=payload, files=files, headers=headers)

    # Check if the response is OK
    if response.status_code == 200:
        # The content could be saved back to S3 or processed further as needed
        return True, response.content
    else:
        logger.error(f"Failed to upscale image. Status: {response.status_code}, Response: {response.text}")
        return False, None

def lambda_handler(event, context):
    # Retrieve the API key from AWS Secrets Manager
    api_key = get_secret()

    # Assuming the 'filename' is passed in the event
    filename = event['filename']
    success, upscaled_image_content = upscale_image(filename, api_key)

    if success:
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Image upscaled successfully'})
            # You can also return the image content or save it to S3 and return the URL
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to upscale image'})
        }
