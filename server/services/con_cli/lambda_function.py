import json
import boto3
import logging

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the boto3 clients for DynamoDB and API Gateway Management API
dynamodb = boto3.resource('dynamodb')
api_gateway_client = boto3.client('apigatewaymanagementapi', endpoint_url='https://0pgyxaha81.execute-api.us-east-1.amazonaws.com/prod/')

TABLE_NAME = 'UserSessions'

def lambda_handler(event, context):
    connection_id = event['requestContext']['connectionId']
    
    # Log the received connectionId
    logger.info(f"Received connectionId: {connection_id}")
    
    # Store the connection ID in DynamoDB and mark it as active
    table = dynamodb.Table(TABLE_NAME)
    response = table.put_item(Item={'connectionId': connection_id, 'isActive': True})
    
    # Log the response from DynamoDB
    logger.info(f"DynamoDB response: {response}")
    
    # Send a welcome message back to the client
    try:
        welcome_message = {
            'message': 'Welcome! Connection established successfully.',
            'connectionId': connection_id
        }
        api_gateway_client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(welcome_message)
        )
        logger.info(f"Welcome message sent to {connection_id}")
    except Exception as e:
        logger.error(f"Error sending welcome message to {connection_id}: {str(e)}")
        raise e
    
    return {'statusCode': 200}

