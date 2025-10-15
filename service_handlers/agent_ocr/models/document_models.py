from pydantic import Field, ConfigDict
from datetime import date
from typing import Union, Any, List
from .field_validators import DateConversionMixin
from enum import Enum


class GenderEnum(str, Enum):
    male = "M"
    female = "F"
    transgender = "T"
    other = "O"


class LicenseClass(str, Enum):
    lmv = "LMV"
    mcwg = "MCWG"
    mcwog = "MCWOG"
    hgmv = "HGMV"
    hmpv = "HPMV"
    fvg = "FVG"
    mc_ex50cc = "MC EX50CC"
    lmv_nt = "LMV-NT"


# Pydantic Models for Documents
class Passport(DateConversionMixin):
    passport_number: Union[str, None] = Field(None)
    surname: Union[str, None] = Field(None)
    given_name: Union[str, None] = Field(None)
    nationality: Union[str, None] = Field(None)
    sex: Union[GenderEnum, None] = Field(None)
    date_of_birth: Union[date, None] = Field(None)
    date_of_expiry: Union[date, None] = Field(None)
    date_of_issue: Union[date, None] = Field(None)
    place_of_birth: Union[str, None] = Field(None)
    place_of_issue: Union[str, None] = Field(None)
    mrz_line_1: Union[str, None] = Field(None)
    mrz_line_2: Union[str, None] = Field(None)
    type: Union[str, None] = Field(None)
    code: Union[str, None] = Field(None)
    nationality: Union[str, None] = Field(None)
    name_of_father: Union[str, None] = Field(None)
    name_of_mother: Union[str, None] = Field(None)
    name_of_spouse: Union[str, None] = Field(None)
    address: Union[str, None] = Field(None)
    pin_code: Union[str, None] = Field(None, description="Zip code, 6 digit number.")
    old_passport_number: Union[str, None] = Field(None)
    old_passport_date_of_issue: Union[str, None] = Field(None)
    old_passport_place_of_issue: Union[str, None] = Field(None)
    state: Union[str, None] = Field(None)
    district: Union[str, None] = Field(None)
    city: Union[str, None] = Field(None)
    country: Union[str, None] = Field(None)
    model_config = ConfigDict(extra="allow")


class PAN(DateConversionMixin):
    permanent_account_number: Union[str, None] = Field(None)
    name: Union[str, None] = Field(None)
    fathers_name: Union[str, None] = Field(None)
    date_of_birth: Union[date, None] = Field(None)
    gender: Union[GenderEnum, None] = Field(None)
    address: Union[str, None] = None
    pin_code: Union[str, None] = Field(None, description="Zip code, 6 digit number.")
    state: Union[str, None] = Field(None)
    district: Union[str, None] = Field(None)
    city: Union[str, None] = Field(None)
    country: Union[str, None] = Field(None)
    model_config = ConfigDict(extra="allow")


class DrivingLicense(DateConversionMixin):
    license_number: Union[str, None] = None
    full_name: Union[str, None] = None
    date_of_issue: Union[date, None] = None
    date_of_expiry: Union[date, None] = None
    category: Union[List[LicenseClass], None] = Field(
        None, description="can have multiple classes."
    )
    address: Union[str, None] = None
    pin_code: Union[str, None] = Field(None, description="Zip code, 6 digit number.")
    state: Union[str, None] = Field(None)
    district: Union[str, None] = Field(None)
    city: Union[str, None] = Field(None)
    country: Union[str, None] = Field(None)
    bloodgroup: Union[str, None] = Field(
        None, description="must be valid blood type. Sometimes represented as B.G."
    )
    son_of: Union[str, None] = Field(None, description="given as s/o in credentials")
    gender: Union[GenderEnum, None] = None
    model_config = ConfigDict(extra="allow")


class Aadhaar(DateConversionMixin):
    aadhaar_number: Union[str, None] = Field(None, description="It is a 12 digit number")
    full_name: Union[str, None] = Field(None)
    date_of_birth: Union[date, None] = Field(None)
    gender: Union[GenderEnum, None] = Field(None)
    full_address: Union[str, None] = Field(None)
    pin_code: Union[str, None] = Field(None, description="Zip code, 6 digit number.")
    state: Union[str, None] = Field(None)
    district: Union[str, None] = Field(None)
    city: Union[str, None] = Field(None)
    country: Union[str, None] = Field(None)
    model_config = ConfigDict(extra="allow")


class VoterId(DateConversionMixin):
    voter_epic_id: Union[str, None] = Field(None)
    full_name: Union[str, None] = Field(None)
    date_of_birth: Union[date, None] = Field(None)
    gender: Union[GenderEnum, None] = Field(None)
    full_address: Union[str, None] = Field(None)
    pin_code: Union[str, None] = Field(None, description="Zip code, 6 digit number.")
    state: Union[str, None] = Field(None)
    district: Union[str, None] = Field(None)
    city: Union[str, None] = Field(None)
    country: Union[str, None] = Field(None)
    model_config = ConfigDict(extra="allow")

class Visa(DateConversionMixin):
    # document_type: str = "Visa"
    issuing_country: str | None = None
    visa_number: str | None = None
    visa_code: str | None = None
    place_of_issue: str | None = None
    holder_name: str | None = None
    surname: str | None = None
    given_names: str | None = None
    passport_number: str | None = None
    date_of_birth: str | None = None
    sex: str | None = None
    nationality: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    entries: str | None = None
    issuing_authority: str | None = None
    annotations: str | None = None
    mrz: str | None = None
    model_config = ConfigDict(extra="allow")
