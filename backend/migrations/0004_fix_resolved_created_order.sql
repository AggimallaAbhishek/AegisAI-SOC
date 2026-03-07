UPDATE soc_cases
SET created_at = resolved_at
WHERE resolved_at IS NOT NULL
  AND created_at > resolved_at;

UPDATE soc_cases
SET triaged_at = created_at
WHERE triaged_at IS NULL
   OR triaged_at < created_at;
