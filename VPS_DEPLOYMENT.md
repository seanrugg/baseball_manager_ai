# Baseball Manager AI - Plesk Deployment Guide

This guide covers deploying Baseball Manager AI to Plesk with direct GitHub integration and MariaDB database.

## Prerequisites

- Plesk-managed VPS with root/admin access
- GitHub repository with your code
- MariaDB 10.11.13 database already running
- Subdomain configured in Plesk
- Python 3.8+ available on the server

## Deployment Steps

### 1. Create Subdomain in Plesk

1. Log in to Plesk Dashboard
2. Go to **Domains** → **Your Main Domain**
3. Click **Subdomains**
4. Create new subdomain (e.g., `api.yourdomain.com`)
5. Set document root to a directory like `/home/yourusername/public_html/api`
6. Note the document root path

### 2. Configure GitHub Deployment

#### Option A: Using Plesk Git Integration (Recommended)

1. In Plesk, go to **Git repositories**
2. Click **Add Git Repository**
3. Select your GitHub repository
4. Set branch to `main` (or your default branch)
5. Set deployment path to your subdomain's document root
6. Configure webhooks for automatic deployment on push

#### Option B: Manual Git Pull (Command Line)

```bash
cd /home/yourusername/public_html/api
git clone https://github.com/yourusername/baseball-manager-ai.git .
```

### 3. Install Python Dependencies

```bash
cd /home/yourusername/public_html/api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
nano .env
```

Update `.env` with your MariaDB credentials:

```
# Database Configuration (MariaDB)
DATABASE_URL=mysql+pymysql://your_db_user:your_db_password@localhost:3306/your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name
DB_HOST=localhost
DB_PORT=3306

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=production

# Logging
LOG_LEVEL=INFO
```

### 5. Initialize Database

```bash
cd /home/yourusername/public_html/api
source venv/bin/activate

# Create tables in MariaDB
python -c "from baseball_manager_ai.database.connection import init_db; init_db()"
```

### 6. Configure Plesk Application Server

#### For Python/FastAPI via Plesk:

1. In Plesk, go to your subdomain
2. Click **Python Handler** or **Application Server**
3. If using Python application:
   - Select Python version (3.8+)
   - Set entry point to your WSGI application

#### Alternative: Use Gunicorn with Systemd

Install Gunicorn:

```bash
source venv/bin/activate
pip install gunicorn
```

Create systemd service file `/etc/systemd/system/baseball-api.service`:

```ini
[Unit]
Description=Baseball Manager AI API
After=network.target

[Service]
User=yourusername
WorkingDirectory=/home/yourusername/public_html/api
Environment="PATH=/home/yourusername/public_html/api/venv/bin"
ExecStart=/home/yourusername/public_html/api/venv/bin/gunicorn \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    baseball_manager_ai.api.model_server:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl start baseball-api
sudo systemctl enable baseball-api
```

### 7. Configure Plesk Proxy

In Plesk for your subdomain:

1. Go to **Proxy** or **Reverse Proxy**
2. Create a new proxy rule:
   - From: `/`
   - To: `http://127.0.0.1:8000`

### 8. Verify Deployment

```bash
# Check if API is running
curl http://your-subdomain.yourdomain.com/health

# Check service status (if using systemd)
sudo systemctl status baseball-api
```

## Database Management (MariaDB)

### Connect to MariaDB

```bash
mysql -u your_db_user -p your_db_name
```

### Backup Database

```bash
mysqldump -u your_db_user -p your_db_name > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database

```bash
mysql -u your_db_user -p your_db_name < backup.sql
```

### Automated Daily Backups

Create `/home/yourusername/backup_mariadb.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/yourusername/backups"
mkdir -p $BACKUP_DIR

mysqldump -u your_db_user -p'your_password' your_db_name | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 7 days of backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
```

Make executable and add to crontab:

```bash
chmod +x /home/yourusername/backup_mariadb.sh
crontab -e
# Add: 0 2 * * * /home/yourusername/backup_mariadb.sh
```

### Query MariaDB

```bash
# List tables
mysql -u your_db_user -p your_db_name -e "SHOW TABLES;"

# View table structure
mysql -u your_db_user -p your_db_name -e "DESCRIBE games;"

# Check database size
mysql -u your_db_user -p your_db_name -e "SELECT table_schema, SUM(data_length + index_length)/1024/1024 AS size_mb FROM information_schema.tables GROUP BY table_schema;"
```

## Continuous Deployment from GitHub

### Auto-Deployment on Push

#### Using Plesk Git Integration:

1. In Plesk dashboard, configure webhook from GitHub
2. Plesk will auto-pull on commits to selected branch

#### Manual Webhook Handler:

Create `/home/yourusername/public_html/api/deploy.php`:

```php
<?php
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $payload = json_decode(file_get_contents('php://input'), true);

    if ($payload['ref'] === 'refs/heads/main') {
        chdir('/home/yourusername/public_html/api');
        shell_exec('git pull origin main');
        shell_exec('source venv/bin/activate && pip install -r requirements.txt');
        // Restart API if needed
        shell_exec('sudo systemctl restart baseball-api');
    }
    http_response_code(200);
}
?>
```

Configure GitHub webhook to send push events to: `https://your-subdomain.yourdomain.com/deploy.php`

## Performance & Monitoring

### Check Application Logs

```bash
# If using systemd
sudo journalctl -u baseball-api -f

# Or check Plesk logs
tail -f /var/log/plesk/apache2ssl_error_log
```

### Monitor Database Performance

```bash
mysql -u your_db_user -p -e "SHOW STATUS LIKE 'Threads%';"
mysql -u your_db_user -p -e "SHOW FULL PROCESSLIST;"
```

### Enable Query Logging (MariaDB)

```bash
mysql -u root -p -e "SET GLOBAL general_log = 'ON';"
```

## Troubleshooting

### API Not Responding

```bash
# Check if service is running
sudo systemctl status baseball-api

# Check for port conflicts
sudo netstat -tlnp | grep 8000

# View logs
sudo journalctl -u baseball-api -n 50
```

### Database Connection Errors

```bash
# Verify MariaDB is running
sudo systemctl status mariadb

# Test connection
mysql -u your_db_user -p your_db_name -e "SELECT 1;"

# Check DATABASE_URL in .env
cat /home/yourusername/public_html/api/.env | grep DATABASE_URL
```

### Git Pull Fails

```bash
cd /home/yourusername/public_html/api

# Check git status
git status

# Reset to remote state if needed
git reset --hard origin/main

# Verify credentials (use SSH keys or token)
git remote -v
```

### Permission Errors

```bash
# Fix directory permissions
sudo chown -R yourusername:yourusername /home/yourusername/public_html/api

# Make venv accessible
chmod -R 755 venv/
```

## SSL Configuration

Plesk typically handles SSL automatically via Let's Encrypt. To manually configure:

1. In Plesk, go to your subdomain
2. Click **SSL/TLS Certificates**
3. Select or create Let's Encrypt certificate
4. Plesk auto-renews 30 days before expiration

## Maintenance Schedule

### Daily
- Monitor logs for errors
- Check disk space: `df -h`

### Weekly
- Backup database manually
- Review error logs
- Check MariaDB performance

### Monthly
- Update system packages: `sudo apt update && sudo apt upgrade`
- Test disaster recovery
- Review database indexing

## Production Checklist

- [ ] GitHub repository connected
- [ ] MariaDB database created and accessible
- [ ] Environment variables configured in .env
- [ ] Python dependencies installed
- [ ] Database tables initialized
- [ ] API service running and responding
- [ ] SSL certificate installed
- [ ] Automatic backups configured
- [ ] Plesk proxy rules working
- [ ] GitHub webhooks configured for auto-deployment
- [ ] Error logging monitored
- [ ] Database credentials secured (not in git)
- [ ] Health endpoint returning success

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
