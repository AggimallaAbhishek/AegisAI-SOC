# AegisAI SOC

AegisAI SOC is a multi-agent incident triage and response orchestration platform with a FastAPI backend and React frontend.

## Current status

Step 1 (project initialization), Step 2 (backend development), Step 3 (frontend setup), Step 4 (infrastructure and deployment), Step 5 (testing and validation), Step 6 (integration and automation readiness), and Step 7 (Phase 3 foundation) are implemented.

## Backend features implemented

- FastAPI API with health and incident analysis endpoints
- SOC orchestrator pipeline for triage, investigation, response, and reporting
- Knowledge base lookup service
- Playbook loader for response automation suggestions
- Sample playbooks (`block_ip`, `isolate_host`)
- Phase 2 readiness service and integration scaffolding
- PostgreSQL migration baseline for case persistence
- Phase 3 RBAC policy service
- Phase 3 threat-intel enrichment hook
- Phase 3 KPI/SLA dashboard services and APIs
- Live Postgres-backed case persistence and dashboard aggregation with sample fallback
- Tests for API and agent orchestration

## Project structure

- `backend/` : API, orchestration, agents, services, migrations
- `frontend/` : Vite + React SOC console UI
- `infra/` : Docker Compose and deployment docs
- `playbooks/` : YAML response playbooks
- `scripts/` : sample data and helper scripts
- `tests/` : API and orchestration tests

## Run locally

1. Create and activate a Python virtual environment.
2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Start the API:
   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```
4. Open API docs:
   - http://localhost:8000/docs

## Run frontend

1. Open a new terminal and go to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install frontend dependencies:
   ```bash
   npm install
   ```
3. Start the UI:
   ```bash
   npm run dev
   ```
4. Open:
   - http://localhost:5173

The frontend uses `VITE_API_BASE_URL` (see `frontend/.env.example`). Default target is `http://localhost:8000`.

## Run tests

```bash
pytest -q
```

## Step 5/6/7 validation

Run full stack validation after deployment:

```bash
./scripts/validate_stack.sh
```

Optional custom endpoints:

```bash
API_URL=http://localhost:8000 FRONTEND_URL=http://localhost:8081 ./scripts/validate_stack.sh
```

## Case-store migration

After setting `POSTGRES_DSN` in `.env`, apply migrations:

```bash
./scripts/migrate_case_store.sh
```

## Useful API endpoints

- `GET /api/v1/health`
- `POST /api/v1/alerts/analyze`
- `POST /api/v1/alerts/analyze/raw`
- `GET /api/v1/knowledge/search?query=mimikatz`
- `GET /api/v1/playbooks`
- `GET /api/v1/next-phases/status`
- `GET /api/v1/next-phases/quickstart`
- `GET /api/v1/next-phases/integrations`
- `GET /api/v1/phase3/rbac/policy`
- `GET /api/v1/phase3/threat-intel/status`
- `GET /api/v1/phase3/case-store/status`
- `GET /api/v1/phase3/kpi/overview`
- `GET /api/v1/phase3/kpi/trends`
- `GET /api/v1/phase3/sla/overview`

## Example analysis request

```json
{
  "source": "SIEM",
  "timestamp": "2026-03-07T12:30:00Z",
  "host": "FIN-WS-442",
  "user": "finance.admin",
  "ip_address": "203.0.113.56",
  "process_name": "mimikatz.exe",
  "command_line": "mimikatz.exe sekurlsa::logonpasswords",
  "description": "Potential credential dumping behavior detected on endpoint"
}
```

## Frontend features implemented

- Alert intake form with sample-fill support
- Live backend health indicator
- Incident analysis output panel (triage, investigation, response, report)
- Knowledge base search UI
- Playbook catalog UI

## Step 4 deployment

Use Docker Compose to run full stack containers (frontend + backend):

```bash
docker compose -f infra/docker-compose.yml up --build -d
```

Deployed endpoints:

- Frontend: `http://localhost:8081`
- Backend docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/v1/health`

Stop stack:

```bash
docker compose -f infra/docker-compose.yml down
```

Detailed guide: `infra/DEPLOYMENT.md`

## CI

GitHub Actions workflow added at `.github/workflows/ci.yml`:

- Runs backend test suite (`pytest`)
- Builds frontend (`npm run build`)

## Phase roadmap docs

- `docs/STEP6_NEXT_PHASES.md`
- `docs/STEP7_PHASE3.md`
