import boto3
import cv2
import numpy as np
import os
from botocore.exceptions import ClientError
import json
from urllib.parse import urlparse
import logging

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb_client = boto3.client('dynamodb')
dynamodb_resource = boto3.resource('dynamodb')

# Define your bucket and table names
DYNAMODB_TABLE_NAME = 'RenderRequests'
S3_BUCKET_NAME = 'draft-images-bucket'
S3_OUTPUT_FOLDER = 'image_no_background'
VECTOR_STATUS_TABLE_NAME = 'VectorStatus'

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Function to update the VectorStatus in DynamoDB
def update_vector_status(render_id, status):
    table = dynamodb_resource.Table(VECTOR_STATUS_TABLE_NAME)
    try:
        response = table.update_item(
            Key={'renderId': render_id},
            UpdateExpression='SET renderStatus = :val',
            ExpressionAttributeValues={':val': status},
            ReturnValues="UPDATED_NEW"
        )
        logger.info(f"VectorStatus updated for renderId: {render_id} to {status}%")
    except Exception as e:
        logger.error(f"Failed to update VectorStatus for renderId: {render_id}. Error: {str(e)}")


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

# The Lambda handler
def lambda_handler(event, context):
    try:
        # Extract renderId from the event
        renderId = event['renderId']

        # Update VectorStatus to 33% at the start
        update_vector_status(renderId, 60)
        
        # Get the image URL and filename from DynamoDB
        response = dynamodb_client.get_item(
            TableName=DYNAMODB_TABLE_NAME,
            Key={'renderId': {'S': renderId}}
        )
        # Assuming 'upscaledImageUrl' directly stores the S3 key
        s3_key = response['Item']['upscaledImageUrl']['S']
        filename = response['Item']['filename']['S']
        
        # Define local file paths for input and output images based on the filename
        input_image_path = f'/tmp/{filename}'
        output_image_path = f'/tmp/processed_{filename}'
        
        # Let's assume s3_key might be a full S3 URL or just an S3 key
        s3_url = urlparse(s3_key)

        # Extract the path component and remove any leading '/'
        extracted_key = s3_url.path.lstrip('/')

        # If extracted_key is empty, s3_key was likely just a key to start with (or an invalid URL)
        if not extracted_key:
            extracted_key = s3_key  # fallback to using s3_key directly

        print(f"Attempting to download from Bucket: {S3_BUCKET_NAME}, Key: {extracted_key}")

        # Perform the S3 download operation using the S3 key
        try:
            s3_client.download_file(S3_BUCKET_NAME, extracted_key, input_image_path)
        except ClientError as error:
            print(f"Error downloading file from S3: {error}")
            raise

        # Process the image
        remove_background_and_preserve_white(input_image_path, output_image_path)
        
        update_vector_status(renderId, 85)

        # Upload the processed image to S3
        output_s3_path = f"{S3_OUTPUT_FOLDER}/{filename}"  # Adjust path as needed
        try:
            s3_client.upload_file(output_image_path, S3_BUCKET_NAME, output_s3_path)
        except ClientError as error:
            print(f"Error uploading file to S3: {error}")
            raise
        
        # Update the DynamoDB table with the new image location
        full_s3_url = f"s3://{S3_BUCKET_NAME}/{output_s3_path}"
        dynamodb_client.update_item(
            TableName=DYNAMODB_TABLE_NAME,
            Key={'renderId': {'S': renderId}},
            UpdateExpression='SET imageNoBackgroundUrl = :val1',
            ExpressionAttributeValues={
                ':val1': {'S': full_s3_url}  # Corrected to use 'output_s3_key'
            }
        )
        
        # Construct the response or perform additional actions as needed
        # Note: Adjust this part based on how you want to handle the Lambda's response
        # Construct the payload to pass to the next step
        next_step_payload = {
            'renderId': renderId,
        }

        # Return this payload directly
        return next_step_payload
    
    except Exception as e:
        print(f"An error occurred: {e}")
        # Consider including error details in the response if this aligns with your error handling strategy
        return {
            'statusCode': 500,
            'error': str(e)
        }
