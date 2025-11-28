# Baseball Manager AI - Self-Hosted Setup Summary

Your application is now fully configured for self-hosted deployment with PostgreSQL.

## What's New

✓ PostgreSQL database support (not Supabase)
✓ SQLAlchemy ORM with database models
✓ Docker Compose with PostgreSQL container
✓ Database initialization script (`init_db.py`)
✓ Updated API server with database integration
✓ Complete VPS deployment guide

## Three Ways to Deploy

### Option 1: Docker Compose (Easiest) - Start Here

```bash
cp .env.example .env
# Edit .env and change DB_PASSWORD to something secure
nano .env

docker-compose up -d
docker-compose exec api python init_db.py
curl http://localhost:8000/health
```

**Time:** 5 minutes
**Requirements:** Docker & Docker Compose only

### Option 2: Local Python Development

```bash
pip install -r requirements.txt
cp .env.example .env
nano .env  # Configure for your local PostgreSQL

python init_db.py
python -m baseball_manager_ai.api.model_server
```

**Time:** 15 minutes
**Requirements:** Python 3.8+, PostgreSQL

### Option 3: Deploy to VPS

See `SELF_HOSTED_SETUP.md` or `VPS_DEPLOYMENT.md` for complete instructions.

**Time:** 30 minutes - 1 hour
**Requirements:** VPS with Docker

## Key Files

| File | Purpose |
|------|---------|
| `SELF_HOSTED_SETUP.md` | **Start here** - Quick setup & troubleshooting |
| `VPS_DEPLOYMENT.md` | Complete VPS setup with Nginx, SSL, backups |
| `init_db.py` | Initialize database tables and indexes |
| `docker-compose.yml` | PostgreSQL + API containers |
| `.env.example` | Configuration template (copy to `.env`) |
| `baseball_manager_ai/database/` | ORM models and database code |

## Database

Your data is stored in PostgreSQL:

- 6 tables auto-created on first run
- Persistent storage in Docker volume
- Easy backup/restore commands
- SQL queries for analysis

## Configuration

Edit `.env` to customize:

```ini
DATABASE_URL=postgresql://baseball_user:password@localhost:5432/baseball_db
DB_PASSWORD=change_this_to_something_secure
API_PORT=8000
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## Quick Commands

```bash
# Start everything
docker-compose up -d

# Initialize database
docker-compose exec api python init_db.py

# View logs
docker-compose logs -f api

# Access database console
docker-compose exec postgres psql -U baseball_user -d baseball_db

# Stop everything
docker-compose down

# Backup database
docker-compose exec postgres pg_dump -U baseball_user baseball_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U baseball_user baseball_db < backup.sql
```

## Health Check

After deployment, verify everything is working:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-...",
  "models_loaded": 0,
  "database": "connected"
}
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Container won't start | Check `docker-compose logs` |
| Database connection refused | Verify `.env` DATABASE_URL |
| Port already in use | Change `API_PORT` in `.env` |
| Out of disk space | Run `docker system prune` |
| Permission denied | Check file ownership/permissions |

See `SELF_HOSTED_SETUP.md` for detailed troubleshooting.

## Next Steps

1. **Read:** `SELF_HOSTED_SETUP.md` (5 min)
2. **Deploy:** Docker Compose setup (5 min)
3. **Initialize:** Run `init_db.py` (1 min)
4. **Test:** Hit the `/health` endpoint (1 min)
5. **Optional:** Download data, train models, set up domain

## Support Resources

- SQLAlchemy docs: https://docs.sqlalchemy.org/
- PostgreSQL docs: https://www.postgresql.org/docs/
- Docker docs: https://docs.docker.com/
- FastAPI docs: https://fastapi.tiangolo.com/

---

**Your Baseball Manager AI is ready to run on your own VPS!**

Next: Read `SELF_HOSTED_SETUP.md` for your specific deployment path.
