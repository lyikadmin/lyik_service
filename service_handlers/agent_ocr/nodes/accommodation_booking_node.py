# nodes/accommodation_booking_node.py
from pydantic_ai import Agent
from ._base_node import BaseNode
from ..models import AccommodationBooking


class AccommodationBookingNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.agent = Agent(
            model=self.fallback_model,
            system_prompt=(
                "You are an OCR document normalizer. "
                "Convert messy OCR text from hotel/accommodation booking confirmations into a structured JSON "
                "matching the AccommodationBooking schema. "
                "Normalize start_date and end_date to YYYY-MM-DD format. "
                "If some fields are missing, return null. "
                "Extract accommodation contact details when present (email/phone) without reformatting."
            ),
            output_type=AccommodationBooking,
        )

    async def extract(self, ocr_text) -> AccommodationBooking:
        result = await self.agent.run(ocr_text)
        return result.output
