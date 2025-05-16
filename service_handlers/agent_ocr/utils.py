from pydantic import BaseModel
import json
from enum import Enum

def convert_pydantic_to_json(obj):
    """Converts Pydantic models to JSON serializable format."""
    if isinstance(obj, BaseModel):
        return obj.model_dump_json(indent=2)
    return json.dumps(obj, default=str, indent=2)

class StrEnum(str, Enum):
    """
    A custom enumeration class that combines the behavior of `str` and `Enum`.
    This class allows enumeration members to be treated as strings, making it
    easier to work with string-based enumerations.
    The `__str__` method is overridden to return the value of the enumeration member as a string.
    """

    def __str__(self):
        return self.value