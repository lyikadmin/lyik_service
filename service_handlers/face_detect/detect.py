import cv2
from models import ResponseStatusEnum, StandardResponse
import cv2
import numpy as np
import math


# Load the pre-trained DNN face detection model
prototxt_path = "service_handlers/face_detect/assets/deploy.prototxt"
caffemodel_path = (
    "service_handlers/face_detect/assets/res10_300x300_ssd_iter_140000_fp16.caffemodel"
)
net = cv2.dnn.readNetFromCaffe(prototxt_path, caffemodel_path)


def detect_face(image_path: str, required_face_coverage: float) -> StandardResponse:
    """
    Detects faces in an image using a DNN-based model, and passes only if there is a single face
    covering at least the required area AND the face is centered in the image.

    Args:
        image_path (str): Path of the image used for detecting face.
        required_face_coverage (float): Minimum percentage of the image area that the face bounding box must cover (e.g., 25 for 25%).

    Returns:
        StandardResponse: A response object containing the status, message, and result.
    """
    # 1. Load the image
    image = cv2.imread(image_path)
    if image is None:
        message = "Invalid image file"
        return StandardResponse(
            status=ResponseStatusEnum.failure, message=message, result=message
        )

    # 2. Get image dimensions and calculate total area
    (h, w) = image.shape[:2]
    image_area = h * w

    # 3. Preprocess the image for face detection
    blob = cv2.dnn.blobFromImage(
        image, scalefactor=1.0, size=(300, 300), mean=(104.0, 177.0, 123.0)
    )
    net.setInput(blob)
    detections = net.forward()

    # 4. Extract detected faces and their bounding boxes
    faces = []
    confidence_threshold = 0.5  # Adjust as needed

    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > confidence_threshold:
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            # Ensure bounding box stays within image dimensions
            startX = max(0, startX)
            startY = max(0, startY)
            endX = min(w, endX)
            endY = min(h, endY)

            faces.append((startX, startY, endX, endY))

    # 5. Check that exactly one face is detected
    if len(faces) != 1:
        message = f"Expected 1 face, found {len(faces)}"
        return StandardResponse(
            status=ResponseStatusEnum.failure, message=message, result=message
        )

    # 6. Calculate the coverage of the detected face
    (startX, startY, endX, endY) = faces[0]
    face_area = (endX - startX) * (endY - startY)
    coverage = (face_area / image_area) * 100
    print(
        f"Detected 1 Face with coverage {math.floor(coverage)}%. Required coverage is {required_face_coverage}%"
    )
    if coverage < required_face_coverage:
        message = f"Face covers {coverage:.2f}% of the image"
        result = f"(needs ≥{required_face_coverage}%)"
        return StandardResponse(
            status=ResponseStatusEnum.failure, message=message, result=result
        )

    # # 7. To check if the face is centered

    # Method 1: With ranges from the corners
    # Defining the region in normalized coordinates (0.0 to 1.0 range)
    region_x_min, region_y_min = 0.10, 0.10  # top-left corner (20% from left and top)
    region_x_max, region_y_max = (
        0.90,
        0.90,
    )  # bottom-right corner (80% from left and top)

    # Convert normalized coordinates to actual pixel coordinates
    allowed_min_x = int(region_x_min * w)
    allowed_min_y = int(region_y_min * h)
    allowed_max_x = int(region_x_max * w)
    allowed_max_y = int(region_y_max * h)

    save_detected_face(
        image,
        allowed_min_x,
        allowed_min_y,
        allowed_max_x,
        allowed_max_y,
        startX,
        startY,
        endX,
        endY,
    )
    
    # Check if the detected face is completely within the defined region
    print(f"Photo coordinate startX ({startX}) >= min_x ({allowed_min_x}) -> {startX >= allowed_min_x}")
    print(f"Photo coordinate startY ({startY}) >= min_y ({allowed_min_y}) -> {startY >= allowed_min_y}")
    print(f"Photo coordinate endX ({endX}) <= max_x ({allowed_max_x}) -> {endX <= allowed_max_x}")
    print(f"Photo coordinate endY ({endY}) <= max_y ({allowed_max_y}) -> {endY <= allowed_max_y}")

    # Check if face is within the region
    is_within = (
        startX >= allowed_min_x,
        startY >= allowed_min_y,
        endX <= allowed_max_x,
        endY <= allowed_max_y,
    )

    if not all(is_within):
        print("face not whithin region!")
        message = "Face is not within the specified region. Please readjust the face to the correct location."
        return StandardResponse(
            status=ResponseStatusEnum.failure, message=message, result=message
        )

    # # Method 2: with specified coordinates
    # allowed_min_x = 100
    # allowed_min_y = 50
    # allowed_max_x = 300
    # allowed_max_y = 350

    # # Where (startX, startY, endX, endY) is your detected face bounding box
    # if (
    #     startX < allowed_min_x or
    #     startY < allowed_min_y or
    #     endX > allowed_max_x or
    #     endY > allowed_max_y
    # ):
    #     message = "Face is not within the specified region."
    #     return StandardResponse(
    #         status=ResponseStatusEnum.failure,
    #         message=message,
    #         result=message
    #     )

    # 8. Return success response
    message = f"Valid single face with sufficient coverage {coverage:.2f}% (centered)"
    return StandardResponse(
        status=ResponseStatusEnum.success, message=message, result=message
    )


def save_detected_face(
    image,
    allowed_min_x,
    allowed_min_y,
    allowed_max_x,
    allowed_max_y,
    startX,
    startY,
    endX,
    endY,
):
    output_image_path = "service_handlers/face_detect/assets/detected.jpeg"
    # Draw the allowed bounding box (black rectangle)
    cv2.rectangle(
        image,
        (allowed_min_x, allowed_min_y),
        (allowed_max_x, allowed_max_y),
        (0, 0, 0),  # Black color (BGR format)
        2,  # Thickness
    )

    # Draw the detected face bounding box (yellow rectangle)
    cv2.rectangle(
        image,
        (startX, startY),
        (endX, endY),
        (0, 255, 255),  # Yellow color (BGR format)
        2,  # Thickness
    )

    # Save the processed image with visualizations
    cv2.imwrite(output_image_path, image)
