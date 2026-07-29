from prometheus_client import Counter, Histogram, Gauge

# Custom metrics for high-precision telemetry
C_ENGINE_LATENCY = Histogram(
    "meditriage_c_engine_execution_seconds",
    "Time spent inside C-engine Aho-Corasick triage parser",
    buckets=[0.00005, 0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05]
)

TRIAGE_PROCESSED_TOTAL = Counter(
    "meditriage_processed_total",
    "Total patient triage requests processed",
    ["urgency_score"]
)

OUTBOX_UNPROCESSED_DEPTH = Gauge(
    "meditriage_outbox_unprocessed_depth",
    "Current count of unprocessed events pending in PostgreSQL transactional outbox"
)

OUTBOX_PUBLISHED_TOTAL = Counter(
    "meditriage_outbox_published_total",
    "Total outbox events published to Redis Streams"
)
