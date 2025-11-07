# import pytesseract
# --- imports -----------------------------------------------------------------
import io
import logging
import mimetypes
import tempfile
from pathlib import Path
from typing import List, Optional

import filetype  # pip install filetype
import fitz  # pip install pymupdf
from PIL import Image
from paddleocr import PaddleOCR

from paddleocr.ppocr.utils.logging import get_logger

# New (for in-memory OCR)
import numpy as np  # pip install numpy
import cv2          # pip install opencv-python

# --- feature flags ------------------------------------------------------------
SUPPORT_PDF_IMAGES = False  # set False to disable OCR for images inside PDFs

logger = get_logger()
logger.setLevel(logging.ERROR)
# try:
#     from src.core.logger import logger  # your project's logger
# except Exception:
#     logger = logging.getLogger(__name__)
#     logging.basicConfig(level=logging.INFO)


# --- OCR engines --------------------------------------------------------------


class TextExtractor:
    """
    Internally initialize PaddleOCR once and reuse it.
    """

    def __init__(self):
        # minimize console noise (match your original intent)
        logger.setLevel(logging.ERROR)
        # Initialize OCR once
        self.ocr = PaddleOCR(
            use_angle_cls=True, lang="en"
        )  # use_gpu=False by default if no GPU

    def extract_text(self, img: str) -> str:
        """
        Image OCR with the same signature as before.
        Keeps a light confidence filter and concatenates lines.
        """
        try:
            ret = self.ocr.ocr(img=img, det=True, rec=True)
        except Exception as e:
            logger.error(f"PaddleOCR failed on image {img}: {e}")
            return ""

        full_text = []
        try:
            if ret and ret[0]:
                for line in ret[0]:
                    # expected: (box, (text, score))
                    _, (text, score) = line
                    if (
                        isinstance(text, str)
                        and text.strip()
                        and (score is None or score >= 0.80)
                    ):
                        full_text.append(text.strip())
        except Exception as e:
            logger.error(f"OCR parse error for image {img}: {e}")

        return "\n".join(full_text)


text_extractor = TextExtractor()


# --- PDF helpers --------------------------------------------------------------

def _extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        texts: List[str] = []
        for page in doc:
            t = page.get_text("text")
            if t and t.strip():
                texts.append(t.strip())
        return "\n".join(texts).strip()
    finally:
        doc.close()


def _pdf_has_images(pdf_bytes: bytes) -> bool:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        for page in doc:
            if page.get_images(full=True):
                return True
        return False
    finally:
        doc.close()


def _extract_images_from_pdf_bytes(pdf_bytes: bytes) -> List[Image.Image]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images: List[Image.Image] = []
    try:
        for page in doc:
            for img in page.get_images(full=True):
                xref = img[0]
                base = doc.extract_image(xref)
                img_bytes = base.get("image")
                if not img_bytes:
                    continue
                try:
                    pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                    images.append(pil_img)
                except Exception as e:
                    logger.error(f"Failed to decode embedded image (xref={xref}): {e}")
    finally:
        doc.close()
    return images


def ocr_text_only_pdf(pdf_bytes: bytes) -> str:
    """Extract copyable text from textual PDFs (fast, no image OCR)."""
    return _extract_text_from_pdf_bytes(pdf_bytes)


# --- In-memory OCR helpers (NumPy / OpenCV) ----------------------------------

def _pil_to_cv_bgr(pil_img: Image.Image):
    """Convert PIL RGB image to OpenCV BGR ndarray."""
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def _ocr_pil_image(pil_img: Image.Image) -> str:
    """
    OCR a PIL image without writing to disk by passing a NumPy array (BGR) to PaddleOCR.
    """
    try:
        arr_bgr = _pil_to_cv_bgr(pil_img)
        ret = text_extractor.ocr.ocr(img=arr_bgr, det=True, rec=True)
    except Exception as e:
        logger.error(f"In-memory OCR failed: {e}")
        return ""

    lines = []
    try:
        if ret and ret[0]:
            for line in ret[0]:
                _, (text, score) = line
                if (
                    isinstance(text, str)
                    and text.strip()
                    and (score is None or score >= 0.80)
                ):
                    lines.append(text.strip())
    except Exception as e:
        logger.error(f"In-memory OCR parse error: {e}")

    return "\n".join(lines)


def ocr_mixed_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text layer (if any) + OCR any embedded raster images.
    Uses in-memory OCR (NumPy) for images to avoid temp files.
    """
    text_part = _extract_text_from_pdf_bytes(pdf_bytes)
    images = _extract_images_from_pdf_bytes(pdf_bytes)

    image_texts: List[str] = []
    for pil_image in images:
        try:
            image_texts.append(_ocr_pil_image(pil_image))
        except Exception as e:
            logger.error(f"Image OCR in mixed PDF failed: {e}")

    combined = "\n".join([t for t in [text_part] + image_texts if t])
    return combined.strip()


def ocr_pdf(pdf_path: str, *, support_images: bool = SUPPORT_PDF_IMAGES) -> str:
    """Detect PDF type (text-only or mixed) and run the correct pipeline."""
    logger.info(f"Processing PDF: {pdf_path}")
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    try:
        if not support_images:
            # Always return only the copyable text layer; no image OCR even if images exist.
            return ocr_text_only_pdf(pdf_bytes)

        # Default behavior (support_images=True): original flow
        if _pdf_has_images(pdf_bytes):
            logger.info("Detected images/text — running mixed OCR pipeline...")
            return ocr_mixed_pdf(pdf_bytes)
        else:
            logger.info("Detected textual PDF — running text-only extraction...")
            return ocr_text_only_pdf(pdf_bytes)
    except Exception as e:
        logger.error(f"PDF OCR failed for {pdf_path}: {e}")
        return ""


# --- Image vs PDF router ------------------------------------------------------

def process_file(file_path: str, *, support_images: bool = SUPPORT_PDF_IMAGES) -> str:
    """
    Detect file type via magic bytes (fallback to extension) and run the right pipeline.
    Signature matches your proposal. The support_images flag controls PDF image OCR.
    """
    path = Path(file_path)

    # 1) Magic bytes
    mime: Optional[str] = None
    try:
        kind = filetype.guess(str(path))
        if kind:
            mime = kind.mime
            logger.info(f"[magic] MIME: {mime}")
    except Exception as e:
        logger.warning(f"filetype.guess failed: {e}")

    # 2) Fallback to extension
    if not mime:
        mime, _ = mimetypes.guess_type(str(path))
        logger.info(f"[ext] MIME: {mime}")

    if not mime:
        raise ValueError(f"Could not detect MIME type for file: {file_path}")

    if mime.startswith("image/"):
        logger.info("Detected Image → running image OCR")
        return text_extractor.extract_text(str(path))

    if mime == "application/pdf":
        logger.info("Detected PDF → running PDF OCR")
        return ocr_pdf(str(path), support_images=support_images)

    raise ValueError(f"Unsupported MIME type: {mime}")
