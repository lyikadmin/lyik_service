from models import StandardResponse, ResponseStatusEnum
from fastapi import HTTPException, UploadFile, Request, Response
from fastapi.responses import JSONResponse
from tempfile import NamedTemporaryFile
import shutil
from typing import List, Union
from io import BytesIO
from service_handlers.signature_ml.utils.signature_extract import extract_signature
from service_handlers.liveness import process_liveness
from service_handlers.face_detect import detect_face
from enum import Enum
from pathlib import Path
import base64
import logging
from PIL import Image
logger = logging.getLogger()


class ServicesEnum(str, Enum):
    SignatureExtraction = "signature_extraction"
    LivenessCheck = "liveness"
    FaceDetection = "detect_face"


class ServiceManager:
    @staticmethod
    async def process_request(
        service_name: str, request: Request, files: List[UploadFile]
    ) -> StandardResponse:
        form = await request.form()
        additional_params = {k: v for k, v in form.items() if k != "service_name"}

        if service_name == ServicesEnum.SignatureExtraction.value:
            return ServiceManager.handle_signature_extraction(files)
        elif service_name == ServicesEnum.LivenessCheck.value:
            return ServiceManager.handle_liveness_check(files, additional_params)
        elif service_name == ServicesEnum.FaceDetection.value:
            return ServiceManager.handle_face_detection(files)
        else:
            return StandardResponse(
                status=ResponseStatusEnum.failure.value,
                message=f"Unknown service: {service_name}",
            )

    @staticmethod
    def handle_signature_extraction(files: List[UploadFile]):
        logger.info("Initiating Signature Extraction")
        if not files:
            return StandardResponse(
                status=ResponseStatusEnum.failure.value,
                message="No file provided for signature extraction.",
            )

        input_file = files[0]

        with NamedTemporaryFile(delete=True, suffix=".png") as temp_file:
            shutil.copyfileobj(input_file.file, temp_file)
            temp_file.flush()

            extracted_signature_response: Union[Union[BytesIO, None],str] = extract_signature(
                temp_file.name
            )

            if extracted_signature_response is None:
                return StandardResponse(
                    status=ResponseStatusEnum.failure.value,
                    message="No signature detected. Could not extract.",
                )
            
            # Returns string error message if the coverage is not as expected.
            # Returns strign erorr if multiple signatures are detected.
            if isinstance(extracted_signature_response, str):
                return StandardResponse(
                    status=ResponseStatusEnum.failure.value,
                    message=extracted_signature_response,
                )

            # Encode binary data as Base64
            base64_signature = base64.b64encode(extracted_signature_response.getvalue()).decode("utf-8")

            _save_image(base64_signature, "extracted_signature.png")

            return StandardResponse(
                status=ResponseStatusEnum.success,
                message="Signature successfully extracted.",
                result={"signature_image": base64_signature},
            )
        
    @staticmethod
    def handle_face_detection(files: List[UploadFile]) -> StandardResponse:
        logger.info("Initiating Liveness Check")
        if not files:
            return StandardResponse(
                status=ResponseStatusEnum.failure.value,
                message="No file provided for face detection",
            )
        input_file = files[0]
        suffix = Path(input_file.filename).suffix

        with NamedTemporaryFile(delete=True, suffix=suffix) as temp_file:
            shutil.copyfileobj(input_file.file, temp_file)
            temp_file.flush()

            result = detect_face(
                image_path=temp_file.name, required_face_coverage=0 # this used to be 25%, now removing the required coverage check
            )

            return result


    @staticmethod
    def handle_liveness_check(files: List[UploadFile], additional_params: dict) -> StandardResponse:
        logger.info("Initiating Liveness Check")
        if not files:
            return StandardResponse(
                status=ResponseStatusEnum.failure.value,
                message="No video file provided for liveness check.",
            )

        lat = float(additional_params.get("lat", 0))
        lng = float(additional_params.get("lng", 0))
        captcha_list = [
            c.strip()
            for c in additional_params.get("captcha", "").split(",")
            if c.strip()
        ]

        input_file = files[0]

        with NamedTemporaryFile(delete=True, suffix=".mp4") as temp_file:
            shutil.copyfileobj(input_file.file, temp_file)
            temp_file.flush()

            result = process_liveness(
                video_path=temp_file.name, lat=lat, lng=lng, captcha_list=captcha_list
            )

            return result


def _save_image(base64_string: str, file_path: str):
    # Add padding if necessary
    missing_padding = len(base64_string) % 4
    if missing_padding:
        base64_string += '=' * (4 - missing_padding)
    
    # Decode the Base64 string
    image_data = base64.b64decode(base64_string)
    
    # Convert the binary data to an image
    image = Image.open(BytesIO(image_data))
    
    # Save the image
    image.save(file_path)
