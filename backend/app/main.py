import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header, Response
from pydantic import BaseModel, Field
import asyncpg
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.core.config import settings
from app.security.envelope import MultiKeyEnvelopeEncryption
from app.services.triage_service import TriageEngineService
from app.metrics.prometheus import TRIAGE_PROCESSED_TOTAL
from fastapi import FastAPI, Response



class TriageRequest(BaseModel):
    phone: str = Field(..., example="+201000000000")
    notes: str = Field(..., example="Patient reports severe chest pain and shortness of breath.")

app_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Key Ring configured with primary v2 key and legacy v1 key
    key_ring = {
        "v1": settings.MASTER_KEY_B64,
        "v2": "+jNucoAFvAewoqnJHZJr3WKBPY9Rr4E2/+dzdyUxLSY=" # Example rotated v2 key
    }
    cipher = MultiKeyEnvelopeEncryption(key_ring=key_ring, active_version="v2")

    app_state["pool"] = await asyncpg.create_pool(
        dsn=settings.DATABASE_URL,
        min_size=settings.DB_MIN_POOL,
        max_size=settings.DB_MAX_POOL
    )
    app_state["service"] = TriageEngineService(
        lib_path=settings.C_LIB_PATH,
        cipher=cipher,
        db_pool=app_state["pool"]
    )
    yield
    await app_state["pool"].close()

app = FastAPI(title="MediTriage Enterprise", lifespan=lifespan)

@app.post("/api/v1/triage")
async def handle_triage(req: TriageRequest):
    service: TriageEngineService = app_state["service"]
    triage_id, urgency = await service.process_incoming_triage(req.phone, req.notes)
    TRIAGE_PROCESSED_TOTAL.labels(urgency_score=str(urgency)).inc()
    return {"triage_id": triage_id, "status": "QUEUED_AND_ENCRYPTED"}

@app.get("/api/v1/triage/{record_id}")
async def get_triage_record(record_id: str, x_actor_id: str = Header(..., alias="X-Actor-ID")):
    """Retrieves and decrypts a PHI record, writing to the audit log."""
    service: TriageEngineService = app_state["service"]
    record = await service.read_patient_record(record_id, actor_id=x_actor_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record

@app.get("/api/v1/audit/verify")
async def verify_audit_chain():
    """Validates the SHA-256 hash chain across all access logs."""
    service: TriageEngineService = app_state["service"]
    return await service.audit.verify_audit_chain_integrity()

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/healthz")
async def healthz():
    return {"status": "healthy"}

# Silence favicon 404 requests
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "MediTriage AI API",
        "docs": "/docs"
    }
