#KeyAWS
#1. Imports
#2. API Defs
#3. Image Processing Defs
#4. Misc Defs
#5. Routes

####Imports##################################################################################
import logging
import numpy as np
import os
import cv2
import base64
import json
import requests
from flask import Flask, request, render_template, jsonify, url_for, session
from datetime import datetime
from PIL import Image
import cairosvg
from werkzeug.utils import secure_filename
from requests_aws4auth import AWS4Auth
import traceback
import tempfile
####Imports##################################################################################

app = Flask(__name__)
# sessions key
app.secret_key = '97249a62a0509e4858d445ff0664e52efef57ecf845aea34'

# Configure logging
logging.basicConfig(filename='prompts.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

####APIs##################################################################################
##Auth


#####API Defs
###Image Generation
#Generate
def generate_image(hero, personality, sport, color, action, uploaded_image_description=None):
    OPENAI_API_KEY = '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'
    api_url = 'https://api.openai.com/v1/images/generations'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {OPENAI_API_KEY}'
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

    # Send the request to the OpenAI API
    response = requests.post(api_url, headers=headers, data=json.dumps(data))

    # Attempt to extract the prompt and log it, and handle exceptions if they occur
    try:
        response_json = response.json()
        final_prompt = response_json.get('data')[0].get('prompt')
        logging.info(f"Final prompt sent to API: {final_prompt}")
    except (ValueError, KeyError):
        logging.error("Error: Could not extract prompt from API response.")
        final_prompt = None  # You may handle this differently depending on your application's needs

    return response

#Image to text
def image_to_txt(uploaded_image_url):
    payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {"role": "system", "content": [{"type": "text", "text": "You are a cool image analyst. Your goal is to describe what is in this image."}]},
                {"role": "user", "content": [{"type": "text", "text": "Describe the attached image of a person in detail in paragraph form. To ensure that the unique characteristics that make this person unique are presented, follow the structure of the 5 items below: Gender, Subject, Expression, Clothing, and Accessories. Use 300 words.  Ensure great emphasis on the items unique to the person. There are some crucial items to ensure that the image looks like the person: clothing, accessories, gender, skin color, and ethnicity. The items to consider are: 1. Gender: a. Type. b. Scale of masculine to feminine 2. Subject: a. Hair b. Forehead c. eyebrows d. eyes e. nose f. lips g. cheeks h. teeth i. chin j. shape of face and indents k. ears l. neck m. jaw n. skin Each of the sub-sections of the subject must incorporate the following 7 further sub-sections: I. color II. size III. texture IV. symmetry V. the shape VI. nuanced positioning VII. Interesting nuances 3. Expression: a. Eye expression b. Mouth expression c. Eyebrow expression d. Microexpressions from any of the 13 subsections of the subject. 4. Clothing: a. Type b. Color. 5. Accessories: Check any of the following items and only include and break them down if visible: Glasses/Earrings/Piercings/Headgear/Facial Hair/beauty spots or freckles I. Included. II Type. III. Color. IV. Size."}, {"type": "image_url", "image_url": {"url": uploaded_image_url}}]}
            ],
            "max_tokens": 4096
        }

    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers=headers,
        json=payload
    )
    
    return response

###Vectorizing
#Upscale
def upscale_image(filename):
    url = "https://ai-picture-upscaler.p.rapidapi.com/supersize-image"

    # Read the original image
    with open(os.path.join(app.root_path, 'static', 'image_original', filename), 'rb') as f:
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
        return True, response.content
    else:
        logging.error(f"Failed to upscale image. Status code: {response.status_code}, "
                      f"Response: {response.text}")
        return False, None

#Remove Background
def remove_background_image(filename, original_image_path):
    # API credentials
    api_key = 'pxgze8ryzbalt7h'
    api_secret = '6oc87e4f5td19tpoo5spi96or5moslsfrulqesls6kdav413pu2q'
    auth = (api_key, api_secret)

    # API endpoint and parameters
    background_removal_url = "https://api.pixian.ai/api/v2/remove-background"
    background_removal_params = {
        "test": "false",
        "output.format": "png",
        "output.jpeg_quality": 75
    }
    
    # Prepare the image for the background removal API call
    with open(original_image_path, 'rb') as file_pointer:
        files = {'image': (filename, file_pointer, 'image/png')}

        # Make the API request for background removal
        response = requests.post(
            url=background_removal_url,
            auth=auth,
            files=files,
            params=background_removal_params
        )

    # Check the status code of the response
    if response.status_code == requests.codes.ok:
        return True, response.content
    else:
        logging.error(f"Error during background removal API call: {response.status_code}, {response.text}")
        return False, None

#Vectorize
def vectorize_image(filename, image_no_background_file_path):
    logging.info("Starting image vectorization...")

    with open(image_no_background_file_path, 'rb') as image_file:
        files = {'image': (filename, image_file, 'image/png')}
        data = {
            'mode': 'production',
            'output.size.width': 1024,
            'output.size.height': 1024,
            # 'output.svg.version': 'svg_tiny_1_2',
            'processing.max_colors': 30,
            'output.group_by': 'color',
            'output.curves.line_fit_tolerance': 0.1,
            'output.size.unit': 'px'
        }
        auth = ('vks6jkifmn7zyyb', '49k3631p2bcb9iouuurrhln5fjeregsoomv7kgu7e0hrokbsjs5v')
        vectorization_response = requests.post(
            'https://vectorizer.ai/api/v1/vectorize',
            files=files,
            data=data,
            auth=auth
        )

    logging.info("Received response from vectorization API.")

    if vectorization_response.status_code == 200:
        logging.info("Vectorization successful.")
        # Return the vectorized content
        return vectorization_response.content
    else:
        # Log error but do not raise exception
        error_message = f"Vectorization API returned status code {vectorization_response.status_code}: {vectorization_response.text}"
        logging.error(error_message)
        return None

####APIs##################################################################################

####Image Processing Defs#################################################################
#Background Check: Pure white vs Non-Pure white
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
                    if r > 245 and g > 245 and b > 245:  # Adjust for different shades of white
                        white_pixels += 1

        total_border_pixels = (width * border_width * 2) + ((height - 2 * border_width) * border_width * 2)
        white_proportion = white_pixels / total_border_pixels

        return white_proportion >= threshold

#Pure white Background Removal: Inhouse
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

#Pure white Background Removal:Refining2: Inhouse
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

#Pure white Background Removal:Refining3: Inhouse
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
    edges_canny = cv2.Canny(blurred_img, 20, 50)  # Adjusted threshold values for experimentation
    
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

#Pure white Background Removal:Refining4:Used by Inhouse & API: Inhouse
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

#Pure white Background Removal:Refining5: Inhouse
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

#Non-Pure white Background Removal:Refining: Use by API Background removal
def create_object_mask_otherbackground(image_content):
    
    #Create an object mask from an image with transparency and smooth the edges.
    #param image_content: The binary content of the image with transparency.
    #return: Binary content of the image with smoothed edges.
   
    # Convert the API result into an image and extract the alpha channel (mask)
    image_data = cv2.imdecode(np.frombuffer(image_content, np.uint8), cv2.IMREAD_UNCHANGED)
    mask = image_data[:, :, 3]  # Assuming the fourth channel is the alpha channel

    # Smooth the edges of the mask
    smoothed_mask = smooth_mask_edges(mask)

    # Combine the RGB channels of the original image with the smoothed alpha channel
    rgba_image = cv2.merge((image_data[:, :, 0], image_data[:, :, 1], image_data[:, :, 2], smoothed_mask))
    
    # Encode the image back to a PNG format
    success, encoded_image = cv2.imencode('.png', rgba_image)
    if success:
        return encoded_image.tobytes()
    else:
        return None

####Image Processing Defs#################################################################

####Misc Defs#############################################################################
#Filename Fomatting
def formatted_filename(hero, personality, sport, color, action):
    timestamp = datetime.now().strftime("%H%M%S%d%m%Y")
    filename_parts = [hero, personality, sport, color, action, timestamp]
    filename = " - ".join([part for part in filename_parts if part]) + ".png"
    # Remove any illegal file characters if necessary
    return "".join(c for c in filename if c.isalnum() or c in " -_.")

#Add PNG Watermarks
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

#Add SVG Watermarks
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

#Convert SVG to PNG for User Display
def convert_svg_to_png(svg_path, png_path):
        # Attempt to convert the SVG to PNG
        cairosvg.svg2png(url=svg_path, write_to=png_path, output_width=1024, output_height=1024)

#Additional utility function for getting the full image path on the server
def get_image_path_from_static_folder(filename): #line 207
    """
    Construct the full file path for the given filename within the static folder of the Flask app.

    Args:
        filename (str): The dynamically generated name of the file.

    Returns:
        str: The full server file path within the static/processed folder.
    """
    # Assumes filename includes the 'processed' sub-directory along with the actual file name
    # e.g., 'processed/hero-Personality-Sport-Color-Action.png'
    return os.path.join(app.root_path, 'static', 'image_hd', filename)

#Extra Feature
def add_svg_watermark(svg_path, watermark_path):
    # Implement watermarking logic for SVG files here
    pass

####Misc Defs#############################################################################

LAMBDA_API_ENDPOINT = 'http://127.0.0.1:3000/test'
####Routes###############################################################################
#Generate Image Route
@app.route('/', methods=['GET', 'POST'])
def index():
    image_url = None
    uploaded_image_description = None
    error_message = None
    hero = ''
    personality = ''
    sport = ''
    color = ''
    action = ''
    final_prompt = ''
    

    if request.method == 'POST':
        hero = request.form.get('hero-custom') if request.form.get('hero') == 'custom' else request.form.get('hero', '').strip()
        personality = request.form.get('personality-custom') if request.form.get('personality') == 'custom' else request.form.get('personality', '').strip()
        sport = request.form.get('sport-custom') if request.form.get('sport') == 'custom' else request.form.get('sport', '').strip()
        color = request.form.get('color-custom') if request.form.get('color') == 'custom' else request.form.get('color', '').strip()
        action = request.form.get('action-custom') if request.form.get('action') == 'custom' else request.form.get('action', '').strip()

        lambda_payload = {
                    'hero': hero,
                    'personality': personality,
                    'sport': sport,
                    'color': color,
                    'action': action,
                    'uploaded_image_description': uploaded_image_description
                }

        if hero.startswith('Uploaded Image'):
            # Read the contents of temp_response.txt
            temp_dir = os.path.join(app.root_path, 'static', 'text_data', 'image_to_text_data')
            temp_file_path = os.path.join(temp_dir, 'temp_response.txt')
            with open(temp_file_path, 'r', encoding='utf-8') as temp_file:
                uploaded_image_description = temp_file.read().strip()

            # Clean up the description by removing extra spaces and line breaks
            uploaded_image_description = ' '.join(uploaded_image_description.split())
            
            lambda_payload = {
                    'hero': hero,
                    'personality': personality,
                    'sport': sport,
                    'color': color,
                    'action': action,
                    'uploaded_image_description': uploaded_image_description
                }

            # Call the API with the character prompt
            lambda_response = requests.post(
            LAMBDA_API_ENDPOINT,
            json=lambda_payload  # Make sure to send a JSON payload
            )
        
        else:
            # Use the standard prompt
            lambda_payload = {
                    'hero': hero,
                    'personality': personality,
                    'sport': sport,
                    'color': color,
                    'action': action
                }

            lambda_response = requests.post(
            LAMBDA_API_ENDPOINT,
            json=lambda_payload  # Make sure to send a JSON payload
            )

        logging.info(f"Generated Prompt: {final_prompt}")

        # Generate the unique filename for the image
        filename = formatted_filename(hero, personality, sport, color, action)

        if lambda_response.status_code == 200:
            # Process the response from the Lambda function
            result = lambda_response.json()
            
            # Extract image_url from the Lambda response if it's present
            image_url = result.get('image_url')

            if image_url:
                # Save image_original image fetched from OpenAI into the 'static/image_original' directory
                image_original_save_directory = os.path.join(app.root_path, 'static', 'image_original')
                os.makedirs(image_original_save_directory, exist_ok=True)
                image_original_file_path = os.path.join(image_original_save_directory, filename)

                # Download the image from OpenAI and save it
                img_response = requests.get(image_url)
                if img_response.status_code == 200:
                    with open(image_original_file_path, 'wb') as image_original_file:
                        image_original_file.write(img_response.content)
                    logging.info(f"Original image saved: {image_original_file_path}")

                    # Make a copy of the original image for watermarking
                    watermarked_image = Image.open(image_original_file_path).convert("RGBA")

                    # Define the watermark path
                    watermark_path = os.path.join(app.root_path, 'static', 'watermark', 'watermark.png')

                    #   Apply watermark to the copy of the image
                    watermark = Image.open(watermark_path).convert("RGBA")
                    watermark = watermark.resize(watermarked_image.size, Image.LANCZOS)
                    combined = Image.alpha_composite(watermarked_image, watermark)
                    combined = combined.convert("RGB")  # Convert back to RGB if you don't need the alpha channel

                    # Define the path to save the watermarked image
                    watermark_save_directory = os.path.join(app.root_path, 'static', 'watermarked_image')
                    os.makedirs(watermark_save_directory, exist_ok=True)
                    watermarked_file_path = os.path.join(watermark_save_directory, "(Watermark) " + filename)

                    # Save the watermarked image as a separate file
                    combined.save(watermarked_file_path)
                    logging.info(f"Watermarked image saved: {watermarked_file_path}")

                    # The response should include a URL for the image_original (unwatermarked) and watermarked images to display in the HTML container
                    return jsonify({
                        'image_original_url': url_for('static', filename=os.path.join('image_original', filename)), # URL for the image_original image
                        'watermarked_url': url_for('static', filename=os.path.join('watermarked_image', "(Watermark) " + filename)), # URL for the watermarked image
                        'filename': filename # The image_original filename you use to fetch the image_original image for vectorizing
                    })

                else:
                    error_message = "Failed to download the image from OpenAI."
                    logging.error(error_message)
                    return jsonify({'error': error_message}), img_response.status_code

            else:
                error_message = "Failed to download the image from OpenAI."
                logging.error(f"{error_message}: {img_response.status_code}")
                return jsonify({'error': error_message}), img_response.status_code

        else:
            error_message = f"Error invoking Lambda function: {lambda_response.status_code}, {lambda_response.text}"
            logging.error(error_message)
            return jsonify({'error': error_message}), lambda_response.status_code

    # Render the initial form template on GET or if POST fails
    return render_template('index.html', image
                           =image_url, error=error_message,
                           hero=hero, personality=personality, sport=sport, color=color, action=action)

#Vectorize Image Route
@app.route('/vectorize-image', methods=['POST'])
def vectorize_image_route():
    logging.info("Vectorize_image route called.")
    filename = request.form.get('filename')

    if not filename:
        logging.error("No filename provided in request.")
        return jsonify({'error': 'No filename provided.'}), 400

    logging.info(f"Requested to vectorize file: {filename}")

    # Call upscale_image before continuing with vectorization
    upscale_successful, upscaled_content = upscale_image(filename)
    if not upscale_successful:
        logging.error('Failed to upscale image.')
        return jsonify({'error': 'Failed to upscale image.'}), 500

    # Upscale image saving
    raw_folder = os.path.join(app.root_path, 'static', 'image_hd')
    os.makedirs(raw_folder, exist_ok=True)
    upscaled_image_path = os.path.join(raw_folder, filename)
    with open(upscaled_image_path, 'wb') as image_hd_file:
        image_hd_file.write(upscaled_content)

    logging.info(f"Upscaled image saved at: {upscaled_image_path}")

    # Directory for background removed images
    image_no_background_path = os.path.join(app.root_path, 'static', 'image_no_background')
    os.makedirs(image_no_background_path, exist_ok=True)
    image_no_background_file_path = os.path.join(image_no_background_path, filename)

    background_removed = False

    if is_background_white(upscaled_image_path):
        # Using OpenCV method for removal if the background is white
        logging.info("Background is predominantly white. Using OpenCV method for removal.")
        background_removed = remove_background_and_preserve_white(upscaled_image_path, image_no_background_file_path)
        logging.info("Background removed using OpenCV method.")
        background_removed = True
    else:
        # Prepare the image for the background removal API call when background is not white
        logging.info("Background is not predominantly white. Using API method for removal.")
        background_removal_successful, background_removed_content = remove_background_image(filename, upscaled_image_path)
        if background_removal_successful:
            # Create object mask with smoothed edges and write to file
            final_image_content = create_object_mask_otherbackground(background_removed_content)
            if final_image_content:
                with open(image_no_background_file_path, 'wb') as image_no_background_file:
                    image_no_background_file.write(final_image_content)
                logging.info("Background removed using API method, mask smoothed, and image saved.")
                background_removed = True
            else:
                logging.error("Failed to process the mask after background removal.")
        else:
            logging.error("Failed to remove background using API method.")

    if background_removed:
        try:
            vectorized_content = vectorize_image(filename, image_no_background_file_path)

            if vectorized_content:
                # Directory for vectorized images
                vectorized_path = os.path.join(app.root_path, 'static', 'image_vectorized')
                os.makedirs(vectorized_path, exist_ok=True)

                vectorized_filename = '(Vector) ' + filename.replace('.png', '.svg')
                vectorized_file_path = os.path.join(vectorized_path, vectorized_filename)

                # Save the vectorized SVG file
                with open(vectorized_file_path, 'wb') as file:
                    file.write(vectorized_content)
                logging.info(f"Vectorized SVG image file written successfully at: {vectorized_file_path}")

                png_file_path = vectorized_file_path.replace('.svg', '.png')
                convert_svg_to_png(vectorized_file_path, png_file_path)
                logging.info("SVG to PNG conversion complete.")

                # Step 8-9: Apply watermark to PNG and save in 'static/watermarked_vector'
                vector_dir = os.path.join(app.root_path, 'static', 'watermarked_vector')
                os.makedirs(vector_dir, exist_ok=True)

                watermarked_png_path = os.path.join(vector_dir, f"Watermarked_{vectorized_filename.replace('.svg', '.png')}")
                watermark_path = os.path.join(app.root_path, 'static', 'watermark', 'watermark.png')
                add_png_watermark(png_file_path, watermark_path, watermarked_png_path)
                logging.info("Watermarked PNG image saved.")

                watermarked_image_url = url_for('static', filename=os.path.join('watermarked_vector', os.path.basename(watermarked_png_path)))
                logging.info(f"Returning watermarked PNG image URL: {watermarked_image_url}")

                return jsonify({'url': watermarked_image_url, 'svg_filename': vectorized_filename})
            else:
                error_message = "Failed to vectorize image."
                logging.error(error_message)
                return jsonify({'error': error_message}), 500

        except requests.exceptions.RequestException as e:
            logging.error(traceback.format_exc())
            return jsonify({'error': str(e)}), 500
        except Exception as e:
            logging.error(traceback.format_exc())
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Background removal was not successful.'}), 500

#Temp code
OPENAI_API_KEY = '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'

#Analyze Image Route
@app.route('/analyze-image', methods=['POST'])
def analyze_image():
    try:
        if 'image-upload' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['image-upload']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Extract file extension and construct new filename
        _, file_extension = os.path.splitext(file.filename)
        standardized_filename = "image" + file_extension

        # Save the file with the new standardized filename
        upload_directory = os.path.join(app.root_path, 'static', 'uploads')
        os.makedirs(upload_directory, exist_ok=True)
        filepath = os.path.join(upload_directory, secure_filename(standardized_filename))
        file.save(filepath)

        # Generate URL for the uploaded image
        uploaded_image_url = url_for('static', filename=os.path.join('uploads', secure_filename(standardized_filename)), _external=True)

        # Call the OpenAI API
        response = image_to_txt(uploaded_image_url)

        if response.status_code == 200:
            r = response.json()
            api_response_text = r["choices"][0]["message"]["content"]

            # Directory for storing temporary files
            temp_dir = os.path.join(app.root_path, 'static', 'text_data', 'image_to_text_data')
            os.makedirs(temp_dir, exist_ok=True)

            # Create a temporary file in the specified directory
            temp_file_path = os.path.join(temp_dir, 'temp_response.txt')
            with open(temp_file_path, 'w', encoding='utf-8') as temp_file:
                temp_file.write(api_response_text)

            # Return the path of the temporary file
            return jsonify({'temp_file_path': temp_file_path})

        else:
            logging.error(f'Non-200 response from OpenAI API: {response.status_code} {response.text}')
            return jsonify({'error': 'Error from OpenAI API'}), response.status_code

    except Exception as e:
        logging.error(f'An error occurred: {e}')
        logging.error(traceback.format_exc())  # This logs the full traceback
        return jsonify({'error': 'Server Error'}), 500
    

####Routes###############################################################################

if __name__ == '__main__':
    app.run(debug=True)
