# Plesk Deployment Plan — Baseball Manager AI

Deploys to a personal VPS via the Plesk web UI, mirroring the proven
`LLM_instruct_models` → `llm.cucorn.com` flow. Two apps + one database:

```
Internet → Plesk nginx (443, Let's Encrypt)
        ├─ baseballapi.cucorn.com → reverse proxy → 127.0.0.1:8000
        │                                       └─ gunicorn + UvicornWorker (systemd) → FastAPI
        └─ baseballai.cucorn.com   → Node.js extension (Phusion Passenger) → static React SPA (dist/)

Database: Plesk local PostgreSQL (localhost:5432), name `baseball_db`
```

## Prerequisites (verify before starting)
- VPS with Plesk installed; domain + subdomain pointed at the VPS
- Plesk **Node.js** extension enabled (for the frontend)
- Plesk **PostgreSQL** extension enabled (for the database)
- SSH access to the VPS (for the systemd backend service)
- GitHub repo `seanrugg/baseball_manager_ai` (already deployed code is pushed)

---

## 0. Code change needed for the backend entry point (do this first)

FastAPI is ASGI, but the app exposes its `app` object inside `ModelServer`, not
at module level, so gunicorn has nothing to import. Add a tiny entry point so
gunicorn can load it:

**Create `baseball_manager_ai/asgi.py`:**
```python
"""ASGI entry point for gunicorn / Plesk deployment."""
from baseball_manager_ai.database import init_db
from baseball_manager_ai.api.model_server import ModelServer

# Create tables on startup so the service is self-initialising.
init_db()

app = ModelServer().app
```

Also tighten CORS for production (currently `allow_origins=["*"]` in
`model_server.py`) — replace with the concrete API domain, e.g.
`allow_origins=["https://baseballapi.cucorn.com"]`.

The systemd service installs a Python venv, so it needs the trimmed
`requirements.txt` (already pruned — no torch/lightgbm/streamlit).

---

## 1. Database — Plesk local PostgreSQL
Plesk UI → **Databases → Add Database**:
- Name: `baseball_db`
- Server: **Local**
- Create a new user: `baseball_user` + generated password
- Grant all privileges

Record the exact username (Plesk may prefix it, e.g. `u12345_baseball_db`).

---

## 2. Backend — systemd + gunicorn (via SSH)
The Plesk **Python** extension is WSGI/uWSGI-oriented and does **not** run
FastAPI's ASGI app cleanly. Use a systemd service with gunicorn's Uvicorn
worker — this is the "Alternative: Use Gunicorn with Systemd" path already in
`VPS_DEPLOYMENT.md`, and it's the reliable option.

SSH into the VPS:
```bash
cd /home/<user>/baseball_manager_ai
git pull origin main
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

**`/etc/systemd/system/baseball-api.service`:**
```ini
[Unit]
Description=Baseball Manager AI API
After=network.target

[Service]
User=<user>
WorkingDirectory=/home/<user>/baseball_manager_ai
Environment="PATH=/home/<user>/baseball_manager_ai/venv/bin"
Environment="DATABASE_URL=postgresql://<user>:<pass>@localhost:5432/baseball_db"
Environment="ENVIRONMENT=production"
Environment="LOG_LEVEL=INFO"
ExecStart=/home/<user>/baseball_manager_ai/venv/bin/gunicorn \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    asgi:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now baseball-api
curl http://127.0.0.1:8000/health   # expect database: connected
```

---

## 3. Backend reverse proxy — Plesk web hosting (web UI)
Plesk UI → **baseballapi.cucorn.com** → **Web Hosting / Reverse Proxy**:
- Proxy path `/` → `http://127.0.0.1:8000`

This makes the API reachable at `https://baseballapi.cucorn.com/health`, `/predict`, etc.

---

## 4. Frontend — Plesk Node.js extension (web UI, mirrors LLM)
The Vite build is static, but to keep the exact `clone → npm install → build`
flow from the LLM project, use the **Node.js extension**. Add a tiny static
server so the extension has a startup file that listens on `$PORT`:

**Create `frontend/server.js`:**
```js
import express from 'express'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const app = express()
app.use(express.static(path.join(__dirname, 'dist')))
const port = process.env.PORT || 3000
app.listen(port, () => console.log(`frontend on :${port}`))
```
(`express` will be installed by the extension's `npm install`.)

Plesk UI → **<domain>** → **Node.js**:
1. **Clone from Git** → repo `seanrugg/baseball_manager_ai`, path `/ball-app`
2. **Node version:** 20.x · **Mode:** Production
3. **Application Root:** `/ball-app/frontend`
4. **Document Root:** `/ball-app/frontend/dist`
5. **Startup File:** `server.js`
6. **Custom env vars:** `VITE_API_URL=https://baseballapi.cucorn.com`
7. Click **NPM install** → **Run script** (builds `dist/`) → **Enable/Restart**

If Plesk won't save the Document Root because `dist/` doesn't exist yet, create
an empty `frontend/dist` folder via File Manager first — the build populates it.

---

## 5. Verify
- `https://baseballapi.cucorn.com/health` → `{"status":"healthy", "database":"connected"}`
- `https://baseballapi.cucorn.com/predict` (POST) → prediction JSON
- `https://<domain>/` → React app loads, backend status = "connected"
- Test `/predict` + `/strategy` flows in the UI; GameSimulator renders
- Check Plesk Node.js logs for the "frontend on :<port>" startup line

---

## Open decisions
1. **Frontend serving: Node.js extension** (chosen) — mirrors the LLM flow, builds on the server.
2. **CORS: tighten to the concrete API domain** (chosen) — set in `model_server.py` at deploy time. Left as a placeholder below.

## Pre-deploy code changes (already applied)
- ✅ `baseball_manager_ai/asgi.py` added — gunicorn entry point exposing `app`
- ✅ `model_server.py` CORS `allow_origins` — tightened to `["https://baseballapi.cucorn.com"]`
