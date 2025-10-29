from pydantic_ai import Agent
from ._base_node import BaseNode
from ..models import Visa

class VisaNode(BaseNode):

    def __init__(self):
        super().__init__()
        self.agent = Agent(
            model=self.fallback_model,
            system_prompt=(
              "You are an OCR document normalizer. "
              "Convert messy OCR text from visas into a structured JSON "
              "matching the Visa schema. "
              "Normalize dates to YYYY-MM-DD format. "
              "If something is missing, return null."
            ),
            output_type=Visa,
        )

    async def extract(self, ocr_text) -> Visa:
        result = await self.agent.run(ocr_text)
        return result.output