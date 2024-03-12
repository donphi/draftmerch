import boto3
import json
import os

# Initialize the API Gateway Management API client outside the handler
api_gateway_client = boto3.client('apigatewaymanagementapi', endpoint_url='https://0pgyxaha81.execute-api.us-east-1.amazonaws.com/prod/')

def lambda_handler(event, context):
    for record in event['Records']:
        if record['eventName'] in ('INSERT', 'MODIFY'):
            new_image = record['dynamodb']['NewImage']
            render_id = new_image['renderId']['S']
            render_status = int(new_image['renderStatus']['N']) if 'renderStatus' in new_image else None
            
            # Here you need to have the connectionId to send the message to the correct WebSocket client
            connection_id = new_image['connectionId']['S'] if 'connectionId' in new_image else None
            
            message = {
                "type": "vectorStatus",
                "renderId": render_id,
                "renderStatus": render_status
            }
            send_update(connection_id, message)

def send_update(connection_id, message):
    try:
        # Convert the message to JSON format
        message_json = json.dumps(message)
        # Send the message to the WebSocket client with the given connection ID
        api_gateway_client.post_to_connection(ConnectionId=connection_id, Data=message_json)
    except api_gateway_client.exceptions.GoneException:
        print(f"Connection {connection_id} is gone, consider cleaning up.")
        # Optional: Delete the connection ID from DynamoDB if disconnected
    except Exception as e:
        print(f"Error sending message to WebSocket client: {e}")
        # Handle other errors here


