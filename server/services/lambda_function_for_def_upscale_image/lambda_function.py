import json
import logging
import os
import requests
import boto3
import base64
from uuid import uuid4

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Boto3 clients
secretsmanager_client = boto3.client('secretsmanager')
s3_client = boto3.client('s3')
dynamodb_client = boto3.resource('dynamodb')
stepfunctions_client = boto3.client('stepfunctions')

# DynamoDB table name
TABLE_NAME = os.environ.get('TABLE_NAME', 'ImageProcessingQueue')

# S3 bucket name and target folder
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'draft-images-bucket')
TARGET_FOLDER = os.environ.get('TARGET_FOLDER', 'image_2x')

# Step Functions state machine ARN
STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN')

# Function to get the API key from AWS Secrets Manager
def get_secret():
    secret_name = os.environ.get('UPSCALER_SECRET_NAME', 'Upscaler')
    try:
        response = secretsmanager_client.get_secret_value(SecretId=secret_name)
        secret_dict = json.loads(response['SecretString'])
        return secret_dict['apiKey']
    except Exception as e:
        logger.error(f"Error fetching secret: {secret_name} - {e}")
        raise e

def upload_to_s3(bucket, key, image_content):
    s3_client.put_object(Body=image_content, Bucket=bucket, Key=key, ContentType='image/png')

def update_dynamodb(job_id, update_info):
    table = dynamodb_client.Table(TABLE_NAME)
    expression_attribute_names = {f"#{k}": k for k in update_info.keys()}
    update_expression = 'SET ' + ', '.join(f"#{k} = :{k}" for k in update_info)
    expression_attribute_values = {f":{k}": v for k, v in update_info.items()}
    table.update_item(
        Key={'jobId': job_id},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values,
        ReturnValues="UPDATED_NEW"
    )

def upscale_image(api_key, image_url):
    url = "https://api.stability.ai/v1/generation/esrgan-v1-x2plus/image-to-image/upscale"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    files = {'image': requests.get(image_url).content}
    data = {
        "height": 2048  # Assuming you want to keep the same height as the original image
    }
    response = requests.post(url, headers=headers, files=files, data=data)
    return response

def start_step_function_execution(job_id, upscaled_key):
    input_payload = json.dumps({
        'jobId': job_id,
        'upscaledImageKey': upscaled_key
    })
    print(f"Starting execution of state machine with ARN: {STATE_MACHINE_ARN}")
    response = stepfunctions_client.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=job_id,
        input=input_payload
    )
    return response

def lambda_handler(event, context):
    # Log the received event to see what data is being passed in
    logger.info("Received event: " + json.dumps(event))

    # Check if this is the initial upscaling event
    if 'filename' in event and 'image_url' in event:
        api_key = get_secret()
        job_id = str(uuid4())
        original_filename = event['filename']
        base_filename, file_extension = os.path.splitext(original_filename)
        upscaled_filename = f"{base_filename}2x{file_extension}"
        upscaled_key = os.path.join(TARGET_FOLDER, upscaled_filename)
        image_url = event['image_url']

        dynamodb_client.Table(TABLE_NAME).put_item(
            Item={
                'jobId': job_id,
                'filename': original_filename,
                'status': 'UPSCALING',
                'originalImageUrl': image_url,
                'upscaledImageUrl': '',
                'processedImageUrl': ''
            }
        )

        response = upscale_image(api_key, image_url)
        if response.status_code == 200:
            data = response.json()
            upscaled_image_content = base64.b64decode(data["artifacts"][0]["base64"])
            upload_to_s3(BUCKET_NAME, upscaled_key, upscaled_image_content)

            update_dynamodb(
                job_id,
                {
                    'upscaledImageUrl': f"s3://{BUCKET_NAME}/{upscaled_key}",
                    'status': 'UPSCALED'
                }
            )

            #sf_response = start_step_function_execution(job_id, upscaled_key)

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': "Upscaled image saved to S3 successfully",
                    'jobId': job_id,
                    'filename': original_filename,
                    'upscaledImageUrl': f"https://{BUCKET_NAME}.s3.amazonaws.com/{upscaled_key}"
                })
            }
        else:
            # Log the error and return a 500 error response
            logger.error(f"Failed to upscale image. Status code: {response.status_code}, Response: {response.text}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to upscale image'})
            }

    else:
        # Log an error if the event doesn't contain 'filename' and 'image_url'
        logger.error("Event object does not contain 'filename' or 'image_url'.")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': "Event object does not contain 'filename' or 'image_url'."})
        }
