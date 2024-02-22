import boto3
import os
import json
from PIL import Image
from io import BytesIO

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def is_background_white(image_bytes, threshold=0.9):
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

def lambda_handler(event, context):
    # Extract information from the event
    print(f"Received event: {event}")
    bucket_name = os.environ['bucketName']
    payload_body = event['Payload']['body']
    decoded_body = json.loads(payload_body)
    render_id = decoded_body['renderId']
    table_name = os.environ['RenderRequests']

    # Fetch the image from S3
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=render_id)
        image_content = response['Body'].read()
    except Exception as e:
        print(f"Error fetching image from S3: {str(e)}")
        raise e

    # Check if the background is white
    white_background = is_background_white(image_content)

    # Update the DynamoDB table
    try:
        table = dynamodb.Table(table_name)
        table.update_item(
            Key={'renderId': render_id},
            UpdateExpression='SET whiteBackground = :val',
            ExpressionAttributeValues={
                ':val': white_background
            },
            ReturnValues="UPDATED_NEW"
        )
    except Exception as e:
        print(f"Error updating DynamoDB: {str(e)}")
        raise e

    # Prepare the return statement to include renderId for the next step
    return {
        'renderId': render_id,
        'whiteBackground': white_background
    }
