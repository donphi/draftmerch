import boto3
import json
import os

# Initialize the API Gateway Management API client
api_gateway_client = boto3.client('apigatewaymanagementapi', endpoint_url='https://0pgyxaha81.execute-api.us-east-1.amazonaws.com/prod/')

def lambda_handler(event, context):
    for record in event['Records']:
        if record['eventName'] in ('INSERT', 'MODIFY'):
            new_image = record['dynamodb']['NewImage']
            render_id = new_image['renderId']['S']
            render_status = int(new_image['renderStatus']['N'])
            
            message = {
                "type": "generateStatus",
                "renderId": render_id,
                "renderStatus": render_status
            }
            # Logic to send this message to the appropriate WebSocket client(s)
            # Based on your setup, this could involve invoking another service or 
            # a component that handles message routing to clients.
            send_update(message)

def send_update(message):
    # Placeholder function where you'd implement sending the message to your WebSocket server
    # or service capable of routing the message based on renderId to the correct client.
    pass

