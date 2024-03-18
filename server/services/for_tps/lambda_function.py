def lambda_handler(event, context):
    request = event['Records'][0]['cf']['request']
    host_header = request['headers']['host'][0]['value']
    
    if host_header == "www.draftmerch.com":
        response = {
            'status': '301',
            'statusDescription': 'Moved Permanently',
            'headers': {
                'location': [{
                    'key': 'Location',
                    'value': 'https://draftmerch.com' + request['uri']
                }]
            },
        }
        return response
    
    return request
