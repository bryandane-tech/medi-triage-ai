import asyncio
import json
import logging
import asyncpg
import redis.asyncio as redis
from app.metrics.prometheus import OUTBOX_UNPROCESSED_DEPTH, OUTBOX_PUBLISHED_TOTAL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OutboxWorker")

async def run_outbox_publisher(db_dsn: str, redis_url: str):
    db_pool = await asyncpg.create_pool(dsn=db_dsn)
    r_client = redis.from_url(redis_url)

    logger.info("Outbox Worker initialized with telemetry instrumentation.")

    while True:
        try:
            async with db_pool.acquire() as conn:
                # Update outbox queue depth gauge metric
                depth = await conn.fetchval("SELECT COUNT(*) FROM transactional_outbox WHERE processed = FALSE;")
                OUTBOX_UNPROCESSED_DEPTH.set(depth)

                async with conn.transaction():
                    rows = await conn.fetch(
                        """
                        SELECT id, aggregate_id, event_type, payload
                        FROM transactional_outbox
                        WHERE processed = FALSE
                        ORDER BY created_at ASC
                        LIMIT 20
                        FOR UPDATE SKIP LOCKED;
                        """
                    )

                    for row in rows:
                        event_id = str(row['id'])
                        payload = json.loads(row['payload'])

                        await r_client.xadd(
                            "stream:triage_events",
                            {
                                "event_id": event_id,
                                "event_type": row['event_type'],
                                "data": json.dumps(payload)
                            }
                        )

                        await conn.execute("UPDATE transactional_outbox SET processed = TRUE WHERE id = $1;", row['id'])
                        OUTBOX_PUBLISHED_TOTAL.inc()

        except Exception as e:
            logger.error(f"Outbox polling error: {str(e)}")

        await asyncio.sleep(0.2)
