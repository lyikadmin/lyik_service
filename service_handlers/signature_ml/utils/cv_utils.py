import numpy as np
import cv2
from PIL import Image


def high_contrast_clean(pil_image, output_size=(512, 512)):
    """
    Extracts and cleans the signature from a grayscale PIL.Image.

    Args:
        pil_image (PIL.Image): Input image in PIL format.
        output_size (tuple): Desired output size as (width, height).

    Returns:
        PIL.Image: Cleaned and processed PIL.Image object.
    """
    # Convert the PIL.Image to a grayscale numpy array
    image = np.array(pil_image.convert("L"))

    # Upscale the image using the provided upscale function if its width is below the threshold
    image = upscale_image(image, min_width=900)

    # Remove black padding from the image
    image = remove_black_padding(image)

    # Apply slight gamma correction for subtle contrast enhancement
    gamma = 0.7  # Adjust gamma to enhance the contrast
    look_up_table = np.array([((i / 255.0) ** (1.0 / gamma)) * 255 for i in np.arange(0, 256)]).astype("uint8")
    image = cv2.LUT(image, look_up_table)

    # Apply Gaussian Blur to reduce noise (optional)
    blurred = cv2.GaussianBlur(image, (3, 3), 0)

    # Apply Otsu's thresholding to binarize the image
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Apply a mild morphological transformation to connect small gaps
    kernel = np.ones((2, 2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    # Resize the binary image to the desired output size with black padding
    binary = make_square(binary, size=output_size[0])

    # Convert the binary image back to a PIL.Image
    cleaned_image = Image.fromarray(binary)

    return cleaned_image

def make_square(image, size=512, fill_color=0):
    '''
    Resizes the image to occupy the full width or height, 
    and pads top/bottom or left/right to make it square (512x512).
    '''
    h, w = image.shape  # Single-channel image (grayscale)
    max_dim = max(h, w)
    
    # Scale the image to fit within the 512x512 frame while preserving aspect ratio
    scale = size / max_dim
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized_image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

    # Create a new image with the desired square size and fill color (0 for black)
    square_image = np.full((size, size), fill_color, dtype=np.uint8)

    # Center the resized image on the square canvas
    y_offset = (size - new_h) // 2
    x_offset = (size - new_w) // 2
    square_image[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized_image

    return square_image



def remove_black_padding(image):
    '''
    Detects and crops out black padding from the top and bottom of a grayscale image.
    '''
    # Calculate the row sums (sum of pixel values along each row)
    row_sums = np.sum(image, axis=1)
    
    # Find indices where the row sums are not zero (i.e., not black)
    non_black_indices = np.where(row_sums != 0)[0]

    if non_black_indices.size > 0:
        # Crop the image to remove black padding
        top = non_black_indices[0]
        bottom = non_black_indices[-1] + 1  # +1 to include the last non-black row
        return image[top:bottom, :]
    else:
        # Return the original image if no padding is detected
        return image

def upscale_image(image, min_width=900):
    '''
    Resizes the image to ensure its width is at least min_width,
    while preserving the aspect ratio.
    '''
    h, w = image.shape  # For grayscale images
    if w < min_width:
        # Calculate the scaling factor to make the width at least min_width
        scale = min_width / w
        new_w = min_width
        new_h = int(h * scale)
        image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
    return image