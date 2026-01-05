"""Ingest endpoint for FHIR-like resources."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.fhir_models import IngestRequest, IngestResponse
from app.database.db import get_session
from app.database.crud import create_fhir_resource
import logging
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_resources(
    request: IngestRequest,
    db: AsyncSession = Depends(get_session),
):
    """
    Ingest FHIR-like resources into the database.
    
    Accepts Condition, Procedure, and Observation resources and persists them
    to SQLite for later analysis.
    
    Args:
        request: IngestRequest containing FHIR resources
        db: Database session
    
    Returns:
        IngestResponse with success status and resource IDs
    """
    try:
        resource_ids = []
        
        # Store conditions
        for condition in request.conditions:
            resource_id = condition.id or f"condition-{uuid.uuid4().hex[:8]}"
            await create_fhir_resource(
                db=db,
                resource_id=resource_id,
                resource_type="Condition",
                data=condition.model_dump(),
            )
            resource_ids.append(resource_id)
            logger.info(f"Stored condition: {resource_id}")
        
        # Store procedures
        for procedure in request.procedures:
            resource_id = procedure.id or f"procedure-{uuid.uuid4().hex[:8]}"
            await create_fhir_resource(
                db=db,
                resource_id=resource_id,
                resource_type="Procedure",
                data=procedure.model_dump(),
            )
            resource_ids.append(resource_id)
            logger.info(f"Stored procedure: {resource_id}")
        
        # Store observations
        for observation in request.observations:
            resource_id = observation.id or f"observation-{uuid.uuid4().hex[:8]}"
            await create_fhir_resource(
                db=db,
                resource_id=resource_id,
                resource_type="Observation",
                data=observation.model_dump(),
            )
            resource_ids.append(resource_id)
            logger.info(f"Stored observation: {resource_id}")
        
        return IngestResponse(
            success=True,
            message=f"Successfully ingested {len(resource_ids)} resources",
            resource_ids=resource_ids,
        )
    
    except Exception as e:
        logger.error(f"Error ingesting resources: {e}")
        raise HTTPException(status_code=500, detail=str(e))
