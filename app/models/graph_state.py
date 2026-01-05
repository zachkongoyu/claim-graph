"""State model for LangGraph workflow."""
from typing import List, Optional, TypedDict, Literal
from pydantic import BaseModel, Field


class ExtractedData(BaseModel):
    """Data extracted from FHIR resources."""
    diagnoses: List[str] = Field(default_factory=list)
    procedures: List[str] = Field(default_factory=list)
    observations: List[str] = Field(default_factory=list)
    patient_id: Optional[str] = None


class CodedData(BaseModel):
    """Medical codes assigned to extracted data."""
    icd10_codes: List[str] = Field(default_factory=list)
    cpt_codes: List[str] = Field(default_factory=list)
    loinc_codes: List[str] = Field(default_factory=list)


class AuditResult(BaseModel):
    """Result of audit check."""
    passed: bool
    issues: List[str] = Field(default_factory=list)
    severity: Literal["low", "medium", "high"] = "low"
    recommendations: List[str] = Field(default_factory=list)


class GraphState(TypedDict):
    """State passed through the LangGraph workflow."""
    resource_ids: List[str]
    extracted_data: Optional[ExtractedData]
    coded_data: Optional[CodedData]
    audit_result: Optional[AuditResult]
    retry_count: int
    max_retries: int
    next_action: Optional[str]
    error: Optional[str]
