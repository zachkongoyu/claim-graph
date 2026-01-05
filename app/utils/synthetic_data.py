"""Synthetic FHIR-like data generator for testing."""
from datetime import datetime, timedelta
from typing import List
import random
from app.models.fhir_models import (
    Condition,
    Procedure,
    Observation,
    CodeableConcept,
    Reference,
    IngestRequest,
)


def generate_codeable_concept(code: str, display: str, system: str = "http://snomed.info/sct") -> CodeableConcept:
    """Generate a CodeableConcept."""
    return CodeableConcept(
        coding=[{
            "system": system,
            "code": code,
            "display": display,
        }],
        text=display,
    )


def generate_patient_reference(patient_id: str = "patient-123") -> Reference:
    """Generate a patient reference."""
    return Reference(
        reference=f"Patient/{patient_id}",
        display=f"Test Patient {patient_id}",
    )


def generate_sample_conditions() -> List[Condition]:
    """Generate sample FHIR Condition resources."""
    conditions_data = [
        ("73211009", "Type 2 Diabetes Mellitus"),
        ("38341003", "Essential Hypertension"),
        ("44054006", "Type 2 Diabetes with hyperglycemia"),
    ]
    
    conditions = []
    for i, (code, display) in enumerate(conditions_data):
        condition = Condition(
            id=f"condition-{i+1}",
            code=generate_codeable_concept(code, display),
            subject=generate_patient_reference(),
            recordedDate=datetime.now() - timedelta(days=random.randint(30, 365)),
            clinicalStatus=generate_codeable_concept("active", "Active", "http://terminology.hl7.org/CodeSystem/condition-clinical"),
        )
        conditions.append(condition)
    
    return conditions


def generate_sample_procedures() -> List[Procedure]:
    """Generate sample FHIR Procedure resources."""
    procedures_data = [
        ("33747003", "Blood glucose monitoring"),
        ("250424006", "Blood pressure measurement"),
        ("269868009", "Hemoglobin A1c measurement"),
    ]
    
    procedures = []
    for i, (code, display) in enumerate(procedures_data):
        procedure = Procedure(
            id=f"procedure-{i+1}",
            code=generate_codeable_concept(code, display, "http://snomed.info/sct"),
            subject=generate_patient_reference(),
            performedDateTime=datetime.now() - timedelta(days=random.randint(1, 30)),
            status="completed",
        )
        procedures.append(procedure)
    
    return procedures


def generate_sample_observations() -> List[Observation]:
    """Generate sample FHIR Observation resources."""
    observations = [
        Observation(
            id="observation-1",
            code=generate_codeable_concept("4548-4", "Hemoglobin A1c", "http://loinc.org"),
            subject=generate_patient_reference(),
            valueString="7.8%",
            effectiveDateTime=datetime.now() - timedelta(days=7),
            status="final",
        ),
        Observation(
            id="observation-2",
            code=generate_codeable_concept("85354-9", "Blood pressure", "http://loinc.org"),
            subject=generate_patient_reference(),
            valueString="140/90 mmHg",
            effectiveDateTime=datetime.now() - timedelta(days=3),
            status="final",
        ),
        Observation(
            id="observation-3",
            code=generate_codeable_concept("2345-7", "Glucose [Mass/volume] in Serum or Plasma", "http://loinc.org"),
            subject=generate_patient_reference(),
            valueQuantity={"value": 145, "unit": "mg/dL"},
            effectiveDateTime=datetime.now() - timedelta(days=1),
            status="final",
        ),
    ]
    
    return observations


def generate_synthetic_dataset() -> IngestRequest:
    """Generate a complete synthetic FHIR dataset for testing."""
    return IngestRequest(
        conditions=generate_sample_conditions(),
        procedures=generate_sample_procedures(),
        observations=generate_sample_observations(),
    )


def generate_minimal_dataset() -> IngestRequest:
    """Generate a minimal dataset with one of each resource type."""
    return IngestRequest(
        conditions=[generate_sample_conditions()[0]],
        procedures=[generate_sample_procedures()[0]],
        observations=[generate_sample_observations()[0]],
    )
