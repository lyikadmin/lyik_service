# base_node.py
from abc import ABC, abstractmethod
from dotenv import load_dotenv
# from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.gemini import GeminiModel
from pydantic import BaseModel


class LLMInvokerBaseNode(ABC):

    def __init__(self):
        load_dotenv()
        self.openai_model = OpenAIModel(model_name="gpt-4o")
        self.gemini_model = GeminiModel(model_name="gemini-2.0-flash")
        # self.anthropic_model = AnthropicModel(model_name="claude-3-5-sonnet-latest")
        self.model = FallbackModel(self.openai_model, self.gemini_model)

    @abstractmethod
    async def extract(self, ocr_text: str) -> BaseModel:
        pass
