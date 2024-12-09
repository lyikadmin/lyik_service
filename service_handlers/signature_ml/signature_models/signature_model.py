from pydantic import BaseModel, Extra
from typing import List, Any

class UploadImagesModel(BaseModel):
    wet_signature_image: str
    proof_of_signature: str

class SignatureValidationModel(BaseModel):
    upload_images: UploadImagesModel

class SignatureFieldModel(BaseModel):
    """
    Represents the structure of the signature validation field.
    """
    signature_validation: SignatureValidationModel
    class Config:
        extra = Extra.allow

class SignatureVerificationResponseModel(BaseModel):
    """
    Represents the response from the accure.ai signature verification endpoint.
    """
    transaction_id: str
    image1: str
    image2: str
    status_code: int
    match_score: float