import boto3
import json
from PIL import Image
from io import BytesIO
import os

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table_name = 'RenderRequests'

def is_background_white(image_bytes, threshold=0.9):
    ##Check if the image has a predominantly white background.
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
    ##Fetch the image location from the DynamoDB table."""
    table = dynamodb.Table(table_name)
    response = table.get_item(Key={'renderId': render_id})
    if 'Item' in response:
        return response['Item'].get('upscaledImageUrl')
    else:
        print(f"No item found for renderId: {render_id}")
        return None

def lambda_handler(event, context):
    print(f"Received event: {event}")
    table_name = os.environ['TABLE_NAME']

    if 'renderId' in event:
        render_id = event['renderId']
        upscaled_image_url = get_image_location_from_dynamodb(render_id, table_name)

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
                
                # Prepare the return statement with renderId and a message for the next Lambda
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'renderId': render_id,
                        'message': 'Background check completed successfully',
                        'whiteBackground': white_background
                    })
                }

            except Exception as e:
                print(f"Error fetching image from S3: {str(e)}")
                raise e
        else:
            return {'statusCode': 404, 'body': json.dumps({'error': 'Upscaled image URL not found'})}
    else:
        return {'statusCode': 400, 'body': json.dumps({'error': "Event object does not contain 'renderId'."})}
