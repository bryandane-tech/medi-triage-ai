import pytest
from app.schemas import TriageRequest, TriageResponse, AuditVerificationResponse
from app.rag_engine import ClinicalRAGEngine


def test_triage_request_schema():
    req = TriageRequest(phone="+15559876543", notes="Acute onset chest pain")
    assert req.phone == "+15559876543"
    assert req.notes == "Acute onset chest pain"


def test_triage_response_schema():
    resp = TriageResponse(
        triage_id="a9a2010f-1d59-4cbe-8c68-316e99df1548",
        status="QUEUED_AND_ENCRYPTED"
    )
    assert resp.triage_id == "a9a2010f-1d59-4cbe-8c68-316e99df1548"
    assert resp.status == "QUEUED_AND_ENCRYPTED"


def test_audit_verification_response_schema():
    res = AuditVerificationResponse(
        valid=True,
        records_verified=10,
        tampered_at_id=None,
        reason=None
    )
    assert res.valid is True
    assert res.records_verified == 10
    assert res.tampered_at_id is None
    assert res.reason is None


def test_clinical_rag_engine_instantiation():
    engine = ClinicalRAGEngine()
    assert engine is not None
