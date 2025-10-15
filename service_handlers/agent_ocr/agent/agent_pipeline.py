from ..models import DocumentProcessingState
import httpx
from PIL import Image
import pytesseract
from ..models import document_models, DocumentTypesEnum
import json
from pydantic import BaseModel, ValidationError
import re
from typing import List, Dict, Type
from langgraph.graph import StateGraph
from .llm_invoke import query_llm
from .utils import (
    clean_llm_response,
    remove_newline_characters,
    does_text_match_patterns,
)
from ..nodes import DOCUMENT_NODE_PATTERN_MAPPING, KNOWN_DOCUMENT_NODE_MAPPING, BaseNode

# from .ocr_handler import run_paddleocr, run_tesseract
from .ocr_handler import TextExtractor

from service_handlers.pincode_service import get_pincode_details
from service_handlers.pincode_service.pin_code_models import PincodeDetails

text_extractor = TextExtractor()


async def extract_text_from_image(
    state: DocumentProcessingState,
) -> DocumentProcessingState:
    """Extract text from an image using multiple OCR engines."""
    # ocr_results = {"paddle": "", "tesseract": ""}
    ocr_results = ""
    try:
        for image_path in state.image_path:
            image = Image.open(image_path)

            # ocr_results["paddle"] += run_paddleocr(image_path)
            ocr_results += text_extractor.extract_text(image_path)
            # ocr_results["tesseract"] += run_tesseract(image)

        state.extracted_text = ocr_results
        # if not any(ocr_results.values()):
        # state.error = "OCR engines detected no text."

    except Exception as e:
        state.error = f"OCR failed: {str(e)}"

    return state


# Identify Document Type Step (Now with Context & One-Word Response)
async def identify_document_type_llm(
    state: DocumentProcessingState,
) -> DocumentProcessingState:
    """Identify the document type using LLM, enforcing structured response."""
    if state.error:
        return state  # Skip if there was an error in OCR

    # Pydantic Model Scehmas for available documents
    document_model_schemas = {
        model_name: model.model_json_schema()
        for model_name, model in document_models.items()
    }

    prompt = f"""
    You are an AI that classifies documents based on their extracted text.
    The possible document types are provided below.
    
    Here are the available document models:
    
    {json.dumps(document_model_schemas, indent=4)}

    Given this extracted text:
    
    "{state.extracted_text}"
    
    Match it with one of the available models and return only one word, which is the model name.
    If an exact match is not found, return the closest match.

    Do not return an explanation, just return a single word.
    No explanation, just single word of EXACT model name, among {list(document_model_schemas.keys())}
    """
    response = await query_llm(prompt)
    state.document_type = response.lower()

    if state.document_type not in document_models.keys():
        state.error = "Could not detect document type"

    return state


async def identify_validate_and_extract_document_with_pattern(
    state: DocumentProcessingState,
) -> DocumentProcessingState:
    """
    1. Identify the document type using predetermined patterns
    2. Calls appropriate Document Node, to get data adhering to Pydantic model associated with it.
    """
    if state.error:
        return state  # Skip if there was an error in OCR

    # Pydantic Model Scehmas for available documents
    data = None
    document_type = None
    for pattern_list, DocumentNodeClass, document_type in DOCUMENT_NODE_PATTERN_MAPPING:
        if does_text_match_patterns(state.extracted_text, pattern_list):
            node: BaseNode = DocumentNodeClass()
            data: BaseModel = await node.extract(ocr_text=state.extracted_text)
            break

    if data is None:
        state.error = f"No Document Node found for data."

    state.extracted_data = data.model_dump()
    state.document_type = document_type

    return state


# Extract Data Step
async def extract_relevant_data(
    state: DocumentProcessingState,
) -> DocumentProcessingState:
    """Extract structured data from the document using LLM."""
    if state.error:
        return state  # Skip processing if an error occurred

    prompt = f"""
    I will provide the ocr of a single document, done twice with different configuration to cover all bases of text available.
    Extract relevant information from the following text based on the {state.document_type} model:

    "{state.extracted_text}"

    Ensure that the output you provide can be validated, and adheres to this Pydantic model schema.
    Make sure dates are in proper format (yyyy-mm-dd). Ignore any additional data for the dates.
    If a pin_code is found, ensure it is a 6-digit number only (no dashes, letters, or spaces). If a letter like 'S' appears due to OCR, replace it with a likely digit (e.g., 'S' → '5'). Do not reformat or restructure it. Output must be strictly numeric and 6 digits long.

    {json.dumps(document_models[state.document_type].model_json_schema(), indent=4)}

    Return the extracted data strictly as a JSON object, such that passing it directly to the model will validate it.
    """

    response = await query_llm(prompt)
    cleaned_response = clean_llm_response(response)  # Remove <think> sections
    try:
        raw_data = json.loads(cleaned_response)

        # If multiple documents are detected, consider the first one.
        if isinstance(raw_data, list):
            raw_data = raw_data[0]

        # Extract only the "properties" field if it exists
        if "properties" in raw_data:
            state.extracted_data = raw_data["properties"]
        else:
            state.extracted_data = raw_data  # Use as-is if already in correct format

    except json.JSONDecodeError:
        state.error = "Failed to parse JSON from LLM response."
    return state


# Validate Data Step
async def validate_document_data(
    state: DocumentProcessingState,
) -> DocumentProcessingState:
    """Validate and structure extracted data using Pydantic models."""
    if state.error:
        return state  # Skip processing if an error occurred

    if state.document_type not in document_models:
        state.error = f"Unrecognized document type: {state.document_type}"
        return state

    try:
        # Try to add information if pincode exists
        extracted_data = state.extracted_data
        pincode = extracted_data.get("pin_code", "")
        if pincode:
            pincode = int(pincode)
            pin_code_details: PincodeDetails = PincodeDetails.model_validate(
                get_pincode_details(pincode)
            )
            extracted_data["state"] = pin_code_details.statename
            extracted_data["district"] = pin_code_details.district
            extracted_data["circlename"] = pin_code_details.circlename
            extracted_data["regionname"] = pin_code_details.regionname
            extracted_data["divisionname"] = pin_code_details.divisionname
            if not extracted_data.get("city"):
                extracted_data["city"] = pin_code_details.district
    except:
        pass

    try:
        validated_data = document_models[state.document_type](**extracted_data)
        state.validated_data = validated_data.model_dump()
    except ValidationError as e:
        state.error = f"Validation error: {e}"

    return state


# LangGraph Workflow
def build_langraph_pipeline():
    """Builds the LangGraph workflow for document processing."""
    graph = StateGraph(DocumentProcessingState)

    graph.add_node("OCR", extract_text_from_image)
    graph.add_node(
        "Identify Document Type Pattern",
        identify_validate_and_extract_document_with_pattern,
    )
    graph.add_node("Validate Data", validate_document_data)

    graph.add_edge("OCR", "Identify Document Type Pattern")
    graph.add_edge("Identify Document Type Pattern", "Validate Data")

    graph.set_entry_point("OCR")
    graph.set_finish_point("Validate Data")

    return graph.compile()


# # LangGraph Workflow
# def build_langraph_pipeline():
#     """Builds the LangGraph workflow for document processing."""
#     graph = StateGraph(DocumentProcessingState)

#     graph.add_node("OCR", extract_text_from_image)
#     graph.add_node("Identify Document Type LLM", identify_document_type_llm)
#     graph.add_node("Extract Data", extract_relevant_data)
#     graph.add_node("Validate Data", validate_document_data)

#     graph.add_edge("OCR", "Identify Document Type LLM")
#     graph.add_edge("Identify Document Type LLM", "Extract Data")
#     graph.add_edge("Extract Data", "Validate Data")

#     graph.set_entry_point("OCR")
#     graph.set_finish_point("Validate Data")

#     return graph.compile()

# Invoking Document Processing Agent pipeline
async def process_document(image_path: List[str]) -> Dict:
    """Runs the LangGraph pipeline for a single document."""
    pipeline = build_langraph_pipeline()
    state = DocumentProcessingState(image_path=image_path)
    return await pipeline.ainvoke(state)

### Specific for known documents

def build_langraph_known_pipeline():
    """
    Known-doc pipeline: OCR → Extract Known → Validate
    Assumes state.document_type is already set to a DocumentTypesEnum.
    """
    graph = StateGraph(DocumentProcessingState)

    graph.add_node("OCR", extract_text_from_image)
    graph.add_node("Extract Known", extract_known_document_node)
    graph.add_node("Validate", validate_document_data)

    graph.add_edge("OCR", "Extract Known")
    graph.add_edge("Extract Known", "Validate")

    graph.set_entry_point("OCR")
    graph.set_finish_point("Validate")
    return graph.compile()

def _coerce_document_type(value: str):
    try:
        return DocumentTypesEnum(value)
    except Exception:
        try:
            return DocumentTypesEnum[value]
        except Exception:
            return None

async def extract_known_document_node(
    state: DocumentProcessingState,
) -> DocumentProcessingState:
    """
    Use state.document_type (enum) to select the BaseNode from KNOWN_DOCUMENT_NODE_MAPPING,
    run extraction, and stash the model_dump() into state.extracted_data.
    """
    if state.error:
        return state

    if not state.document_type:
        state.error = "document_type is required for known-document extraction."
        return state

    NodeClass: Type[BaseNode] | None = KNOWN_DOCUMENT_NODE_MAPPING.get(state.document_type)
    if NodeClass is None:
        state.error = f"No Document Node found for {state.document_type!s}."
        return state

    try:
        node = NodeClass()
        model_obj: BaseModel = await node.extract(ocr_text=state.extracted_text)
        state.extracted_data = model_obj.model_dump()
    except Exception as e:
        state.error = f"Known-document extract failed: {e}"

    return state

async def process_known_document(image_path: List[str], ocr_document_type: str) -> Dict:
    """
    Entry for known-doc flow using a LangGraph pipeline.
    """
    state = DocumentProcessingState(image_path=image_path)

    coerced = _coerce_document_type(ocr_document_type.strip())
    if coerced is None or coerced not in document_models.keys():
        state.error = f"Could not detect document type: {ocr_document_type!r}"
        return state

    state.document_type = coerced

    pipeline = build_langraph_known_pipeline()
    # Graph will: OCR → Extract Known → Validate
    return await pipeline.ainvoke(state)