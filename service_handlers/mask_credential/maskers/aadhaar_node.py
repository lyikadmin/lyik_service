from pydantic_ai import Agent, BinaryContent
from llm_invoker import LLMInvokerBaseNode
from pathlib import Path
import mimetypes
from typing import List, Tuple
from pydantic import BaseModel, Field


# class BoundingBox(BaseModel):
#     top_left: Tuple[int, int]
#     width: int
#     height: int


# class MaskCoordinates(BaseModel):
#     bounding_boxes: List[BoundingBox]


# class MaskAadhaarNode(LLMInvokerBaseNode):
#     def __init__(
#         self,
#     ):
#         super().__init__()
#         self.agent = Agent(
#             model=self.model,
#             system_prompt=(
#                 "You are a document image understanding expert. Given an Aadhaar card image and a value to mask, "
#                 "your task is to find all rectangular regions where this value appears (either completely or partially). "
#                 "For example, the Aadhaar number 9120 7937 5716 may appear in multiple places and in different orientations. "
#                 "Return a list of bounding boxes for each detected instance. "
#                 "Each bounding box should include: the top-left coordinate as [x, y], the width, and the height. "
#                 'Format: [{"top_left": [x, y], "width": w, "height": h}].'
#             ),
#             output_type=MaskCoordinates,
#         )

#     async def extract(self, image_file: str, mask_value: str) -> MaskCoordinates:
#         f = Path(image_file)
#         result = await self.agent.run(
#             [
#                 f"Value to mask: {mask_value}",
#                 BinaryContent(
#                     data=f.read_bytes(),
#                     media_type=mimetypes.guess_type(image_file)[0],
#                 ),
#             ]
#         )
#         print(f"LLM Result is: {result.output}")
#         return result.output


class BoundingBox(BaseModel):
    """Normalised bounding box; each field is 0 – 1."""

    top_left: Tuple[float, float] = Field(
        ..., description="[x, y] of top-left corner, 0–1"
    )
    width: float = Field(..., description="width  as fraction of image")
    height: float = Field(..., description="height as fraction of image")


class MaskCoordinates(BaseModel):
    bounding_boxes: List[BoundingBox]


class MaskAadhaarNode(LLMInvokerBaseNode):
    """
    Vision-LLM prompt wrapper that detects every occurrence of an Aadhaar number
    and returns normalised rectangles.
    """

    def __init__(
        self,
    ):
        super().__init__()
        self.agent = Agent(
            model=self.model,
            system_prompt=(
                "You are a document-image expert. You receive an image of an Aadhaar card "
                "and the string that must be masked. Return a JSON list of bounding boxes "
                "covering every place where the value appears, in any orientation.  "
                "Coordinates **must be normalised floats between 0 and 1**:\n"
                '[{"top_left":[x,y],"width":w,"height":h}, …]'
            ),
            output_type=MaskCoordinates,
        )

    async def extract(self, image_file: str, mask_value: str) -> MaskCoordinates:
        f = Path(image_file)
        result = await self.agent.run(
            [
                f"Value to mask: {mask_value}",
                BinaryContent(
                    data=f.read_bytes(),
                    media_type=mimetypes.guess_type(image_file)[0],
                ),
            ]
        )
        print(f"LLM Result is: {result.output}")
        return result.output
