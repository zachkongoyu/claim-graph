"""FHIR-like data models using Pydantic."""
from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class CodeableConcept(BaseModel):
    """A concept that may be defined by one or more codes from formal definitions."""
    coding: List[dict] = Field(default_factory=list)
    text: Optional[str] = None


class Reference(BaseModel):
    """A reference from one resource to another."""
    reference: Optional[str] = None
    display: Optional[str] = None


class Condition(BaseModel):
    """FHIR Condition resource fragment."""
    id: Optional[str] = None
    resourceType: Literal["Condition"] = "Condition"
    code: CodeableConcept
    subject: Reference
    recordedDate: Optional[datetime] = None
    severity: Optional[CodeableConcept] = None
    clinicalStatus: Optional[CodeableConcept] = None


class Procedure(BaseModel):
    """FHIR Procedure resource fragment."""
    id: Optional[str] = None
    resourceType: Literal["Procedure"] = "Procedure"
    code: CodeableConcept
    subject: Reference
    performedDateTime: Optional[datetime] = None
    status: Optional[str] = "completed"


class Observation(BaseModel):
    """FHIR Observation resource fragment."""
    id: Optional[str] = None
    resourceType: Literal["Observation"] = "Observation"
    code: CodeableConcept
    subject: Reference
    valueString: Optional[str] = None
    valueQuantity: Optional[dict] = None
    effectiveDateTime: Optional[datetime] = None
    status: Optional[str] = "final"


class ClaimItem(BaseModel):
    """Item within a Claim."""
    sequence: int
    productOrService: CodeableConcept
    servicedDate: Optional[str] = None
    unitPrice: Optional[dict] = None
    net: Optional[dict] = None


class Claim(BaseModel):
    """FHIR Claim resource."""
    id: Optional[str] = None
    resourceType: Literal["Claim"] = "Claim"
    status: str = "active"
    type: CodeableConcept
    patient: Reference
    created: datetime = Field(default_factory=datetime.now)
    provider: Optional[Reference] = None
    diagnosis: List[dict] = Field(default_factory=list)
    item: List[ClaimItem] = Field(default_factory=list)
    total: Optional[dict] = None


class IngestRequest(BaseModel):
    """Request model for ingesting FHIR-like resources."""
    conditions: List[Condition] = Field(default_factory=list)
    procedures: List[Procedure] = Field(default_factory=list)
    observations: List[Observation] = Field(default_factory=list)


class IngestResponse(BaseModel):
    """Response model for ingest endpoint."""
    success: bool
    message: str
    resource_ids: List[str] = Field(default_factory=list)
