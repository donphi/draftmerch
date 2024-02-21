import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Assuming you have the same API Gateway setup as Lambda A
api_gw_client = boto3.client('apigatewaymanagementapi', endpoint_url='https://0pgyxaha81.execute-api.us-east-1.amazonaws.com/prod/')

def lambda_handler(event, context):
    connection_id = event.get('connectionId')
    render_id = event.get('renderId')

    if not connection_id:
        return {'statusCode': 400, 'body': json.dumps({'error': 'Missing connectionId'})}
    if not render_id:
        return {'statusCode': 400, 'body': json.dumps({'error': 'Missing renderId'})}

    # Compose your message logic here, possibly varying based on event content
    message = {
        'message': 'Your custom message or command to the client',
        'status': 'ProcessingComplete',
        'renderId': render_id,
        'connectionId': connection_id
    }

    logger.info(f"Processing with connectionId: {connection_id} and renderId: {render_id}")

    try:
        logger.info(f"Sending message to connectionId: {connection_id}")
        api_gw_client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(message)
        )
        return {'statusCode': 200, 'body': json.dumps({'success': True})}
    except api_gw_client.exceptions.GoneException as e:
        logger.error(f"Connection gone error: {str(e)}")
        # Handling cases where the connection ID is no longer valid
        return {'statusCode': 410, 'body': json.dumps({'error': 'Connection gone'})}
    except Exception as e:
        logger.error(f"General exception: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
