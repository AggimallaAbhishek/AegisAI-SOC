# Step 6 - Next Phases (Phase 2 and Phase 3)

This document defines the post-MVP execution plan now that Steps 1-5 are complete.

## Phase 2: Integration and Automation

Objective: Connect the SOC engine to real enterprise systems and automate case workflows.

### Scope

- SIEM integration adapter (Splunk-compatible)
- Ticketing integration adapter (Jira-compatible)
- Notification integration adapter (Slack webhook)
- Persistent case store preparation (PostgreSQL DSN)

### Backend readiness APIs implemented

- `GET /api/v1/next-phases/status`
- `GET /api/v1/next-phases/quickstart`

### Required environment variables

- `SPLUNK_BASE_URL`
- `SPLUNK_API_TOKEN`
- `JIRA_BASE_URL`
- `JIRA_PROJECT_KEY`
- `SLACK_WEBHOOK_URL`
- `POSTGRES_DSN`

## Phase 3: Intelligence and Scale

Objective: Add SOC intelligence loops and enterprise governance.

### Scope

- Threat-intelligence enrichment pipeline
- Role-based access control for analyst workflows
- KPI and SLA reporting endpoints
- Analyst feedback loop for tuning detections and response heuristics

## Execution checklist

1. Configure Phase 2 integration env vars in `.env`.
2. Implement adapters under `backend/services/connectors/`.
3. Add DB migrations and persistence tables.
4. Add role model and authorization middleware.
5. Add trend analytics endpoints and dashboard wiring.

## Validation

Use unified stack validation after each change:

```bash
./scripts/validate_stack.sh
```
