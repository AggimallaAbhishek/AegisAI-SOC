# Step 7 - Phase 3 Foundation (RBAC, Threat Intel, KPI/SLA)

This step adds the first implementation slice for Phase 3 goals: access governance, intelligence enrichment, and performance observability.

## Scope Implemented

- RBAC policy service with role-header-based enforcement controls.
- Threat-intel enrichment hook in the analysis pipeline.
- KPI and SLA dashboard APIs backed by Postgres case records when available, with sample fallback.
- Case-store persistence from analysis pipeline for audit and dashboard aggregation.

## New Services

- `backend/services/rbac.py`
- `backend/services/threat_intel.py`
- `backend/services/metrics.py`
- `backend/services/case_store.py`

## New Sample Data

- `scripts/sample_data/threat_intel_iocs.json`
- `scripts/sample_data/phase3_metrics.json`

## New API Endpoints

- `GET /api/v1/phase3/rbac/policy`
- `GET /api/v1/phase3/threat-intel/status`
- `GET /api/v1/phase3/case-store/status`
- `GET /api/v1/phase3/kpi/overview`
- `GET /api/v1/phase3/kpi/trends`
- `GET /api/v1/phase3/sla/overview`

## RBAC Usage

Header-based role routing:

- Header: `x-soc-role` (configurable via `SOC_ROLE_HEADER`)
- Roles: `admin`, `manager`, `analyst`, `viewer`
- Enforcement flag: `PHASE3_RBAC_ENFORCED`

When enforcement is `false`, the default role (`SOC_DEFAULT_ROLE`) is used if the header is missing.

## Threat Intel Enrichment

Alert analysis responses now include `investigation.threat_intel` with:

- Match counts
- IOC details
- Threat score
- Mapped techniques
- Escalation recommendation

## Case Store Persistence

Analysis responses now include `case_id`.

When `POSTGRES_DSN` is configured and reachable, each analysis is written to:

- `soc_cases` (case summary row)
- `soc_case_events` (analysis event payload)

Migrations `backend/migrations/0002_phase3_case_metrics.sql`, `backend/migrations/0003_fix_severity_enum_strings.sql`, and `backend/migrations/0004_fix_resolved_created_order.sql` align live case data for KPI/SLA reporting.

## KPI/SLA Endpoints

KPI overview exposes incident volume, severity split, MTTR, automation rate, and false-positive rate.
SLA overview exposes triage compliance percentage against target minutes (`PHASE3_SLA_TARGET_MINUTES`).

Each KPI/SLA payload now includes `data_source` (`postgres` or `sample_file`).

## Validation

Use stack validation script:

```bash
./scripts/validate_stack.sh
```
