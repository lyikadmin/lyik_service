from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Form
from fastapi.responses import JSONResponse
from typing import List
import uvicorn
import traceback
from models import StandardResponse, ResponseStatusEnum
import logging
from service_manager.service_manager import ServicesEnum
from datetime import datetime
import os
from pathlib import Path
import shutil
import uuid

logger = logging.getLogger()

from license_manager import LicenseManager
from service_manager import ServiceManager

app = FastAPI(debug=True)

# Define storage directory (must be mounted as a volume in Docker)
if os.getenv("DOCKER_ENV") == "true":  # Docker environment variable
    STORAGE_DIR = "/data/uploads"
else:  # Running locally (Mac)
    STORAGE_DIR = os.path.expanduser("~/lyik_services_uploads")

# Ensure the storage directory exists
Path(STORAGE_DIR).mkdir(parents=True, exist_ok=True)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.post("/process", response_model=StandardResponse)
async def process_endpoint(
    request: Request,
    service_name: ServicesEnum = Form(...),
    license_key: str = Form(None),
    license_endpoint: str = Form(None),
    files: List[UploadFile] = File([]),
):
    # # Verify the license key
    # lm = LicenseManager(license_key=license_key, licensing_endpoint=license_endpoint)
    # res, message = await lm.verify()

    # if not res:
    #     return StandardResponse(
    #         status=ResponseStatusEnum.failure.value,
    #         message=str(message),
    #     )

    # Call ServiceManager and get Response
    try:
        logger.info(f"Received request for {service_name}")

        # # previously saving files for audit purposes. Not anymore.
        # if files:
        #     await save_files(service_name=service_name, files=files)

        response = await ServiceManager.process_request(
            service_name=service_name,
            request=request,
            files=files,
        )
        return response
    except Exception as e:
        logger.error(e)
        return StandardResponse(
            status=ResponseStatusEnum.failure,
            message="Services has failed. Please contact lyik support.",
            result=None,
        )


async def save_files(service_name: str, files: List[UploadFile]):
    """
    Method to save the files given when api is invoked, in a directory including its timestamp, and service name.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex
    save_dir = os.path.join(STORAGE_DIR, f"{timestamp}_{service_name}_{unique_id}")
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving files to: {save_dir}")

    # Save files
    for file in files:
        file_path = os.path.join(save_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"File saved: {file_path}")
        file.file.seek(0)


if __name__ == "__main__":
    # This is the safest way to start the server.
    # It looks like the startup is sequential just like any python app
    # NOTE: There are ways to instruct uvicorn to start the application with import string
    # But in that case it looks like the python imports are not handled properly. Have to investigate this more
    uvicorn.run(app=app, host="0.0.0.0", port=8000, reload=False, log_level="debug")
