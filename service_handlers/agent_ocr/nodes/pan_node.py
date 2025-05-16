#pan_node.py
from pydantic_ai import Agent

from ._base_node import BaseNode
from ..models import PAN


class PANNode(BaseNode):

    def __init__(self):
        super().__init__()
        self.agent = Agent(
            model=self.fallback_model,
            system_prompt=(
                "I want you to analyze the input text which is extracted from an image"
                "The text is that of the PAN card issued by Government of India"
            ),
            output_type=PAN,
        )

    async def extract(self, ocr_text) -> PAN:
        result = await self.agent.run(ocr_text)
        return result.output
