# nodes/travel_insurance_node.py
from pydantic_ai import Agent
from ._base_node import BaseNode
from ..models import TravelInsurance


class TravelInsuranceNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.agent = Agent(
            model=self.fallback_model,
            system_prompt=(
                "You are an OCR document normalizer. "
                "Convert messy OCR text from travel insurance documents into a structured JSON "
                "matching the TravelInsurance schema. "
                "Normalize all date-like fields (dob, travel_start_date, travel_end_date, issue_date_of_travel) "
                "to YYYY-MM-DD format. "
                "If a field is absent, return null. "
                "Preserve phone numbers/emails as-is (no formatting beyond trimming)."
            ),
            output_type=TravelInsurance,
        )

    async def extract(self, ocr_text) -> TravelInsurance:
        result = await self.agent.run(ocr_text)
        return result.output
