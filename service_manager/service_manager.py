from models import StandardResponse, ResponseStatusEnum
from fastapi import HTTPException, UploadFile, Request, Response
from fastapi.responses import JSONResponse
from tempfile import NamedTemporaryFile
import shutil
from typing import List, Union
from io import BytesIO
# from service_handlers.signature_ml.utils.signature_extract import extract_signature
from service_handlers.liveness import process_liveness
from service_handlers.face_detect import detect_face
from service_handlers.agent_ocr import (
    process_document,
    OCRResponse,
    DocumentProcessingState,
    convert_pydantic_to_json,
)
from service_handlers.pincode_service import get_pincode_details
from service_handlers.pincode_service.pin_code_models import PincodeDetails
from service_handlers.mask_credential import mask_credential
from service_handlers.signature_detect import detect_signature
from enum import Enum
from pathlib import Path
import base64
import logging
from PIL import Image
import os

logger = logging.getLogger()


class ServicesEnum(str, Enum):
    SignatureExtraction = "signature_extraction"
    LivenessCheck = "liveness"
    FaceDetection = "detect_face"
    OCR = "ocr"
    PinCodeDataExtraction = "pin_code_data_extraction"
    MaskCredential = "mask_credential"
    SignatureDetection = "detect_signature"


class ServiceManager:
    @staticmethod
    async def process_request(
        service_name: str, request: Request, files: List[UploadFile]
    ) -> StandardResponse:
        form = await request.form()
        additional_params = {k: v for k, v in form.items() if k != "service_name"}

        if service_name == ServicesEnum.LivenessCheck.value:
            return ServiceManager.handle_liveness_check(files, additional_params)
        # elif service_name == ServicesEnum.SignatureExtraction.value:
        #     return ServiceManager.handle_signature_extraction(files)
        elif service_name == ServicesEnum.FaceDetection.value:
            return ServiceManager.handle_face_detection(files)
        elif service_name == ServicesEnum.OCR.value:
            return await ServiceManager.handle_ocr(files)
        elif service_name == ServicesEnum.PinCodeDataExtraction.value:
            return ServiceManager.handle_pincode_data_extraction(additional_params)
        elif service_name == ServicesEnum.MaskCredential.value:
            return await ServiceManager.handle_mask_credential(files, additional_params)
        elif service_name == ServicesEnum.SignatureDetection.value:
            return await ServiceManager.handle_signature_detection(files)
        else:
            return StandardResponse(
                status=ResponseStatusEnum.failure.value,
                message=f"Unknown service: {service_name}",
            )

    # @staticmethod
    # def handle_signature_extraction(files: List[UploadFile]):
    #     logger.info("Initiating Signature Extraction")
    #     if not files:
    #         return StandardResponse(
    #             status=ResponseStatusEnum.failure.value,
    #             message="No file provided for signature extraction.",
    #         )

    #     input_file = files[0]

    #     with NamedTemporaryFile(delete=True, suffix=".png") as temp_file:
    #         shutil.copyfileobj(input_file.file, temp_file)
    #         temp_file.flush()

    #         extracted_signature_response: Union[Union[BytesIO, None], str] = (
    #             extract_signature(temp_file.name)
    #         )

    #         if extracted_signature_response is None:
    #             return StandardResponse(
    #                 status=ResponseStatusEnum.failure.value,
    #                 message="No signature detected. Could not extract.",
    #             )

    #         # Returns string error message if the coverage is not as expected.
    #         # Returns strign erorr if multiple signatures are detected.
    #         if isinstance(extracted_signature_response, str):
    #             return StandardResponse(
    #                 status=ResponseStatusEnum.failure.value,
    #                 message=extracted_signature_response,
    #             )

    #         # Encode binary data as Base64
    #         base64_signature = base64.b64encode(
    #             extracted_signature_response.getvalue()
    #         ).decode("utf-8")

    #         _save_image(base64_signature, "extracted_signature.png")

    #         return StandardResponse(
    #             status=ResponseStatusEnum.success,
    #             message="Signature successfully extracted.",
    #             result={"signature_image": base64_signature},
    #         )

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
                image_path=temp_file.name,
                required_face_coverage=0,  # this used to be 25%, now removing the required coverage check
            )

            return result

    @staticmethod
    def handle_liveness_check(
        files: List[UploadFile], additional_params: dict
    ) -> StandardResponse:
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

    @staticmethod
    async def handle_ocr(files: List[UploadFile]) -> StandardResponse:
        logger.info("Initiating OCR")
        if not files:
            return StandardResponse(
                status=ResponseStatusEnum.failure.value,
                message="No file provided for face detection",
            )
        image_paths = []
        try:
            for file in files:
                contents = await file.read()
                file_extension = os.path.splitext(file.filename)[1]
                with NamedTemporaryFile(delete=False, suffix=file_extension) as tmp:
                    tmp.write(contents)
                    image_paths.append(tmp.name)

            result = await process_document(image_path=image_paths)
            result = DocumentProcessingState.model_validate(result)
        finally:
            for path in image_paths:
                try:
                    os.remove(path)
                except OSError as e:
                    print(f"Error deleting temporary file {path}: {e}")

        print(convert_pydantic_to_json(result))
        if not result.validated_data:
            return StandardResponse(
                status=ResponseStatusEnum.failure, message=result.error
            )
        return StandardResponse(
            status=ResponseStatusEnum.success,
            message=f"Detected document of type '{result.document_type}' successfully",
            result=OCRResponse(
                document_type=result.document_type, validated_data=result.validated_data
            ),
        )

    @staticmethod
    def handle_pincode_data_extraction(additional_params: dict) -> StandardResponse:
        logger.info("Initiating Pin Code Data Extraction")
        try:
            pincode = int(additional_params.get("pin_code", 0))
            pin_code_details: PincodeDetails = PincodeDetails.model_validate(
                get_pincode_details(pincode)
            )
            return StandardResponse(
                status=ResponseStatusEnum.success,
                message=f"Successfully extracted Pin Code for {pin_code_details.pincode}",
                result=pin_code_details,
            )
        except Exception as e:
            return StandardResponse(
                status=ResponseStatusEnum.failure,
                message=f"Failed to get data for Pin Code {pin_code_details.pincode}",
                result=e,
            )

    @staticmethod
    async def handle_mask_credential(
        files: List[UploadFile], additional_params: dict
    ) -> StandardResponse:
        """
        Masks the given credential. provided the type. Currently only supports Aadhaar type.
        Returns:
        [{
            "file_name": f"masked_file_name.jpeg",
            "file_base64": Base64 of file content,
        }]
        """
        logger.info("Initiating Credential Masking")
        if not files:
            return StandardResponse(
                status=ResponseStatusEnum.failure.value,
                message="No file provided for masking",
            )
        files_response = list()
        for file in files:
            input_file = file
            suffix = Path(input_file.filename).suffix

            mask_value = additional_params.get("mask_value", None)

            # Save the uploaded file temporarily in memory
            with NamedTemporaryFile(delete=True, suffix=suffix) as tmp:
                shutil.copyfileobj(input_file.file, tmp)
                tmp.flush()
                # Process the image and get base64 encoded result
                encoded_file = await mask_credential(
                    image_path=tmp.name, mask_value=mask_value
                )
            encoded_file_response = {
                "file_name": f"masked_{input_file.filename}",
                "file_base64": encoded_file,
            }
            files_response.append(encoded_file_response)
        return StandardResponse(
            status=ResponseStatusEnum.success,
            message="File processed successfully",
            result=files_response,
        )

    async def handle_signature_detection(files: List[UploadFile]) -> StandardResponse:
        if not files or len(files) == 0:
            return StandardResponse(
                status=ResponseStatusEnum.failure,
                message="No file in input",
                result=None,
            )

        f = files[0]
        suffix = Path(f.filename).suffix
        with NamedTemporaryFile(delete=True, suffix=suffix) as tmp:
            shutil.copyfileobj(f.file, tmp)
            tmp.flush()
            resp = await detect_signature(image_file=tmp.name)
            return StandardResponse(
                status=ResponseStatusEnum.success,
                message="See the result payload",
                result=resp,
            )


def _save_image(base64_string: str, file_path: str):
    # Add padding if necessary
    missing_padding = len(base64_string) % 4
    if missing_padding:
        base64_string += "=" * (4 - missing_padding)

    # Decode the Base64 string
    image_data = base64.b64decode(base64_string)

    # Convert the binary data to an image
    image = Image.open(BytesIO(image_data))

    # Save the image
    image.save(file_path)
