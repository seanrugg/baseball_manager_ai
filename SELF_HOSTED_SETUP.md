# Baseball Manager AI - Self-Hosted Setup (PostgreSQL)

Your application is now configured for self-hosted deployment with PostgreSQL database.

## What Changed

✓ Added PostgreSQL database driver (`psycopg2-binary`, `sqlalchemy`, `alembic`)
✓ Created database module with ORM models
✓ Updated docker-compose.yml to include PostgreSQL container
✓ Updated API server to initialize database on startup
✓ Updated .env.example with PostgreSQL credentials

## Architecture

```
Your VPS
├── Docker Container (Baseball Manager AI)
│   ├── FastAPI Server (Port 8000)
│   └── SQLAlchemy ORM
│
└── Docker Container (PostgreSQL)
    ├── Database (baseball_db)
    └── Persistent Storage (postgres_data volume)
```

## Quick Start (3 Steps)

### Step 1: Upload to VPS

```bash
# From your local machine:
scp -r /path/to/baseball-manager-ai your-user@your-vps:/opt/
```

### Step 2: Configure

```bash
# On your VPS:
cd /opt/baseball-manager-ai
cp .env.example .env

# Edit .env (change DB_PASSWORD to something secure):
nano .env
```

### Step 3: Deploy

```bash
# Start everything
docker-compose up -d

# Check status (wait 10-15 seconds for database to start)
docker-compose ps

# Test API
curl http://localhost:8000/health
```

## Database Management

### Access PostgreSQL Console

```bash
docker-compose exec postgres psql -U baseball_user -d baseball_db
```

### Common Commands

```sql
-- List all tables
\dt

-- View table structure
\d games

-- Create backup
\copy games TO 'games.csv' WITH CSV HEADER;

-- Count records
SELECT COUNT(*) FROM games;

-- Exit
\q
```

### Backup Database

```bash
# Quick backup
docker-compose exec postgres pg_dump -U baseball_user baseball_db > backup.sql

# Compressed backup
docker-compose exec postgres pg_dump -U baseball_user baseball_db | gzip > backup.sql.gz
```

### Restore Database

```bash
docker-compose exec -T postgres psql -U baseball_user baseball_db < backup.sql
```

## Database Tables

The application automatically creates these tables on first run:

- **games**: Game results and metadata
- **players**: Player statistics
- **play_by_play**: Detailed game events
- **manager_decisions**: Manager decision history
- **simulation_results**: Simulation outcomes
- **team_stats**: Team statistics by season

## API Endpoints

After deployment, access via:

```
http://your-domain.com/health       # Health check + database status
http://your-domain.com/predict      # Game predictions
http://your-domain.com/recommend    # Player recommendations
http://your-domain.com/strategy     # Strategy optimization
http://your-domain.com/models       # List loaded models
```

## Environment Variables

Key variables in `.env`:

```
DATABASE_URL              # PostgreSQL connection string
DB_USER                   # Database user (baseball_user)
DB_PASSWORD               # Database password (change this!)
DB_NAME                   # Database name (baseball_db)
API_PORT                  # API port (8000)
ENVIRONMENT               # development or production
LOG_LEVEL                 # INFO or DEBUG
```

## Troubleshooting

### Database won't start
```bash
# Check logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres

# Check disk space
df -h
```

### API can't connect to database
```bash
# Check connection in logs
docker-compose logs api

# Verify database is ready
docker-compose exec postgres pg_isready -U baseball_user

# Test connection manually
docker-compose exec postgres psql -U baseball_user -d baseball_db -c "SELECT 1"
```

### Permission denied errors
```bash
# Fix file permissions
chmod -R 755 /opt/baseball-manager-ai

# Run as correct user
docker-compose down
docker-compose up -d
```

## Data Persistence

Your database data is stored in a Docker volume:

```bash
# View volumes
docker volume ls

# Database data location:
# /var/lib/docker/volumes/baseball-manager-ai_postgres_data/_data

# To backup volume:
docker run --rm -v baseball-manager-ai_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```

## Monitoring

### View Recent Logs

```bash
# Last 50 lines
docker-compose logs --tail=50 api

# Follow in real-time
docker-compose logs -f api
```

### Check Container Health

```bash
docker-compose ps
docker stats
```

### Database Statistics

```bash
docker-compose exec postgres psql -U baseball_user -d baseball_db -c "
  SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
  FROM pg_tables
  WHERE schemaname != 'pg_catalog'
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

## Performance Tips

1. **Database Indexes**: Already configured for common queries
2. **Connection Pooling**: Configured with pool_size=10
3. **Query Caching**: Enabled in API layer
4. **Keep Backups**: Daily backups recommended

## Scaling

To run multiple API instances:

```bash
# Edit docker-compose.yml and set replicas
# Then restart:
docker-compose down
docker-compose up -d
```

## Security Checklist

- [ ] Change DB_PASSWORD in .env to strong password
- [ ] Use HTTPS with Let's Encrypt (see VPS_DEPLOYMENT.md)
- [ ] Restrict database access to localhost only
- [ ] Enable firewall on VPS
- [ ] Regular database backups
- [ ] Monitor logs for suspicious activity

## File Organization

```
/opt/baseball-manager-ai/
├── .env                          # Your configuration (keep secret!)
├── docker-compose.yml            # Docker setup
├── Dockerfile                     # App container definition
├── requirements.txt               # Python dependencies
├── config/                        # Configuration files
│   ├── database.yaml             # Database configuration
│   ├── model_config.yaml
│   └── ...
├── baseball_manager_ai/
│   ├── api/                      # API server
│   ├── database/                 # Database models & connection
│   │   ├── __init__.py
│   │   ├── connection.py         # Database connection
│   │   └── models.py             # SQLAlchemy models
│   ├── simulation/               # Game simulation
│   └── ...
├── logs/                         # Application logs
├── data/                         # Data files
└── models/                       # Trained models
```

## Next Steps After Deployment

1. **Test API is working**
   ```bash
   curl -s http://localhost:8000/health | python -m json.tool
   ```

2. **Create sample data** (for testing)
   ```bash
   docker-compose exec api python quick_start.py
   ```

3. **Download real baseball data** (optional)
   ```bash
   docker-compose exec api python scripts/download_data.py --seasons 2024
   ```

4. **Train models** (optional)
   ```bash
   docker-compose exec api python scripts/train_model.py --model all
   ```

5. **Set up domain and SSL** (see VPS_DEPLOYMENT.md)

## Production Deployment

For production use:

1. Update `.env`:
   - Set `ENVIRONMENT=production`
   - Use strong DB_PASSWORD
   - Set `LOG_LEVEL=WARNING`

2. Configure domain with Nginx (see VPS_DEPLOYMENT.md)

3. Enable SSL with Let's Encrypt

4. Set up automated backups

5. Monitor logs and performance

## Getting Help

Check these files for detailed information:

- **VPS_DEPLOYMENT.md** - Complete VPS setup & troubleshooting
- **DEPLOYMENT_GUIDE.md** - General deployment info
- **test_basic.py** - Run to verify setup
- **logs/** - Check application logs for errors

## Database Queries Examples

### Find recent games

```sql
SELECT * FROM games ORDER BY date DESC LIMIT 10;
```

### Get player statistics

```sql
SELECT name, team, position, season_ops FROM players WHERE team = 'NYY';
```

### Analysis: Win probability by situation

```sql
SELECT
  inning,
  AVG(win_probability_added) as avg_wpa,
  COUNT(*) as decisions
FROM manager_decisions
GROUP BY inning
ORDER BY inning;
```

---

Your Baseball Manager AI is ready for production self-hosted deployment!
