from typing import Optional, Any
import asyncio
import os
import requests
import logging

logger = logging.getLogger()

from pydantic import BaseModel

from enum import Enum


# Mock or sample models for testing purposes
class ContextModel:
    # Define your mock structure for ContextModel
    pass


class SingleFieldModel:
    def __init__(self, field_value):
        self.field_value = field_value


class LivenessFieldModel:
    @staticmethod
    def parse_obj(data):
        return LivenessFieldModel(**data)

    def __init__(self, liveness_geo_loc, liveness_captcha, liveness_video):
        self.liveness_geo_loc = liveness_geo_loc
        self.liveness_captcha = liveness_captcha
        self.liveness_video = liveness_video


class GeoLocation:
    def __init__(self, lat, lng):
        self.lat = lat
        self.lng = lng


class VERIFY_RESPONSE_STATUS:
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class ResponseStatusEnum(str, Enum):
    success = "success"
    failure = "failure"


class StandardResponse(BaseModel):
    status: ResponseStatusEnum
    message: str
    result: Optional[Any] = None


class GeoLocation(BaseModel):
    lat: float
    lng: float


class LivenessFieldModel(BaseModel):
    liveness_geo_loc: GeoLocation
    liveness_captcha: list[str]
    liveness_video: str


# Assuming your verify_handler is a method within a class named VerificationService
class VerificationService:
    async def verify_handler(self, payload):
        """
        Instead of local verification, this now calls the generic API endpoint.
        The API handles geolocation checks, audio extraction, speech-to-text,
        and captcha keyword matching for liveness verification.
        """
        try:
            # Parse payload into the liveness model
            liveness_model: LivenessFieldModel = LivenessFieldModel.parse_obj(
                payload.field_value
            )

            # Extract the details
            lat = liveness_model.liveness_geo_loc.lat
            lng = liveness_model.liveness_geo_loc.lng
            captcha_list = liveness_model.liveness_captcha
            video_path = liveness_model.liveness_video

            # Check if the video file exists before sending to API
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file '{video_path}' not found.")

            # Prepare the request to the generic API
            license_key = "test_key"

            captcha_str = ",".join(captcha_list)

            data = {
                "service_name": "liveness",
                "license_key": license_key,
                "license_endpoint": "https://asia-south1-esoteric-fx-345801.cloudfunctions.net",
                "lat": str(lat),
                "lng": str(lng),
                "captcha": captcha_str,
            }

            file_name = os.path.basename(video_path)
            file_extension = os.path.splitext(file_name)[1].lstrip(
                "."
            )  # Extract extension without the dot

            # Open the video file and send it to the API
            with open(video_path, "rb") as vid_file:
                files = {"files": (file_name, vid_file, f"video/{file_extension}")}

                # Make the POST request to the generic server
                response = requests.post(
                    "http://98.70.99.42/process", data=data, files=files
                )

            # Check the response
            if response.status_code != 200:
                raise Exception(f"Error from liveness API: {response.text}")

            # Parse the response using the StandardResponse model
            resp_json = response.json()
            standard_response = StandardResponse.parse_obj(resp_json)

            return standard_response

            # # Map response status to VERIFY_RESPONSE_STATUS
            # if standard_response.status == ResponseStatusEnum.success.value:
            #     final_status = VERIFY_RESPONSE_STATUS.SUCCESS
            # else:
            #     final_status = VERIFY_RESPONSE_STATUS.FAILURE

            # return VerifyHandlerResponseModel(
            #     id=None, status=final_status, message=standard_response.message, actor="system"
            # )

        except Exception as e:
            logger.exception("Failed liveness verification.")
            raise Exception(f"Failed liveness verification. {e}")


async def main():
    import json
    # Create a sample payload
    geo_loc = GeoLocation(lat=28.6139, lng=77.2090)
    liveness_payload = {
        "liveness_geo_loc": geo_loc,
        "liveness_captcha": ["python", "react", "tarantula"],
        "liveness_video": "/Users/akhilbabu/Documents/work/servers/signature_server/demo/liveness.mov",
    }
    lpj = json.dumps(liveness_payload, default=lambda o: o.__dict__)
    print(lpj)

    payload = SingleFieldModel(field_value=liveness_payload)
    context = None  # or a proper instance of ContextModel if required

    # Initialize the service
    service = VerificationService()

    # Call the verify_handler method
    try:
        response = await service.verify_handler(payload)
        print(response.json())
    except Exception as e:
        print(f"Error during verification: {e}")


if __name__ == "__main__":
    asyncio.run(main())
