from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Form
from fastapi.responses import JSONResponse
from typing import List
import uvicorn
import traceback
from models import StandardResponse, ResponseStatusEnum

from license_manager import LicenseManager
from service_manager import ServiceManager

app = FastAPI(debug=True)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": str(exc)})



@app.post("/process", response_model=StandardResponse)
async def process_endpoint(
    request: Request,
    service_name: str = Form(...),
    license_key: str = Form(None),
    license_endpoint: str = Form(None),
    files: List[UploadFile] = File([]),
):
    # Verify the license key
    lm = LicenseManager(license_key=license_key, licensing_endpoint=license_endpoint)
    res, message = await lm.verify()

    if not res:
        return StandardResponse(
            status=ResponseStatusEnum.failure.value,
            message=str(message),
        )

    # Call ServiceManager and get Response
    response = await ServiceManager.process_request(
        service_name=service_name,
        request=request,
        files=files,
    )
    return response



if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")
