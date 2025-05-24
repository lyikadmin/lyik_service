# import pytesseract
# from PIL import Image
# from .utils import remove_newline_characters

from paddleocr import PaddleOCR
from paddleocr.ppocr.utils.logging import get_logger
import logging


# def run_tesseract(image: Image.Image) -> str:
#     try:
#         text = pytesseract.image_to_string(image, lang="eng", config="--psm 1")
#         text += pytesseract.image_to_string(image, lang="eng", config="--psm 12")
#         return remove_newline_characters(text)
#     except Exception as e:
#         print(f"Exception for ocr tesseract: {str(e)}")
#         return ""

# def run_paddleocr(image_path: str) -> str:
#     try:
#         ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)
#         result = ocr.ocr(image_path, cls=True)
#         lines = [line[1][0] for line in result[0]]
#         return remove_newline_characters(" ".join(lines))
#     except Exception as e:
#         print(f"Exception for ocr paddleocr: {str(e)}")
#         return ""
    
class TextExtractor:

    def __init__(self):
        # Set paddle ocr logging off ! It prints a whole of messages
        logger = get_logger()
        logger.setLevel(logging.ERROR)

        # Initialize the OCR object. It takes about .5 secs to initialize it
        # Hence initializing it once saves time
        self.ocr = PaddleOCR(use_angle_cls=True, lang="en")

    def extract_text(self, img: str) -> str:
        ret = self.ocr.ocr(img=img, det=True, rec=True)

        full_text = ""
        if ret[0]:
            for line in ret[0]:
                box, (text, score) = line
                if score > 0.8:
                    full_text += f"\n{text}"

        return full_text
