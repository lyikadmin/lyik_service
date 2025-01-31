from io import BytesIO
from PIL import Image
from ..SOURCE.yolo_files import detect
from ..utils import gan_utils, cv_utils
from typing import Union

import warnings
warnings.filterwarnings("ignore")

import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logging.getLogger().setLevel(logging.INFO)


def extract_signature(document_image_path: str) -> Union[BytesIO, None]:
    """
    Main function to detect and clean a signature from a document image.

    Args:
        document_image_path (str): Path to the document image.

    Returns:
        Bytes, if signature is detected, string if known error, None if not detected.
    """

    # Step 1: Detect signatures in the document
    detect_signature_response = detect_signature(document_image_path)
    if not detect_signature_response:
        print("Signature detection failed.")
        return

    # Returns string error message if the coverage is not as expected
    if isinstance(detect_signature_response, str):
        return detect_signature_response
    
    if len(detect_signature_response)>1:
        print(f"Detected {len(detect_signature_response)} signature(s)")
        return "Detected multiple signatures. Make sure there is only a single signature, and write it in a clean manner without gaps."

    # Get the first detected signature.
    signature_cropped_image_buffer = detect_signature_response[0]

    # Step 2: Clean the detected signature
    cleaned_image = clean_signature(signature_cropped_image_buffer)
    if not cleaned_image:
        print("Signature cleaning failed.")
        return
    
    return cleaned_image


def detect_signature(document_image_path: str) -> list[BytesIO]:
    """
    Detects signatures in the document image using YOLO,
    applies make_square to each detected signature, and returns in-memory images.

    Args:
        document_image_path (str): Path to the document image.

    Returns:
        list[BytesIO]: List of BytesIO objects containing the processed signature images.
    """
    detect_image_response = detect.detect(image_path=document_image_path, check_wet_signature_coverage=True, coverage_threshold=0.0)

    # Returns string error message if the coverage is not as expected
    if isinstance(detect_image_response, str):
        return detect_image_response

    processed_images = []


    if detect_image_response:
        for img_buffer in detect_image_response:
            # Load the image from the buffer and process it
            img_buffer.seek(0)
            detected_image = Image.open(img_buffer).convert("RGB")
            squared_image = gan_utils.make_square(detected_image)

            # Save the squared image back to a new BytesIO object
            new_img_buffer = BytesIO()
            squared_image.save(new_img_buffer, format="JPEG")
            new_img_buffer.seek(0)
            processed_images.append(new_img_buffer)

    return processed_images


def clean_signature(image_buffer: BytesIO) -> Union[BytesIO, None]:
    """
    Cleans the signature image and applies high-contrast cleaning
    as the final step.

    Args:
        image_buffer (BytesIO): BytesIO object of the detected signature image.

    Returns:
        Union[BytesIO, None]: BytesIO object of the cleaned and processed image or None on failure.
    """
    # Convert the input BytesIO object to an image and save it for GAN processing
    input_image = Image.open(image_buffer)

    # Apply high-contrast cleaning
    high_contrast_image = cv_utils.high_contrast_clean(input_image)

    # Save the high-contrast image back to a BytesIO object
    final_img_buffer = BytesIO()
    high_contrast_image.save(final_img_buffer, format="JPEG")
    final_img_buffer.seek(0)

    return final_img_buffer

