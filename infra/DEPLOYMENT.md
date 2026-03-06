# Step 4 Infrastructure & Deployment

This project ships with production-style containers for both backend and frontend.

## Services

- `api` (FastAPI + Uvicorn) on port `8000`
- `frontend` (Nginx serving Vite build) on port `8081`

Frontend proxies `/api/*` to backend inside Docker network.

## Prerequisites

- Docker Engine
- Docker Compose v2

## Build and run

From repository root:

```bash
docker compose -f infra/docker-compose.yml up --build -d
```

## Verify

- Frontend UI: `http://localhost:8081`
- Backend docs: `http://localhost:8000/docs`
- Backend health: `http://localhost:8000/api/v1/health`

## Stop stack

```bash
docker compose -f infra/docker-compose.yml down
```

## Rebuild after changes

```bash
docker compose -f infra/docker-compose.yml up --build -d
```
