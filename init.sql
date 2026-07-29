-- Enable pgcrypto extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- -----------------------------------------------------------------------------
-- 1. Encrypted Triage Records Table
-- Stores patient intakes encrypted via multi-version AES-256-GCM envelope keys.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS triage_records (
    triage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    encrypted_phone TEXT NOT NULL,
    encrypted_notes TEXT NOT NULL,
    urgency_score INT NOT NULL CHECK (urgency_score BETWEEN 0 AND 5),
    key_version VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'ENQUEUED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_triage_records_created_at ON triage_records(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_triage_records_status ON triage_records(status);

-- -----------------------------------------------------------------------------
-- 2. Transactional Outbox Table
-- Guarantees atomicity between DB writes and Redis stream processing.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS outbox_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type VARCHAR(64) NOT NULL,
    aggregate_id UUID NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_outbox_pending ON outbox_events(status, created_at)
WHERE status = 'PENDING';

-- -----------------------------------------------------------------------------
-- 3. Tamper-Evident HIPAA Audit Log Table
-- Hash-chained access logs where current_hash = SHA256(previous_hash + payload).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id BIGSERIAL PRIMARY KEY,
    actor_id VARCHAR(128) NOT NULL,
    action VARCHAR(64) NOT NULL,
    resource_id UUID NOT NULL,
    previous_hash VARCHAR(64) NOT NULL,
    current_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_id);

-- Insert genesis hash entry for audit log verification bootstrapping
INSERT INTO audit_logs (actor_id, action, resource_id, previous_hash, current_hash)
VALUES (
    'SYSTEM_INIT',
    'GENESIS',
    '00000000-0000-0000-0000-000000000000',
    '0000000000000000000000000000000000000000000000000000000000000000',
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
)
ON CONFLICT DO NOTHING;

-- Automatic updated_at trigger function
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_triage_records_timestamp
BEFORE UPDATE ON triage_records
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();
