import hashlib
import asyncpg

class AuditLoggerService:
    """Immutable, hash-chained HIPAA access logging service for PHI operations."""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    async def log_phi_access(
        self, actor_id: str, action: str, resource_id: str, key_version: str
    ) -> str:
        """Appends an immutable audit entry chained to the previous entry's SHA-256 hash."""
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Fetch entry_hash of the most recent log
                last_hash = await conn.fetchval(
                    "SELECT entry_hash FROM audit_access_logs ORDER BY created_at DESC LIMIT 1;"
                )
                if not last_hash:
                    # Genesis seed hash for initial entry
                    last_hash = "0" * 64

                # Cryptographic chain: SHA256(prev_hash | actor | action | resource | key_version)
                hash_input = f"{last_hash}|{actor_id}|{action}|{resource_id}|{key_version}"
                entry_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

                row = await conn.fetchrow(
                    """
                    INSERT INTO audit_access_logs
                        (actor_id, action, resource_id, key_version_used, previous_hash, entry_hash)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id;
                    """,
                    actor_id, action, resource_id, key_version, last_hash, entry_hash
                )
                return str(row['id'])

    async def verify_audit_chain_integrity(self) -> dict:
        """Audits the entire log chain to detect any manual database tampering."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, actor_id, action, resource_id, key_version_used, previous_hash, entry_hash "
                "FROM audit_access_logs ORDER BY created_at ASC;"
            )

            expected_prev_hash = "0" * 64
            verified_count = 0

            for row in rows:
                if row["previous_hash"] != expected_prev_hash:
                    return {"valid": False, "tampered_at_id": str(row["id"]), "reason": "PREVIOUS_HASH_MISMATCH"}

                hash_input = f"{expected_prev_hash}|{row['actor_id']}|{row['action']}|{row['resource_id']}|{row['key_version_used']}"
                computed_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

                if computed_hash != row["entry_hash"]:
                    return {"valid": False, "tampered_at_id": str(row["id"]), "reason": "ENTRY_HASH_CORRUPTED"}

                expected_prev_hash = row["entry_hash"]
                verified_count += 1

            return {"valid": True, "records_verified": verified_count}
