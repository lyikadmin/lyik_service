import pytesseract
from pytesseract import Output
from PIL import Image, ImageDraw, ImageOps
import numpy as np
import cv2
import base64
import io
import pathlib
import re
import logging
from typing import List, NamedTuple
from paddleocr import PaddleOCR
from paddleocr.ppocr.utils.logging import get_logger
import piexif

# ---------- Named Tuples ----------
class Box(NamedTuple):
    x: int
    y: int
    w: int
    h: int

class PatternMatches(NamedTuple):
    full_text: str
    match_text: str
    box: Box

# ---------- Tesseract Orientation Detection ----------
def get_image_orientation(img: Image.Image) -> int:
    osd = pytesseract.image_to_osd(img, output_type=Output.DICT)
    return int(osd["rotate"])

def rotate_image(img: Image.Image, angle: int) -> Image.Image:
    if angle == 0:
        return img
    return img.rotate(-angle, expand=True)

# ---------- PaddleOCR TextExtractor ----------
class TextExtractor:
    def __init__(self, ocr_instance: PaddleOCR):
        self.ocr = ocr_instance

    def get_bounding_box_from_result(
        self, ocr_result, match: List[re.Pattern]
    ) -> List[PatternMatches]:
        results = []
        if ocr_result and ocr_result[0]:
            for line in ocr_result[0]:
                box_coords, (text, score) = line
                if score > 0.8:
                    for pattern in match:
                        if pattern.search(text):
                            (x11, y11), (x12, y12), (x22, y22), (x21, y21) = box_coords
                            x_min = min(x11, x21)
                            y_min = min(y11, y12)
                            x_max = max(x12, x22)
                            y_max = max(y21, y22)
                            box = Box(x_min, y_min, x_max - x_min, y_max - y_min)
                            results.append(PatternMatches(text, pattern.pattern, box))
        return results

# ---------- TextMasker ----------
class TextMasker:
    def __init__(self, image: Image.Image):
        self.image = image.convert("RGB")
        self.draw = ImageDraw.Draw(self.image)

    def mask(self, text_to_mask: str, full_text: str, box: Box):
        res = re.search(text_to_mask, full_text)
        if not res:
            return
        start_idx, end_idx = res.span()
        text_len = len(full_text)

        x = box.x + (start_idx * box.w / text_len)
        w = (end_idx - start_idx) * box.w / text_len
        y, h = box.y, box.h

        self.draw.rectangle([x, y, x + w, y + h], fill="black")

    def to_base64(self) -> str:
        buffer = io.BytesIO()

        # Determine format (JPEG or PNG etc.)
        img_format = self.image.format or "JPEG"  # fallback to JPEG if format is missing

        if img_format.upper() == "JPEG":
            # Set EXIF Orientation to 1 (upright)
            exif_dict = {"0th": {piexif.ImageIFD.Orientation: 1}}
            exif_bytes = piexif.dump(exif_dict)
            self.image.save(buffer, format="JPEG", exif=exif_bytes)
        else:
            # PNG and others don't support EXIF; just save as-is
            self.image.save(buffer, format="PNG")

        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode("utf-8")

# ---------- Global PaddleOCR Instance ----------
logger = get_logger()
logger.setLevel(logging.ERROR)
PADDLE_OCR = PaddleOCR(use_angle_cls=True, lang="en")
EXTRACTOR = TextExtractor(PADDLE_OCR)

# ---------- Main Async Masking Function ----------
async def mask_aadhaar_paddle(image_path: str, mask_value: str) -> str:
    """
    Detects orientation using Tesseract, corrects image, runs PaddleOCR,
    masks Aadhaar-like text, and returns base64-encoded masked image.
    """
    # Step 1: Load and correct orientation
    path = pathlib.Path(image_path)
    assert path.exists(), f"Image not found: {image_path}"
    pil_img = Image.open(path)

    angle = get_image_orientation(pil_img)
    rotated_img = rotate_image(pil_img, angle)

    # Step 2: Prepare patterns
    # cleaned = mask_value.replace(" ", "")
    # patterns = [cleaned[i:i+4] for i in range(0, len(cleaned), 4)]
    # compiled_patterns = [re.compile(p) for p in patterns]

    compiled_patterns = [mask_value]

    print(f"The compiled patterns are: {compiled_patterns}")

    # Step 3: OCR and get matches
    np_img = np.array(rotated_img)
    ocr_result = PADDLE_OCR.ocr(np_img, det=True, rec=True)
    matches = EXTRACTOR.get_bounding_box_from_result(ocr_result, compiled_patterns)

    # Step 4: Mask and return base64
    masker = TextMasker(rotated_img)
    for match in matches:
        masker.mask(full_text=match.full_text, text_to_mask=match.match_text, box=match.box)

    return masker.to_base64()
