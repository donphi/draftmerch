import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Assuming you have the same API Gateway setup
api_gw_client = boto3.client('apigatewaymanagementapi', endpoint_url='https://0pgyxaha81.execute-api.us-east-1.amazonaws.com/prod/')

def lambda_handler(event, context):
    connection_id = event.get('connectionId')
    render_id = event.get('renderId')
    message_content = event.get('message', 'Vector image processing complete. Please fetch vector images.')
    action = event.get('action', 'fetch_vector_images')

    # Ensure renderId is present as per requirement
    if not render_id:
        logger.error("Missing renderId")
        return {'statusCode': 400, 'body': json.dumps({'error': 'Missing renderId'})}

    # Compose the message with specific instructions for vector images
    message = {
        'message': message_content,
        'status': 'VectorComplete',
        'renderId': render_id,
        'action': action
    }

    # Only attempt WebSocket communication if connectionId is provided
    if connection_id:
        try:
            logger.info(f"Attempting to send vector image processing completion message via WebSocket.")
            api_gw_client.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(message)
            )
        except Exception as e:
            logger.error(f"An error occurred when sending message via WebSocket: {str(e)}")
            # Log the error but do not stop execution; proceed with lambda's other tasks

    # Continue with Lambda's other operations here
    # This is where you would add any additional logic that should execute regardless
    # of whether a connectionId was provided or whether the WebSocket message was successfully sent.

    # Return a success status to indicate completion of the lambda's tasks
    return {'statusCode': 200, 'body': json.dumps({'success': True, 'info': 'Operation completed, with or without WebSocket communication'})}

