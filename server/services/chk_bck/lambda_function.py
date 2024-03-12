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
table_name = os.environ['TABLE_NAME']  # Ensure the environment variable is correctly set.
vector_status_table_name = 'VectorStatus'

def is_background_white(image_bytes, threshold=0.9):
    # Check if the image has a predominantly white background.
    with Image.open(BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        border_width = 10
        width, height = img.size
        white_pixels = 0

        for y in range(height):
            for x in range(width):
                if x < border_width or x >= width - border_width or y < border_width or y >= height - border_width:
                    r, g, b = img.getpixel((x, y))
                    if r > 245 and g > 245 and b > 245:  # Adjust for different shades of white
                        white_pixels += 1

        total_border_pixels = (width * border_width * 2) + ((height - 2 * border_width) * border_width * 2)
        white_proportion = white_pixels / total_border_pixels

        return white_proportion >= threshold

def get_image_location_from_dynamodb(render_id, table_name):
    # Fetch the image location from the DynamoDB table.
    table = dynamodb.Table(table_name)
    response = table.get_item(Key={'renderId': render_id})
    if 'Item' in response:
        return response['Item'].get('upscaledImageUrl')
    else:
        logger.info(f"No item found for renderId: {render_id}")
        return None
    
def update_vector_status(render_id, status):
    # Function to update the VectorStatus in DynamoDB using a hardcoded table name
    table = dynamodb.Table(vector_status_table_name)
    response = table.update_item(
        Key={'renderId': render_id},
        UpdateExpression='SET vectorStatus = :val',
        ExpressionAttributeValues={':val': status},
        ReturnValues="UPDATED_NEW"
    )
    logger.info(f"VectorStatus updated for renderId: {render_id} to {status}%")

def lambda_handler(event, context):
    logger.info(f"Received event: {event}")

    try:
        # Attempt to decode the nested Payload body from the received event.
        payload_body = json.loads(event.get('Payload', {}).get('body', '{}'))
    except json.JSONDecodeError as e:
        logger.error("Failed to decode JSON from the event's Payload body.")
        return {'statusCode': 400, 'body': json.dumps({'error': "Bad JSON in event's Payload body."})}

    render_id = payload_body.get('renderId')

    if render_id:
        upscaled_image_url = get_image_location_from_dynamodb(render_id, table_name)
        update_vector_status(render_id, 9)

        if upscaled_image_url:
            # Parse the S3 bucket and key from the URL
            bucket_name = upscaled_image_url.split('/')[2]
            key = '/'.join(upscaled_image_url.split('/')[3:])

            try:
                # Fetch the image from S3
                response = s3_client.get_object(Bucket=bucket_name, Key=key)
                image_content = response['Body'].read()

                # Check if the background is white
                white_background = is_background_white(image_content)

                # Log before updating DynamoDB
                logger.info(f"Updating DynamoDB for renderId: {render_id} with whiteBackground: {white_background}")

                # Update the DynamoDB table
                table = dynamodb.Table(table_name)
                update_response = table.update_item(
                    Key={'renderId': render_id},
                    UpdateExpression='SET whiteBackground = :val',
                    ExpressionAttributeValues={
                        ':val': white_background
                    },
                    ReturnValues="UPDATED_NEW"
                )

                # Log after updating DynamoDB successfully
                logger.info(f"DynamoDB update successful for renderId: {render_id}, response: {update_response}")
                update_vector_status(render_id, 33)

                return {
		    'statusCode': 200,
		    'renderId': render_id,
		    'message': 'Background check completed successfully',
		    'whiteBackground': white_background  # Now directly accessible at the top level
		}

            except Exception as e:
                logger.error(f"Error fetching image from S3: {str(e)}")
                raise e
        else:
            return {'statusCode': 404, 'body': json.dumps({'error': 'Upscaled image URL not found'})}
    else:
        # Modified error log for clarity on what's missing in the event.
        logger.error("Event object's Payload body does not contain 'renderId'.")
        return {'statusCode': 400, 'body': json.dumps({'error': "Event object's Payload body does not contain 'renderId'."})}
