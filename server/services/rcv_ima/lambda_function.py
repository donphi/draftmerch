import boto3
import json
import os

# Initialize a DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = os.getenv('RenderRequests')  # Ensure this environment variable is set
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    # Extract 'connectionId' from the query string parameters
    connection_id = event['queryStringParameters']['connectionId']
    
    try:
        # Fetch item from DynamoDB
        response = table.get_item(
            Key={'connectionId': connection_id}
        )
        item = response.get('Item', {})
        
        # Check if item is found
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
