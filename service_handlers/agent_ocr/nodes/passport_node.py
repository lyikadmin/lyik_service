from pydantic_ai import Agent
from ._base_node import BaseNode
from ..models import Passport


class PassportNode(BaseNode):

    def __init__(self):
        super().__init__()
        self.agent = Agent(
            model=self.fallback_model,
            system_prompt=(
                "I want you to analyze the input text which is extracted from an image"
                "The text is that of the Passport, issued by Government of India"
            ),
            output_type=Passport,
        )

    async def extract(self, ocr_text) -> Passport:
        result = await self.agent.run(ocr_text)
        return result.output
