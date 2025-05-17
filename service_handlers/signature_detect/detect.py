from ._base_node import BaseNode
from pydantic import BaseModel
from pydantic_ai import Agent, BinaryContent
from pathlib import Path
import mimetypes

class SignatureDetectionResponse(BaseModel):
    # This model is returned by the signature detection service
    is_signature_clear: bool
    contains_signature_only: bool
    contains_signature: bool


class SignatureNode(BaseNode):

    def __init__(self):
        super().__init__()
        self.agent = Agent(
            model=self.model,
            system_prompt=(
                "I want you to analyze the input image and tell me if it contains a Signature"
                "Tell me if signature is clear and if the image contains only a signature and no other content"
            ),
            output_type=SignatureDetectionResponse,
        )

    async def extract(self, image_file: str) -> SignatureDetectionResponse:
        f = Path(image_file)
        result = await self.agent.run(
            [
                BinaryContent(
                    data=f.read_bytes(), media_type=mimetypes.guess_type(image_file)[0]
                )
            ]
        )
        return result.output


sign_node = SignatureNode()


async def detect_signature(image_file: str) -> SignatureDetectionResponse:
    resp = await sign_node.extract(image_file=image_file)
    return resp