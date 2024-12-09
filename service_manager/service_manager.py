from models import StandardResponse, ResponseStatusEnum
from fastapi import HTTPException, UploadFile, Request, Response
from fastapi.responses import JSONResponse
from tempfile import NamedTemporaryFile
import shutil
from typing import List, Union
from io import BytesIO
from service_handlers.signature_ml.utils.signature_extract import extract_signature
from service_handlers.liveness import process_liveness
from enum import Enum
import base64


class ServicesEnum(str, Enum):
    SignatureExtraction = "signature_extraction"
    LivenessCheck = "liveness"


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
        else:
            return StandardResponse(
                status=ResponseStatusEnum.failure.value,
                message=f"Unknown service: {service_name}",
            )

    @staticmethod
    def handle_signature_extraction(files: List[UploadFile]):
        if not files:
            return StandardResponse(
                status=ResponseStatusEnum.failure.value,
                message="No file provided for signature extraction.",
            )

        input_file = files[0]

        with NamedTemporaryFile(delete=True, suffix=".png") as temp_file:
            shutil.copyfileobj(input_file.file, temp_file)
            temp_file.flush()

            extracted_signature_bytes: Union[BytesIO, None] = extract_signature(
                temp_file.name
            )

            if extracted_signature_bytes is None:
                return StandardResponse(
                    status=ResponseStatusEnum.failure.value,
                    message="No signature detected. Could not extract.",
                )

            # Encode binary data as Base64
            base64_signature = base64.b64encode(extracted_signature_bytes.getvalue()).decode("utf-8")

            return StandardResponse(
                status=ResponseStatusEnum.success,
                message="Signature successfully extracted.",
                result={"signature_image": base64_signature},
            )

    @staticmethod
    def handle_liveness_check(files: List[UploadFile], additional_params: dict) -> StandardResponse:
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
