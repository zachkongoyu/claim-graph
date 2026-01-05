"""Main Robyn application."""
from robyn import Robyn, jsonify, Request, Response
from robyn.robyn import Headers
import logging
import os
import json
import anyio
from typing import Optional

from app.config import settings
from app.database.db import init_db, async_session_maker
from app.models.fhir_models import IngestRequest, Claim
from app.models.graph_state import ExtractedData, CodedData, AuditResult
from app.database.crud import (
    create_fhir_resource,
    create_analysis_result,
    get_latest_analysis,
)
from app.graph.graph import run_workflow
from datetime import datetime
from pydantic import BaseModel, ValidationError
import uuid

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = Robyn(__file__)

# CORS headers
CORS_HEADERS = Headers({
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
})


@app.startup_handler
async def startup():
    """Application startup handler."""
    logger.info("Starting Claim Graph RCM Agent with Robyn")
    
    # Create data directory if it doesn't exist
    os.makedirs("./data", exist_ok=True)
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")


@app.shutdown_handler
def shutdown():
    """Application shutdown handler."""
    logger.info("Shutting down Claim Graph RCM Agent")


@app.get("/")
async def root(request: Request):
    """Root endpoint."""
    return Response(
        status_code=200,
        headers=CORS_HEADERS,
        description=jsonify({
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "endpoints": {
                "ingest": "/api/v1/ingest",
                "analyze": "/api/v1/analyze",
                "generate_claim": "/api/v1/generate-claim",
            },
        })
    )


@app.get("/health")
async def health(request: Request):
    """Health check endpoint."""
    return Response(
        status_code=200,
        headers=CORS_HEADERS,
        description=jsonify({"status": "healthy"})
    )


@app.post("/api/v1/ingest")
async def ingest_resources(request: Request):
    """
    Ingest FHIR-like resources into the database.
    
    Accepts Condition, Procedure, and Observation resources and persists them
    to SQLite for later analysis.
    """
    try:
        # Parse request body
        body = json.loads(request.body)
        ingest_req = IngestRequest(**body)
        
        resource_ids = []
        
        # Use AnyIO to run async database operations
        async def store_resources():
            async with async_session_maker() as db:
                # Store conditions
                for condition in ingest_req.conditions:
                    resource_id = condition.id or f"condition-{uuid.uuid4().hex[:8]}"
                    await create_fhir_resource(
                        db=db,
                        resource_id=resource_id,
                        resource_type="Condition",
                        data=condition.model_dump(mode='json'),
                    )
                    resource_ids.append(resource_id)
                    logger.info(f"Stored condition: {resource_id}")
                
                # Store procedures
                for procedure in ingest_req.procedures:
                    resource_id = procedure.id or f"procedure-{uuid.uuid4().hex[:8]}"
                    await create_fhir_resource(
                        db=db,
                        resource_id=resource_id,
                        resource_type="Procedure",
                        data=procedure.model_dump(mode='json'),
                    )
                    resource_ids.append(resource_id)
                    logger.info(f"Stored procedure: {resource_id}")
                
                # Store observations
                for observation in ingest_req.observations:
                    resource_id = observation.id or f"observation-{uuid.uuid4().hex[:8]}"
                    await create_fhir_resource(
                        db=db,
                        resource_id=resource_id,
                        resource_type="Observation",
                        data=observation.model_dump(mode='json'),
                    )
                    resource_ids.append(resource_id)
                    logger.info(f"Stored observation: {resource_id}")
                
                await db.commit()
        
        await store_resources()
        
        return Response(
            status_code=200,
            headers=CORS_HEADERS,
            description=jsonify({
                "success": True,
                "message": f"Successfully ingested {len(resource_ids)} resources",
                "resource_ids": resource_ids,
            })
        )
    
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return Response(
            status_code=400,
            headers=CORS_HEADERS,
            description=jsonify({"detail": str(e)}),
        )
    except Exception as e:
        logger.error(f"Error ingesting resources: {e}")
        return Response(
            status_code=500,
            headers=CORS_HEADERS,
            description=jsonify({"detail": str(e)}),
        )


@app.post("/api/v1/analyze")
async def analyze_resources(request: Request):
    """
    Run the LangGraph workflow on ingested resources.
    
    Executes the multi-agent workflow:
    1. Extractor - extracts medical information from FHIR resources
    2. Coder - assigns ICD-10, CPT, LOINC codes
    3. Auditor - validates codes and triggers retry if needed
    """
    try:
        # Parse request body
        body = json.loads(request.body)
        resource_ids = body.get("resource_ids", [])
        max_retries = body.get("max_retries", 3)
        
        logger.info(f"Starting analysis on {len(resource_ids)} resources")
        
        # Run the LangGraph workflow
        final_state = run_workflow(
            resource_ids=resource_ids,
            max_retries=max_retries,
        )
        
        # Extract results from final state
        extracted_data = final_state.get("extracted_data")
        coded_data = final_state.get("coded_data")
        audit_result = final_state.get("audit_result")
        retry_count = final_state.get("retry_count", 0)
        error = final_state.get("error")
        
        # Store analysis result in database
        async def store_analysis():
            if extracted_data and coded_data and audit_result:
                async with async_session_maker() as db:
                    await create_analysis_result(
                        db=db,
                        resource_ids=resource_ids,
                        extracted_data=extracted_data.model_dump() if extracted_data else {},
                        coded_data=coded_data.model_dump() if coded_data else {},
                        audit_result=audit_result.model_dump() if audit_result else {},
                    )
                    await db.commit()
        
        await store_analysis()
        
        if error:
            logger.error(f"Workflow completed with error: {error}")
            return Response(
                status_code=500,
                headers=CORS_HEADERS,
                description=jsonify({"detail": error}),
            )
        
        return Response(
            status_code=200,
            headers=CORS_HEADERS,
            description=jsonify({
                "success": True,
                "message": "Analysis completed successfully",
                "extracted_data": extracted_data.model_dump() if extracted_data else None,
                "coded_data": coded_data.model_dump() if coded_data else None,
                "audit_result": audit_result.model_dump() if audit_result else None,
                "retry_count": retry_count,
            })
        )
    
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        return Response(
            status_code=500,
            headers=CORS_HEADERS,
            description=jsonify({"detail": str(e)}),
        )


@app.post("/api/v1/generate-claim")
async def generate_claim_endpoint(request: Request):
    """
    Generate a FHIR Claim resource from analysis results.
    
    Uses the most recent analysis results to construct a draft FHIR Claim
    with proper schema validation via Pydantic.
    
    TODO: Integrate with actual LLM for intelligent claim generation
    TODO: Add instructor for structured output validation
    """
    try:
        # Parse request body
        body = json.loads(request.body)
        patient_id = body.get("patient_id", "patient-123")
        provider_id = body.get("provider_id", "provider-456")
        
        # Fetch latest analysis results
        async def get_analysis():
            async with async_session_maker() as db:
                return await get_latest_analysis(db)
        
        analysis = await get_analysis()
        
        if not analysis:
            return Response(
                status_code=404,
                headers=CORS_HEADERS,
                description=jsonify({
                    "detail": "No analysis results found. Please run /analyze first."
                }),
            )
        
        # Parse analysis data
        coded_data_dict = json.loads(analysis.coded_data)
        
        # Build diagnosis list from ICD-10 codes
        diagnoses = []
        for i, icd_code in enumerate(coded_data_dict.get("icd10_codes", [])):
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
        for i, cpt_code in enumerate(coded_data_dict.get("cpt_codes", [])):
            items.append({
                "sequence": i + 1,
                "productOrService": {
                    "coding": [{
                        "system": "http://www.ama-assn.org/go/cpt",
                        "code": cpt_code,
                    }],
                },
                "servicedDate": datetime.now().isoformat(),
                "unitPrice": {"value": 100.00 + (i * 50), "currency": "USD"},
                "net": {"value": 100.00 + (i * 50), "currency": "USD"},
            })
        
        # Calculate total
        total_amount = sum(item["net"]["value"] for item in items if "net" in item)
        
        # Create the Claim resource with schema validation
        from app.models.fhir_models import ClaimItem, CodeableConcept, Reference
        
        claim_items = []
        for item_data in items:
            claim_items.append(ClaimItem(
                sequence=item_data["sequence"],
                productOrService=CodeableConcept(
                    coding=item_data["productOrService"]["coding"],
                ),
                servicedDate=item_data["servicedDate"],
                unitPrice=item_data["unitPrice"],
                net=item_data["net"],
            ))
        
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
                reference=f"Patient/{patient_id}",
                display=f"Patient {patient_id}",
            ),
            provider=Reference(
                reference=f"Organization/{provider_id}",
                display=f"Provider {provider_id}",
            ) if provider_id else None,
            created=datetime.now(),
            diagnosis=diagnoses,
            item=claim_items,
            total={"value": total_amount, "currency": "USD"} if total_amount > 0 else None,
        )
        
        logger.info(f"Generated claim {claim.id} with {len(items)} items")
        
        return Response(
            status_code=200,
            headers=CORS_HEADERS,
            description=jsonify({
                "success": True,
                "message": f"Successfully generated claim with {len(items)} items",
                "claim": claim.model_dump(mode='json'),
            })
        )
    
    except Exception as e:
        logger.error(f"Error generating claim: {e}")
        return Response(
            status_code=500,
            headers=CORS_HEADERS,
            description=jsonify({"detail": str(e)}),
        )


if __name__ == "__main__":
    app.start(host="0.0.0.0", port=8000)
