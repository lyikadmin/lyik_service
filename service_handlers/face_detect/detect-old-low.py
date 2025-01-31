import cv2
from models import ResponseStatusEnum, StandardResponse


def detect_face(image_path, required_face_coverage) -> StandardResponse:
    """
    Detects faces in an image, and passes only if there is a single face covering atleast the area required.
    1. image_path = Path of the image used for detecting face
    2. required_face_coverage = Value in of area required to be covered by the face bounding box (e.g. 25 for 25%)
    """
    # 1. Load the Haar cascade for frontal face detection
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    # 2. Read the image from file
    image = cv2.imread(image_path)
    if image is None:
        message = "Invalid image file"
        return StandardResponse(
            status=ResponseStatusEnum.failure, message=message, result=message
        )

    # 3. Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    (h, w) = image.shape[:2]
    image_area = h * w

    # 4. Detect faces using the Haar cascade
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,  # adjust as needed
        minNeighbors=5,  # adjust as needed
        minSize=(30, 30),  # adjust as nereturn Falseeded
    )

    # 5. Check that exactly one face is detected
    if len(faces) != 1:
        message = f"Expected 1 face, found {len(faces)}"
        return StandardResponse(
            status=ResponseStatusEnum.failure, message=message, result=message
        )

    # 6. Calculate the coverage of the detected face
    (x, y, fw, fh) = faces[0]
    face_area = fw * fh
    coverage = (face_area / image_area) * 100

    if coverage < required_face_coverage:
        message = f"Face covers {coverage:.2f}% of the image "
        result = f"(needs ≥{required_face_coverage}%)"
        return StandardResponse(
            status=ResponseStatusEnum.failure, message=message, result=result
        )

    message = f"Valid single face with sufficient coverage {coverage:.2f}%"
    return StandardResponse(
        status=ResponseStatusEnum.success, message=message, result=message
    )
