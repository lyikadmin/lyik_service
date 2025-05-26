import cv2
import pytesseract
import base64

async def mask_aadhaar_tesseract(image_path: str, mask_value: str) -> str:
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

    _, buffer = cv2.imencode(".jpg", image)
    encoded_file = base64.b64encode(buffer).decode("utf-8")

    return encoded_file