# Baseball Manager AI - VPS Deployment Guide

This guide covers deploying Baseball Manager AI to your personal VPS with PostgreSQL database.

## Prerequisites

- Ubuntu 20.04+ VPS with root or sudo access
- Domain name (optional, for production)
- 2GB+ RAM recommended
- Docker & Docker Compose (or native Python setup)

## Quick Start (Docker) - Recommended

### 1. SSH into your VPS

```bash
ssh root@your-vps-ip
```

### 2. Install Docker and Docker Compose

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 3. Clone or Upload Your Project

```bash
# Option A: Clone from git (if you have a repo)
git clone https://github.com/yourusername/baseball-manager-ai.git
cd baseball-manager-ai

# Option B: Upload using scp from your local machine
# On your local machine:
scp -r /path/to/baseball-manager-ai root@your-vps-ip:/opt/
```

### 4. Configure Environment

```bash
cd /opt/baseball-manager-ai
cp .env.example .env
nano .env
```

Update these values in `.env`:

```
# Database Configuration
DATABASE_URL=postgresql://baseball_user:baseball_password@postgres:5432/baseball_db
DB_USER=baseball_user
DB_PASSWORD=your_secure_password_here
DB_NAME=baseball_db
DB_HOST=postgres
DB_PORT=5432

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=production

# Logging
LOG_LEVEL=INFO
```

### 5. Deploy with Docker Compose

```bash
# Build and start containers
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api

# Check database connection
docker-compose logs postgres
```

### 6. Verify Deployment

```bash
# Test health endpoint
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","timestamp":"...","models_loaded":0,"database":"connected"}
```

## Setup Nginx Reverse Proxy

For production with your domain:

### 1. Install Nginx

```bash
sudo apt update
sudo apt install nginx
```

### 2. Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/baseball-manager
```

Add this configuration:

```nginx
upstream baseball_api {
    server localhost:8000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    client_max_body_size 10M;

    location / {
        proxy_pass http://baseball_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 3. Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/baseball-manager /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl start nginx
sudo systemctl enable nginx
```

## Setup SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

## Database Backup and Restore

### Backup Database

```bash
docker-compose exec postgres pg_dump -U baseball_user baseball_db > backup.sql
```

### Restore Database

```bash
docker-compose exec -T postgres psql -U baseball_user baseball_db < backup.sql
```

### Automated Daily Backups

Create `/opt/baseball-manager-ai/backup.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/baseball-manager-ai/backups"
mkdir -p $BACKUP_DIR

docker-compose exec -T postgres pg_dump -U baseball_user baseball_db | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 7 days of backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
```

Add to crontab:

```bash
crontab -e
# Add this line:
0 2 * * * /opt/baseball-manager-ai/backup.sh
```

## Database Management

### Connect to PostgreSQL

```bash
docker-compose exec postgres psql -U baseball_user -d baseball_db
```

### Create Database Backups

```bash
# List all tables
\dt

# View table schema
\d tablename

# Exit
\q
```

### Create New Tables

Inside the container:

```bash
docker-compose exec postgres psql -U baseball_user -d baseball_db -c "
CREATE TABLE IF NOT EXISTS your_table (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW()
);
"
```

## Monitoring and Logs

### View Application Logs

```bash
# Last 100 lines
docker-compose logs --tail=100 api

# Follow logs in real-time
docker-compose logs -f api

# All services
docker-compose logs -f
```

### Check Container Status

```bash
docker-compose ps
docker stats
```

### View Database Logs

```bash
docker-compose logs postgres
```

## Troubleshooting

### Container won't start

```bash
docker-compose logs api
docker-compose logs postgres

# Rebuild containers
docker-compose build --no-cache
docker-compose up -d
```

### Database connection errors

```bash
# Check if database is ready
docker-compose exec postgres pg_isready -U baseball_user

# Check database size
docker-compose exec postgres psql -U baseball_user -d baseball_db -c "
SELECT pg_size_pretty(pg_database_size('baseball_db'));
"
```

### Port already in use

Change in `.env`:

```
API_PORT=8001
DB_PORT=5433
```

And update Nginx configuration.

### Disk space issues

```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune

# Check database size
docker-compose exec postgres psql -U baseball_user -d baseball_db -c "SELECT * FROM pg_stat_user_tables;"
```

## Performance Optimization

### Increase Database Pool Size

Edit `.env`:

```
DATABASE_POOL_SIZE=20
```

### Enable Query Caching

In application code (already configured in model_server.py):

```python
# Cache predictions in memory
self.prediction_cache = {}
```

### Database Indexing

The application automatically creates indexes on frequently queried columns. To add custom indexes:

```bash
docker-compose exec postgres psql -U baseball_user -d baseball_db -c "
CREATE INDEX idx_games_date ON games(date);
CREATE INDEX idx_decisions_game ON manager_decisions(game_id);
"
```

## Scaling for Production

### Multiple Workers

Update docker-compose.yml:

```yaml
api:
  # ... existing config
  deploy:
    replicas: 3
```

### Load Balancing

Update Nginx upstream:

```nginx
upstream baseball_api {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}
```

## Updating Application

### Pull latest changes

```bash
cd /opt/baseball-manager-ai
git pull origin main  # if using git
```

### Rebuild and restart

```bash
docker-compose down
docker-compose build
docker-compose up -d
```

## Firewall Configuration

### UFW (Ubuntu Firewall)

```bash
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw enable
```

## System Cleanup

### Remove old Docker images

```bash
docker image prune -a
```

### Remove unused containers

```bash
docker container prune
```

### Free up database space

```bash
docker-compose exec postgres VACUUM ANALYZE;
```

## Production Checklist

- [ ] Domain name configured
- [ ] SSL certificate installed (Let's Encrypt)
- [ ] Firewall configured
- [ ] Regular backups enabled
- [ ] Monitoring set up
- [ ] Error logging configured
- [ ] Database credentials secured
- [ ] SSH keys configured (no password auth)
- [ ] Nginx reverse proxy working
- [ ] Health checks passing
- [ ] Load testing completed
- [ ] Disaster recovery plan documented

## Getting Help

### Common Issues

1. **Can't connect to database**
   - Check `.env` DATABASE_URL
   - Verify postgres container is healthy: `docker-compose logs postgres`
   - Test connection: `docker-compose exec postgres psql -U baseball_user -d baseball_db`

2. **API not responding**
   - Check if container is running: `docker-compose ps`
   - View logs: `docker-compose logs api`
   - Test endpoint: `curl http://localhost:8000/health`

3. **Out of disk space**
   - Check usage: `df -h`
   - Clean Docker: `docker system prune`
   - Check database size: `docker-compose exec postgres psql -U baseball_user -d baseball_db -c "SELECT pg_size_pretty(pg_database_size('baseball_db'));"`

4. **Port conflicts**
   - Check what's using the port: `netstat -tlnp | grep 8000`
   - Change ports in `.env` and Nginx config

## Support Resources

- Docker documentation: https://docs.docker.com
- PostgreSQL documentation: https://www.postgresql.org/docs
- Nginx documentation: https://nginx.org/en/docs
- Let's Encrypt: https://letsencrypt.org

## Next Steps

1. **Download Data** (optional for testing)
   ```bash
   docker-compose exec api python scripts/download_data.py --seasons 2024
   ```

2. **Train Models** (optional)
   ```bash
   docker-compose exec api python scripts/train_model.py --model all
   ```

3. **Run Simulations**
   ```bash
   docker-compose exec api python scripts/run_simulation.py --home-team NYY --away-team BOS --games 100
   ```

## Maintenance Schedule

### Daily
- Monitor logs for errors
- Check disk space

### Weekly
- Backup database
- Review error logs
- Check system resources

### Monthly
- Update system packages
- Review and optimize queries
- Test disaster recovery

---

Your Baseball Manager AI is now ready to serve predictions from your VPS!
