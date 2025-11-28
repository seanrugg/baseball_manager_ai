# Baseball Manager AI - Self-Hosted Deployment

**You asked for self-hosted on your own VPS. Here's what I've set up for you.**

## What Changed

Your app has been converted from Supabase (cloud) to **PostgreSQL (self-hosted)**:

✓ Full control over your database
✓ Runs on your VPS with your domain
✓ Docker containers for easy deployment
✓ Complete backup & restore capabilities
✓ No monthly SaaS fees

## One-Minute Overview

**What you get:**
- 6 database tables (games, players, decisions, simulations, etc.)
- FastAPI REST API server
- Docker Compose for easy deployment
- PostgreSQL database in a container
- Complete documentation and setup scripts

**How it works:**
- Docker Compose starts PostgreSQL container
- Docker Compose starts FastAPI API container
- They communicate internally
- You access API via `http://your-domain.com`
- Data persists in PostgreSQL volume

## 5-Minute Quick Start

### Step 1: Prepare
```bash
cp .env.example .env
nano .env  # Change DB_PASSWORD to something secure
```

### Step 2: Deploy
```bash
docker-compose up -d
```

### Step 3: Initialize
```bash
docker-compose exec api python init_db.py
```

### Step 4: Test
```bash
curl http://localhost:8000/health
```

You should see:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

**That's it!** Your API is running locally with PostgreSQL.

## Documentation (Read In Order)

1. **START_HERE.md** (this file) - Overview
2. **SETUP_SUMMARY.md** - Quick setup & what's included
3. **SELF_HOSTED_SETUP.md** - Database management & troubleshooting
4. **VPS_DEPLOYMENT.md** - Complete VPS setup with domain/SSL
5. **DEPLOYMENT_CHECKLIST.md** - Step-by-step checklist

## Three Deployment Paths

### Path A: Docker Locally (Testing)
- Run on your laptop/desktop
- PostgreSQL in Docker
- 5 minutes to get running
- Perfect for testing

→ See: SETUP_SUMMARY.md

### Path B: Python Locally (Development)  
- Run native Python
- Local PostgreSQL
- Good for development
- 15 minutes

→ See: SELF_HOSTED_SETUP.md

### Path C: VPS with Domain (Production)
- Deploy to your VPS
- Configure domain
- Add SSL certificate
- Set up backups
- 1 hour total

→ See: VPS_DEPLOYMENT.md + DEPLOYMENT_CHECKLIST.md

## Key Files

```
Project Root/
├── START_HERE.md                    ← You are here
├── SETUP_SUMMARY.md                 ← Quick overview
├── SELF_HOSTED_SETUP.md             ← Database management
├── VPS_DEPLOYMENT.md                ← Full VPS setup
├── DEPLOYMENT_CHECKLIST.md          ← Step-by-step guide
│
├── .env.example                     ← Copy to .env
├── docker-compose.yml               ← PostgreSQL + API
├── Dockerfile                       ← API container
├── init_db.py                       ← Initialize database
├── test_basic.py                    ← Test your setup
├── quick_start.py                   ← Create sample data
│
├── config/
│   ├── database.yaml                ← Database config
│   ├── model_config.yaml
│   ├── training_config.yaml
│   └── simulation_config.yaml
│
└── baseball_manager_ai/
    ├── database/                    ← NEW: Database code
    │   ├── models.py                ← SQLAlchemy models
    │   └── connection.py            ← Database connection
    ├── api/
    │   └── model_server.py          ← Updated for PostgreSQL
    ├── simulation/
    ├── utils/
    └── ...
```

## Database

You now have PostgreSQL with these tables:

- **games** - Game results and metadata
- **players** - Player statistics
- **play_by_play** - Detailed game events
- **manager_decisions** - Manager decision history
- **simulation_results** - Simulation outcomes
- **team_stats** - Team statistics by season

All created automatically on first run.

## Configuration

Edit `.env` with your settings:

```ini
# Database (auto-configured, just change password)
DB_PASSWORD=your_secure_password_here

# API
API_PORT=8000
ENVIRONMENT=development

# Logging
LOG_LEVEL=INFO
```

That's it! Docker Compose handles the rest.

## Common Commands

```bash
# Start everything
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api

# Access database
docker-compose exec postgres psql -U baseball_user -d baseball_db

# Backup database
docker-compose exec postgres pg_dump -U baseball_user baseball_db > backup.sql

# Stop everything
docker-compose down
```

## What's Different From Before

### Before (Supabase)
- Cloud database (monthly cost)
- Limited control
- API managed by Supabase
- Proprietary authentication

### Now (PostgreSQL Self-Hosted)
- Your own database server
- Full control & flexibility
- Your own API server
- Complete ownership

## Troubleshooting

**Container won't start?**
```bash
docker-compose logs api
```

**Can't connect to database?**
```bash
docker-compose logs postgres
```

**Port already in use?**
Edit `.env` and change `API_PORT` to 8001

See **SELF_HOSTED_SETUP.md** for detailed troubleshooting.

## Next Steps

1. **Right now (5 min):**
   - Copy `.env.example` to `.env`
   - Change `DB_PASSWORD`
   - Run `docker-compose up -d`

2. **Then (1 min):**
   - Run `docker-compose exec api python init_db.py`
   - Test: `curl http://localhost:8000/health`

3. **For production (30-60 min):**
   - Read `VPS_DEPLOYMENT.md`
   - Deploy to your VPS
   - Configure domain with Nginx
   - Add SSL certificate (Let's Encrypt)

## Resources

- PostgreSQL docs: https://www.postgresql.org/docs/
- Docker docs: https://docs.docker.com/
- FastAPI docs: https://fastapi.tiangolo.com/
- SQLAlchemy docs: https://docs.sqlalchemy.org/

## Support

If you get stuck:
1. Check logs: `docker-compose logs -f`
2. Read the relevant guide above
3. Check the troubleshooting section
4. Review DEPLOYMENT_CHECKLIST.md

## Summary

Your Baseball Manager AI is now ready for self-hosted deployment on your VPS:

- ✓ PostgreSQL database (self-hosted)
- ✓ Docker containers (easy deployment)
- ✓ Complete documentation
- ✓ Backup/restore capabilities
- ✓ Production-ready setup

**Ready to start?**

```bash
cp .env.example .env
nano .env
docker-compose up -d
docker-compose exec api python init_db.py
curl http://localhost:8000/health
```

That's all you need to get running locally.

For VPS deployment, read **VPS_DEPLOYMENT.md**.

---

**Questions?** Check the documentation files above. They have complete troubleshooting and setup guides.

**Let's go!** 🚀
