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
render_requests_table_name = 'RenderRequests'

def generate_presigned_url(bucket, key, expiration=3600):
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
    
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept'
    }
    
    # Initialize render_id early to ensure it's accessible throughout the function
    render_id = str(datetime.utcnow().timestamp()).replace('.', '')

    try:
        # Body extraction, handling both API Gateway and direct invocations
        if 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event  # Assuming direct invocation provides necessary data directly
            
        connection_id = body.get('connectionId')
        
        if not connection_id:
            logger.error("connectionId not provided")
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'error': 'connectionId not provided'})}

        dynamodb_client.put_item(
            TableName=render_requests_table_name,
            Item={
                'renderId': {'S': render_id},
                'connectionId': {'S': connection_id},
                'originalImageUrl': {'S': ''},
                'watermarkedImageUrl': {'S': ''},
                'status': {'S': 'pending'},
                'options': {  # Including nested fields right from the start.
                    'M': {
                        'hero': {'S': body.get('hero', 'N/A')},
                        'personality': {'S': body.get('personality', 'N/A')},
                        'sport': {'S': body.get('sport', 'N/A')},
                        'color': {'S': body.get('color', 'N/A')},
                        'action': {'S': body.get('action', 'N/A')},
                        'uploaded_image_description': {'S': body.get('uploaded_image_description', 'N/A')}
                    }
                }
            }
        )

        # Ensure the connection_id and render_id are correctly assigned
        # as per your earlier code.

        # Payload correction - both connectionId and renderId included properly
        response = lambda_client.invoke(
            FunctionName='gen_ima',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'body': json.dumps({
                    'connectionId': connection_id,
                    'renderId': render_id,
                    # Including other expected fields
                    'hero': body.get('hero'),
                    'personality': body.get('personality'),
                    'sport': body.get('sport'),
                    'color': body.get('color'),
                    'action': body.get('action'),
                    'uploaded_image_description': body.get('uploaded_image_description'),
                })
            })
        )

        response_payload = json.loads(response['Payload'].read().decode("utf-8"))
        logger.info(f'gen_ima response payload: {response_payload}')

        if 'statusCode' in response_payload and response_payload['statusCode'] == 200:
            gen_ima_result = json.loads(response_payload['body'])
            image_url = gen_ima_result.get('image_url')

            response = requests.get(image_url)
            response.raise_for_status()

            original_image = Image.open(BytesIO(response.content)).convert('RGBA')
            filename = formatted_filename(body['hero'], body['personality'], body['sport'], body['color'], body['action'])
            original_image_key = f"image_original/{filename}"
            watermarked_image_key = f"watermarked_image/(Watermark) {filename}"

            original_image_url = upload_to_s3(bucket_name, original_image_key, original_image)

            watermark_image_key = "watermark/watermark.png"
            watermark_response = s3_client.get_object(Bucket=bucket_name, Key=watermark_image_key)
            watermark_image = Image.open(watermark_response['Body']).convert('RGBA')
            watermark_image = watermark_image.resize(original_image.size, Image.LANCZOS)

            watermarked_image = Image.alpha_composite(original_image, watermark_image).convert('RGB')
            watermarked_image_url = upload_to_s3(bucket_name, watermarked_image_key, watermarked_image)

            dynamodb_client.update_item(
                TableName=render_requests_table_name,
                Key={'renderId': {'S': render_id}},
                UpdateExpression='SET originalImageUrl = :origUrl, watermarkedImageUrl = :waterUrl, #status = :statusVal',
                ExpressionAttributeValues={
                    ':origUrl': {'S': original_image_url},
                    ':waterUrl': {'S': watermarked_image_url},
                    ':statusVal': {'S': 'completed'}
                },
                ExpressionAttributeNames={
                    '#status': 'status'
                }
            )

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
            return {'statusCode': response_payload.get('statusCode', 500), 'headers': headers, 'body': json.dumps({'error': 'Error calling gen_ima Lambda function'})}

    except Exception as e:
        logger.exception(f"Exception occurred: {e}")
        dynamodb_client.update_item(
            TableName=render_requests_table_name,
            Key={'renderId': {'S': render_id}},
            UpdateExpression='SET #status = :statusVal',
            ExpressionAttributeValues={
                ':statusVal': {'S': 'error'}
            },
            ExpressionAttributeNames={
                '#status': 'status'
            }
        )
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}

def formatted_filename(hero, personality, sport, color, action):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename_parts = [hero, personality, sport, color, action, timestamp]
    filename = "_".join(filter(None, filename_parts)) + ".png"
    filename = "".join(c for c in filename if c.isalnum() or c in " _-.")
    return filename