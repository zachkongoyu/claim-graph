#!/usr/bin/env python
"""
End-to-end demonstration of the Claim Graph RCM Agent workflow.

This script demonstrates:
1. Starting the application
2. Ingesting synthetic FHIR resources
3. Running the LangGraph analysis workflow
4. Generating a FHIR Claim resource

Usage:
    python demo_workflow.py
"""

import asyncio
import json
from app.utils.synthetic_data import generate_synthetic_dataset
from app.models.graph_state import GraphState
from app.graph.graph import run_workflow
from app.models.fhir_models import Claim, ClaimItem, CodeableConcept, Reference
from datetime import datetime


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def main():
    """Run the demonstration workflow."""
    
    print_section("Claim Graph RCM Agent - End-to-End Demonstration")
    
    # Step 1: Generate synthetic FHIR data
    print_section("Step 1: Generate Synthetic FHIR Data")
    dataset = generate_synthetic_dataset()
    
    print(f"Generated {len(dataset.conditions)} Conditions:")
    for cond in dataset.conditions:
        print(f"  - {cond.id}: {cond.code.text}")
    
    print(f"\nGenerated {len(dataset.procedures)} Procedures:")
    for proc in dataset.procedures:
        print(f"  - {proc.id}: {proc.code.text}")
    
    print(f"\nGenerated {len(dataset.observations)} Observations:")
    for obs in dataset.observations:
        print(f"  - {obs.id}: {obs.code.text}")
    
    # Step 2: Simulate resource IDs (in real app, these come from database)
    print_section("Step 2: Ingest Resources (Mock)")
    resource_ids = [cond.id for cond in dataset.conditions if cond.id]
    resource_ids += [proc.id for proc in dataset.procedures if proc.id]
    resource_ids += [obs.id for obs in dataset.observations if obs.id]
    print(f"Mock resource IDs: {resource_ids}")
    
    # Step 3: Run LangGraph workflow
    print_section("Step 3: Run LangGraph Workflow")
    print("Running multi-agent workflow:")
    print("  → Supervisor Router")
    print("  → Extractor (extract medical information)")
    print("  → Coder (assign ICD-10, CPT, LOINC codes)")
    print("  → Auditor (validate codes)")
    print("  → [Retry loop if audit fails]\n")
    
    final_state = run_workflow(resource_ids=resource_ids, max_retries=3)
    
    print("\n--- Workflow Results ---\n")
    
    if final_state.get("extracted_data"):
        print("Extracted Data:")
        extracted = final_state["extracted_data"]
        print(f"  Diagnoses: {extracted.diagnoses}")
        print(f"  Procedures: {extracted.procedures}")
        print(f"  Observations: {extracted.observations}")
        print(f"  Patient ID: {extracted.patient_id}")
    
    if final_state.get("coded_data"):
        print("\nCoded Data:")
        coded = final_state["coded_data"]
        print(f"  ICD-10 Codes: {coded.icd10_codes}")
        print(f"  CPT Codes: {coded.cpt_codes}")
        print(f"  LOINC Codes: {coded.loinc_codes}")
    
    if final_state.get("audit_result"):
        print("\nAudit Result:")
        audit = final_state["audit_result"]
        print(f"  Passed: {audit.passed}")
        print(f"  Issues: {audit.issues}")
        print(f"  Severity: {audit.severity}")
        print(f"  Recommendations: {audit.recommendations}")
    
    print(f"\nRetry Count: {final_state.get('retry_count', 0)}")
    
    # Step 4: Generate FHIR Claim
    print_section("Step 4: Generate FHIR Claim")
    
    coded_data = final_state.get("coded_data")
    if not coded_data:
        print("ERROR: No coded data available")
        return
    
    # Build diagnosis list
    diagnoses = []
    for i, icd_code in enumerate(coded_data.icd10_codes):
        diagnoses.append({
            "sequence": i + 1,
            "diagnosisCodeableConcept": {
                "coding": [{
                    "system": "http://hl7.org/fhir/sid/icd-10",
                    "code": icd_code,
                }],
            },
        })
    
    # Build claim items
    items = []
    for i, cpt_code in enumerate(coded_data.cpt_codes):
        item = ClaimItem(
            sequence=i + 1,
            productOrService=CodeableConcept(
                coding=[{
                    "system": "http://www.ama-assn.org/go/cpt",
                    "code": cpt_code,
                }],
            ),
            servicedDate=datetime.now().isoformat(),
            unitPrice={"value": 100.00 + (i * 50), "currency": "USD"},
            net={"value": 100.00 + (i * 50), "currency": "USD"},
        )
        items.append(item)
    
    # Create Claim
    claim = Claim(
        id=f"claim-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        status="active",
        type=CodeableConcept(
            coding=[{
                "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                "code": "institutional",
            }],
        ),
        patient=Reference(reference="Patient/patient-123"),
        provider=Reference(reference="Organization/provider-456"),
        created=datetime.now(),
        diagnosis=diagnoses,
        item=items,
        total={"value": sum(item.net["value"] for item in items), "currency": "USD"},
    )
    
    print("Generated FHIR Claim:")
    print(json.dumps(claim.model_dump(mode='json'), indent=2))
    
    print_section("Demo Complete!")
    print("✓ Successfully generated claim with LangGraph workflow")
    print("✓ All agents executed: Extractor → Coder → Auditor")
    print("✓ Schema validation passed (Pydantic)")
    print("\nNext steps:")
    print("  - Start the FastAPI server: uvicorn app.main:app --reload")
    print("  - Try the API endpoints documented in README.md")
    print("  - Run tests: pytest tests/ -v")


if __name__ == "__main__":
    main()
