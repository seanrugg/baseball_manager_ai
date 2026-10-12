# Local Dev + Pre-Deploy Plan

Goal: run the backend locally in a venv against PostgreSQL, wire real data
(simulator) through the API, build the React frontend, then deploy.

## Phase 1 — Fix four pre-deploy issues

1. Rename `utils/__inti__.py` -> `utils/__init__.py`  [DONE]
2. Consolidate on PostgreSQL: `config/database.yaml` already says postgres;
   drop the SQLite hardcode in `data_ingestion.py` (add env override), keep
   docker-compose as the Postgres source of truth.
3. Trim deps: drop torch/transformers/lightgbm/pybaseball/streamlit/matplotlib/
   seaborn/joblib from requirements.txt + pyproject.toml (not imported).
4. Scrub default creds: remove `baseball_user:baseball_password` defaults from
   `.env.example` and `database/connection.py`; fall back to an empty
   DATABASE_URL that forces the user to set one.

## Phase 2 — Run locally

- Create venv, install trimmed deps
- `cp .env.example .env`, set DATABASE_URL to local postgres
- init_db.py, then `python -m baseball_manager_ai.api.model_server`
- verify /health, /predict (wire simulator into one route)

## Phase 3 — React frontend (Vite)

- scaffold frontend/
- talk to FastAPI on :8000
- build: /predict, simulator, lineup

## Phase 4 — Deploy

- Frontend: Plesk Node.js extension (clone from Git, npm install, build, serve static)
- Backend: systemd service (gunicorn + UvicornWorker) + reverse proxy
