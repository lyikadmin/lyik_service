from pydantic import BaseModel


class PincodeDetails(BaseModel):
    circlename: str
    regionname: str
    divisionname: str
    statename: str
    district: str
    pincode: int
