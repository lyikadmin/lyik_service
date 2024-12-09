from enum import Enum
from pydantic import BaseModel
from typing import Optional, Any

class ResponseStatusEnum(str, Enum):
    success = "success"
    failure = "failure"

class StandardResponse(BaseModel):
    status: ResponseStatusEnum
    message: str
    result: Optional[Any] = None
