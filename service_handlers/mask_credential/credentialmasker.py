import cv2
import pytesseract
import base64
from typing_extensions import Literal

CREDENTIAL_TYPES = Literal["aadhaar"]


def mask_credential(
    image_path: str,
    mask_value: str | None = None,
    credential_type: CREDENTIAL_TYPES = "aadhaar",
) -> str:
    """Masks the given credential, provided the type."""
    if credential_type == "aadhaar":
        return mask_aadhaar(image_path=image_path, mask_value=mask_value)
    else:
        raise Exception("Unsupported credential type for masking.")


def mask_aadhaar(image_path: str, mask_value: str) -> str:
    """Masks Aadhaar numbers in an image, then returns it as a Base64 string."""
    image = cv2.imread(image_path)

    # chunk_count = 0
    # image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # image = Image.open(image_path)

    # Extract text and bounding boxes
    data = pytesseract.image_to_data(
        image, output_type=pytesseract.Output.DICT, lang="eng", config="--psm 12"
    )

    for i, text in enumerate(data["text"]):
        text = text.strip()
        formatted_text = text.replace(" ", "")  # Remove spaces

        if (
            len(formatted_text) == 4 
            and formatted_text.isdigit() 
            and (str(formatted_text) in str(mask_value) if mask_value else True)
        ):  # Aadhaar number check
            x, y, w, h = (
                data["left"][i],
                data["top"][i],
                data["width"][i],
                data["height"][i],
            )

            # chunk_count += 1
            # if chunk_count == 3:
            #     chunk_count = 0
            #     continue

            # Mask Aadhaar number (black rectangle)
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 0), -1)

    # Encode processed image in memory.
    _, buffer = cv2.imencode(".jpg", image)
    encoded_file = base64.b64encode(buffer).decode("utf-8")

    # with open("output_aadhaar_file.jpg", "wb") as file:
    #     file.write(base64.b64decode(encoded_file))
    return encoded_file
