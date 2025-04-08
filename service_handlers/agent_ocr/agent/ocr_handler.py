import pytesseract
from PIL import Image
from .utils import remove_newline_characters
import easyocr
from paddleocr import PaddleOCR
from typing import List
import json

def run_tesseract(image: Image.Image) -> str:
    try:
        text = pytesseract.image_to_string(image, lang="eng", config="--psm 1")
        text += pytesseract.image_to_string(image, lang="eng", config="--psm 12")
        return remove_newline_characters(text)
    except Exception as e:
        print(f"Exception for ocr tesseract: {str(e)}")
        return ""

def run_easyocr(image_path: str) -> str:
    try:
        reader = easyocr.Reader(['en'], gpu=False)
        results = reader.readtext(image_path, detail=0)
        return remove_newline_characters(" ".join(results))
    except Exception as e:
        print(f"Exception for ocr easyocr: {str(e)}")
        return ""

def run_paddleocr(image_path: str) -> str:
    try:
        ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)
        result = ocr.ocr(image_path, cls=True)
        lines = [line[1][0] for line in result[0]]
        return remove_newline_characters(" ".join(lines))
    except Exception as e:
        print(f"Exception for ocr paddleocr: {str(e)}")
        return ""
