from pydantic_ai import Agent
from ._base_node import BaseNode
from ..models import VoterId

class VoterIDNode(BaseNode):

    def __init__(self):
        super().__init__()
        self.agent = Agent(
            model=self.fallback_model,
            system_prompt=(
                "I want you to analyze the input text which is extracted from an image"
                "The text is that of the Voter ID which is also called EPIC card, issued by Government of India"
            ),
            output_type=VoterId,
        )

    async def extract(self, ocr_text) -> VoterId:
        result = await self.agent.run(ocr_text)
        return result.output
