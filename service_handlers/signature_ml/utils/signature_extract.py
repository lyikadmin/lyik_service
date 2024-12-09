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
        None
    """

    # Step 1: Detect signatures in the document
    detected_images = detect_signature(document_image_path)
    if not detected_images:
        print("Signature detection failed.")
        return

    # Get the first detected signature.
    signature_cropped_image_buffer = detected_images[0]

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
    detected_images = detect.detect(document_image_path)
    processed_images = []

    if detected_images:
        for img_buffer in detected_images:
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

