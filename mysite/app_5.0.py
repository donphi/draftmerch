import logging
import os
import json
import requests
from flask import Flask, request, render_template, jsonify, url_for
from datetime import datetime
from PIL import Image
import cairosvg
import traceback

app = Flask(__name__)

# Configure logging
logging.basicConfig(filename='prompts.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

def convert_svg_to_png(svg_path, png_path):
        # Attempt to convert the SVG to PNG
        cairosvg.svg2png(url=svg_path, write_to=png_path, output_width=1024, output_height=1024)

#def add_png_watermark(image_path, watermark_path, output_path):
    #with Image.open(image_path).convert("RGBA") as base_image:
        #with Image.open(watermark_path).convert("RGBA") as watermark:
            #watermark = watermark.resize(base_image.size, Image.ANTIALIAS)
            #combined = Image.alpha_composite(base_image, watermark)
            #combined = combined.convert("RGB")
            #combined.save(output_path)

def add_png_watermark(image_path, watermark_path, output_path):
    # Open the base image (to be watermarked) and the watermark image
    with Image.open(image_path) as base_image, Image.open(watermark_path) as watermark:
        # Ensure both images have an alpha channel (for transparency)
        base_image = base_image.convert("RGBA")
        watermark = watermark.convert("RGBA")

        # Resize watermark to match the size of the base image
        watermark = watermark.resize(base_image.size, Image.ANTIALIAS)

        # Create an empty (transparent) image for the final output
        transparent_img = Image.new("RGBA", base_image.size)

        # Paste the base image onto the transparent image
        transparent_img.paste(base_image, (0, 0), base_image)

        # Now paste the watermark onto the transparent image, with the watermark mask for transparency
        transparent_img.paste(watermark, (0, 0), watermark)

        # Save this to a new file, maintaining the transparency
        transparent_img.save(output_path, format="PNG")

def formatted_filename(animal, personality, sport, color, action):
    timestamp = datetime.now().strftime("%H%M%S%d%m%Y")
    filename_parts = [animal, personality, sport, color, action, timestamp]
    filename = " - ".join([part for part in filename_parts if part]) + ".png"
    # Remove any illegal file characters if necessary
    return "".join(c for c in filename if c.isalnum() or c in " -_.")

def add_watermark(image_path, watermark_path):
    with Image.open(image_path).convert("RGBA") as base_image:
        with Image.open(watermark_path).convert("RGBA") as watermark:
            # Resize watermark to match the base image size
            watermark = watermark.resize(base_image.size, Image.ANTIALIAS)

            # Now the watermark is the same size as the base image
            # Combine the base image and the watermark
            combined = Image.alpha_composite(base_image, watermark)

            # Convert back to RGB and save the image
            combined = combined.convert("RGB")
            combined.save(image_path)

# Define your upscale_image function
def upscale_image(filename):
    url = "https://ai-picture-upscaler.p.rapidapi.com/supersize-image"
    temp_folder = os.path.join('mysite/static', 'temp')
    os.makedirs(temp_folder, exist_ok=True)
    temp_file_path = os.path.join(temp_folder, filename)

    # Read the original image
    with open(os.path.join('mysite/static/raw', filename), 'rb') as f:
        files = {"image": f}
        payload = {
            "sizeFactor": "2",
            "imageStyle": "default",
            "noiseCancellationFactor": "0"
        }
        headers = {
            "X-RapidAPI-Key": "f11731b818msh7a295f044947cf9p1f908ejsncfd12a96ba01",
            "X-RapidAPI-Host": "ai-picture-upscaler.p.rapidapi.com"
        }

        response = requests.post(url, data=payload, files=files, headers=headers)

    # Check if the response is OK
    if response.status_code == 200:
        # Extract the content from the response
        upscaled_content = response.content

        # Write the upscaled content to the temp folder
        with open(temp_file_path, 'wb') as temp_file:
            temp_file.write(upscaled_content)
        return True, temp_file_path
    else:
        logging.error(f"Failed to upscale image. Status code: {response.status_code}, "
                      f"Response: {response.text}")
        return False, None

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
            prompt = ("Design a new image based on the image with the referenced image ID [46rGDvYUaAZqSxIv]. It must be a very detailed, two-dimensional, non-symmetrical emblem featuring a {animal} mascot {action} for a logo. The only object should be this single emblem as it is for printing purposes, which should be outlined in a bold, thick line style with only solid color. The central theme is to embody the facial expression of the {animal}'s {personality} traits. Use a striking {color} to accentuate key elements like the sportswear and equipment, ensuring they stand out against a stark white background, surrounding the entire single emblem. The design should be vibrant and expressive, capturing the movement and spirit of {sport} through the {action}, with a clear emphasis on the emblem's outline and stylistic elements. The {animal}'s features should be real and proportionally correct. It is very important to make sure the image structure is a emblem.")
        else:
            prompt = ("Design a new image based on the image with the referenced image ID [46rGDvYUaAZqSxIv]. It must be a very detailed, two-dimensional, non-symmetrical emblem featuring a {animal} mascot for a logo. The only object should be this single emblem as it is for printing purposes, which should be outlined in a bold, thick line style with only solid color. The central theme is to embody the facial expression of the {animal}'s {personality} traits. Use a striking {color} to accentuate key elements like the sportswear and equipment, ensuring they stand out against a stark white background, surrounding the entire single emblem. The design should be vibrant and expressive, capturing the movement and spirit of {sport}, with a clear emphasis on the emblem's outline and stylistic elements. The {animal}'s features should be real and proportionally correct. It is very important to make sure the image structure is a emblem.")

        final_prompt = prompt.format(animal=animal, action=action, personality=personality, sport=sport, color=color)

        logging.info(f"Generated Prompt: {final_prompt}")

        if not final_prompt.strip():
            error_message = "Error: Prompt is empty."
            logging.error(error_message)
            return jsonify({'error': error_message}), 400

        # Generate the unique filename for the image
        filename = formatted_filename(animal, personality, sport, color, action)

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

            # Save raw image fetched from OpenAI into the 'static/raw' directory
            raw_save_directory = os.path.join(app.root_path, 'static', 'raw')
            os.makedirs(raw_save_directory, exist_ok=True)
            raw_file_path = os.path.join(raw_save_directory, filename)

            img_response = requests.get(image_url)
            if img_response.status_code == 200:
                with open(raw_file_path, 'wb') as raw_file:
                    raw_file.write(img_response.content)
                logging.info(f"Original image saved: {raw_file_path}")

                # Make a copy of the original image for watermarking
                watermarked_image = Image.open(raw_file_path).convert("RGBA")

                # Define the watermark path
                watermark_path = os.path.join(app.root_path, 'static', 'watermark', 'watermark.png')

                # Apply watermark to the copy of the image
                watermark = Image.open(watermark_path).convert("RGBA")
                watermark = watermark.resize(watermarked_image.size, Image.ANTIALIAS)
                combined = Image.alpha_composite(watermarked_image, watermark)
                combined = combined.convert("RGB")  # Convert back to RGB if you don't need the alpha channel

                # Define the path to save the watermarked image
                watermark_save_directory = os.path.join(app.root_path, 'static', 'temp')
                os.makedirs(watermark_save_directory, exist_ok=True)
                watermarked_file_path = os.path.join(watermark_save_directory, "(Watermark) " + filename)

                # Save the watermarked image as a separate file
                combined.save(watermarked_file_path)
                logging.info(f"Watermarked image saved: {watermarked_file_path}")

                # The response should include a URL for the raw (unwatermarked) and watermarked images to display in the HTML container
                return jsonify({
                    'raw_url': url_for('static', filename=os.path.join('raw', filename)), # URL for the raw image
                    'watermarked_url': url_for('static', filename=os.path.join('temp', "(Watermark) " + filename)), # URL for the watermarked image
                    'filename': filename # The raw filename you use to fetch the raw image for vectorizing
                })

            else:
                error_message = "Failed to download the image from OpenAI."
                logging.error(f"{error_message}: {img_response.status_code}")
                return jsonify({'error': error_message}), img_response.status_code

        else:
            error_message = f"Error generating image: {response.status_code}, {response.text}"
            logging.error(f"{error_message}")
            return jsonify({'error': error_message}), response.status_code

    # Render the initial form template on GET or if POST fails
    return render_template('index.html', image_url=image_url, error=error_message,
                           animal=animal, personality=personality, sport=sport, color=color, action=action)


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
    return os.path.join(app.root_path, 'static', 'raw', filename)

def add_svg_watermark(svg_path, watermark_path):
    # Implement watermarking logic for SVG files here
    pass

@app.route('/vectorize_image', methods=['POST'])
def vectorize_image():
    logging.info("Vectorize_image route called.")
    filename = request.form.get('filename')
    logging.info(f"Requested to vectorize file: {filename}")

    image_path = get_image_path_from_static_folder(filename)
    logging.info(f"Image path resolved to: {image_path}")

    if not os.path.exists(image_path):
        error_message = f"File does not exist at path: {image_path}"
        logging.info(error_message)
        return jsonify({'error': error_message}), 400

    vectorized_filename = '(Vector) ' + filename.replace('.png', '.svg')  # Use consistent naming convention
    api_key = "V4XJ7Q712"  # Use your actual API key
    save_directory = os.path.join(app.root_path, 'static', 'vector')
    os.makedirs(save_directory, exist_ok=True)

    vectorized_file_path = os.path.join(save_directory, vectorized_filename)
    logging.info(f"Vectorized file path: {vectorized_file_path}")

    try:
        with open(image_path, 'rb') as image_file:
            files = {'image': (filename, image_file, 'image/png')}
            data = {
                'format': 'svg',
                'colors': 8,
                'model': 'clipart',
                'algorithm': 'overlap',
                'detail': 'max',
                'antialiasing': 'max',
                'background-threshold': 255,
                'transparency-color': 'transparent',
                'roundness': 'max',
                'noisereduction': 'high',
                'unit': 'px',
                'width': 2048,
                'height': 2048
            }
            headers = {'X-CREDITS-CODE': api_key}

            logging.info("Sending request to vectorization API.")
            response = requests.post('https://api.vectorizer.io/v4.0/vectorize', headers=headers, data=data, files=files)
            logging.info(f"Received response from vectorization API with status code: {response.status_code}")

            # Log the size of the vectorization response content (Added for step 6)
            logging.info(f"Size of vectorization response content: {len(response.content)} bytes")

            if response.content:
                with open(vectorized_file_path, 'wb') as file:
                    file.write(response.content)
                    logging.info("Vectorized SVG image file written successfully.")

                # Convert SVG to PNG
                png_file_path = vectorized_file_path.replace('.svg', '.png')
                convert_svg_to_png(vectorized_file_path, png_file_path)
                logging.info("SVG to PNG conversion complete.")

                temp_vector_dir = os.path.join(app.root_path, 'static', 'tempvector')
                os.makedirs(temp_vector_dir, exist_ok=True)

                # Apply watermark to PNG
                watermarked_png_path = os.path.join(temp_vector_dir, f"Vector_{filename.replace('.png', '_watermarked.png')}")
                watermark_path = os.path.join(app.root_path, 'static', 'watermark', 'watermark.png')
                add_png_watermark(png_file_path, watermark_path, watermarked_png_path)
                logging.info("Watermarked PNG image saved.")

                watermarked_image_url = url_for('static', filename=os.path.join('tempvector', os.path.basename(watermarked_png_path)))
                logging.info(f"Returning watermarked PNG image URL: {watermarked_image_url}")

                return jsonify({'url': watermarked_image_url,
                'svg_filename': vectorized_filename  # Just the filename, not the full path
                })
            pass  # This will be where you process the image and interact with the API
    except requests.exceptions.RequestException as e:
        logging.error(traceback.format_exc())  # This logs the full stack trace
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logging.error(traceback.format_exc())  # This also logs the full stack trace
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)