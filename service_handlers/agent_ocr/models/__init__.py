from .document_models import Passport, PAN, DrivingLicense, Aadhaar, VoterId
from .processing_models import DocumentProcessingState
from .response_models import OCRResponse
from ..utils import StrEnum

class DocumentTypesEnum(StrEnum):
    passport = "passport"
    driving_license = "driving_license"
    pan = "pan"
    aadhaar = "aadhaar"
    voter_id = "voter_id"

  

# Available Document Models
document_models = {
    DocumentTypesEnum.passport: Passport,
    DocumentTypesEnum.driving_license: DrivingLicense,
    DocumentTypesEnum.pan: PAN,
    DocumentTypesEnum.aadhaar: Aadhaar,
    DocumentTypesEnum.voter_id: VoterId
}
