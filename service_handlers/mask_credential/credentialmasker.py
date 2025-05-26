import cv2
import pytesseract
import base64
from typing_extensions import Literal
from .aadhaar_node import MaskAadhaarNode
from PIL import Image, ImageDraw, ImageOps, ExifTags
import io
from tempfile import NamedTemporaryFile

CREDENTIAL_TYPES = Literal["aadhaar"]

def print_exif_orientation(img: Image.Image):
    try:
        exif = img._getexif()
        if exif:
            for tag, val in exif.items():
                if ExifTags.TAGS.get(tag) == "Orientation":
                    print(f"[DEBUG] Original EXIF Orientation: {val}")
                    return val
        print("[DEBUG] No EXIF Orientation tag found.")
    except Exception as e:
        print(f"[DEBUG] Failed to get EXIF Orientation: {e}")
    return None

async def mask_credential(
    image_path: str,
    mask_value: str | None = None,
    credential_type: CREDENTIAL_TYPES = "aadhaar",
) -> str:
    """Masks the given credential, provided the type."""
    if credential_type == "aadhaar":
        return await mask_aadhaar(image_path=image_path, mask_value=mask_value)
    else:
        raise Exception("Unsupported credential type for masking.")

async def mask_aadhaar_with_llm(image_path: str, mask_value: str) -> str:
    """
    Detects every instance of `mask_value` in the Aadhaar image and blacks it out.
    Returns a base64-encoded JPEG string.
    """

    # -- 1. Load and put image upright -----------------------------------------
    img = Image.open(image_path)
    img = ImageOps.exif_transpose(img)           # honour Orientation tag
    img.info.pop("exif", None)                   # strip all EXIF afterwards

    # -- 2. Create a 1024-px thumbnail for the LLM -----------------------------
    thumb = img.copy()
    thumb.thumbnail((1024, 1024))
    try:
        with NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            thumb.save(tmp.name, quality=88)
            aadhaar_node = MaskAadhaarNode()
            boxes = await aadhaar_node.extract(tmp.name, mask_value)
            # boxes = await MaskAadhaarNode().extract(tmp.name, mask_value)
    except Exception as e:
        print(e)

    # -- 3. Draw rectangles on the *full-size* image ---------------------------
    draw = ImageDraw.Draw(img)

    for b in boxes.bounding_boxes:
        # normalised → absolute
        x = int(b.top_left[0] * img.width)
        y = int(b.top_left[1] * img.height)
        w = int(b.width       * img.width)
        h = int(b.height      * img.height)

        draw.rectangle([x, y, x + w, y + h], fill="black")

    # -- 4. Return as base64 ----------------------------------------------------
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


async def mask_aadhaar(image_path: str, mask_value: str) -> str:
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