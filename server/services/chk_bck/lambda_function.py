import boto3
import json
from PIL import Image
from io import BytesIO
import os
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # You can adjust this to DEBUG for more detailed output

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table_name = 'RenderRequests'

def is_background_white(image_bytes, threshold=0.9):
    logger.info("Entering is_background_white function.")  # Additional Log
    with Image.open(BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        border_width = 10
        width, height = img.size
        white_pixels = 0

        for y in range(height):
            for x in range(width):
                if x < border_width or x >= width - border_width or y < border_width or y >= height - border_width:
                    r, g, b = img.getpixel((x, y))
                    if r > 245 and g > 245 and b > 245:
                        white_pixels += 1

        total_border_pixels = (width * border_width * 2) + ((height - 2 * border_width) * border_width * 2)
        white_proportion = white_pixels / total_border_pixels

        logger.info(f"White proportion: {white_proportion}")  # Additional Log
        return white_proportion >= threshold

def get_image_location_from_dynamodb(render_id, table_name):
    logger.info(f"Fetching image location from DynamoDB for renderId: {render_id}")  # Additional Log
    table = dynamodb.Table(table_name)
    response = table.get_item(Key={'renderId': render_id})
    if 'Item' in response:
        return response['Item'].get('upscaledImageUrl')
    else:
        logger.info(f"No item found for renderId: {render_id}")  # Adjusted from print to logger.info
        return None

def lambda_handler(event, context):
    logger.info(f"Received event: {event}")
    if 'renderId' in event:
        render_id = event['renderId']
        upscaled_image_url = get_image_location_from_dynamodb(render_id, table_name)

        if upscaled_image_url:
            logger.info(f"Upscaled image URL found: {upscaled_image_url}")  # Additional Log
            bucket_name = upscaled_image_url.split('/')[2]
            key = '/'.join(upscaled_image_url.split('/')[3:])

            try:
                # Log before fetching from S3
                logger.info(f"Fetching image from S3. Bucket: {bucket_name}, Key: {key}")
                response = s3_client.get_object(Bucket=bucket_name, Key=key)
                image_content = response['Body'].read()
                
                logger.info("Checking if the background is white.")  # Additional Log
                white_background = is_background_white(image_content)

                logger.info(f"Updating DynamoDB for renderId: {render_id} with whiteBackground: {white_background}")
                try:
                    table = dynamodb.Table(table_name)
                    update_response = table.update_item(
                        Key={'renderId': render_id},
                        UpdateExpression='SET whiteBackground = :val',
                        ExpressionAttributeValues={':val': white_background},
                        ReturnValues="UPDATED_NEW"
                    )

                    logger.info(f"DynamoDB update successful for renderId: {render_id}, response: {update_response}")
                
                except Exception as e:
                    logger.error(f"Error updating DynamoDB: {str(e)}")
                    raise e
                
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'renderId': render_id,
                        'message': 'Background check completed successfully',
                        'whiteBackground': white_background
                    })
                }

            except Exception as e:
                logger.error(f"Error fetching image from S3: {str(e)}")
                raise e
        else:
            logger.info("Upscaled image URL not found.")  # Adjusted from return to logging
            return {'statusCode': 404, 'body': json.dumps({'error': 'Upscaled image URL not found'})}
    else:
        logger.info("Event object does not contain 'renderId'.")  # Adjusted from return to logging
        return {'statusCode': 400, 'body': json.dumps({'error': "Event object does not contain 'renderId'."})}