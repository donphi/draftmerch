import json
import logging
import os
import requests
import boto3

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize a Secrets Manager client
secretsmanager_client = boto3.client('secretsmanager')

def get_secret(secret_name):
    try:
        response = secretsmanager_client.get_secret_value(SecretId=secret_name)
        secret_dict = json.loads(response['SecretString'])  # Parse the secret string as JSON
        return secret_dict['apiKey']  # Access the API key using the 'apiKey' key
    except Exception as e:
        logger.error(f"Error fetching secret: {e}")
        raise e

def lambda_handler(event, context):
    # Fetch the API key from Secrets Manager
    api_key = get_secret('Generator')
    # Extract parameters from the event object, assuming it's a JSON payload
    # You may need to change this part to match the structure of the incoming event
    body = json.loads(event['body'])
    hero = body['hero']
    personality = body['personality']
    sport = body['sport']
    color = body['color']
    action = body['action']
    uploaded_image_description = body.get('uploaded_image_description')

    api_url = 'https://api.openai.com/v1/images/generations'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    # Construct the prompt depending on whether an uploaded image description is provided
    if uploaded_image_description:
        final_prompt = ("Use the generation ID TXLnYeq6rsLqVTTa, uvpARKZcAUCKOBn7 and P3PUOoDqFsKHJXAA. Medium: 2D, "
                        "shield-like shaped, very detailed sports vector emblem only. Subject: A character is engaged in {sport}, "
                        "depicting intricate detail in the character wearing the {sport}'s attire and equipment. This character will "
                        "be detailed at the end. The character is depicted {action}. Emotion: {personality}, displayed in detail on the character's face. Lighting: Flat, "
                        "Vivid, and bold, and use striking {color} to accentuate key elements. White background. Scene: The emblem is "
                        "surrounded by a pure white background, highlighted by a prominent, heavy black border. Style: Sharp, clean lines, "
                        "bold use of {color}. The description of the character is {character}.").format(character=uploaded_image_description, personality=personality, sport=sport, color=color, action=action)
    else:
        final_prompt = ("Use the generation ID TXLnYeq6rsLqVTTa, uvpARKZcAUCKOBn7 and P3PUOoDqFsKHJXAA. Medium: 2D, shield-like shaped, "
                        "very detailed sports vector emblem only. Subject: A {hero} mascot for {sport}, depicting intricate detail in the "
                        "{sport}'s attire and equipment. The {hero} is depicted {action}. Emotion: {personality}, displayed in detail on the "
                        "{hero}'s face. Lighting: Flat, Vivid, and bold, and use striking {color} to accentuate key elements. White background. "
                        "Scene: The emblem is surrounded by a pure white background, highlighted by a prominent, heavy black border. Style: Sharp, "
                        "clean lines, bold use of {color}. --ar 1:1").format(hero=hero, action=action, personality=personality, sport=sport, color=color)

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
        logger.info("OpenAI API call successful.")
        # Parse the JSON response safely
        response_json = response.json()
        # Safely access the image URL
        image_url = response_json.get('data', [{}])[0].get('url', '')  # Provide defaults to avoid KeyError or TypeError

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