# Baseball Manager AI - Supabase to PostgreSQL Conversion

## What Was Done

Your Baseball Manager AI application has been completely converted from **Supabase** (cloud-based) to **PostgreSQL** (self-hosted). This gives you full control over your database on your own VPS.

### Changes Made

#### 1. Database Layer
- ✓ Created `baseball_manager_ai/database/` module
- ✓ Implemented SQLAlchemy ORM with 6 models:
  - Games
  - Players
  - PlayByPlay
  - ManagerDecisions
  - SimulationResults
  - TeamStats
- ✓ Database connection pooling with SQLAlchemy
- ✓ Automatic table creation on first run

#### 2. Dependencies Updated
- ✓ Added `psycopg2-binary` - PostgreSQL driver
- ✓ Added `sqlalchemy>=1.4.0` - ORM framework
- ✓ Added `alembic>=1.8.0` - Database migrations
- ✓ Added `python-dotenv` - Environment configuration

#### 3. Docker Setup
- ✓ Updated `docker-compose.yml` with PostgreSQL service
- ✓ Added automatic database initialization
- ✓ Added health checks
- ✓ Configured persistent volume for data

#### 4. API Updates
- ✓ Updated `model_server.py` for PostgreSQL
- ✓ Added database connection to health check
- ✓ Added `init_db()` on startup
- ✓ Environment variable support

#### 5. Configuration
- ✓ Updated `.env.example` with PostgreSQL settings
- ✓ Created `config/database.yaml`
- ✓ Added `init_db.py` initialization script

#### 6. Documentation
- ✓ START_HERE.md - Main entry point
- ✓ SETUP_SUMMARY.md - Quick setup guide
- ✓ SELF_HOSTED_SETUP.md - Database & management
- ✓ VPS_DEPLOYMENT.md - Complete VPS setup
- ✓ DEPLOYMENT_CHECKLIST.md - Step-by-step guide
- ✓ SELF_HOSTED_README.txt - Quick reference
- ✓ This file - Conversion summary

## File Structure Changes

### New Files Created
```
baseball_manager_ai/database/
├── __init__.py              - Module initialization
├── connection.py            - Database connection & pooling
└── models.py                - SQLAlchemy ORM models

config/
└── database.yaml            - Database configuration

Root level:
├── init_db.py               - Database initialization
├── START_HERE.md            - New main documentation
├── SETUP_SUMMARY.md         - Quick setup guide
├── SELF_HOSTED_SETUP.md     - Database management
├── SELF_HOSTED_README.txt   - Quick reference
├── VPS_DEPLOYMENT.md        - VPS setup guide
├── DEPLOYMENT_CHECKLIST.md  - Deployment steps
└── CONVERSION_SUMMARY.md    - This file
```

### Files Updated
```
.env.example                 - Changed to PostgreSQL variables
docker-compose.yml           - Added PostgreSQL service
Dockerfile                   - Uses updated dependencies
requirements.txt             - Added PostgreSQL packages
baseball_manager_ai/api/
└── model_server.py          - Updated for database integration
```

## Database Architecture

### PostgreSQL Setup
```
Your VPS
│
├─ Docker Container: PostgreSQL
│  └─ Database: baseball_db
│     ├─ games table
│     ├─ players table
│     ├─ play_by_play table
│     ├─ manager_decisions table
│     ├─ simulation_results table
│     └─ team_stats table
│
└─ Docker Container: FastAPI
   └─ Python Application
      └─ SQLAlchemy ORM
         └─ Connected to PostgreSQL
```

### Database Models

#### Games
```sql
- id (PRIMARY KEY)
- date, home_team, away_team
- home_score, away_score
- stadium, weather, attendance
- created_at, updated_at
```

#### Players
```sql
- id (PRIMARY KEY)
- name, team, position
- bats, throws
- season stats: avg, ops, era, k9, etc.
- created_at, updated_at
```

#### PlayByPlay
```sql
- id (PRIMARY KEY)
- game_id (FOREIGN KEY)
- inning, batter_id, pitcher_id
- result, runs_scored
- win_probability_added
- created_at
```

#### ManagerDecisions
```sql
- id (PRIMARY KEY)
- game_id (FOREIGN KEY)
- inning, outs, decision_type
- success, wpa (win probability added)
- metadata (JSON)
- created_at, updated_at
```

#### SimulationResults
```sql
- id (PRIMARY KEY)
- home_team, away_team
- num_simulations
- win_probabilities, expected_scores
- metadata (JSON)
- created_at
```

#### TeamStats
```sql
- id (PRIMARY KEY)
- team, season
- wins, losses, runs_for, runs_against
- batting/pitching statistics
- created_at, updated_at
```

## Configuration Changes

### Before (Supabase)
```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_ROLE_KEY=xxx
```

### After (PostgreSQL)
```env
DATABASE_URL=postgresql://baseball_user:password@postgres:5432/baseball_db
DB_USER=baseball_user
DB_PASSWORD=your_password
DB_HOST=postgres
DB_PORT=5432
```

## Deployment Methods

### Three Ways to Deploy

1. **Docker Locally** (5 minutes)
   - Everything in containers
   - PostgreSQL runs locally
   - Perfect for testing

2. **Native Python** (15 minutes)
   - Python runs natively
   - PostgreSQL runs locally
   - Good for development

3. **VPS with Domain** (1 hour)
   - Docker on VPS
   - Domain + SSL
   - Production-ready

See documentation files for complete setup instructions.

## Data Persistence

### Where Data Lives
- **Docker Volume**: `baseball-manager-ai_postgres_data`
- **Location**: `/var/lib/docker/volumes/baseball-manager-ai_postgres_data/_data`
- **Persistence**: Data survives container restart/recreation

### Backup Capabilities
```bash
# Full database backup
docker-compose exec postgres pg_dump -U baseball_user baseball_db > backup.sql

# Automated daily backups (see VPS_DEPLOYMENT.md)
# Restore from backup
docker-compose exec -T postgres psql -U baseball_user baseball_db < backup.sql
```

## Key Advantages

### Control
- ✓ Full control over database
- ✓ Own your data
- ✓ Custom queries and optimization
- ✓ No vendor lock-in

### Cost
- ✓ No monthly SaaS fees
- ✓ Single VPS cost covers everything
- ✓ Free open-source software

### Flexibility
- ✓ Add custom tables/columns easily
- ✓ Configure connection pooling
- ✓ Optimize indexes for your queries
- ✓ Run complex analytics

### Reliability
- ✓ Automated backups
- ✓ Point-in-time recovery
- ✓ Monitoring and alerting
- ✓ Disaster recovery plan

## Migration Path

If you had data in Supabase:
1. Export data from Supabase as CSV/JSON
2. Import into PostgreSQL tables
3. Verify data integrity
4. Start using PostgreSQL

(See VPS_DEPLOYMENT.md for detailed import instructions)

## What Stays The Same

- ✓ All Python code structure
- ✓ API endpoints
- ✓ Model serving
- ✓ Simulation engine
- ✓ Data processing
- ✓ Configuration files

## What's New

- ✓ Database models (SQLAlchemy ORM)
- ✓ Database initialization script
- ✓ PostgreSQL in docker-compose.yml
- ✓ Database configuration
- ✓ Complete deployment documentation

## Getting Started

### Quick Test (5 minutes)
```bash
cp .env.example .env
nano .env
docker-compose up -d
docker-compose exec api python init_db.py
curl http://localhost:8000/health
```

### VPS Deployment (1 hour)
See **START_HERE.md** and **VPS_DEPLOYMENT.md**

## Support

### Documentation Files (In Order)
1. **START_HERE.md** - Overview & quick start
2. **SETUP_SUMMARY.md** - What's included
3. **SELF_HOSTED_SETUP.md** - Database management
4. **VPS_DEPLOYMENT.md** - Production setup
5. **DEPLOYMENT_CHECKLIST.md** - Step by step

### Common Issues

| Issue | Solution |
|-------|----------|
| Can't connect to database | Check `docker-compose logs postgres` |
| API won't start | Check `docker-compose logs api` |
| Container won't start | Verify `.env` configuration |
| Permission errors | Run `chmod 600 .env` |

## Next Steps

1. **Read**: START_HERE.md (10 minutes)
2. **Deploy Locally**: Try docker-compose locally (5 minutes)
3. **Test**: Run init_db.py and test endpoints (2 minutes)
4. **Deploy to VPS**: Read VPS_DEPLOYMENT.md (30-60 minutes)
5. **Configure Domain**: Set up Nginx & SSL (20 minutes)

## Summary

Your Baseball Manager AI has been successfully converted from Supabase to PostgreSQL:

- ✓ Complete database models
- ✓ Docker & docker-compose setup
- ✓ Full documentation
- ✓ Three deployment options
- ✓ Backup/restore capabilities
- ✓ Production-ready

**You're ready to deploy!**

Start with **START_HERE.md** → **SETUP_SUMMARY.md** → **VPS_DEPLOYMENT.md**

---

For questions, check the documentation or review troubleshooting sections in the guides above.

Happy deploying! 🚀
