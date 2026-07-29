from pydantic import BaseModel, Field
from typing import List, Optional

class TriageRequest(BaseModel):
    phone: str = Field(..., example="+201000000000")
    notes: str = Field(..., example="Patient experiencing acute chest pain and shortness of breath.")

class TriageResponse(BaseModel):
    triage_id: str
    status: str

class DecryptedTriageRecord(BaseModel):
    triage_id: str
    phone: str
    notes: str
    urgency_score: int
    decrypted_with_key: str

class AuditVerificationResponse(BaseModel):
    valid: bool
    records_verified: Optional[int] = None
    tampered_at_id: Optional[str] = None
    reason: Optional[str] = None
