import cv2
import pytesseract
import base64
from typing_extensions import Literal
from .maskers.masker_tesseract import mask_aadhaar_tesseract
from .maskers.masker_llm import mask_aadhaar_with_llm
from .maskers.masker_paddle import mask_aadhaar_paddle

CREDENTIAL_TYPES = Literal["aadhaar"]

async def mask_credential(
    image_path: str,
    mask_value: str | None = None,
    credential_type: CREDENTIAL_TYPES = "aadhaar",
) -> str:
    """Masks the given credential, provided the type."""
    if credential_type == "aadhaar":
        return await mask_aadhaar_paddle(image_path=image_path, mask_value=mask_value)
        # return await mask_aadhaar_tesseract(image_path=image_path, mask_value=mask_value)
        # return await mask_aadhaar_with_llm(image_path=image_path, mask_value=mask_value)
    else:
        raise Exception("Unsupported credential type for masking.")