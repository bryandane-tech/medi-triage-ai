CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Patient Triage Table with explicit Key Version tracking
CREATE TABLE IF NOT EXISTS patient_triage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    encrypted_phone_number TEXT NOT NULL,
    encrypted_clinical_notes TEXT NOT NULL,
    key_version VARCHAR(16) NOT NULL DEFAULT 'v1',
    ac_matched_count INT NOT NULL,
    urgency_score INT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Transactional Outbox
CREATE TABLE IF NOT EXISTS transactional_outbox (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    aggregate_type VARCHAR(64) NOT NULL,
    aggregate_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_outbox_unprocessed ON transactional_outbox(created_at) WHERE processed = FALSE;

-- Immutable Tamper-Evident HIPAA Audit Log Table
CREATE TABLE IF NOT EXISTS audit_access_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_id VARCHAR(128) NOT NULL,
    action VARCHAR(64) NOT NULL,
    resource_id VARCHAR(128) NOT NULL,
    key_version_used VARCHAR(16) NOT NULL,
    previous_hash VARCHAR(64) NOT NULL,
    entry_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_access_logs(created_at);
