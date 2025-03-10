from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Form
from fastapi.responses import JSONResponse
from typing import List
import uvicorn
import traceback
from models import StandardResponse, ResponseStatusEnum
import logging
logger = logging.getLogger()

from license_manager import LicenseManager
from service_manager import ServiceManager

app2 = FastAPI(debug=True)


@app2.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": str(exc)})

@app2.post("/process")
async def process_endpoint(
    service_name: str = Form(...),
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
    logger.info(f"Received request for {service_name}")
    return service_name


if __name__ == "__main__":
    uvicorn.run("app2:app2", host="0.0.0.0", port=8000, reload=True, log_level="debug")
