import json
import boto3
from botocore.exceptions import ClientError

def fetch_secret(secret_name):
    client = boto3.client('secretsmanager')
    
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise e
    else:
        secret = get_secret_value_response['SecretString']
        return json.loads(secret)

def lambda_handler(event, context):
    # Replace 'accessGen' and 'accessRen' with your actual secret names
    secrets = {
        'accessGen': fetch_secret('accessGen'),
        'accessRen': fetch_secret('accessRen')
    }
    return {
        'statusCode': 200,
        'body': json.dumps(secrets)
    }
