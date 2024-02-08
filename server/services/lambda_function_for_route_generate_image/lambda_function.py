import json
import boto3
import requests
from datetime import datetime
from PIL import Image
from io import BytesIO

# Initialize AWS clients for Lambda and S3
s3_client = boto3.client('s3')
lambda_client = boto3.client('lambda')

# Environment Variables or hardcoded values
WATERMARK_BUCKET_NAME = "draft-images-bucket"
WATERMARK_KEY = "watermark/watermark.png"
IMAGE_BUCKET_NAME = "draft-images-bucket"

def lambda_handler(event, context):
    if event['httpMethod'] != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Method not allowed'})
        }

    try:
        body = json.loads(event['body'])

        # Invoke the gen_ima Lambda function to generate the image
        response = lambda_client.invoke(
            FunctionName='GenImaFunctionName', # Replace with the actual name of the gen_ima Lambda function
            InvocationType='RequestResponse',
            Payload=json.dumps(body)
        )

        # Parse the response payload
        gen_ima_result = json.load(response['Payload'])

        if gen_ima_result['statusCode'] == 200:
            image_url = gen_ima_result['body']['image_url']  # Assuming this is how the URL is returned
            
            # Download the original image using the URL
            response = requests.get(image_url)
            response.raise_for_status()  # Raises an HTTPError if the status is 4xx, 5xx
            original_image = Image.open(BytesIO(response.content)).convert('RGBA')

            # Generate filenames
            filename = formatted_filename(body['hero'], body['personality'], body['sport'], body['color'], body['action'])

            # Save the original image in S3
            original_image_buffer = BytesIO()
            original_image.save(original_image_buffer, format='PNG')
            original_image_key = f"original_image/{filename}.png"
            s3_client.put_object(
                Bucket=IMAGE_BUCKET_NAME,
                Key=original_image_key,
                Body=original_image_buffer.getvalue(),
                ContentType='image/png'
            )

            # Get the watermark image from S3
            watermark_object = s3_client.get_object(Bucket=WATERMARK_BUCKET_NAME, Key=WATERMARK_KEY)
            watermark_image = Image.open(BytesIO(watermark_object['Body'].read())).convert('RGBA')
            
            watermark_image = watermark_image.resize(original_image.size, Image.ANTIALIAS)
            watermarked_image = Image.alpha_composite(original_image, watermark_image).convert('RGB')

            # Save the watermarked image in S3
            watermarked_imag_buffer = BytesIO()
            watermarked_image.save(watermarked_imag_buffer, format='PNG')
            watermarked_image_key = f"watermarked_image/(watermark){filename}.png"
            s3_client.put_object(
                Bucket=IMAGE_BUCKET_NAME,
                Key=watermarked_image_key,
                Body=watermarked_imag_buffer.getvalue(),
                ContentType='image/png'
            )

            # Construct URLs for the images in S3
            watermarked_image_url = f"""https://{IMAGE_BUCKET_NAME}.s3.amazonaws.com/{watermarked_image_key}"""

            # Return success response
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'watermarked_image_url': watermarked_image_url
                })
            }

        else:
            # Handle error from gen_ima function
            return {
                'statusCode': gen_ima_result['statusCode'],
                'body': json.dumps({'error': 'Error calling gen_ima Lambda function'}),
                'headers': {'Content-Type': 'application/json'}
            }

    except requests.RequestException as e:
        # Handle image download failure
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {'Content-Type': 'application/json'}
        }

    except Exception as e:
        # Handle general errors
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {'Content-Type': 'application/json'}
        }

def formatted_filename(hero, personality, sport, color, action):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename_parts = [hero, personality, sport, color, action, timestamp]
    filename = "_".join(filter(None, filename_parts)) + ".png"
    # Remove any illegal file characters if necessary
    filename = "".join(c for c in filename if c.isalnum() or c in " _-.")
    return filename