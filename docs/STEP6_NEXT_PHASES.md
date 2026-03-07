# Step 6 - Next Phases (Phase 2 and Phase 3)

This document defines the post-MVP execution plan now that Steps 1-5 are complete.

## Phase 2: Integration and Automation

Objective: Connect the SOC engine to real enterprise systems and automate case workflows.

### Scope

- SIEM integration adapter (Splunk-compatible)
- Ticketing integration adapter (Jira-compatible)
- Notification integration adapter (Slack webhook)
- Persistent case store migration baseline (PostgreSQL)

### Implemented in this step

- Connector scaffolding under `backend/services/connectors/`:
  - `splunk.py`
  - `jira.py`
  - `slack.py`
  - `postgres.py`
- Aggregation helpers:
  - `backend/services/connectors/factory.py`
- Case-store migration baseline:
  - `backend/migrations/0001_case_tables.sql`
  - `scripts/migrate_case_store.sh`

### Backend readiness APIs

- `GET /api/v1/next-phases/status`
- `GET /api/v1/next-phases/quickstart`
- `GET /api/v1/next-phases/integrations`

### Required environment variables

- `SPLUNK_BASE_URL`
- `SPLUNK_API_TOKEN`
- `JIRA_BASE_URL`
- `JIRA_PROJECT_KEY`
- `JIRA_USER_EMAIL` (for live Jira ticket creation)
- `JIRA_API_TOKEN` (for live Jira ticket creation)
- `JIRA_ISSUE_TYPE` (optional, default `Task`)
- `SLACK_WEBHOOK_URL`
- `POSTGRES_DSN`
- `PHASE2_AUTOMATION_ENABLED` (default `true`)

### Phase 2 enablement runbook

1. Fill integration values in `.env`.
2. Apply DB schema baseline:
   ```bash
   ./scripts/migrate_case_store.sh
   ```
3. Verify readiness output:
   ```bash
   curl -s http://localhost:8000/api/v1/next-phases/status
   curl -s http://localhost:8000/api/v1/next-phases/integrations
   ```
4. Run a sample incident analysis and confirm `automation` payload includes Jira/Slack outcomes.

## Phase 3: Intelligence and Scale

Objective: Add SOC intelligence loops and enterprise governance.

### Scope

- Threat-intelligence enrichment pipeline
- Role-based access control for analyst workflows
- KPI and SLA reporting endpoints
- Analyst feedback loop for tuning detections and response heuristics

## Validation

Use unified stack validation after each change:

```bash
./scripts/validate_stack.sh
```
