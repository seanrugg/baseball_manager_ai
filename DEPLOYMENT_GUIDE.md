# Baseball Manager AI - Deployment Guide

## Current Status

Your Baseball Manager AI application is now in a **pre-deployment state**. All configuration files have been created, and the codebase is ready for testing.

## What You Have

✓ Complete codebase with all modules
✓ Configuration files (config/)
✓ API server implementation
✓ Simulation engine
✓ Model training scripts
✓ Data processing pipelines

## Quick Start (Local Testing)

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Or install the package in development mode
pip install -e .
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Supabase credentials
nano .env
```

Required environment variables:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Your Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key (for admin operations)

### 3. Set Up Database (Supabase)

Create the following tables in your Supabase project:

**Table: games**
```sql
CREATE TABLE games (
    game_id TEXT PRIMARY KEY,
    date TIMESTAMP NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    stadium TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE games ENABLE ROW LEVEL SECURITY;
```

**Table: players**
```sql
CREATE TABLE players (
    player_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    team TEXT,
    position TEXT,
    season_avg REAL,
    season_ops REAL,
    season_era REAL,
    created_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE players ENABLE ROW LEVEL SECURITY;
```

**Table: manager_decisions**
```sql
CREATE TABLE manager_decisions (
    decision_id TEXT PRIMARY KEY,
    game_id TEXT REFERENCES games(game_id),
    inning INTEGER,
    outs INTEGER,
    decision_type TEXT,
    success BOOLEAN,
    wpa REAL,
    created_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE manager_decisions ENABLE ROW LEVEL SECURITY;
```

### 4. Run Quick Start Check

```bash
python3 quick_start.py
```

This will verify your setup and create sample data.

### 5. Test the API Server

```bash
# Start the API server
python -m baseball_manager_ai.api.model_server

# In another terminal, test the health endpoint
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-XX-XX...",
  "models_loaded": 0
}
```

## Deployment to Ubuntu VPS

### Option 1: Direct Deployment (Simplest)

```bash
# 1. Copy your project to the VPS
scp -r /path/to/baseball_manager_ai user@your-vps:/opt/baseball_manager_ai

# 2. SSH into your VPS
ssh user@your-vps

# 3. Install dependencies
cd /opt/baseball_manager_ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Set up environment
cp .env.example .env
nano .env  # Add your Supabase credentials

# 5. Run the API server
python -m baseball_manager_ai.api.model_server
```

### Option 2: Docker Deployment (Recommended)

```bash
# 1. Build Docker image
docker build -t baseball-manager-ai .

# 2. Run container
docker run -d \
  -p 8000:8000 \
  -e SUPABASE_URL=your_url \
  -e SUPABASE_ANON_KEY=your_key \
  --name baseball-manager \
  baseball-manager-ai

# 3. Check logs
docker logs -f baseball-manager
```

### Option 3: Systemd Service (Production)

Create `/etc/systemd/system/baseball-manager.service`:

```ini
[Unit]
Description=Baseball Manager AI API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/baseball_manager_ai
Environment="PATH=/opt/baseball_manager_ai/venv/bin"
EnvironmentFile=/opt/baseball_manager_ai/.env
ExecStart=/opt/baseball_manager_ai/venv/bin/python -m baseball_manager_ai.api.model_server
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable baseball-manager
sudo systemctl start baseball-manager
sudo systemctl status baseball-manager
```

## Setting Up Nginx (Optional)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Testing Without Real Data

You can test the system using sample data:

```bash
# Create sample data
python3 quick_start.py

# Run a simulation with sample data
python scripts/run_simulation.py \
  --home-team NYY \
  --away-team BOS \
  --games 100 \
  --output results/
```

## Next Steps After Deployment

### 1. Download Real Data
```bash
# Download Statcast data
python scripts/download_data.py --sources statcast --seasons 2024

# Download Retrosheet data
python scripts/download_data.py --sources retrosheet --seasons 2024
```

### 2. Train Models
```bash
# Train all models
python scripts/train_model.py --model all --config config/training_config.yaml
```

### 3. Run Simulations
```bash
# Run game simulations
python scripts/run_simulation.py \
  --home-team NYY \
  --away-team BOS \
  --games 1000
```

### 4. Deploy Models
```bash
# Package models for deployment
python scripts/deploy_model.py --package --tag v1.0
```

## API Endpoints

Once deployed, your API will have these endpoints:

- `GET /` - API information
- `GET /health` - Health check
- `POST /predict/lineup` - Get lineup recommendation
- `POST /predict/decision` - Get in-game decision
- `POST /predict/pitching` - Get pitching decision
- `POST /simulate` - Run game simulation

## Troubleshooting

### Dependencies Not Installing
```bash
# Try upgrading pip first
pip install --upgrade pip
pip install -r requirements.txt
```

### Port Already in Use
```bash
# Change port in .env
echo "API_PORT=8001" >> .env
```

### Database Connection Issues
- Verify Supabase credentials in .env
- Check Supabase dashboard for service status
- Ensure network connectivity to Supabase

### Models Not Loading
- Models need to be trained first
- Run: `python scripts/train_model.py --model all`
- Or use the API without models for testing

## Monitoring

Check logs:
```bash
# Application logs
tail -f logs/api.log

# Systemd service logs (if using systemd)
sudo journalctl -u baseball-manager -f
```

## Security Checklist

- [ ] Change default .env values
- [ ] Use strong Supabase credentials
- [ ] Set up RLS policies in Supabase
- [ ] Enable firewall on VPS
- [ ] Use HTTPS (Let's Encrypt)
- [ ] Restrict API access if needed
- [ ] Regular backups of database

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review configuration in `config/` files
3. Verify Supabase connection
4. Check GitHub issues

## Useful Commands

```bash
# Check if API is running
curl http://localhost:8000/health

# View API documentation
curl http://localhost:8000/docs

# Run tests
pytest tests/

# Build project
python setup.py build
```
