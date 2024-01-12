import logging
import numpy as np
import os
import cv2
import base64
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
        watermark = watermark.resize(base_image.size, Image.LANCZOS)

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
            watermark = watermark.resize(base_image.size, Image.LANCZOS)

            # Now the watermark is the same size as the base image
            # Combine the base image and the watermark
            combined = Image.alpha_composite(base_image, watermark)

            # Convert back to RGB and save the image
            combined = combined.convert("RGB")
            combined.save(image_path)

# Define your upscale_image function
def upscale_image(filename):
    url = "https://ai-picture-upscaler.p.rapidapi.com/supersize-image"
    raw_folder = os.path.join(app.root_path, 'static', 'raw2x')
    os.makedirs(raw_folder, exist_ok=True)
    raw_file_path = os.path.join(raw_folder, filename)

    # Read the original image
    with open(os.path.join(app.root_path, 'static', 'raw', filename), 'rb') as f:
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
        with open(raw_file_path, 'wb') as raw2x_file:
            raw2x_file.write(upscaled_content)
        return True, raw_file_path
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

        
        prompt = ("Use the generation ID TXLnYeq6rsLqVTTa, uvpARKZcAUCKOBn7 and P3PUOoDqFsKHJXAA. Medium: 2D, shield-like shaped, very detailed sports vector emblem only. Subject: A {animal} mascot for {sport}, depicting intricate detail in the {sport}'s attire and equipment.  The {animal} is depicted {action}. Emotion: {personality}, displayed in detail on the {animal}'s face. Lighting: Flat, Vivid, and bold, and use striking {color} to accentuate key elements. White background. Scene: The emblem is surrounded by a pure white background, highlighted by a prominent, heavy black border. Style: Sharp, clean lines, bold use of {color}. --ar 1:1")

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
            "size": "1024x1024",
            "quality": "hd",
            "style": "vivid"
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
                watermark = watermark.resize(watermarked_image.size, Image.LANCZOS)
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
    return os.path.join(app.root_path, 'static', 'raw2x', filename)

def add_svg_watermark(svg_path, watermark_path):
    # Implement watermarking logic for SVG files here
    pass

def is_background_white(image_path, threshold=0.9):
    with Image.open(image_path) as img:
        img = img.convert("RGB")

        border_width = 10
        width, height = img.size
        white_pixels = 0

        for y in range(height):
            for x in range(width):
                if x < border_width or x >= width - border_width or y < border_width or y >= height - border_width:
                    r, g, b = img.getpixel((x, y))
                    if r > 180 and g > 180 and b > 180:  # Adjust for different shades of white
                        white_pixels += 1

        total_border_pixels = (width * border_width * 2) + ((height - 2 * border_width) * border_width * 2)
        white_proportion = white_pixels / total_border_pixels

        return white_proportion >= threshold

def remove_background_and_preserve_white(input_image_path, output_image_path, white_threshold=100, debug=False):
    # Read the image
    img = cv2.imread(input_image_path)
    img_rgba = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    
    # Step 1: Remove the white background
    lower_white = np.array([white_threshold, white_threshold, white_threshold, 255], dtype=np.uint8)
    mask_background = np.ones_like(img_rgba, dtype=np.uint8) * 255  # Full opacity mask
    mask_background[np.all(img_rgba >= lower_white, axis=2)] = [0, 0, 0, 0]  # Set white areas to transparent

    # Apply the background removal mask to the image
    result_background_removed = cv2.bitwise_and(img_rgba, mask_background)

    
    # Step 2: Use the object mask to add back any white areas within the emblem
    object_mask1 = create_object_mask(input_image_path)

    # Third object mask
    object_mask2 = create_object_mask2(input_image_path)

    # Combine all object masks
    combined_mask = cv2.bitwise_or(object_mask1, object_mask2)

    # Smooth the mask edges before applying it to add white areas back
    smoothed_object_mask = smooth_mask_edges(combined_mask, kernel_size=5, sigma=2, erosion_iterations=6, dilation_iterations=1)
    
    # Debug: Save the smoothed object mask
    if debug:
        cv2.imwrite('debug_smoothed_object_mask.png', smoothed_object_mask)

    # Apply the smoothed object mask to the entire image, adding back the white within the emblem
    img_rgba[:, :, 3] = cv2.bitwise_or(result_background_removed[:, :, 3], smoothed_object_mask)
    
    # Debug: Save the result after applying the smoothed object mask
    if debug:
        cv2.imwrite('debug_final_with_white.png', img_rgba)

    # Save the final result with transparency
    cv2.imwrite(output_image_path, img_rgba)

def create_object_mask2(image_path, debug=False):
    # Read the image and convert to grayscale
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    # Apply a blur to reduce noise
    blurred_img = cv2.GaussianBlur(img, (5, 5), 0)

    # Apply Sobel edge detection
    sobelx = cv2.Sobel(blurred_img, cv2.CV_64F, 1, 0, ksize=5)
    sobely = cv2.Sobel(blurred_img, cv2.CV_64F, 0, 1, ksize=5)
    sobel_mag = np.hypot(sobelx, sobely)
    sobel_mag = np.uint8(sobel_mag / np.max(sobel_mag) * 255)

    # Apply edge detection using Canny
    edges_canny = cv2.Canny(blurred_img, 0, 30)  # Adjusted threshold values for experimentation
    
    # Combine Sobel and Canny edges
    combined_edges = cv2.bitwise_or(edges_canny, sobel_mag)

    # Debug: Save the edge detection result
    if debug:
        cv2.imwrite('debug_edges.png', combined_edges)
    
    # Find contours
    contours, _ = cv2.findContours(combined_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Create an empty mask
    mask = np.zeros_like(img, dtype=np.uint8)

    # Identify contours that are sufficiently large
    min_contour_area = 250  # Adjust as necessary for your image
    large_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_contour_area]

    # Fill these contours
    cv2.drawContours(mask, large_contours, -1, color=255, thickness=cv2.FILLED)

    # Debug: Save the initial mask
    if debug:
        cv2.imwrite('debug_object_mask.png', mask)
    
    return mask

def create_object_mask(image_path, debug=False):
    # Read the image and convert to grayscale
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    # Thresholding to create a binary image
    _, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Debugging: Save the binary image for inspection
    if debug:
        cv2.imwrite('debug_binary.png', binary)
    
    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Create an empty mask
    mask = np.zeros_like(img)

    # If there are contours found
    if contours:
        # Assume the largest contour is the emblem
        largest_contour = max(contours, key=cv2.contourArea)
        # Fill the largest contour with white
        cv2.drawContours(mask, [largest_contour], -1, color=255, thickness=cv2.FILLED)

    # Debugging: Save the mask for inspection
    if debug:
        cv2.imwrite('debug_object_mask.png', mask)

    return mask

def smooth_mask_edges(mask, kernel_size=5, sigma=1, erosion_iterations=2, dilation_iterations=1):
    # Define the erosion kernel size
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    
    # Apply erosion to contract the edges of the mask
    eroded_mask = cv2.erode(mask, kernel, iterations=erosion_iterations)
    
    # Optionally, apply dilation to expand the mask again, if you find it necessary
    dilated_mask = cv2.dilate(eroded_mask, kernel, iterations=dilation_iterations)
    
    # Apply Gaussian blur to the mask
    blurred_mask = cv2.GaussianBlur(dilated_mask, (kernel_size, kernel_size), sigma)
    
    # Normalize the mask to ensure that values are still between 0 and 255
    _, normalized_mask = cv2.threshold(blurred_mask, 1, 255, cv2.THRESH_BINARY)
    
    return normalized_mask

def remove_background_with_mask(input_image_path, output_image_path, debug=False):
    # Create the object's mask
    object_mask = create_object_mask(input_image_path, debug=debug)

    # Smooth the edges of the mask by blurring
    smoothed_mask = smooth_mask_edges(object_mask.astype(np.float32))

    # Debug: Save intermediate results
    if debug:
        cv2.imwrite('debug_object_mask.png', object_mask)
        cv2.imwrite('debug_smoothed_mask.png', smoothed_mask)

    # Read the original image and convert to RGBA
    img = cv2.imread(input_image_path)
    img_rgba = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)

    # Create an alpha channel based on the smoothed mask
    alpha_channel = np.zeros_like(img[:, :, 0], dtype=np.uint8)
    alpha_channel[smoothed_mask > 0] = smoothed_mask[smoothed_mask > 0]

    # Merge the alpha channel back into the image
    img_rgba[:, :, 3] = alpha_channel

    # Debug: Save the image with alpha channel applied
    if debug:
        cv2.imwrite('debug_img_with_alpha.png', img_rgba)

    # Save the image with the background removed (transparent background)
    cv2.imwrite(output_image_path, img_rgba)

@app.route('/vectorize_image', methods=['POST'])
def vectorize_image():
    logging.info("Vectorize_image route called.")
    filename = request.form.get('filename')
    logging.info(f"Requested to vectorize file: {filename}")

    # Call upscale_image before continuing
    upscale_successful, upscaled_image_path = upscale_image(filename)
    if not upscale_successful:
        return jsonify({'error': 'Failed to upscale image.'}), 500

    logging.info(f"Upscaled image path resolved to: {upscaled_image_path}")

    logging.info("Vectorize_image route called.")
    filename = request.form.get('filename')
    logging.info(f"Requested to vectorize file: {filename}")

    # Step 1: Get the original image path in 'static/raw2x'
    original_image_path = get_image_path_from_static_folder(filename)
    logging.info(f"Original image path resolved to: {original_image_path}")

    # Directory for background removed images
    background_rm_path = os.path.join(app.root_path, 'static', 'background_rm')
    os.makedirs(background_rm_path, exist_ok=True)
    background_rm_file_path = os.path.join(background_rm_path, filename)

    # Make sure the file exists before proceeding
    if not os.path.exists(original_image_path):
        error_message = f"File does not exist at path: {original_image_path}"
        logging.error(error_message)
        return jsonify({'error': error_message}), 400
    
    logging.info(f"Background remove file path resolved to: {background_rm_file_path}")
    
    # Define background_removal_files outside the if/else block
    bbackground_removed = False

    if is_background_white(upscaled_image_path):
        # Using OpenCV method for removal if the background is white
        logging.info("Background is predominantly white. Using OpenCV method for removal.")
        remove_background_and_preserve_white(upscaled_image_path, background_rm_file_path) #Add Def either flood or remove background with mask
        logging.info("Background removed using OpenCV method.")
        background_removed = True
    else:
        # Prepare the image for the background removal API call when background is not white
        image_file = open(original_image_path, 'rb') 
        background_removal_files = {'image': (filename, image_file, 'image/png')}
        logging.info("Background is not predominantly white. Using API method for removal.")

        # API details
        background_removal_url = "https://background-removal4.p.rapidapi.com/v1/results"
        background_removal_headers = {
            "X-RapidAPI-Key": "f11731b818msh7a295f044947cf9p1f908ejsncfd12a96ba01",
            "X-RapidAPI-Host": "background-removal4.p.rapidapi.com"
        }
        background_removal_params = {"mode": "fg-image"}

        # Make the API request for background removal
        response = requests.post(
            url=background_removal_url,
            headers=background_removal_headers,
            files=background_removal_files,
            params=background_removal_params
        )

        # Check the JSON response and the status code
        response_json = response.json()

        if response.status_code == 200:
            result = response_json['results'][0]
            status = result['status']

            if status['code'] == 'ok':
                background_removed = True
                # Extracts the base64-encoded image data from the response
                img_data = base64.b64decode(result['entities'][0]['image'])

                # Save the processed image data to a file
                with open(background_rm_file_path, 'wb') as image_file:
                    image_file.write(img_data)
                logging.info(f"Background-removed image saved at: {background_rm_file_path}")

            else:
                # Handle cases where the API operation was not successful
                logging.error(f"Background removal API returned an error: {status['message']}")
                return jsonify({'error': status['message']}), 422
        else:
            # Handle cases where the API HTTP response was not OK
            error_message = f"Failed with status code: {response.status_code}, response: {response_json}"
            logging.error(error_message)
            return jsonify({'error': error_message}), response.status_code


    if background_removed:
        try:
            with open(background_rm_file_path, 'rb') as image_file:
                files = {'image': (filename, image_file, 'image/png')}
                data = {
                    'mode': 'production',
                    'output.size.width': 1024,
                    'output.size.height': 1024,
                    'output.svg.version': 'svg_tiny_1_2',
                    'processing.max_colors': 30,
                    'output.group_by': 'color',
                    'output.curves.line_fit_tolerance': 0.09,
                    'output.size.unit': 'px'
                }
                auth = ('vk8pdr7het9gzzc', 'dmkle2kd6ddhefamk9ln6rn7rcuos12e2633qf6405v7qgvhbbb7')
                vectorization_response = requests.post(
                    'https://vectorizer.ai/api/v1/vectorize',
                    files=files,
                    data=data,
                    auth=auth
                )

            logging.info("Received response from vectorization API.")
            files['image'][1].close()
            # Directory for vectorized images
            vectorized_path = os.path.join(app.root_path, 'static', 'vector')
            os.makedirs(vectorized_path, exist_ok=True)
            vectorized_filename = '(Vector) ' + filename.replace('.png', '.svg')
            vectorized_file_path = os.path.join(vectorized_path, vectorized_filename)

            if vectorization_response.status_code == 200:
                # Step 7: Save and convert SVG to PNG, assuming convert_svg_to_png is correctly implemented
                with open(vectorized_file_path, 'wb') as file:
                    file.write(vectorization_response.content)
                logging.info(f"Vectorized SVG image file written successfully at: {vectorized_file_path}")

                png_file_path = vectorized_file_path.replace('.svg', '.png')
                convert_svg_to_png(vectorized_file_path, png_file_path)
                logging.info("SVG to PNG conversion complete.")

                # Step 8-9: Apply watermark to PNG and save in 'static/tempvector'
                temp_vector_dir = os.path.join(app.root_path, 'static', 'tempvector')
                os.makedirs(temp_vector_dir, exist_ok=True)

                watermarked_png_path = os.path.join(temp_vector_dir, f"Watermarked_{vectorized_filename.replace('.svg', '.png')}")
                watermark_path = os.path.join(app.root_path, 'static', 'watermark', 'watermark.png')
                add_png_watermark(png_file_path, watermark_path, watermarked_png_path)
                logging.info("Watermarked PNG image saved.")

                watermarked_image_url = url_for('static', filename=os.path.join('tempvector', os.path.basename(watermarked_png_path)))
                logging.info(f"Returning watermarked PNG image URL: {watermarked_image_url}")

                return jsonify({'url': watermarked_image_url,
                                'svg_filename': vectorized_filename})

            else:
                # If vectorization API did not return success
                error_message = f"Vectorization API returned status code {vectorization_response.status_code}"
                logging.error(error_message)
                return jsonify({'error': error_message}), 500

        except requests.exceptions.RequestException as e:
            logging.error(traceback.format_exc())
            return jsonify({'error': str(e)}), 500
        except Exception as e:
            logging.error(traceback.format_exc())
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
