import json
import logging
import os
import requests
import boto3
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize a Secrets Manager client
secretsmanager_client = boto3.client('secretsmanager')

# Initialize a DynamoDB client
dynamodb_client = boto3.client('dynamodb')

# DynamoDB table names
render_table_name = 'Render'
user_sessions_table_name = 'UserSessions'
render_requests_table_name = 'RenderRequests'
generate_status_table_name = 'GenerateStatus'

def get_secret(secret_name):
    try:
        response = secretsmanager_client.get_secret_value(SecretId=secret_name)
        secret_dict = json.loads(response['SecretString'])  # Parse the secret string as JSON
        return secret_dict  # Return the whole secret dictionary
    except Exception as e:
        logger.error(f"Error fetching secret: {secret_name} - {e}")
        raise e

def lambda_handler(event, context):
    try:

        # Fetch the API key from Secrets Manager
        secrets_generator = get_secret('Generator')
        api_key = secrets_generator['apiKey']  # Access the API key using the 'apiKey' key

        # Correct handling of event 'body'
        if 'body' in event:
            event_body = json.loads(event['body'])
        else:
            event_body = event  # Use directly if there's no 'body'

        render_id = event_body.get('renderId')
        
        if not render_id:
            logger.error("No 'renderId' found in the event")
            return {'statusCode': 400, 'body': json.dumps({'error': 'No renderId provided'})}
            
        # Update before invoking Lambda B
        dynamodb_client.update_item(
            TableName=generate_status_table_name,
            Key={'renderId': {'S': render_id}},
            UpdateExpression='SET renderStatus = :statusVal',
            ExpressionAttributeValues={
                ':statusVal': {'N': '25'},  # Updating status to 25%
            }
        )
        
        response = dynamodb_client.get_item(
            TableName=render_requests_table_name,
            Key={'renderId': {'S': render_id}}
        )
        
        item = response.get('Item')
        if not item:
            logger.error(f"No item found with renderId: {render_id} in RenderRequests table")
            return {'statusCode': 404, 'body': json.dumps({'error': 'renderId not found in RenderRequests'})}

        # Fetch the templates from Secrets Manager
        template_with_photo = get_secret('PromptTemplateWithPhoto')['promptTemplate']
        template_without_photo = get_secret('PromptTemplateWithoutPhoto')['promptTemplate']
    except Exception as e:
        logger.error(f"An error occurred while fetching secrets: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'An unexpected error occurred while fetching secrets'})
        }
    
    # Extract parameters from the event object, assuming it's a JSON payload
    body = json.loads(event['body'])
    hero = body['hero']
    personality = body['personality']
    sport = body['sport']
    color = body['color']
    action = body['action']
    uploaded_image_description = body.get('uploaded_image_description')
    connection_id = body['connectionId']  # The userId is the connectionId

    # Insert the renderId and options into the DynamoDB table
    try:
        dynamodb_client.put_item(
            TableName=render_table_name,
            Item={
                'renderId': {'S': render_id},
                'options': {'M': {
                    'hero': {'S': hero},
                    'personality': {'S': personality},
                    'sport': {'S': sport},
                    'color': {'S': color},
                    'action': {'S': action}  # Assuming action is a dictionary that needs to be converted to a JSON string
                }},
                'status': {'S': 'pending'},  # Initial status
                'connectionId': {'S': connection_id}  # Store the connectionId
            }
        )
        logger.info(f"Inserted item with renderId={render_id} into DynamoDB table {render_table_name}")
    except ClientError as e:
        logger.error(f"Failed to insert item into DynamoDB: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Failed to insert item into DynamoDB'})
        }

    api_url = 'https://api.openai.com/v1/images/generations'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    # Construct the prompt depending on whether an uploaded image description is provided
    if uploaded_image_description:
        final_prompt = template_with_photo.format(character=uploaded_image_description, personality=personality, sport=sport, color=color, action=action)
    else:
        final_prompt = template_without_photo.format(hero=hero, action=action, personality=personality, sport=sport, color=color)

    # Log the generated prompt on the server side
    logging.info(f"Generated Prompt: {final_prompt}")

    # Construct the data payload for the API request
    data = {
        "model": "dall-e-3",
        "prompt": final_prompt,
        "n": 1,
        "size": "1024x1024",
        "quality": "hd",
        "style": "vivid"
    }

    response = requests.post(api_url, headers=headers, data=json.dumps(data))

    # Check if response status is a success
    if response.status_code == 200:
        # Update after saving images to S3 but before invoking Lambda C
        dynamodb_client.update_item(
            TableName=generate_status_table_name,
            Key={'renderId': {'S': render_id}},
            UpdateExpression='SET renderStatus = :statusVal',
            ExpressionAttributeValues={
                ':statusVal': {'N': '65'}, 
            }
        )

        logger.info("OpenAI API call successful.")
        # Parse the JSON response safely
        response_json = response.json()
        # Safely access the image URL
        image_url = response_json.get('data', [{}])[0].get('url', '')  # Provide defaults to avoid KeyError or TypeError

        # Update the status in the DynamoDB table to 'completed'
        try:
            dynamodb_client.update_item(
                TableName=render_table_name,
                Key={'renderId': {'S': render_id}},
                UpdateExpression='SET #status_alias = :status',  # Use an alias
                ExpressionAttributeNames={
                    '#status_alias': 'status'  # Alias mapping
                },
                ExpressionAttributeValues={
                    ':status': {'S': 'completed'}
                }
            )
            logger.info(f"Updated item status in DynamoDB: renderId={render_id}")
        except ClientError as e:
            logger.error(f"Failed to update item status in DynamoDB: {e}")
            # Handle error as needed

        # Return the correct response
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'image_url': image_url  # Return the image URL
            })
        }
    else:
        logger.error(f"OpenAI API call failed with status code {response.status_code}: {response.text}")
        # Return a descriptive error message
        return {
            'statusCode': response.status_code,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Failed to call OpenAI API'})
        }
