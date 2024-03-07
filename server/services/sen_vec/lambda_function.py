import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Assuming you have the same API Gateway setup
api_gw_client = boto3.client('apigatewaymanagementapi', endpoint_url='YOUR_API_GATEWAY_ENDPOINT')

def lambda_handler(event, context):
    connection_id = event.get('connectionId')
    render_id = event.get('renderId')
    message_content = event.get('message', 'Vector image processing complete. Please fetch vector images.')
    action = event.get('action', 'fetch_vector_images')

    if not connection_id or not render_id:
        logger.error("Missing connectionId or renderId")
        return {'statusCode': 400, 'body': json.dumps({'error': 'Missing connectionId or renderId'})}

    # Compose the message with specific instructions for vector images
    message = {
        'message': message_content,
        'status': 'ProcessingComplete',
        'renderId': render_id,
        'connectionId': connection_id,
        'action': action  # This could be used by the client to determine the next steps
    }

    try:
        logger.info(f"Sending vector image processing completion message to connectionId: {connection_id}")
        api_gw_client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(message)
        )
        return {'statusCode': 200, 'body': json.dumps({'success': True})}
    except api_gw_client.exceptions.GoneException:
        logger.error("Connection ID no longer valid")
        return {'statusCode': 410, 'body': json.dumps({'error': 'Connection gone'})}
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}

