# Claim Graph - Autonomous RCM Agent

An intelligent Revenue Cycle Management (RCM) agent built with LangGraph and Robyn. This system processes FHIR-like medical resources, extracts clinical information, assigns medical codes, and generates insurance claims with automated quality validation.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Robyn Application                        │
│  ┌──────────┐  ┌──────────┐  ┌─────────────────────┐       │
│  │  Ingest  │  │ Analyze  │  │  Generate Claim     │       │
│  │ Endpoint │  │ Endpoint │  │     Endpoint        │       │
│  └────┬─────┘  └────┬─────┘  └──────────┬──────────┘       │
└───────┼─────────────┼────────────────────┼──────────────────┘
        │             │                    │
        ▼             ▼                    ▼
   ┌────────────────────────────────────────────┐
   │           SQLite Database                  │
   │  (FHIR Resources + Analysis Results)       │
   └────────────────┬───────────────────────────┘
                    │
                    ▼
   ┌────────────────────────────────────────────┐
   │         LangGraph Workflow                 │
   │                                            │
   │  ┌──────────────────────────────────┐     │
   │  │        Supervisor Router         │     │
   │  └────────┬─────────────────────────┘     │
   │           │                                │
   │  ┌────────▼─────────┐                     │
   │  │    Extractor     │                     │
   │  │  (Extract data)  │                     │
   │  └────────┬─────────┘                     │
   │           │                                │
   │  ┌────────▼─────────┐                     │
   │  │      Coder       │◄───┐                │
   │  │  (Assign codes)  │    │ Retry Loop     │
   │  └────────┬─────────┘    │                │
   │           │               │                │
   │  ┌────────▼─────────┐    │                │
   │  │     Auditor      │────┘                │
   │  │  (Validate)      │ (on failure)        │
   │  └──────────────────┘                     │
   │                                            │
   └────────────────────────────────────────────┘
```

## Features

- **Multi-Agent Workflow**: LangGraph orchestrates Extractor, Coder, and Auditor agents
- **Retry Logic**: Automatic retry when audit validation fails
- **Schema Validation**: Pydantic models ensure FHIR-compliant data structures
- **RESTful API**: Robyn (ASGI) endpoints for ingestion, analysis, and claim generation
- **Persistent Storage**: SQLite database for FHIR resources and analysis results
- **Async Support**: Built with AnyIO for efficient async operations
- **Mock LLM Support**: Development-friendly with mock responses (TODO: add real LLM integration)
- **Synthetic Data**: Built-in test data generator for end-to-end testing

## Minimal FHIR Resource Schema for RCM

The agent should support the following R4 resources end-to-end, covering clinical inputs, coding, claims submission, and adjudication.

| Resource | Purpose | Key Fields |
| --- | --- | --- |
| Patient | Demographics | id, name, gender, birthDate, address, language |
| Coverage | Insurance details | payor, policyNumber, coveragePeriod, subscriberId |
| Encounter | Visit/interaction with provider | id, type, date, location, provider |
| Condition | Diagnoses (ICD-10-CM) | code, onsetDate, clinicalStatus, verificationStatus |
| Procedure | Services performed (CPT/HCPCS) | code, performedDate, performer, location |
| MedicationRequest / MedicationStatement | Prescriptions (RxNorm) | medicationCodeableConcept, dosage, status |
| Observation | Labs & screenings (LOINC) | code, value, unit, effectiveDateTime |
| Claim | Insurance claim submission | id, patient, provider, diagnosis, procedure, item, total |
| ClaimResponse | Payer adjudication | status, outcome, paymentAmount, errorCodes |

### Data sources and rule sets
- Synthetic clinical data: Synthea 1M Patients (FHIR R4), MIMIC-IV on FHIR demo, FHIR-AgentBench
- Coding standards: ICD-10-CM 2026, CPT/HCPCS 2026, LOINC, RxNorm (UMLS)
- Payer and claims rules: CMS Public Use Files, QRDA III 2026 IG, Medicare Physician Fee Schedule CY 2026 Final Rule

### Flow alignment
1) Ingest synthetic FHIR data (Patient, Encounter, Observation, Condition, Procedure)
2) Map to codes (ICD-10, CPT/HCPCS, LOINC, RxNorm)
3) Generate Claim resources with line items, charges, and provider info
4) Validate against payer rules and produce ClaimResponse adjudication

## End-to-End Sample Dataset (Synthetic)

Single-patient example showing connected resources from demographics through adjudicated claim.

### Patient (Demographics)
```json
{
  "resourceType": "Patient",
  "id": "patient-123",
  "name": [{ "family": "Doe", "given": ["John"] }],
  "gender": "male",
  "birthDate": "2003-03-20",
  "address": [{ "city": "Boston", "state": "MA", "country": "USA" }],
  "communication": [{ "language": { "coding": [{ "code": "en-US" }] } }]
}
```

### Coverage (Insurance)
```json
{
  "resourceType": "Coverage",
  "id": "coverage-789",
  "status": "active",
  "subscriberId": "SUB-456789",
  "payor": [{ "reference": "Organization/insurer-001" }],
  "period": { "start": "2025-01-01", "end": "2026-12-31" }
}
```

### Encounter (Visit)
```json
{
  "resourceType": "Encounter",
  "id": "encounter-001",
  "status": "finished",
  "class": { "code": "AMB" },
  "type": [{ "coding": [{ "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB", "display": "Ambulatory" }] }],
  "subject": { "reference": "Patient/patient-123" },
  "period": { "start": "2026-01-05T10:00:00Z", "end": "2026-01-05T11:00:00Z" },
  "participant": [{ "individual": { "reference": "Practitioner/practitioner-456" } }]
}
```

### Condition (Diagnosis)
```json
{
  "resourceType": "Condition",
  "id": "condition-001",
  "clinicalStatus": { "coding": [{ "code": "active" }] },
  "verificationStatus": { "coding": [{ "code": "confirmed" }] },
  "code": { "coding": [{ "system": "http://hl7.org/fhir/sid/icd-10-cm", "code": "F32.1", "display": "Major depressive disorder, single episode, moderate" }] },
  "subject": { "reference": "Patient/patient-123" },
  "onsetDateTime": "2026-01-05"
}
```

### Procedure (Service Performed)
```json
{
  "resourceType": "Procedure",
  "id": "procedure-001",
  "status": "completed",
  "code": { "coding": [{ "system": "http://www.ama-assn.org/cpt", "code": "90834", "display": "Psychotherapy, 45 minutes" }] },
  "subject": { "reference": "Patient/patient-123" },
  "performedDateTime": "2026-01-05T10:15:00Z",
  "performer": [{ "actor": { "reference": "Practitioner/practitioner-456" } }]
}
```

### MedicationRequest
```json
{
  "resourceType": "MedicationRequest",
  "id": "med-001",
  "status": "active",
  "intent": "order",
  "medicationCodeableConcept": { "coding": [{ "system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "161", "display": "Acetaminophen 325 mg oral tablet" }] },
  "subject": { "reference": "Patient/patient-123" },
  "authoredOn": "2026-01-05",
  "dosageInstruction": [{ "text": "Take 1 tablet every 6 hours as needed for pain" }]
}
```

### Observation (Lab Result)
```json
{
  "resourceType": "Observation",
  "id": "obs-001",
  "status": "final",
  "code": { "coding": [{ "system": "http://loinc.org", "code": "718-7", "display": "Hemoglobin [Mass/volume] in Blood" }] },
  "subject": { "reference": "Patient/patient-123" },
  "effectiveDateTime": "2026-01-05T09:30:00Z",
  "valueQuantity": { "value": 14.2, "unit": "g/dL" }
}
```

### Claim (Insurance Submission)
```json
{
  "resourceType": "Claim",
  "id": "claim-001",
  "status": "active",
  "type": { "coding": [{ "system": "http://terminology.hl7.org/CodeSystem/claim-type", "code": "professional" }] },
  "use": "claim",
  "patient": { "reference": "Patient/patient-123" },
  "created": "2026-01-06",
  "insurer": { "reference": "Organization/insurer-001" },
  "provider": { "reference": "Practitioner/practitioner-456" },
  "diagnosis": [{ "sequence": 1, "diagnosisCodeableConcept": { "coding": [{ "system": "http://hl7.org/fhir/sid/icd-10-cm", "code": "F32.1" }] } }],
  "procedure": [{ "sequence": 1, "procedureCodeableConcept": { "coding": [{ "system": "http://www.ama-assn.org/cpt", "code": "90834" }] }, "date": "2026-01-05" }],
  "insurance": [{ "sequence": 1, "focal": true, "coverage": { "reference": "Coverage/coverage-789" } }],
  "item": [{ "sequence": 1, "productOrService": { "coding": [{ "system": "http://www.ama-assn.org/cpt", "code": "90834" }] }, "diagnosisSequence": [1], "net": { "value": 150.00, "currency": "USD" } }],
  "total": { "value": 150.00, "currency": "USD" }
}
```

### ClaimResponse (Payer Adjudication)
```json
{
  "resourceType": "ClaimResponse",
  "id": "response-001",
  "status": "active",
  "outcome": "complete",
  "patient": { "reference": "Patient/patient-123" },
  "insurer": { "reference": "Organization/insurer-001" },
  "request": { "reference": "Claim/claim-001" },
  "payment": { "amount": { "value": 120.00, "currency": "USD" }, "date": "2026-01-10" },
  "error": []
}
```

### Full picture
- Patient: John Doe, male, born 2003
- Encounter: Ambulatory visit on 2026-01-05
- Condition: ICD-10 F32.1 major depressive disorder
- Procedure: CPT 90834 psychotherapy
- Medication: RxNorm acetaminophen order
- Observation: LOINC 718-7 hemoglobin result
- Coverage: Active plan
- Claim: Submitted for $150
- ClaimResponse: Approved, paid $120

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (optional, for containerized deployment)

## Installation

### Local Development

```bash
# Clone the repository
git clone https://github.com/zachkongoyu/claim-graph.git
cd claim-graph

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build
```

## Running the Application

### Using Robyn CLI (Local)

```bash
# From the project root
python -m app.main
```

The API will be available at `http://localhost:8000`

Alternatively, you can use the Robyn CLI directly:

```bash
# Install Robyn globally if not already installed
pip install robyn

# Run the application
python app/main.py
```

### Using Docker Compose

```bash
docker-compose up
```

The API will be available at `http://localhost:8000`

## API Endpoints

### 1. POST /api/v1/ingest

Ingest FHIR-like resources (Conditions, Procedures, Observations) into the database.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "conditions": [
      {
        "id": "condition-1",
        "code": {
          "coding": [{"system": "http://snomed.info/sct", "code": "73211009", "display": "Diabetes mellitus"}],
          "text": "Type 2 Diabetes"
        },
        "subject": {"reference": "Patient/patient-123"}
      }
    ],
    "procedures": [
      {
        "id": "procedure-1",
        "code": {
          "coding": [{"system": "http://snomed.info/sct", "code": "33747003", "display": "Glucose monitoring"}],
          "text": "Blood glucose test"
        },
        "subject": {"reference": "Patient/patient-123"}
      }
    ],
    "observations": [
      {
        "id": "observation-1",
        "code": {
          "coding": [{"system": "http://loinc.org", "code": "4548-4", "display": "HbA1c"}],
          "text": "Hemoglobin A1c"
        },
        "subject": {"reference": "Patient/patient-123"},
        "valueString": "7.8%"
      }
    ]
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully ingested 3 resources",
  "resource_ids": ["condition-1", "procedure-1", "observation-1"]
}
```

### 2. POST /api/v1/analyze

Run the LangGraph workflow to extract, code, and audit medical data.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "resource_ids": ["condition-1", "procedure-1", "observation-1"],
    "max_retries": 3
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Analysis completed successfully",
  "extracted_data": {
    "diagnoses": ["Type 2 Diabetes Mellitus", "Hypertension"],
    "procedures": ["Blood glucose monitoring"],
    "observations": ["HbA1c elevated at 7.8%"],
    "patient_id": "patient-123"
  },
  "coded_data": {
    "icd10_codes": ["E11.9", "I10"],
    "cpt_codes": ["82947", "99213"],
    "loinc_codes": ["4548-4"]
  },
  "audit_result": {
    "passed": true,
    "issues": [],
    "severity": "low",
    "recommendations": ["Consider follow-up in 3 months"]
  },
  "retry_count": 0
}
```

### 3. POST /api/v1/generate-claim

Generate a FHIR Claim resource from the latest analysis results.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/generate-claim" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient-123",
    "provider_id": "provider-456"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully generated claim with 2 items",
  "claim": {
    "resourceType": "Claim",
    "id": "claim-20260105152430",
    "status": "active",
    "type": {
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/claim-type",
        "code": "institutional"
      }]
    },
    "patient": {
      "reference": "Patient/patient-123"
    },
    "diagnosis": [
      {
        "sequence": 1,
        "diagnosisCodeableConcept": {
          "coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": "E11.9"}]
        }
      }
    ],
    "item": [
      {
        "sequence": 1,
        "productOrService": {
          "coding": [{"system": "http://www.ama-assn.org/go/cpt", "code": "82947"}]
        },
        "unitPrice": {"value": 100.0, "currency": "USD"}
      }
    ],
    "total": {"value": 250.0, "currency": "USD"}
  }
}
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

## Project Structure

```
claim-graph/
├── app/
│   ├── api/                    # API route handlers (legacy FastAPI structure)
│   │   ├── ingest.py          # POST /api/v1/ingest (now in main.py)
│   │   ├── analyze.py         # POST /api/v1/analyze (now in main.py)
│   │   └── generate_claim.py  # POST /api/v1/generate-claim (now in main.py)
│   ├── database/              # Database layer
│   │   ├── db.py             # SQLAlchemy setup with AnyIO
│   │   └── crud.py           # CRUD operations
│   ├── graph/                 # LangGraph workflow
│   │   ├── nodes.py          # Extractor, Coder, Auditor nodes
│   │   ├── supervisor.py     # Supervisor router
│   │   └── graph.py          # Graph definition
│   ├── models/                # Pydantic models
│   │   ├── fhir_models.py    # FHIR-like resources
│   │   └── graph_state.py    # LangGraph state
│   ├── utils/                 # Utilities
│   │   ├── llm_mock.py       # Mock LLM responses
│   │   └── synthetic_data.py # Test data generator
│   ├── config.py              # Application configuration
│   └── main.py                # Robyn application (all endpoints)
├── tests/                     # Test suite
│   ├── conftest.py           # Pytest fixtures
│   ├── test_api.py           # API endpoint tests
│   ├── test_router.py        # Router logic tests
│   └── test_schemas.py       # Schema validation tests
├── docker-compose.yml         # Docker Compose configuration
├── Dockerfile                 # Docker image definition
├── pyproject.toml            # Project metadata and dependencies
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Development

### Code Formatting

```bash
# Format code with Black
black app/ tests/

# Lint with Ruff
ruff check app/ tests/
```

### Adding Real LLM Integration

The current implementation uses mock LLM responses. To integrate a real LLM provider:

1. **Install provider SDK:**
   ```bash
   pip install openai  # or anthropic, langchain-openai, etc.
   ```

2. **Update `app/utils/llm_mock.py`** with actual LLM calls

3. **Configure API keys** in environment variables or `.env` file:
   ```bash
   OPENAI_API_KEY=your-key-here
   ```

4. **Use instructor for structured outputs:**
   ```python
   import instructor
   from openai import OpenAI
   
   client = instructor.from_openai(OpenAI())
   
   result = client.chat.completions.create(
       model="gpt-4",
       response_model=ExtractedData,
       messages=[{"role": "user", "content": prompt}]
   )
   ```

## Roadmap and TODOs

### High Priority
- [ ] **LLM Integration**: Replace mock responses with OpenAI/Anthropic
- [ ] **Instructor Integration**: Add structured output validation with retry
- [ ] **Enhanced Audit Logic**: Implement comprehensive validation rules
- [ ] **FHIR Server Integration**: Connect to HAPI-FHIR server
  - Update docker-compose.yml to include HAPI-FHIR service
  - Add FHIR client for resource retrieval
  - Implement resource synchronization

### Medium Priority
- [ ] **Payer Simulator**: Add mock payer API for claim submission testing
- [ ] **Authentication**: Add API key or OAuth2 authentication
- [ ] **Rate Limiting**: Implement API rate limits
- [ ] **Async Processing**: Add background task queue for long-running analyses
- [ ] **Metrics/Monitoring**: Add Prometheus metrics and health checks
- [ ] **Error Handling**: Enhanced error responses and logging

### Low Priority
- [ ] **Web UI**: Simple frontend for visualization
- [ ] **Export Formats**: Support for X12 837 claim format
- [ ] **Batch Processing**: Process multiple patient records
- [ ] **Reporting**: Analytics dashboard for coding patterns

## Migration Notes

This project has been migrated from FastAPI to Robyn + AnyIO:
- **Framework**: FastAPI → Robyn (ASGI framework)
- **Async Runtime**: Uvicorn → AnyIO
- **API Documentation**: Swagger/ReDoc not available (Robyn doesn't have built-in docs)
- **Dependency Injection**: FastAPI's DI system removed; using direct async context managers
- **Testing**: Custom mock client for Robyn endpoints

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Contact

For questions or support, please open an issue on GitHub.