"""LangGraph nodes for the RCM workflow."""
from typing import Dict, Any
from app.models.graph_state import GraphState, ExtractedData, CodedData, AuditResult
from app.utils.llm_mock import mock_structured_output
import logging

logger = logging.getLogger(__name__)


def extractor_node(state: GraphState) -> Dict[str, Any]:
    """
    Extract medical information from FHIR resources.
    
    This node retrieves raw FHIR data and extracts structured medical information
    including diagnoses, procedures, and observations.
    """
    logger.info(f"Extractor node processing {len(state.get('resource_ids', []))} resources")
    
    # TODO: Actually fetch and parse FHIR resources from database
    # For now, use mock LLM to extract data
    extracted_data = mock_structured_output(
        ExtractedData,
        prompt="Extract diagnoses, procedures, and observations from FHIR resources",
    )
    
    return {
        "extracted_data": extracted_data,
        "next_action": "code",
    }


def coder_node(state: GraphState) -> Dict[str, Any]:
    """
    Assign medical codes to extracted data.
    
    This node takes extracted medical information and assigns appropriate
    ICD-10, CPT, and LOINC codes using structured output validation.
    """
    logger.info("Coder node assigning medical codes")
    
    extracted_data = state.get("extracted_data")
    if not extracted_data:
        return {
            "error": "No extracted data available for coding",
            "next_action": "end",
        }
    
    # TODO: Use actual LLM with instructor for structured output
    coded_data = mock_structured_output(
        CodedData,
        prompt=f"Assign ICD-10, CPT, and LOINC codes to: {extracted_data}",
    )
    
    return {
        "coded_data": coded_data,
        "next_action": "audit",
    }


def auditor_node(state: GraphState) -> Dict[str, Any]:
    """
    Audit coded data for correctness and compliance.
    
    This node validates that codes are properly assigned, checks for conflicts,
    and determines if retry is needed.
    """
    logger.info("Auditor node validating coded data")
    
    coded_data = state.get("coded_data")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    
    if not coded_data:
        return {
            "error": "No coded data available for audit",
            "next_action": "end",
        }
    
    # TODO: Implement actual audit logic with LLM
    audit_result = mock_structured_output(
        AuditResult,
        prompt=f"Audit the following coded data: {coded_data}",
    )
    
    # Simulate occasional audit failure to test retry logic
    if retry_count == 0 and len(coded_data.icd10_codes) > 0:
        # First time, sometimes fail to demonstrate retry
        audit_result.passed = False
        audit_result.issues = ["ICD-10 code E11.9 needs more specificity"]
        audit_result.severity = "medium"
        audit_result.recommendations = ["Use E11.65 for Type 2 diabetes with hyperglycemia"]
    
    if not audit_result.passed:
        if retry_count < max_retries:
            logger.warning(f"Audit failed, retry {retry_count + 1}/{max_retries}")
            return {
                "audit_result": audit_result,
                "retry_count": retry_count + 1,
                "next_action": "retry_code",
            }
        else:
            logger.error("Max retries reached, audit still failing")
            return {
                "audit_result": audit_result,
                "next_action": "end",
            }
    
    logger.info("Audit passed successfully")
    return {
        "audit_result": audit_result,
        "next_action": "end",
    }
