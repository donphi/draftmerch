import boto3
import json
import os

# Initialize a DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = os.getenv('RenderRequests')  # Ensure this environment variable is set
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    # Extract 'renderId' from the query string parameters
    render_id = event.get('queryStringParameters', {}).get('renderId')
    
    if not render_id:
        return {'statusCode': 400, 'body': json.dumps({'message': 'Missing renderId'})}
    
    try:
        # Fetch item from DynamoDB using renderId
        response = table.get_item(Key={'renderId': render_id})
        item = response.get('Item', {})
        
        if not item:
            return {'statusCode': 404, 'body': json.dumps({'message': 'Data not found'})}
        
        # Structure response to be sent back to the client
        return {
            'statusCode': 200,
            'body': json.dumps({
                'original_image_url': item.get('originalimageurl', ''),
                'watermarked_image_url': item.get('watermarkedimageurl', ''),
                'filename': item.get('filename', '')
            })
        }
    except Exception as e:
        print(e)
        return {'statusCode': 500, 'body': json.dumps({'message': 'Internal server error'})}