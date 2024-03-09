import boto3
import json
import os

# Initialize AWS S3 client and DynamoDB resource
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Fetch table name from environment variable
table_name = os.getenv('RenderRequests')  # Ensure this environment variable is correctly set
table = dynamodb.Table(table_name)

# CORS headers
cors_headers = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept',
}

def generate_presigned_url(bucket, key, expiration=3600):
    """Generates a presigned URL for an S3 object."""
    try:
        url = s3_client.generate_presigned_url('get_object',
                                               Params={'Bucket': bucket, 'Key': key},
                                               ExpiresIn=expiration)
    except Exception as e:
        print(f"Error generating pre-signed URL: {e}")
        return None
    return url

def lambda_handler(event, context):
    render_id = event.get('queryStringParameters', {}).get('renderId')
    if not render_id:
        return {
            'statusCode': 400,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Missing renderId'})
        }
    
    try:
        response = table.get_item(Key={'renderId': render_id})
        item = response.get('Item', {})
        if not item:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'message': 'Data not found'})
            }
        
        # Extract the bucket name and key from the S3 path for vector images
        vector_image_path = item.get('imageVectorUrl', '')
        watermarked_vector_image_path = item.get('imageWatermarkVectorUrl', '')
        
        # Assuming the format is "s3://{bucket}/{key}"
        vector_bucket, vector_key = vector_image_path.replace("s3://", '').split('/', 1)
        watermarked_vector_bucket, watermarked_vector_key = watermarked_vector_image_path.replace("s3://", '').split('/', 1)

        # Generate pre-signed URLs
        vector_image_url = generate_presigned_url(vector_bucket, vector_key)
        watermarked_vector_image_url = generate_presigned_url(watermarked_vector_bucket, watermarked_vector_key)
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'vectorImageUrl': vector_image_url,  # Changed from vector_image_url to vectorImageUrl
        	'watermarkedVectorImageUrl': watermarked_vector_image_url,  # Changed from watermarked_vector_image_url to watermarkedVectorImageUrl
                'filename': item.get('filename', '')  # Assuming the filename is still relevant
            })
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Internal server error'})
        }

