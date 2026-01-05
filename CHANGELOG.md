# Changelog

All notable changes to the Claim Graph project will be documented in this file.

## [0.1.0] - 2026-01-05

### Initial Release - Complete LangGraph + FastAPI RCM Agent Scaffold

#### Added

**Core Application:**
- FastAPI application with async/await support
- Pydantic v2 models for FHIR-like resources (Condition, Procedure, Observation, Claim)
- SQLite database with SQLAlchemy async ORM for resource persistence
- Environment-based configuration with pydantic-settings

**LangGraph Workflow:**
- Multi-agent graph with Supervisor router pattern
- Extractor node: Extracts medical information from FHIR resources
- Coder node: Assigns ICD-10, CPT, and LOINC codes with structured output
- Auditor node: Validates coded data and triggers retry on failure
- Retry logic with configurable max attempts (default: 3)
- Shared state management through TypedDict GraphState

**API Endpoints:**
- `POST /api/v1/ingest` - Ingest FHIR-like resources (Condition/Procedure/Observation)
- `POST /api/v1/analyze` - Run LangGraph workflow on ingested data
- `POST /api/v1/generate-claim` - Generate FHIR Claim with schema validation
- `GET /` - API information endpoint
- `GET /health` - Health check endpoint

**Testing:**
- 22 comprehensive tests covering:
  - Router logic and workflow transitions
  - Pydantic schema validation
  - API endpoint smoke tests
  - Full end-to-end workflow
- pytest with async support
- Test fixtures for database and HTTP client
- All tests passing ✅

**Development Tools:**
- Mock LLM responses for development (TODOs for real integration)
- Synthetic FHIR data generator with realistic medical scenarios
- Demo workflow script (`demo_workflow.py`) showcasing end-to-end flow
- Docker support with Dockerfile and docker-compose.yml
- Type hints throughout codebase
- Comprehensive logging

**Documentation:**
- Detailed README with:
  - ASCII architecture diagram
  - Installation instructions
  - API usage examples with curl
  - Project structure overview
  - Development guidelines
  - Roadmap and TODOs
- Code comments and docstrings
- Example data for testing

**Infrastructure:**
- Docker Compose configuration with app and db services
- SQLite in-container support
- Volume mounts for development
- Environment variable configuration
- `.gitignore` for Python projects

#### Technical Stack
- Python 3.11+
- FastAPI 0.104+
- LangGraph 0.0.40+
- Pydantic v2.5+
- SQLAlchemy 2.0+ (async)
- pytest 7.4+
- instructor 0.4+

#### TODOs and Future Work
- [ ] Replace mock LLM with OpenAI/Anthropic integration
- [ ] Add instructor for structured output validation with retry
- [ ] Implement comprehensive audit validation rules
- [ ] Integrate HAPI-FHIR server
- [ ] Add payer simulator for claim submission
- [ ] Implement authentication (API key or OAuth2)
- [ ] Add rate limiting
- [ ] Background task queue for async processing
- [ ] Prometheus metrics and monitoring
- [ ] Web UI for visualization
- [ ] X12 837 claim format export
- [ ] Batch processing support

### Notes
This initial scaffold provides a complete working prototype with:
- ✅ Working multi-agent LangGraph workflow
- ✅ RESTful API with FastAPI
- ✅ Schema validation with Pydantic
- ✅ Database persistence with SQLite
- ✅ Comprehensive test coverage
- ✅ Docker support
- ✅ Mock LLM for development
- ✅ Synthetic data generation
- ✅ Detailed documentation

The system is ready for:
1. Local development with `uvicorn app.main:app --reload`
2. Docker deployment with `docker compose up`
3. Testing with `pytest tests/ -v`
4. Demo workflow with `python demo_workflow.py`
