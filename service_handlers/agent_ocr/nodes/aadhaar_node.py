from pydantic_ai import Agent

from ._base_node import BaseNode
from ..models import Aadhaar

class AadhaarNode(BaseNode):

    def __init__(self):
        super().__init__()
        self.agent = Agent(
            model=self.fallback_model,
            system_prompt=(
                "I want you to analyze the input text which is extracted from an image"
                "The text is that of the Aadhaar card issued by Government of India"
                "The aadhaar number may be masked which is indicated by 8 times x followed by a 4 digit number"
            ),
            output_type=Aadhaar,
        )

    async def extract(self, ocr_text) -> Aadhaar:
        result = await self.agent.run(ocr_text)
        return result.output
