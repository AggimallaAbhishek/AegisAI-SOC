UPDATE soc_cases
SET severity = lower(replace(severity, 'Severity.', ''))
WHERE severity LIKE 'Severity.%';
