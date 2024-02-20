import json
import boto3
import logging

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the boto3 clients for DynamoDB and API Gateway Management API
dynamodb = boto3.resource('dynamodb')
api_gateway_client = boto3.client('apigatewaymanagementapi', endpoint_url='https://0pgyxaha81.execute-api.us-east-1.amazonaws.com/prod/')
lambda_client = boto3.client('lambda')

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
    
    # Prepare the payload for invoking Lambda A
    payload = {
        "requestContext": {
            "connectionId": connection_id
        }
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName='arn:aws:lambda:us-east-1:905418180959:function:sen_msg', 
            InvocationType='Event', # Use 'Event' for asynchronous execution
            Payload=json.dumps(payload),
        )
        logger.info(f"Invoked Lambda A for connectionId {connection_id} with response: {response}")
    except Exception as e:
        logger.error(f"Error invoking Lambda A for connectionId {connection_id}: {str(e)}")
        raise e
    
    return {'statusCode': 200}

