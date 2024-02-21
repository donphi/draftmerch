import boto3
import json
import os

# Initialize a DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = os.getenv('RenderRequests')  # Ensure this environment variable is set correctly
table = dynamodb.Table(table_name)

# Define a common set of CORS headers for all responses
cors_headers = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',  # Allows access from any origin, adjust as necessary
    'Access-Control-Allow-Methods': 'GET, OPTIONS',  # Adjust based on the methods your Lambda function should support
    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept',
}

def lambda_handler(event, context):
    # Extract 'renderId' from the query string parameters
    render_id = event.get('queryStringParameters', {}).get('renderId')
    
    if not render_id:
        return {
            'statusCode': 400,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Missing renderId'})
        }
    
    try:
        # Fetch item from DynamoDB using renderId
        response = table.get_item(Key={'renderId': render_id})
        item = response.get('Item', {})
        
        if not item:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'message': 'Data not found'})
            }
        
        # Structure response to be sent back to the client
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'original_image_url': item.get('originalImageUrl', ''),
                'watermarked_image_url': item.get('watermarkedImageUrl', ''),
                'filename': item.get('filename', '')
            })
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Internal server error'})
        }
