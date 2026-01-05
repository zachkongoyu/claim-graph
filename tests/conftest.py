"""Pytest configuration and fixtures."""
import pytest
import asyncio
from typing import AsyncGenerator
import httpx
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.database.db import Base
import os
import json
from unittest.mock import AsyncMock, MagicMock

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # Set test database URL in environment before importing app
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    
    # Ensure data directory exists for file-based databases
    os.makedirs("./data", exist_ok=True)
    
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    test_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with test_session_maker() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


class MockRobynClient:
    """Mock client for testing Robyn endpoints."""
    
    def __init__(self, base_url: str = "http://test"):
        self.base_url = base_url
        # Import endpoints after environment is set
        from app import main
        self.app_module = main
    
    async def get(self, path: str):
        """Mock GET request."""
        from app.main import root, health
        
        request = MagicMock()
        
        if path == "/":
            response = await root(request)
        elif path == "/health":
            response = await health(request)
        else:
            return MockResponse(404, {"detail": "Not found"})
        
        # Handle Response object from Robyn
        if hasattr(response, 'description'):
            return MockResponse(response.status_code, json_module.loads(response.description))
        return MockResponse(200, response)
    
    async def post(self, path: str, json: dict = None):
        """Mock POST request."""
        from app.main import ingest_resources, analyze_resources, generate_claim_endpoint
        
        request = MagicMock()
        request.body = json_module.dumps(json) if json else "{}"
        
        try:
            if path == "/api/v1/ingest":
                response = await ingest_resources(request)
            elif path == "/api/v1/analyze":
                response = await analyze_resources(request)
            elif path == "/api/v1/generate-claim":
                response = await generate_claim_endpoint(request)
            else:
                return MockResponse(404, {"detail": "Not found"})
            
            # Handle Response object from Robyn
            if hasattr(response, 'description'):
                return MockResponse(response.status_code, json_module.loads(response.description))
            return MockResponse(200, response)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return MockResponse(500, {"detail": str(e)})


class MockResponse:
    """Mock response object."""
    
    def __init__(self, status_code: int, data: dict):
        self.status_code = status_code
        self._data = data
    
    def json(self):
        """Return JSON data."""
        return self._data


import json as json_module


@pytest.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[MockRobynClient, None]:
    """
    Create a mock test client for Robyn app.
    
    Since Robyn doesn't have built-in test client support like FastAPI,
    we create a mock client that calls the endpoint functions directly.
    """
    # Ensure test database is being used
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    
    # Ensure data directory exists
    os.makedirs("./data", exist_ok=True)
    
    # Initialize database tables
    from app.database.db import init_db
    await init_db()
    
    mock_client = MockRobynClient()
    yield mock_client
