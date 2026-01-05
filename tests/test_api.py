"""API smoke tests."""
import pytest
from httpx import AsyncClient
from app.utils.synthetic_data import generate_minimal_dataset


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint returns API information."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "endpoints" in data


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_ingest_endpoint(client: AsyncClient):
    """Test ingest endpoint with synthetic data."""
    dataset = generate_minimal_dataset()
    
    response = await client.post(
        "/api/v1/ingest",
        json=dataset.model_dump(mode='json'),
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["resource_ids"]) == 3  # 1 condition, 1 procedure, 1 observation


@pytest.mark.asyncio
async def test_analyze_endpoint(client: AsyncClient):
    """Test analyze endpoint."""
    # First ingest some data
    dataset = generate_minimal_dataset()
    ingest_response = await client.post(
        "/api/v1/ingest",
        json=dataset.model_dump(mode='json'),
    )
    assert ingest_response.status_code == 200
    resource_ids = ingest_response.json()["resource_ids"]
    
    # Then analyze it
    response = await client.post(
        "/api/v1/analyze",
        json={"resource_ids": resource_ids, "max_retries": 3},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "extracted_data" in data
    assert "coded_data" in data
    assert "audit_result" in data


@pytest.mark.asyncio
async def test_generate_claim_endpoint(client: AsyncClient):
    """Test generate claim endpoint."""
    # First ingest and analyze data
    dataset = generate_minimal_dataset()
    ingest_response = await client.post(
        "/api/v1/ingest",
        json=dataset.model_dump(mode='json'),
    )
    resource_ids = ingest_response.json()["resource_ids"]
    
    analyze_response = await client.post(
        "/api/v1/analyze",
        json={"resource_ids": resource_ids},
    )
    assert analyze_response.status_code == 200
    
    # Then generate claim
    response = await client.post(
        "/api/v1/generate-claim",
        json={"patient_id": "patient-123"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "claim" in data
    assert data["claim"]["resourceType"] == "Claim"


@pytest.mark.asyncio
async def test_generate_claim_without_analysis(client: AsyncClient):
    """Test generate claim endpoint fails without prior analysis."""
    response = await client.post(
        "/api/v1/generate-claim",
        json={"patient_id": "patient-123"},
    )
    
    assert response.status_code == 404
    assert "No analysis results found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_full_workflow(client: AsyncClient):
    """Test complete workflow: ingest -> analyze -> generate claim."""
    # 1. Ingest data
    dataset = generate_minimal_dataset()
    ingest_response = await client.post(
        "/api/v1/ingest",
        json=dataset.model_dump(mode='json'),
    )
    assert ingest_response.status_code == 200
    resource_ids = ingest_response.json()["resource_ids"]
    
    # 2. Analyze data
    analyze_response = await client.post(
        "/api/v1/analyze",
        json={"resource_ids": resource_ids, "max_retries": 3},
    )
    assert analyze_response.status_code == 200
    analysis = analyze_response.json()
    assert analysis["coded_data"] is not None
    
    # 3. Generate claim
    claim_response = await client.post(
        "/api/v1/generate-claim",
        json={"patient_id": "patient-123", "provider_id": "provider-456"},
    )
    assert claim_response.status_code == 200
    claim = claim_response.json()["claim"]
    assert claim["patient"]["reference"] == "Patient/patient-123"
    assert len(claim["item"]) > 0
