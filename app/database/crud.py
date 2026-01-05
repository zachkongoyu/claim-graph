"""Database models and CRUD operations."""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db import Base
import json


class FHIRResource(Base):
    """Model for storing FHIR-like resources."""
    __tablename__ = "fhir_resources"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String, unique=True, index=True)
    resource_type = Column(String, index=True)
    data = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnalysisResult(Base):
    """Model for storing analysis results."""
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    resource_ids = Column(Text)  # JSON array of resource IDs
    extracted_data = Column(Text)  # JSON
    coded_data = Column(Text)  # JSON
    audit_result = Column(Text)  # JSON
    created_at = Column(DateTime, default=datetime.utcnow)


async def create_fhir_resource(
    db: AsyncSession, resource_id: str, resource_type: str, data: dict
) -> FHIRResource:
    """Create a new FHIR resource."""
    resource = FHIRResource(
        resource_id=resource_id,
        resource_type=resource_type,
        data=json.dumps(data),
    )
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    return resource


async def get_fhir_resources(
    db: AsyncSession, resource_ids: List[str]
) -> List[FHIRResource]:
    """Get FHIR resources by IDs."""
    result = await db.execute(
        select(FHIRResource).where(FHIRResource.resource_id.in_(resource_ids))
    )
    return result.scalars().all()


async def create_analysis_result(
    db: AsyncSession,
    resource_ids: List[str],
    extracted_data: dict,
    coded_data: dict,
    audit_result: dict,
) -> AnalysisResult:
    """Store analysis result."""
    result = AnalysisResult(
        resource_ids=json.dumps(resource_ids),
        extracted_data=json.dumps(extracted_data),
        coded_data=json.dumps(coded_data),
        audit_result=json.dumps(audit_result),
    )
    db.add(result)
    await db.commit()
    await db.refresh(result)
    return result


async def get_latest_analysis(db: AsyncSession) -> Optional[AnalysisResult]:
    """Get the most recent analysis result."""
    result = await db.execute(
        select(AnalysisResult).order_by(AnalysisResult.created_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()
