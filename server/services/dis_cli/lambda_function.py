import boto3

# Replace 'YourDynamoDBTableName' with your actual DynamoDB table name
TABLE_NAME = 'UserSessions'
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

def dis_cli(event, context):
    connection_id = event['requestContext']['connectionId']
    
    # Delete the connection ID from DynamoDB
    table.delete_item(Key={'connectionId': connection_id})
    
    return {
        'statusCode': 200,
        'body': 'Disconnected.'
    }
