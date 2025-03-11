from .document_models import Passport, PAN, DrivingLicense, Aadhaar, VoterId
from .processing_models import DocumentProcessingState
from .response_models import OCRResponse

# Available Document Models
document_models = {
    "passport": Passport,
    "driving_license": DrivingLicense,
    "pan": PAN,
    "aadhaar": Aadhaar,
    "voter_id": VoterId
}
