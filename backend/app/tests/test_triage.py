import pytest
import asyncpg
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_triage_creation_and_phi_encryption():
    db_url = str(getattr(settings, "DATABASE_URL", getattr(settings, "POSTGRES_URL", "")))
    dsn = db_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(dsn)

    raw_phone = "+15559876543"
    raw_notes = "Patient presents with acute onset chest pain and dyspnea."

    with TestClient(app) as client:
        res = client.post(
            "/api/v1/triage",
            json={"phone": raw_phone, "notes": raw_notes}
        )
        assert res.status_code in (200, 201)
        triage_id = res.json()["triage_id"]

        row = await conn.fetchrow(
            "SELECT * FROM triage_records WHERE id = $1;",
            triage_id
        )
        assert row is not None, "Triage record not found in database"

        db_row_dump = str(dict(row))
        assert raw_notes not in db_row_dump, "Cleartext PHI notes leaked into raw database row!"

        get_res = client.get(
            f"/api/v1/triage/{triage_id}",
            headers={"X-Actor-ID": "dr_triage_test"}
        )
        assert get_res.status_code == 200
        payload = get_res.json()
        assert payload["phone"] == raw_phone
        assert payload["notes"] == raw_notes

    await conn.close()


@pytest.mark.asyncio
async def test_triage_not_found():
    with TestClient(app) as client:
        res = client.get(
            "/api/v1/triage/00000000-0000-0000-0000-000000000000",
            headers={"X-Actor-ID": "dr_triage_test"}
        )
        assert res.status_code == 404
