CREATE TABLE IF NOT EXISTS soc_cases (
    case_id TEXT PRIMARY KEY,
    alert_id TEXT NOT NULL,
    source TEXT NOT NULL,
    host TEXT NOT NULL,
    severity TEXT NOT NULL,
    category TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    triage_reason TEXT NOT NULL,
    confidence NUMERIC(5,4) NOT NULL DEFAULT 0.0,
    summary TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS soc_case_events (
    event_id BIGSERIAL PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES soc_cases(case_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_soc_cases_severity ON soc_cases (severity);
CREATE INDEX IF NOT EXISTS idx_soc_cases_status ON soc_cases (status);
CREATE INDEX IF NOT EXISTS idx_soc_case_events_case_id ON soc_case_events (case_id);
