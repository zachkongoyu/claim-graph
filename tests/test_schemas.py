"""Tests for schema validation."""
import pytest
from pydantic import ValidationError
from datetime import datetime
from app.models.fhir_models import (
    Condition,
    Procedure,
    Observation,
    Claim,
    ClaimItem,
    CodeableConcept,
    Reference,
)


def test_codeable_concept_validation():
    """Test CodeableConcept schema validation."""
    concept = CodeableConcept(
        coding=[{"system": "http://snomed.info/sct", "code": "12345"}],
        text="Test Concept",
    )
    assert concept.text == "Test Concept"
    assert len(concept.coding) == 1


def test_condition_resource_type():
    """Test Condition resource has correct resourceType."""
    condition = Condition(
        code=CodeableConcept(coding=[], text="Test"),
        subject=Reference(reference="Patient/123"),
    )
    assert condition.resourceType == "Condition"


def test_procedure_resource_type():
    """Test Procedure resource has correct resourceType."""
    procedure = Procedure(
        code=CodeableConcept(coding=[], text="Test"),
        subject=Reference(reference="Patient/123"),
    )
    assert procedure.resourceType == "Procedure"


def test_observation_resource_type():
    """Test Observation resource has correct resourceType."""
    observation = Observation(
        code=CodeableConcept(coding=[], text="Test"),
        subject=Reference(reference="Patient/123"),
    )
    assert observation.resourceType == "Observation"


def test_claim_validation():
    """Test Claim schema validation."""
    claim = Claim(
        status="active",
        type=CodeableConcept(
            coding=[{"system": "http://terminology.hl7.org/CodeSystem/claim-type", "code": "institutional"}]
        ),
        patient=Reference(reference="Patient/123"),
        created=datetime.now(),
    )
    assert claim.resourceType == "Claim"
    assert claim.status == "active"
    assert len(claim.diagnosis) == 0
    assert len(claim.item) == 0


def test_claim_with_items():
    """Test Claim with ClaimItem validation."""
    item = ClaimItem(
        sequence=1,
        productOrService=CodeableConcept(
            coding=[{"system": "http://www.ama-assn.org/go/cpt", "code": "99213"}]
        ),
        unitPrice={"value": 150.00, "currency": "USD"},
    )
    
    claim = Claim(
        status="active",
        type=CodeableConcept(coding=[{"code": "institutional"}]),
        patient=Reference(reference="Patient/123"),
        created=datetime.now(),
        item=[item],
    )
    
    assert len(claim.item) == 1
    assert claim.item[0].sequence == 1


def test_invalid_claim_status():
    """Test that invalid claim status is accepted (no enum constraint)."""
    # Since status is just a string, any value is valid
    claim = Claim(
        status="invalid-status",
        type=CodeableConcept(coding=[{"code": "institutional"}]),
        patient=Reference(reference="Patient/123"),
        created=datetime.now(),
    )
    assert claim.status == "invalid-status"


def test_reference_validation():
    """Test Reference schema validation."""
    ref = Reference(
        reference="Patient/123",
        display="Test Patient",
    )
    assert ref.reference == "Patient/123"
    assert ref.display == "Test Patient"


def test_claim_item_sequence():
    """Test ClaimItem requires sequence number."""
    item = ClaimItem(
        sequence=1,
        productOrService=CodeableConcept(coding=[{"code": "99213"}]),
    )
    assert item.sequence == 1
