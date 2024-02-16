import json
import logging
from datetime import datetime
from PIL import Image
from io import BytesIO
import boto3
import requests

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS Lambda client, S3 client, and DynamoDB client
lambda_client = boto3.client('lambda')
s3_client = boto3.client('s3')
dynamodb_client = boto3.client('dynamodb')

# Bucket name
bucket_name = 'draft-images-bucket'

# DynamoDB table names
user_sessions_table_name = 'UserSessions'
render_requests_table_name = 'RenderRequests'
render_table_name = 'Render'  # Name of the table where renderId and options are stored

def generate_presigned_url(bucket, key, expiration=3600):
    # Generate a pre-signed URL to share an S3 object
    try:
        url = s3_client.generate_presigned_url('get_object',
                                               Params={'Bucket': bucket, 'Key': key},
                                               ExpiresIn=expiration)
    except Exception as e:
        logger.error(f"Error generating pre-signed URL: {e}")
        return None
    return url

def upload_to_s3(bucket, key, image):
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)  # Reset buffer position

    # Upload to S3
    s3_client.upload_fileobj(buffer, bucket, key, ExtraArgs={'ContentType': 'image/png'})
    
    # Generate a pre-signed URL for the uploaded image
    return generate_presigned_url(bucket, key)

def lambda_handler(event, context):
    logger.info(f'Event: {event}')
    
    # Initialize render_id as None or a default value at the start
    render_id = None
    
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept'
    }

    try:
        # Adjusted to check for 'httpMethod' in event
        http_method = event.get('httpMethod')
        if http_method == 'OPTIONS':
            return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'CORS preflight response'})}

        if http_method and http_method != 'POST':
            return {'statusCode': 405, 'headers': headers, 'body': json.dumps({'error': 'Method not allowed'})}

        # Direct Lambda invocation adaptation
        body = event if not http_method else json.loads(event['body'])
        
        # Check if 'requestContext' exists in the event, before extracting connectionId
        if 'requestContext' in event:
            connection_id = event['requestContext'].get('connectionId')
        else:
            # Handle the case where requestContext is not available
            logger.error("requestContext not found in event")
            # Decide on how to handle this error; you might want to stop execution or set a default value
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'error': 'requestContext not found'})}

        # Generate unique renderId
        render_id = str(datetime.utcnow().timestamp()).replace('.', '')

        # Insert initial record into DynamoDB
        dynamodb_client.put_item(
            TableName=render_requests_table_name,
            Item={
                'renderId': {'S': render_id},
                'connectionId': {'S': connection_id},
                'originalImageUrl': {'S': ''},  # To be updated after image processing
                'watermarkedImageUrl': {'S': ''},  # To be updated after image processing
                'status': {'S': 'pending'}
            }
        )
        
        # Invoke the image generation Lambda function
        response = lambda_client.invoke(
            FunctionName='gen_ima',
            InvocationType='RequestResponse',
            Payload=json.dumps({'body': json.dumps(body)})
        )

        response_payload = json.loads(response['Payload'].read().decode("utf-8"))
        logger.info(f'gen_ima response payload: {response_payload}')

        if 'statusCode' in response_payload and response_payload['statusCode'] == 200:
            gen_ima_result = json.loads(response_payload['body'])
            image_url = gen_ima_result.get('image_url')
            
            response = requests.get(image_url)
            response.raise_for_status()

            original_image = Image.open(BytesIO(response.content)).convert('RGBA')
            filename = f"{render_id}.png"
            original_image_key = f"image_original/{filename}"
            watermarked_image_key = f"watermarked_image/(Watermark) {filename}"

            original_image_url = upload_to_s3(bucket_name, original_image_key, original_image)

            watermark_image_key = "watermark/watermark.png"
            watermark_response = s3_client.get_object(Bucket=bucket_name, Key=watermark_image_key)
            watermark_image = Image.open(watermark_response['Body']).convert('RGBA')
            watermark_image = watermark_image.resize(original_image.size, Image.LANCZOS)

            watermarked_image = Image.alpha_composite(original_image, watermark_image).convert('RGB')
            watermarked_image_url = upload_to_s3(bucket_name, watermarked_image_key, watermarked_image)

            # After processing and uploading the original and watermarked images, update the DynamoDB table
            dynamodb_client.update_item(
                TableName=render_requests_table_name,
                Key={'renderId': {'S': render_id}},
                UpdateExpression='SET originalImageUrl = :origUrl, watermarkedImageUrl = :waterUrl, status = :status',
                ExpressionAttributeValues={
                    ':origUrl': {'S': original_image_url},
                    ':waterUrl': {'S': watermarked_image_url},
                    ':status': {'S': 'completed'}
                }
            )

            # Return a successful response
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'original_image_url': original_image_url,
                    'watermarked_image_url': watermarked_image_url,
                    'filename': filename
                })
            }
        else:
            logger.error(f"Error calling gen_ima Lambda function: {response_payload}")
            return {
                'statusCode': response_payload.get('statusCode', 500),
                'headers': headers,
                'body': json.dumps({'error': 'Error calling gen_ima Lambda function'})
            }

    except Exception as e:
        logger.exception(f"Exception occurred: {e}")
        # Update DynamoDB table with error status
        dynamodb_client.update_item(
            TableName=render_requests_table_name,
            Key={'renderId': {'S': render_id}},
            UpdateExpression='SET status = :status',
            ExpressionAttributeValues={
                ':status': {'S': 'error'}
            }
        )
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}