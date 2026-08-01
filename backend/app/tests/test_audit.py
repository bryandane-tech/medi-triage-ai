import pytest
import asyncpg
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_audit_chain_detects_tampering():
    """Verifies that unauthorized direct mutations to audit_access_logs are caught by hash validation."""
    db_url = str(getattr(settings, "DATABASE_URL", getattr(settings, "POSTGRES_URL", "")))
    dsn = db_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(dsn)

    # 1. Retrieve the latest audit log entry directly from the DB
    row = await conn.fetchrow(
        "SELECT id, actor_id FROM audit_access_logs ORDER BY created_at DESC LIMIT 1;"
    )
    assert row is not None, "No audit log entries found in database to test."

    record_id = row["id"]
    original_actor = row["actor_id"]

    try:
        # 2. Mutate actor_id without updating cryptographic entry_hash
        await conn.execute(
            "UPDATE audit_access_logs SET actor_id = $1 WHERE id = $2;",
            "unauthorized_actor",
            record_id,
        )

        # 3. Trigger integrity check endpoint using TestClient context
        with TestClient(app) as client:
            verify_res = client.get("/api/v1/audit/verify")
            assert verify_res.status_code == 200

            res_data = verify_res.json()
            assert res_data["valid"] is False
            assert res_data["tampered_at_id"] == str(record_id)
            assert res_data["reason"] == "ENTRY_HASH_CORRUPTED"

    finally:
        # 4. Clean up and restore original row state
        await conn.execute(
            "UPDATE audit_access_logs SET actor_id = $1 WHERE id = $2;",
            original_actor,
            record_id,
        )
        await conn.close()
