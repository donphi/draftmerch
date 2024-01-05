import logging
from flask import Flask, request, render_template, jsonify
import requests
import json
import os

# Configure logging
logging.basicConfig(filename='prompts.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

app = Flask(__name__)

# OpenAI API setup
OPENAI_API_KEY = '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'
api_url = 'https://api.openai.com/v1/images/generations'
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {OPENAI_API_KEY}'
}

@app.route('/', methods=['GET', 'POST'])
def index():
    image_url = None
    error_message = None
    animal = ''
    personality = ''
    sport = ''
    color = ''
    action = ''
    final_prompt = ''

    if request.method == 'POST':
        animal = request.form.get('animal-custom') if request.form.get('animal') == 'custom' else request.form.get('animal', '').strip()
        personality = request.form.get('personality-custom') if request.form.get('personality') == 'custom' else request.form.get('personality', '').strip()
        sport = request.form.get('sport-custom') if request.form.get('sport') == 'custom' else request.form.get('sport', '').strip()
        color = request.form.get('color-custom') if request.form.get('color') == 'custom' else request.form.get('color', '').strip()
        action = request.form.get('action-custom') if request.form.get('action') == 'custom' else request.form.get('action', '').strip()

        if action:
            prompt = ("Design a new image based on the image with the referenced image ID [ZfbtTkwJ76RiqbrN]. It must be a very detailed non-symmetrical emblem, featuring a {animal} mascot {action} for a logo. This emblem should be outlined in a bold, thick line style. The central theme is to embody the facial expression of the {animal}'s {personality} traits. Use a striking {color} to accentuate key elements like the sportswear and equipment, ensuring they stand out against a stark white background. The design should be vibrant and expressive, capturing the movement and spirit of {sport} through the {action}, with a clear emphasis on the emblem's outline and stylistic elements.")
        else:
            prompt = ("Design a new image based on the image with the referenced image ID [ZfbtTkwJ76RiqbrN]. It must be a very detailed non-symmetrical emblem, featuring a {animal} mascot for a logo. This emblem should be outlined in a bold, thick line style. The central theme is to embody the facial expression of the {animal}'s {personality} traits. Use a striking {color} to accentuate key elements like the sportswear and equipment, ensuring they stand out against a stark white background. The design should be vibrant and expressive, capturing the movement and spirit of {sport}, with a clear emphasis on the emblem's outline and stylistic elements.")

        final_prompt = prompt.format(animal=animal, action=action, personality=personality, sport=sport, color=color)

        logging.info(f"Generated Prompt: {final_prompt}")

        if not final_prompt.strip():
            error_message = "Error: Prompt is empty."
            logging.error(error_message)
            return jsonify({'error': error_message}), 400

        data = {
            "model": "dall-e-3",
            "prompt": final_prompt,
            "n": 1,
            "size": "1024x1024"
        }

        response = requests.post(api_url, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            result = response.json()
            image_url = result['data'][0]['url']

            filename_parts = [animal, personality, sport, color]
            if action:
                filename_parts.append(action)
            filename = " - ".join(filename_parts) + ".png"
            filename = "".join(c for c in filename if c.isalnum() or c in " -_.")

            try:
                img_response = requests.get(image_url)
                if img_response.status_code == 200:
                    save_directory = os.path.join('mysite/static', 'raw')
                    os.makedirs(save_directory, exist_ok=True)

                    file_path = os.path.join(save_directory, filename)
                    with open(file_path, 'wb') as f:
                        f.write(img_response.content)
                    logging.info(f"File saved: {file_path}")
                else:
                    error_message = "Failed to download the image."
                    logging.error(f"Error downloading image: {img_response.status_code} - {img_response.text}")

            except Exception as e:
                error_message = "An internal error occurred. Please try again later."
                logging.error(f"An error occurred while saving the file: {str(e)}")

        else:
            error_message = f"Error: {response.status_code}, {response.text}"
            logging.error(error_message)

        if error_message:
            return jsonify({'error': error_message}), 500
        elif image_url:
            return jsonify({'url': image_url})
        else:
            return jsonify({'error': 'An unknown error occurred'}), 500

    return render_template('index.html', image_url=image_url, error=error_message,
                           animal=animal, personality=personality, sport=sport, color=color, action=action)

@app.route('/generate_action', methods=['POST'])
def generate_action():
    data = request.json
    animal = data.get('animal', 'Animal')
    personality = data.get('personality', 'Personality')

    prompt = f"Design an action for a {animal} mascot that is both dynamic and whimsical, suitable for a sports team logo. The action should be two words, capturing both the energy and uniqueness of the {animal} mascot, embodying a {personality} personality."

    logging.info(f"Generated Action Prompt: {prompt}")

    response = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers=headers,
        json={
            "model": "gpt-4",
            "messages": [{"role": "system", "content": "You are a creative assistant."},
                         {"role": "user", "content": prompt}]
        }
    )

    if response.status_code == 200:
        result = response.json()
        generated_action = result['choices'][0]['message']['content']
        return generated_action
    else:
        return f"Error: {response.status_code}, {response.text}"

if __name__ == '__main__':
    app.run(debug=True)
