import json
import logging
import os
import requests
import boto3
import base64
from urllib.parse import urlparse

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Boto3 clients
secretsmanager_client = boto3.client('secretsmanager')
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Environment variables
TABLE_NAME = os.getenv('TABLE_NAME', 'RenderRequests')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'draft-images-bucket')
TARGET_FOLDER = os.getenv('TARGET_FOLDER', 'image_2x')
UPSCALER_SECRET_NAME = os.getenv('UPSCALER_SECRET_NAME', 'Upscaler')

def get_secret():
    response = secretsmanager_client.get_secret_value(SecretId=UPSCALER_SECRET_NAME)
    secret_dict = json.loads(response['SecretString'])
    return secret_dict['apiKey']

def get_item_from_dynamodb(render_id):
    table = dynamodb.Table(TABLE_NAME)
    response = table.get_item(Key={'renderId': render_id})
    if 'Item' in response:
        return response['Item']
    else:
        logger.error(f"No item found for renderId: {render_id}")
        return None

def upload_to_s3(bucket, key, image_content):
    s3_client.put_object(Body=image_content, Bucket=bucket, Key=key, ContentType='image/png')

def update_dynamodb(render_id, upscaled_image_url):
    table = dynamodb.Table(TABLE_NAME)
    response = table.update_item(
        Key={'renderId': render_id},
        UpdateExpression='SET upscaledImageUrl = :val',
        ExpressionAttributeValues={':val': upscaled_image_url},
        ReturnValues="UPDATED_NEW"
    )
    return response

def upscale_image(api_key, image_url):
    url = "https://api.stability.ai/v1/generation/esrgan-v1-x2plus/image-to-image/upscale"
    headers = {"Authorization": f"Bearer {api_key}"}
    files = {'image': requests.get(image_url).content}
    response = requests.post(url, headers=headers, files=files)
    return response

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    
    if 'renderId' in event:
        api_key = get_secret()
        render_id = event['renderId']
        item = get_item_from_dynamodb(render_id)

        if item and 'originalImageUrl' in item and 'filename' in item:
            original_image_url = item['originalImageUrl']
            original_filename = item['filename']
            response = upscale_image(api_key, original_image_url)

            if response.status_code == 200:
                upscaled_image_content = base64.b64decode(response.json()["artifacts"][0]["base64"])
                base_filename, file_extension = os.path.splitext(original_filename)
                upscaled_filename = f"{base_filename}_2x{file_extension}"
                upscaled_key = f"{TARGET_FOLDER}/{upscaled_filename}"
                upload_to_s3(BUCKET_NAME, upscaled_key, upscaled_image_content)
                upscaled_image_url = f"s3://{BUCKET_NAME}/{upscaled_key}"

                update_dynamodb(render_id, upscaled_image_url)

                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'message': "Image upscaled successfully",
                        'renderId': render_id,
                        'upscaledImageUrl': upscaled_image_url
                    })
                }
            else:
                logger.error("Failed to upscale image.")
                return {'statusCode': 500, 'body': json.dumps({'error': 'Failed to upscale image'})}
        else:
            return {'statusCode': 404, 'body': json.dumps({'error': 'Original image URL or filename not found'})}
    else:
        logger.error("Event object does not contain 'renderId'.")
        return {'statusCode': 400, 'body': json.dumps({'error': "Event object does not contain 'renderId'"})}