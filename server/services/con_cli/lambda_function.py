import boto3

# Replace 'YourDynamoDBTableName' with your actual DynamoDB table name
TABLE_NAME = 'ClientInformation'
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

def con_cli(event, context):
    connection_id = event['requestContext']['connectionId']
    
    # Store the connection ID in DynamoDB
    table.put_item(Item={'connectionId': connection_id})
    
    return {
        'statusCode': 200,
        'body': 'Connected.'
    }
