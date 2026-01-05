"""Analyze endpoint for running LangGraph workflow."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from app.database.db import get_session
from app.database.crud import create_analysis_result
from app.graph.graph import run_workflow
from app.models.graph_state import ExtractedData, CodedData, AuditResult
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class AnalyzeRequest(BaseModel):
    """Request model for analyze endpoint."""
    resource_ids: List[str]
    max_retries: int = 3


class AnalyzeResponse(BaseModel):
    """Response model for analyze endpoint."""
    success: bool
    message: str
    extracted_data: Optional[ExtractedData] = None
    coded_data: Optional[CodedData] = None
    audit_result: Optional[AuditResult] = None
    retry_count: int = 0


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_resources(
    request: AnalyzeRequest,
    db: AsyncSession = Depends(get_session),
):
    """
    Run the LangGraph workflow on ingested resources.
    
    Executes the multi-agent workflow:
    1. Extractor - extracts medical information from FHIR resources
    2. Coder - assigns ICD-10, CPT, LOINC codes
    3. Auditor - validates codes and triggers retry if needed
    
    Args:
        request: AnalyzeRequest with resource IDs to process
        db: Database session
    
    Returns:
        AnalyzeResponse with workflow results
    """
    try:
        logger.info(f"Starting analysis on {len(request.resource_ids)} resources")
        
        # Run the LangGraph workflow
        final_state = run_workflow(
            resource_ids=request.resource_ids,
            max_retries=request.max_retries,
        )
        
        # Extract results from final state
        extracted_data = final_state.get("extracted_data")
        coded_data = final_state.get("coded_data")
        audit_result = final_state.get("audit_result")
        retry_count = final_state.get("retry_count", 0)
        error = final_state.get("error")
        
        # Store analysis result in database
        if extracted_data and coded_data and audit_result:
            await create_analysis_result(
                db=db,
                resource_ids=request.resource_ids,
                extracted_data=extracted_data.model_dump() if extracted_data else {},
                coded_data=coded_data.model_dump() if coded_data else {},
                audit_result=audit_result.model_dump() if audit_result else {},
            )
        
        if error:
            logger.error(f"Workflow completed with error: {error}")
            raise HTTPException(status_code=500, detail=error)
        
        return AnalyzeResponse(
            success=True,
            message="Analysis completed successfully",
            extracted_data=extracted_data,
            coded_data=coded_data,
            audit_result=audit_result,
            retry_count=retry_count,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
