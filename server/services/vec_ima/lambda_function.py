import boto3
import os
import logging
import requests
from PIL import Image
import cairosvg
from io import BytesIO
from urllib.parse import urlparse
import json

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb_client = boto3.client('dynamodb')
secrets_manager_client = boto3.client('secretsmanager')

# Constants for S3 bucket and folder paths
BUCKET_NAME = 'draft-images-bucket'
IMAGE_NO_BACKGROUND_FOLDER = 'image_no_background/'
IMAGE_VECTORIZED_FOLDER = 'image_vectorized/'
WATERMARK_FOLDER = 'watermark/'
WATERMARKED_VECTOR_FOLDER = 'watermarked_vector/'

# Vectorize image
def vectorize_image(api_key, api_secret, filename, image_no_background_file_path):
    logging.info("Starting image vectorization...")

    with open(image_no_background_file_path, 'rb') as image_file:
        files = {'image': (filename, image_file, 'image/png')}
        data = {
            'mode': 'production',
            'output.size.width': 1024,
            'output.size.height': 1024,
            'processing.max_colors': 30,
            'output.group_by': 'color',
            'output.curves.line_fit_tolerance': 0.1,
            'output.size.unit': 'px'
        }
        vectorization_response = requests.post(
            'https://vectorizer.ai/api/v1/vectorize',
            files=files,
            data=data,
            auth=(api_key, api_secret)
        )

    logging.info("Received response from vectorization API.")

    if vectorization_response.status_code == 200:
        logging.info("Vectorization successful.")
        return vectorization_response.content
    else:
        error_message = f"Vectorization API returned status code {vectorization_response.status_code}: {vectorization_response.text}"
        logging.error(error_message)
        return None

# Add watermark to PNG
def add_png_watermark(image_path, watermark_path, output_path):
    with Image.open(image_path) as base_image, Image.open(watermark_path) as watermark:
        base_image = base_image.convert("RGBA")
        watermark = watermark.convert("RGBA")
        watermark = watermark.resize(base_image.size, Image.LANCZOS)
        transparent_img = Image.new("RGBA", base_image.size)
        transparent_img.paste(base_image, (0, 0), base_image)
        transparent_img.paste(watermark, (0, 0), watermark)
        transparent_img.save(output_path, format="PNG")

# Convert SVG to PNG
def convert_svg_to_png(svg_content, png_path):
    cairosvg.svg2png(bytestring=svg_content, write_to=png_path, output_width=1024, output_height=1024)

def get_s3_key_from_url(url):
    parsed_url = urlparse(url)
    # Use .lstrip('/') to remove the leading slash
    return parsed_url.path.lstrip('/')

# Lambda handler function
def lambda_handler(event, context):
    try:
        # Extract renderId and message from the event
        render_id = event['renderId']

        # Retrieve the item from DynamoDB
        response = dynamodb_client.get_item(
            TableName='RenderRequests',
            Key={'renderId': {'S': render_id}}
        )
        item = response['Item']
        image_no_background_url = item['imageNoBackgroundUrl']['S']
        filename = item['filename']['S']

        # Download the image with no background from S3
        image_no_background_file_path = '/tmp/' + filename

        # Extract the S3 object key from the full URL
        object_key = get_s3_key_from_url(image_no_background_url)

        # Then use object_key for downloading the file
        image_no_background_file_path = '/tmp/' + object_key.split('/')[-1]  # If you want to keep the filename same as on S3
        s3_client.download_file(BUCKET_NAME, object_key, image_no_background_file_path)

        # Get the secrets for the vectorization API
        secret_name = "Vectorizer"
        secrets = secrets_manager_client.get_secret_value(SecretId=secret_name)
        credentials = json.loads(secrets['SecretString'])
        # The API key is the value of the unique key in your secret
        api_key, api_secret = next(iter(credentials.items()))

        # Vectorize the image
        vectorized_content = vectorize_image(api_key, api_secret, filename, image_no_background_file_path)
        if vectorized_content:
            vectorized_filename = '(Vector) ' + filename.replace('.png', '.svg')
            vectorized_file_path = '/tmp/' + vectorized_filename

            # Save the vectorized SVG file
            with open(vectorized_file_path, 'wb') as file:
                file.write(vectorized_content)
            logging.info(f"Vectorized SVG image file written successfully at: {vectorized_file_path}")

            # Convert SVG to PNG
            png_file_path = vectorized_file_path.replace('.svg', '.png')
            convert_svg_to_png(vectorized_content, png_file_path)
            logging.info("SVG to PNG conversion complete.")

            # Apply watermark to PNG
            watermark_path = '/tmp/watermark.png'
            s3_client.download_file('draft-images-bucket', 'watermark/watermark.png', watermark_path)
            watermarked_png_path = '/tmp/Watermarked_' + vectorized_filename.replace('.svg', '.png')
            add_png_watermark(png_file_path, watermark_path, watermarked_png_path)
            logging.info("Watermarked PNG image saved.")

            # Upload the vectorized and watermarked images to S3
            s3_client.upload_file(vectorized_file_path, BUCKET_NAME, IMAGE_VECTORIZED_FOLDER + vectorized_filename)
            s3_client.upload_file(watermarked_png_path, BUCKET_NAME, WATERMARKED_VECTOR_FOLDER + 'Watermarked_' + vectorized_filename.replace('.svg', '.png'))
            # Update the DynamoDB table with the new URLs
            dynamodb_client.update_item(
                TableName='RenderRequests',
                Key={'renderId': {'S': render_id}},
                UpdateExpression='SET imageVectorUrl = :imageVectorUrl, imageWatermarkVectorUrl = :imageWatermarkVectorUrl',
                ExpressionAttributeValues={
                    ':imageVectorUrl': {'S': f's3://{BUCKET_NAME}/{IMAGE_VECTORIZED_FOLDER}' + vectorized_filename},
                    ':imageWatermarkVectorUrl': {'S': f's3://{BUCKET_NAME}/{WATERMARKED_VECTOR_FOLDER}' + vectorized_filename.replace('.svg', '.png')}
                }
            )
            return {
                'statusCode': 200,
                'body': {
                    'imageVectorUrl': 's3://draft-images-bucket/image_vectorized/' + vectorized_filename,
                    'imageWatermarkVectorUrl': 's3://draft-images-bucket/watermarked_vector/Watermarked_' + vectorized_filename.replace('.svg', '.png')
                }
            }
        else:
            error_message = "Failed to vectorize image."
            logging.error(error_message)
            return {
                'statusCode': 500,
                'body': {'error': error_message}
            }

    except Exception as e:
        logging.error(str(e))
        return {
            'statusCode': 500,
            'body': {'error': str(e)}
        }

# Ensure the function is properly set up to be triggered by AWS Step Functions with the correct event structure.
