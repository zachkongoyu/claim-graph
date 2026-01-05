"""Generate claim endpoint with schema validation."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from app.database.db import get_session
from app.database.crud import get_latest_analysis
from app.models.fhir_models import Claim, ClaimItem, CodeableConcept, Reference
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class GenerateClaimRequest(BaseModel):
    """Request model for claim generation."""
    patient_id: str = "patient-123"
    provider_id: Optional[str] = "provider-456"


class GenerateClaimResponse(BaseModel):
    """Response model for claim generation."""
    success: bool
    message: str
    claim: Optional[Claim] = None


@router.post("/generate-claim", response_model=GenerateClaimResponse)
async def generate_claim(
    request: GenerateClaimRequest,
    db: AsyncSession = Depends(get_session),
):
    """
    Generate a FHIR Claim resource from analysis results.
    
    Uses the most recent analysis results to construct a draft FHIR Claim
    with proper schema validation via Pydantic.
    
    TODO: Integrate with actual LLM for intelligent claim generation
    TODO: Add instructor for structured output validation
    
    Args:
        request: GenerateClaimRequest with patient and provider IDs
        db: Database session
    
    Returns:
        GenerateClaimResponse with validated FHIR Claim
    """
    try:
        # Fetch latest analysis results
        analysis = await get_latest_analysis(db)
        
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail="No analysis results found. Please run /analyze first.",
            )
        
        # Parse analysis data
        import json
        coded_data = json.loads(analysis.coded_data)
        
        # Build diagnosis list from ICD-10 codes
        diagnoses = []
        for i, icd_code in enumerate(coded_data.get("icd10_codes", [])):
            diagnoses.append({
                "sequence": i + 1,
                "diagnosisCodeableConcept": {
                    "coding": [{
                        "system": "http://hl7.org/fhir/sid/icd-10",
                        "code": icd_code,
                    }],
                },
            })
        
        # Build claim items from CPT codes
        items = []
        for i, cpt_code in enumerate(coded_data.get("cpt_codes", [])):
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
        
        # Calculate total
        total_amount = sum(item.net["value"] for item in items if item.net)
        
        # Create the Claim resource with schema validation
        claim = Claim(
            id=f"claim-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            status="active",
            type=CodeableConcept(
                coding=[{
                    "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                    "code": "institutional",
                    "display": "Institutional",
                }],
            ),
            patient=Reference(
                reference=f"Patient/{request.patient_id}",
                display=f"Patient {request.patient_id}",
            ),
            provider=Reference(
                reference=f"Organization/{request.provider_id}",
                display=f"Provider {request.provider_id}",
            ) if request.provider_id else None,
            created=datetime.now(),
            diagnosis=diagnoses,
            item=items,
            total={"value": total_amount, "currency": "USD"} if total_amount > 0 else None,
        )
        
        # Pydantic automatically validates the schema
        # If validation fails, it will raise a ValidationError
        
        logger.info(f"Generated claim {claim.id} with {len(items)} items")
        
        return GenerateClaimResponse(
            success=True,
            message=f"Successfully generated claim with {len(items)} items",
            claim=claim,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating claim: {e}")
        raise HTTPException(status_code=500, detail=str(e))
