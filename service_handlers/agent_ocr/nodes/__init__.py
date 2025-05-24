from typing import List, Tuple
from ._base_node import BaseNode
from .aadhaar_node import AadhaarNode
from .dl_node import DrivingLicenseNode
from .pan_node import PANNode
from .passport_node import PassportNode
from .voterid_node import VoterIDNode
from ..models import DocumentTypesEnum


# NOTE:
# We are not comparing the actual ID regex as this is not deterministic.
# The passport may contain text that could match some other document and so on

DOCUMENT_NODE_PATTERN_MAPPING: List[Tuple[List[str], BaseNode, str]] = [
    (
        ["INCOME\s*TAX\s*DEPARTMENT", "PERMANENT\s*ACCOUNT\s*NUMBER"],
        PANNode,
        DocumentTypesEnum.pan,
    ),
    (
        ["DL\s+NO", "FORM-7", "DRIVING\s*LICENSE"],
        DrivingLicenseNode,
        DocumentTypesEnum.driving_license,
    ),
    (
        [
            "election\s*commission",
            "election",
            "voter",
            "constituency",
            # "[A-Z]{3}[0-9]{7}",
        ],
        VoterIDNode,
        DocumentTypesEnum.voter_id,
    ),
    (
        [
            "ADHAAR",
            "Aadhaar",
            "uid",
            "identification\s*authority",
            "unique\*identification\*authority",
            # "[0-9]{4}\s*[0-9]{4}\s*[0-9]{4}",
            # "[xX]{4}\s*[xX]{4}\s[0-9]{4}",
        ],
        AadhaarNode,
        DocumentTypesEnum.aadhaar,
    ),
    (
        [
            "Passport",
            "REPUBLIC\s*OF\s*INDIA",
            "PASSPORT\s*OFFICE",
            "Ministry\s*of\s*External\s*Affairs",
            # "[A-Z][0-9]{7}",
        ],
        PassportNode,
        DocumentTypesEnum.passport,
    ),
]
