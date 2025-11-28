# Baseball Manager AI - Self-Hosted Deployment Checklist

## Pre-Deployment Setup

### Local Machine
- [ ] Project files downloaded/cloned
- [ ] Docker & Docker Compose installed (`docker --version`, `docker-compose --version`)
- [ ] `.env.example` copied to `.env`
- [ ] `DB_PASSWORD` in `.env` changed to strong password
- [ ] `DATABASE_URL` in `.env` reviewed and correct

### VPS (if deploying to VPS)
- [ ] VPS access verified (can SSH in)
- [ ] Ubuntu 20.04+ running
- [ ] 2GB+ RAM available
- [ ] 10GB+ disk space available
- [ ] Docker & Docker Compose installed on VPS
- [ ] Project uploaded to VPS (e.g., `/opt/baseball-manager-ai`)

## Deployment Phase

### Docker Compose Startup
- [ ] Run: `docker-compose up -d`
- [ ] Wait 15-20 seconds for PostgreSQL to start
- [ ] Check: `docker-compose ps` shows both containers "Up"
- [ ] Check: `docker-compose logs postgres` for any errors
- [ ] Check: `docker-compose logs api` for any errors

### Database Initialization
- [ ] Run: `docker-compose exec api python init_db.py`
- [ ] Verify: ✓ marks indicate successful steps
- [ ] Check: "All required tables exist" message
- [ ] Confirm: Database connection successful

### API Health Check
- [ ] Run: `curl http://localhost:8000/health`
- [ ] Verify response contains `"database":"connected"`
- [ ] Status should be `"healthy"`

## Post-Deployment Verification

### Container Status
- [ ] `docker-compose ps` shows both services running
- [ ] `docker stats` shows reasonable resource usage
- [ ] Logs show no errors: `docker-compose logs --tail=20`

### Database Connectivity
- [ ] Can connect to database: `docker-compose exec postgres psql -U baseball_user -d baseball_db`
- [ ] Can list tables: `\dt` (in psql console)
- [ ] Database size is reasonable: `SELECT pg_size_pretty(pg_database_size('baseball_db'));`

### API Functionality
- [ ] Health endpoint works: `/health`
- [ ] API responds to requests: Check logs for activity
- [ ] No connection errors in logs: `docker-compose logs api | grep -i error`

### Data Persistence
- [ ] Docker volume created: `docker volume ls | grep postgres_data`
- [ ] Volume has data: `docker volume inspect baseball-manager-ai_postgres_data`
- [ ] Backup can be created: `docker-compose exec postgres pg_dump -U baseball_user baseball_db > test_backup.sql`

## Optional: Domain Setup (Production)

### Nginx Setup
- [ ] Nginx installed: `nginx -v`
- [ ] Nginx config created at `/etc/nginx/sites-available/baseball-manager`
- [ ] Config symlinked to sites-enabled
- [ ] Nginx test passes: `sudo nginx -t`
- [ ] Nginx running: `sudo systemctl status nginx`

### SSL Certificate
- [ ] Certbot installed: `which certbot`
- [ ] Certificate obtained: `sudo certbot --nginx -d your-domain.com`
- [ ] Certificate auto-renewal configured
- [ ] HTTPS working: `curl https://your-domain.com`

### DNS & Domain
- [ ] Domain DNS points to VPS IP
- [ ] DNS propagated (may take 24 hours)
- [ ] Can access via domain: `https://your-domain.com`

## Backup & Recovery

### Initial Backup
- [ ] First backup created: `docker-compose exec postgres pg_dump -U baseball_user baseball_db > backup_init.sql`
- [ ] Backup file verified: `ls -lh backup*.sql`
- [ ] Test restore works (on dev environment)

### Backup Automation (Optional)
- [ ] Backup script created: `/opt/baseball-manager-ai/backup.sh`
- [ ] Cron job configured: `crontab -e`
- [ ] First automated backup created
- [ ] Old backups deleted automatically

## Monitoring & Logging

### Logs Setup
- [ ] Log directory exists: `ls -la logs/`
- [ ] Logs are being written: Check recent timestamps
- [ ] No persistent errors in logs: Review last 100 lines

### System Monitoring (Optional)
- [ ] Disk usage monitored: `df -h`
- [ ] Memory usage reasonable: `docker stats`
- [ ] Database size growing appropriately
- [ ] No out-of-space errors

## Security Checklist

- [ ] `DB_PASSWORD` is strong (12+ chars, mixed case, numbers, symbols)
- [ ] `.env` file not in version control (add to `.gitignore`)
- [ ] `.env` permissions restricted: `chmod 600 .env`
- [ ] Firewall configured: `sudo ufw status`
- [ ] SSH key-based auth only (no password auth)
- [ ] Regular security updates: `sudo apt update && sudo apt upgrade`

## Production Checklist

- [ ] `ENVIRONMENT` set to `production` in `.env`
- [ ] `LOG_LEVEL` set to `WARNING`
- [ ] Database backups scheduled (daily or more frequent)
- [ ] Monitoring/alerting configured
- [ ] Disaster recovery plan documented
- [ ] Load testing completed
- [ ] Performance benchmarks recorded

## Testing & Validation

### API Endpoints
- [ ] GET `/` returns API info
- [ ] GET `/health` returns status
- [ ] GET `/models` returns model list
- [ ] Database field in health check shows "connected"

### Database
- [ ] All 6 tables exist: games, players, play_by_play, manager_decisions, simulation_results, team_stats
- [ ] Indexes created on performance-critical columns
- [ ] Can read/write data to each table

### Sample Data
- [ ] Sample data created (optional): `docker-compose exec api python quick_start.py`
- [ ] Can query sample data
- [ ] Simulations run successfully

## Troubleshooting Checklist

If something fails:

1. [ ] Check logs: `docker-compose logs -f api`
2. [ ] Verify `.env` configuration
3. [ ] Ensure containers are running: `docker-compose ps`
4. [ ] Check disk space: `df -h`
5. [ ] Restart containers: `docker-compose down && docker-compose up -d`
6. [ ] Verify database connection: `docker-compose exec postgres psql -U baseball_user -d baseball_db -c "SELECT 1"`
7. [ ] Review VPS_DEPLOYMENT.md troubleshooting section

## Documentation

- [ ] SELF_HOSTED_SETUP.md read and understood
- [ ] VPS_DEPLOYMENT.md reviewed
- [ ] Database connection credentials saved securely
- [ ] Backup/restore procedures documented
- [ ] Team members briefed on deployment

## Sign-Off

- [ ] All checks passed
- [ ] System is production-ready
- [ ] Monitoring is in place
- [ ] Backups are automated
- [ ] Documentation is complete

**Deployment Date:** _______________

**Deployed By:** _______________

**Notes:** 
```
_________________________________________________________
_________________________________________________________
_________________________________________________________
```

---

## Quick Reference - Common Commands

```bash
# Status
docker-compose ps
docker-compose logs -f

# Database access
docker-compose exec postgres psql -U baseball_user -d baseball_db

# Backup
docker-compose exec postgres pg_dump -U baseball_user baseball_db > backup.sql

# Restore
docker-compose exec -T postgres psql -U baseball_user baseball_db < backup.sql

# Restart
docker-compose restart

# Stop
docker-compose down

# Start
docker-compose up -d

# Rebuild
docker-compose down
docker-compose build
docker-compose up -d
```

## Support Resources

- Logs: `docker-compose logs -f`
- PostgreSQL: https://www.postgresql.org/docs/
- Docker: https://docs.docker.com/
- FastAPI: https://fastapi.tiangolo.com/
- Nginx: https://nginx.org/en/docs/

---

**You're ready to deploy!** ✓
