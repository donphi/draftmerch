import boto3
import logging

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the boto3 client for DynamoDB
dynamodb = boto3.resource('dynamodb')

# Specify your DynamoDB table name
TABLE_NAME = 'UserSessions'
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    connection_id = event['requestContext']['connectionId']
    
    # Log the received connectionId
    logger.info(f"Received connectionId: {connection_id}")
    
    # Store the connection ID in DynamoDB and mark it as active
    response = table.put_item(Item={'connectionId': connection_id, 'isActive': True})
    
    # Log the response from DynamoDB
    logger.info(f"DynamoDB response: {response}")
    
    return {'statusCode': 200}

