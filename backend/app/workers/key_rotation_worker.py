import asyncio
import logging
import asyncpg
from app.security.envelope import MultiKeyEnvelopeEncryption

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KeyRotationWorker")

async def run_key_rotation(db_dsn: str, cipher: MultiKeyEnvelopeEncryption, batch_size: int = 20):
    db_pool = await asyncpg.create_pool(dsn=db_dsn)
    target_version = cipher.active_version

    logger.info(f"Key Rotation Worker online. Target key version: {target_version}")

    while True:
        try:
            async with db_pool.acquire() as conn:
                async with conn.transaction():
                    # Batch fetch records encrypted with older keys
                    rows = await conn.fetch(
                        """
                        SELECT id, encrypted_phone_number, encrypted_clinical_notes, key_version
                        FROM patient_triage
                        WHERE key_version != $1
                        LIMIT $2
                        FOR UPDATE SKIP LOCKED;
                        """,
                        target_version, batch_size
                    )

                    if not rows:
                        await asyncio.sleep(5)
                        continue

                    for row in rows:
                        record_id = str(row['id'])
                        old_version = row['key_version']

                        # Decrypt with old key, re-encrypt with target key
                        plain_phone, _ = cipher.decrypt(row['encrypted_phone_number'])
                        plain_notes, _ = cipher.decrypt(row['encrypted_clinical_notes'])

                        new_enc_phone, new_ver = cipher.encrypt(plain_phone)
                        new_enc_notes, _ = cipher.encrypt(plain_notes)

                        await conn.execute(
                            """
                            UPDATE patient_triage
                            SET encrypted_phone_number = $1,
                                encrypted_clinical_notes = $2,
                                key_version = $3
                            WHERE id = $4;
                            """,
                            new_enc_phone, new_enc_notes, new_ver, row['id']
                        )
                        logger.info(f"Rotated record {record_id} key: {old_version} -> {new_ver}")

        except Exception as e:
            logger.error(f"Error during key rotation batch: {str(e)}")
            await asyncio.sleep(5)
