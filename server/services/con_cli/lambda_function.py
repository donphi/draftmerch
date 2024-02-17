import json
import boto3
import logging

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the boto3 clients for DynamoDB and API Gateway Management API
dynamodb = boto3.resource('dynamodb')
api_gateway_client = boto3.client('apigatewaymanagementapi', endpoint_url='https://0pgyxaha81.execute-api.us-east-1.amazonaws.com/prod/')

# Specify your DynamoDB table name
TABLE_NAME = 'UserSessions'
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    connection_id = event['requestContext']['connectionId']
    
    # Store the connection ID in DynamoDB
    try:
        response = table.put_item(
            Item={
                'connectionId': connection_id
            }
        )
        logger.info(f"DynamoDB put_item response: {response}")
    except Exception as e:
        logger.error(f"Error storing connection ID in DynamoDB: {str(e)}")
        raise e
    
    # Send a response message back to the client
    try:
        response_message = {
            'message': 'This is a response from sendMessage.',
            'connectionId': connection_id
        }
        api_gateway_client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(response_message)
        )
        logger.info(f"Message sent to {connection_id}")
    except Exception as e:
        logger.error(f"Error sending message to {connection_id}: {str(e)}")
        raise e

    return {'statusCode': 200}

