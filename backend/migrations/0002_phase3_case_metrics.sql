ALTER TABLE soc_cases
    ADD COLUMN IF NOT EXISTS triaged_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS automated_containment BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS false_positive BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_soc_cases_created_at ON soc_cases (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_soc_cases_triaged_at ON soc_cases (triaged_at DESC);
