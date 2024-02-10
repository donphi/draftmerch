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

# Initialize AWS Lambda client and S3 client
lambda_client = boto3.client('lambda')
s3_client = boto3.client('s3')

# Bucket name
bucket_name = 'draft-images-bucket'

def upload_to_s3(bucket, key, image):
    # Save image in BytesIO
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)  # Move the cursor to the beginning of the file

    # Upload to S3
    s3_client.upload_fileobj(buffer, bucket, key, ExtraArgs={'ContentType': 'image/png'})

    # Return the URL for the uploaded image
    return f"https://{bucket}.s3.amazonaws.com/{key}"

def lambda_handler(event, context):
    logger.info(f'Event: {event}')

    # Initializing response headers
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept'
    }

    try:
        if event['httpMethod'] == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'CORS preflight response'})
            }

        if event['httpMethod'] != 'POST':
            return {
                'statusCode': 405,
                'headers': headers,
                'body': json.dumps({'error': 'Method not allowed'})
            }

        body = json.loads(event['body'])
        logger.info(f'Body after JSON deserialization: {body}')

        response = lambda_client.invoke(
            FunctionName='gen_ima',
            InvocationType='RequestResponse',
            Payload=json.dumps(body)
        )

        response_payload = json.loads(response['Payload'].read().decode("utf-8"))
        logger.info(f'gen_ima response payload: {response_payload}')

        if 'statusCode' in response_payload and response_payload['statusCode'] == 200:
            gen_ima_result = json.loads(response_payload['body'])
            image_url = gen_ima_result.get('image_url')
            logger.info(f'Image URL: {image_url}')

            response = requests.get(image_url)
            response.raise_for_status()

            original_image = Image.open(BytesIO(response.content)).convert('RGBA')
            filename = formatted_filename(body['hero'], body['personality'], body['sport'], body['color'], body['action'])
            original_image_key = f"image_original/{filename}"
            watermarked_image_key = f"watermarked_image/(Watermark) {filename}"

            # Upload the original image to S3
            original_image_url = upload_to_s3(bucket_name, original_image_key, original_image)

            # Get the watermark image from S3
            watermark_image_key = "watermark/watermark.png"
            watermark_response = s3_client.get_object(Bucket=bucket_name, Key=watermark_image_key)
            watermark_image = Image.open(watermark_response['Body']).convert('RGBA')
            watermark_image = watermark_image.resize(original_image.size, Image.LANCZOS)

            # Apply the watermark to the original image and upload to S3
            watermarked_image = Image.alpha_composite(original_image, watermark_image).convert('RGB')
            watermarked_image_url = upload_to_s3(bucket_name, watermarked_image_key, watermarked_image)

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
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def formatted_filename(hero, personality, sport, color, action):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename_parts = [hero, personality, sport, color, action, timestamp]
    filename = "_".join(filter(None, filename_parts)) + ".png"
    filename = "".join(c for c in filename if c.isalnum() or c in " _-.")
    return filename
