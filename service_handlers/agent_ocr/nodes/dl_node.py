from pydantic_ai import Agent

from ._base_node import BaseNode
from ..models import DrivingLicense

class DrivingLicenseNode(BaseNode):

    def __init__(self):
        super().__init__()
        self.agent = Agent(
            model=self.fallback_model,
            system_prompt=(
                "I want you to analyze the input text which is extracted from an image"
                "The text is that of the Driving License card issued by the Transport Department in India"
            ),
            output_type=DrivingLicense,
        )

    async def extract(self, ocr_text) -> DrivingLicense:
        result = await self.agent.run(ocr_text)
        return result.output
