# AegisAI SOC

AegisAI SOC is a multi-agent incident triage and response orchestration platform with a FastAPI backend and React frontend.

## Current status

Step 1 (project initialization), Step 2 (backend development), and Step 3 (frontend setup) are implemented.

## Backend features implemented

- FastAPI API with health and incident analysis endpoints
- SOC orchestrator pipeline for triage, investigation, response, and reporting
- Knowledge base lookup service
- Playbook loader for response automation suggestions
- Sample playbooks (`block_ip`, `isolate_host`)
- Sample alert and seed script
- Tests for API and agent orchestration

## Project structure

- `backend/` : API, orchestration, agents, and services
- `frontend/` : Vite + React SOC console UI
- `playbooks/` : YAML response playbooks
- `scripts/` : sample data and helper scripts
- `tests/` : API and orchestration tests
- `infra/` : Docker compose setup

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

## Useful API endpoints

- `GET /api/v1/health`
- `POST /api/v1/alerts/analyze`
- `POST /api/v1/alerts/analyze/raw`
- `GET /api/v1/knowledge/search?query=mimikatz`
- `GET /api/v1/playbooks`

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
