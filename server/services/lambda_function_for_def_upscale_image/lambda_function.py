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
dynamodb_client = boto3.client('dynamodb')

# Environment variables
TABLE_NAME = os.getenv('TABLE_NAME', 'RenderRequests')
TABLE_NAME_VECTOR_STATUS = 'VectorStatus'
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
    try:
        s3_client.put_object(Body=image_content, Bucket=bucket, Key=key, ContentType='image/png')
        return True
    except Exception as e:
        logger.error(f"Failed to upload image to S3: {str(e)}")
        return False

def update_dynamodb(render_id, upscaled_image_url):
    try:
        table = dynamodb.Table(TABLE_NAME)
        response = table.update_item(
            Key={'renderId': render_id},
            UpdateExpression='SET upscaledImageUrl = :val',
            ExpressionAttributeValues={':val': upscaled_image_url},
            ReturnValues="UPDATED_NEW"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to update DynamoDB: {str(e)}")
        return False

def upscale_image(api_key, image_content):
    url = "https://api.stability.ai/v1/generation/esrgan-v1-x2plus/image-to-image/upscale"
    headers = {"Authorization": f"Bearer {api_key}"}
    files = {'image': image_content}
    try:
        response = requests.post(url, headers=headers, files=files)
        if response.status_code == 200:
            return response
        else:
            logger.error(f"Failed to upscale image. Status Code: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception occurred during image upscaling: {str(e)}")
        return None
        
def update_vector_status(render_id, status, connection_id):
    try:
        update_exp = 'SET renderStatus = :val'
        exp_attr_values = {':val': {'N': str(status)}}

        if connection_id:
            update_exp += ', connectionId = :connectionId'
            exp_attr_values[':connectionId'] = {'S': connection_id}
        
        dynamodb_client.update_item(
            TableName=TABLE_NAME_VECTOR_STATUS,
            Key={'renderId': {'S': render_id}},
            UpdateExpression=update_exp,
            ExpressionAttributeValues=exp_attr_values
        )
        logger.info(f"VectorStatus updated for renderId: {render_id} to {status}%")
        return True
    except Exception as e:
        logger.error(f"Failed to update VectorStatus in DynamoDB: {str(e)}")
        return False

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Check if 'body' exists in the event
    if 'body' in event and event['body']:
        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding event body: {str(e)}")
            return {'statusCode': 400, 'body': json.dumps({'error': 'Malformed JSON body'})}

        render_id = body.get('renderId')
        connection_id = body.get('connectionId')
        
        # Ensure both renderId and connectionId are present
        if render_id and connection_id:
            api_key = get_secret()
            
            update_vector_status(render_id, 0, connection_id)
            item = get_item_from_dynamodb(render_id)

            if item and 'originalImageUrl' in item:
                parsed_url = urlparse(item['originalImageUrl'])
                key = parsed_url.path.lstrip('/')

                try:
                    # Download the image content from S3
                    image_object = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
                    image_content = image_object['Body'].read()

                    # Proceed with the upscaling using the image content
                    response = upscale_image(api_key, image_content)

                    if response and response.status_code == 200:
                        upscaled_image_content = base64.b64decode(response.json()["artifacts"][0]["base64"])
                        base_filename, file_extension = os.path.splitext(os.path.basename(key))
                        upscaled_filename = f"{base_filename}_2x{file_extension}"
                        upscaled_key = f"{TARGET_FOLDER}/{upscaled_filename}"
                        update_vector_status(render_id, 9)

                        if upload_to_s3(BUCKET_NAME, upscaled_key, upscaled_image_content):
                            upscaled_image_url = f"s3://{BUCKET_NAME}/{upscaled_key}"
                            if update_dynamodb(render_id, upscaled_image_url):
                                return {
                                    'statusCode': 200,
                                    'body': json.dumps({
                                        'message': "Image upscaled successfully",
                                        'renderId': render_id,
                                        'upscaledImageUrl': upscaled_image_url
                                    })
                                }
                            else:
                                return {'statusCode': 500, 'body': json.dumps({'error': 'Failed to update DynamoDB'})}
                        else:
                            return {'statusCode': 500, 'body': json.dumps({'error': 'Failed to upload upscaled image to S3'})}
                    else:
                        return {'statusCode': 500, 'body': json.dumps({'error': 'Failed to upscale image'})}
                except Exception as e:
                    logger.error(f"Error processing image: {str(e)}")
                    return {'statusCode': 500, 'body': json.dumps({'error': 'Error processing image'})}
            else:
                return {'statusCode': 404, 'body': json.dumps({'error': 'Original image URL or filename not found'})}
        else:
            return {'statusCode': 400, 'body': json.dumps({'error': "Missing 'renderId' or 'connectionId'"})}
    else:
        return {'statusCode': 400, 'body': json.dumps({'error': "Missing or empty 'body'"})}