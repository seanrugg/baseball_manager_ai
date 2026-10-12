"""ASGI entry point for gunicorn / Plesk deployment.

FastAPI is ASGI, but ``model_server.py`` exposes the ``app`` object inside
``ModelServer`` rather than at module level, so gunicorn has nothing to
import. This module flattens that so a systemd service can launch the API:

    gunicorn --worker-class uvicorn.workers.UvicornWorker asgi:app
"""
from baseball_manager_ai.database import init_db
from baseball_manager_ai.api.model_server import ModelServer

# Create tables on startup so the service is self-initialising.
init_db()

app = ModelServer().app
