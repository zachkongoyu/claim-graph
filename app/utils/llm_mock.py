"""Mock LLM responses for development and testing."""
from typing import Any, Dict


def mock_llm_call(prompt: str, **kwargs) -> str:
    """
    Mock LLM call that returns predefined responses.
    
    TODO: Replace with actual LLM provider integration (OpenAI, Anthropic, etc.)
    """
    if "extract" in prompt.lower():
        return """
        Extracted medical information:
        - Diagnoses: Type 2 Diabetes Mellitus, Hypertension
        - Procedures: Blood glucose monitoring, Blood pressure check
        - Observations: HbA1c elevated, BP 140/90
        - Patient ID: patient-123
        """
    
    elif "code" in prompt.lower() or "icd" in prompt.lower() or "cpt" in prompt.lower():
        return """
        Medical codes assigned:
        - ICD-10: E11.9 (Type 2 diabetes mellitus without complications)
        - ICD-10: I10 (Essential hypertension)
        - CPT: 82947 (Glucose; quantitative, blood)
        - LOINC: 4548-4 (Hemoglobin A1c)
        """
    
    elif "audit" in prompt.lower() or "validate" in prompt.lower():
        return """
        Audit result: PASS
        - All codes are valid and properly formatted
        - Diagnoses align with procedures
        - No conflicts detected
        """
    
    elif "route" in prompt.lower() or "supervisor" in prompt.lower():
        return "extractor"
    
    return "Mock LLM response"


def mock_structured_output(schema_class: type, prompt: str) -> Any:
    """
    Mock structured output generation using instructor-like pattern.
    
    TODO: Replace with actual instructor + LLM integration
    """
    from app.models.graph_state import ExtractedData, CodedData, AuditResult
    
    if schema_class == ExtractedData:
        return ExtractedData(
            diagnoses=["Type 2 Diabetes Mellitus", "Hypertension"],
            procedures=["Blood glucose monitoring", "Blood pressure check"],
            observations=["HbA1c elevated at 7.8%", "BP 140/90 mmHg"],
            patient_id="patient-123",
        )
    
    elif schema_class == CodedData:
        return CodedData(
            icd10_codes=["E11.9", "I10"],
            cpt_codes=["82947", "99213"],
            loinc_codes=["4548-4"],
        )
    
    elif schema_class == AuditResult:
        return AuditResult(
            passed=True,
            issues=[],
            severity="low",
            recommendations=["Consider follow-up in 3 months"],
        )
    
    return None
