from .document_models import (
    Passport,
    PAN,
    DrivingLicense,
    Aadhaar,
    VoterId,
    Visa,
    FlightTicket,
    AccommodationBooking,
    TravelInsurance,
)
from .processing_models import DocumentProcessingState
from .response_models import OCRResponse
from ..utils import StrEnum

class DocumentTypesEnum(StrEnum):
    passport = "passport"
    driving_license = "driving_license"
    pan = "pan"
    aadhaar = "aadhaar"
    voter_id = "voter_id"
    # Known document Types follow
    visa = "visa"
    flight_ticket = "flight_ticket"
    travel_insurance = "travel_insurance"
    accomodation_booking = "accomodation_booking"


# Available Document Models
document_models = {
    DocumentTypesEnum.passport: Passport,
    DocumentTypesEnum.driving_license: DrivingLicense,
    DocumentTypesEnum.pan: PAN,
    DocumentTypesEnum.aadhaar: Aadhaar,
    DocumentTypesEnum.voter_id: VoterId,
    DocumentTypesEnum.visa: Visa,
    DocumentTypesEnum.flight_ticket: FlightTicket,
    DocumentTypesEnum.accomodation_booking: AccommodationBooking,
    DocumentTypesEnum.travel_insurance: TravelInsurance,
}
