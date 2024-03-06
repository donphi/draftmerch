import boto3
import requests
import json
from urllib.parse import urlparse
import logging

dynamodb = boto3.resource('dynamodb')
secretsmanager = boto3.client('secretsmanager')
s3 = boto3.client('s3')

# Function to remove background - updated with Secrets Manager integration
def remove_background_image(api_key, api_secret, filename, original_image_path):
    background_removal_url = "https://api.pixian.ai/api/v2/remove-background"
    background_removal_params = {
        "test": "false",
        "output.format": "png",
        "output.jpeg_quality": 75
    }
    
    # Since original_image_path now contains the binary data of the image, adjust accordingly
    files = {'image': (filename, original_image_path, 'image/png')}
    
    response = requests.post(
        url=background_removal_url,
        auth=(api_key, api_secret),
        files=files,
        params=background_removal_params
    )
    
    if response.status_code == requests.codes.ok:
        return True, response.content  # Return content as binary
    else:
        logging.error(f"Error during background removal API call: {response.status_code}, {response.text}")
        return False, None

def lambda_handler(event, context):
    # Initialize the response payload
    next_step_payload = {
        'renderId': event.get('renderId'),  # Use .get() to avoid KeyError if 'renderId' is not present
        'message': event.get('message')     # Use .get() to avoid KeyError if 'message' is not present
    }

    try:
        renderId = next_step_payload['renderId']
        if renderId is None:
            raise ValueError("renderId not provided in the event.")
        
        # Retrieve secret
        secret_name = "Backgroundremover"
        secret = secretsmanager.get_secret_value(SecretId=secret_name)
        credentials = json.loads(secret['SecretString'])
        
        # The API key is the value of the unique key in your secret
        api_key = credentials.get('apiKey')
        api_secret = credentials.get('apiSecret')
        
        # Look up in the DynamoDB table for upscaledImageUrl
        table = dynamodb.Table('RenderRequests')
        response = table.get_item(Key={'renderId': renderId})
        if 'Item' in response:
            item = response['Item']
            if 'upscaledImageUrl' in item and 'filename' in item:
                upscaled_image_url = item['upscaledImageUrl']
                filename = item['filename']
            else:
                logging.error(f"Missing 'upscaledImageUrl' or 'filename' for renderId: {renderId}")
                next_step_payload['error'] = "Missing 'upscaledImageUrl' or 'filename'."
                return next_step_payload
        else:
            logging.error(f"No item found with renderId: {renderId}")
            next_step_payload['error'] = "Item not found."
            return next_step_payload
        
        # Parse the S3 bucket and object key from the S3 URL
        parsed_url = urlparse(upscaled_image_url)
        bucket_name = parsed_url.netloc
        object_key = parsed_url.path.lstrip('/')
        
        # Get the image from S3
        original_image = s3.get_object(Bucket=bucket_name, Key=object_key)
        original_image_path = original_image['Body'].read()
        
        # Remove background from the image
        background_removed, new_image = remove_background_image(api_key, api_secret, filename, original_image_path)
        
        if background_removed:
            # Define new S3 path
            new_path = f"image_no_background/{filename}.png"
            
            # Save the new image without background to S3
            s3.put_object(Bucket='draft-image-bucket', Key=new_path, Body=new_image)
            
            # Update DynamoDB with the new image URL
            new_image_url = f"s3://draft-image-bucket/{new_path}"
            table.update_item(
                Key={'renderId': renderId},
                UpdateExpression='SET imageNoBackgroundUrl = :val1',
                ExpressionAttributeValues={
                    ':val1': new_image_url
                }
            )
        else:
            next_step_payload['error'] = "Failed to remove background."
            return next_step_payload
    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
        next_step_payload['error'] = str(e)
        return next_step_payload
    
    # Pass renderId and message to the next Lambda / step
    return next_step_payload