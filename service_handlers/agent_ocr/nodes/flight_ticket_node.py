from pydantic_ai import Agent
from ._base_node import BaseNode
from ..models import FlightTicket


class FlightTicketNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.agent = Agent(
            model=self.fallback_model,
            system_prompt=(
                "You are an OCR document normalizer. "
                "Convert messy OCR text from airline flight tickets into a structured JSON "
                "matching the FlightTicket schema. "
                "Normalize dates to YYYY-MM-DD format. "
                "If something is missing, return null. "
                "If multiple segments are present, choose the primary itinerary segment; "
                "But list the other traveller names appropriately."
                "prefer the international leg, otherwise the earliest departing segment."
            ),
            output_type=FlightTicket,
        )

    async def extract(self, ocr_text) -> FlightTicket:
        result = await self.agent.run(ocr_text)
        return result.output
