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
    
    # Log the connectionId being disconnected
    logger.info(f"Disconnecting connectionId: {connection_id}")
    
    # Update the connection ID in DynamoDB to mark it as inactive instead of deleting it
    response = table.update_item(
        Key={'connectionId': connection_id},
        UpdateExpression='SET isActive = :val',
        ExpressionAttributeValues={':val': False}
    )
    
    # Log the response from DynamoDB
    logger.info(f"DynamoDB response: {response}")
    
    return {'statusCode': 200, 'body': 'Disconnected.'}
