import logging
import os
import json
import requests
from flask import Flask, request, render_template, jsonify, url_for, Response

app = Flask(__name__)

# Configure logging
logging.basicConfig(filename='prompts.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

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

                    # Here, return the URL and the filename to the client
                    # Corrected to use the full file path for 'url_for'
                    return jsonify({
                        'url': url_for('static', filename=os.path.join('raw', filename)),
                        'filename': filename  # Returning the filename used for saving the image
                    })

                else:
                    error_message = "Failed to download the image."
                    logging.error(f"Error downloading image: {img_response.status_code} - {img_response.text}")
                    return jsonify({'error': error_message}), 400

            except Exception as e:
                error_message = "An internal error occurred. Please try again later."
                logging.error(f"An error occurred while saving the file: {str(e)}")
                return jsonify({'error': error_message}), 500

        else:
            error_message = f"Error: {response.status_code}, {response.text}"
            logging.error(error_message)
            return jsonify({'error': error_message}), 400

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

@app.route('/remove_background', methods=['POST'])
def remove_background():
    # Extract filename from form data
    filename = request.form.get('filename')

    if not filename:
        logging.error('No filename provided in the form data.')
        return jsonify({'error': 'No filename provided'}), 400

    try:
        # Construct the path to the raw image file
        raw_image_path = os.path.join('mysite/static', 'raw', filename)

        # Check if the raw image file exists before attempting to read it
        if not os.path.isfile(raw_image_path):
            logging.error(f'Raw image file not found: {raw_image_path}')
            return jsonify({'error': 'Image file not found'}), 404

        # Read the image file from local storage
        with open(raw_image_path, 'rb') as f:
            image_data = f.read()
        logging.info(f"Raw image file read successfully: {raw_image_path}")

        # Sending the image file to the Removal.ai API
        url = "https://api.removal.ai/3.0/remove"
        token = '6588daaf2dead9.14285907'  # Replace with your actual token
        headers = {'Rm-Token': token}

        files = [('image_file', ('image.png', image_data, 'image/png'))]
        response = requests.post(url, headers=headers, files=files)

        if response.status_code != 200:
            # Log an error if the status code indicates a failure
            logging.error(f"Background removal API returned an error: {response.status_code}, Response: {response.content}")
            return jsonify({'error': 'Failed to remove background'}), 500

        removal_data = response.json()

        # tmp fix: we need to check if removal_data has the 'url' key
        if 'url' not in removal_data:
            logging.error(f"No 'url' in Removal API response: {removal_data}")
            return jsonify({'error': 'No URL in Removal API response'}), 500

        # tmp fix: Don't write response.content, write the content of the removal_data['url']
        # First we need to GET the image from the provided URL
        img_response = requests.get(removal_data['url'])
        if img_response.status_code == 200:
            # Now we have the image, save it
            processed_image_path = os.path.join('mysite/static', 'processed', filename)
            os.makedirs(os.path.dirname(processed_image_path), exist_ok=True)
            with open(processed_image_path, 'wb') as file:
                file.write(img_response.content)

            return jsonify({'url': removal_data['preview_demo']})  # Make sure to return only within this 'if' statement

        else:
            logging.error(f"Failed to fetch processed image from Removal API: {img_response.status_code}")
            return jsonify({'error': 'Failed to fetch processed image from Removal API'}), 500

    except Exception as e:
        logging.exception("An internal error occurred while removing the background.")
        return jsonify({'error': 'An internal error occurred'}), 500


# Additional utility function for getting the full image path on the server
def get_image_path_from_static_folder(filename): #line 207
    """
    Construct the full file path for the given filename within the static folder of the Flask app.

    Args:
        filename (str): The dynamically generated name of the file.

    Returns:
        str: The full server file path within the static/processed folder.
    """
    # Assumes filename includes the 'processed' sub-directory along with the actual file name
    # e.g., 'processed/Animal-Personality-Sport-Color-Action.png'
    return os.path.join(app.root_path, 'static', 'processed', filename)


@app.route('/vectorize_image', methods=['POST'])
def vectorize_image():
    filename = request.form['filename']  # This should be the original filename from the form
    print('Filename:', filename)  # Add this line
    image_path = get_image_path_from_static_folder(filename)
    response = None

    with open(image_path, 'rb') as image_file:
        response = requests.post(
            'https://vectorizer.ai/api/v1/vectorize',
            files={'image': image_file},
            data={'mode': 'production', 'output.size.width': 1024, 'output.size.height': 1024},  # Using 'production' mode
            auth=('vk8pdr7het9gzzc', 'dmkle2kd6ddhefamk9ln6rn7rcuos12e2633qf6405v7qgvhbbb7')
        )

    if response and response.status_code == requests.codes.ok:
        # Change 'vectorized_image.svg' to use the dynamic 'filename'
        # Note that filename is with .png extension you need to change to .svg
        vectorized_filename = filename.replace('.png', '.svg')

        save_directory = os.path.join(app.root_path, 'static', 'vector')
        os.makedirs(save_directory, exist_ok=True)
        vectorized_file_path = os.path.join(save_directory, vectorized_filename)

        with open(vectorized_file_path, 'wb') as file:
            file.write(response.content)

        # Construct the URL to the saved SVG file
        vectorized_image_url = url_for('static', filename=os.path.join('vector', vectorized_filename))

        # Log and return the URL to the client
        print(f"Contents of the Vector directory: {os.listdir(save_directory)}")
        print(f"URL constructed using url_for: {vectorized_image_url}")
        return jsonify({'url': vectorized_image_url})

    elif response:
        return jsonify({'error': 'API request failed', 'details': response.text}), response.status_code
    else:
        return jsonify({'error': 'No response from vectorization API'}), 500


if __name__ == '__main__':
    app.run(debug=True)