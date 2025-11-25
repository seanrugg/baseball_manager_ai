"""
Data ingestion API for baseball data sources.

Handles data collection from:
- MLB Stats API
- Baseball Reference
- Retrosheet
- Real-time game feeds
- Custom data sources
"""

import logging
import asyncio
import aiohttp
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
import json
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

# Data models
class DataSourceConfig(BaseModel):
    """Configuration for data sources."""
    name: str
    endpoint: str
    api_key: Optional[str] = None
    rate_limit: int = Field(default=10, description="Requests per minute")
    enabled: bool = True

class IngestionRequest(BaseModel):
    """Request model for data ingestion."""
    data_source: str
    start_date: str
    end_date: str
    data_types: List[str] = Field(..., description="Types of data to ingest")
    team_filter: Optional[List[str]] = None
    player_filter: Optional[List[str]] = None

class IngestionStatus(BaseModel):
    """Ingestion job status."""
    job_id: str
    status: str  # running, completed, failed
    progress: float = Field(..., ge=0, le=1)
    records_processed: int
    error_message: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None

class DataIngestionAPI:
    """
    API for ingesting baseball data from various sources.
    """
    
    def __init__(self, db_path: str = "data/baseball.db"):
        self.app = FastAPI(
            title="Baseball Data Ingestion API",
            description="API for collecting and processing baseball data",
            version="1.0.0"
        )
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.data_sources: Dict[str, DataSourceConfig] = {}
        self.ingestion_jobs: Dict[str, IngestionStatus] = {}
        
        self._setup_database()
        self._setup_routes()
        self._register_default_sources()
        
        logger.info("Data ingestion API initialized")
    
    def _setup_database(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_data (
                game_id TEXT PRIMARY KEY,
                date TEXT,
                home_team TEXT,
                away_team TEXT,
                home_score INTEGER,
                away_score INTEGER,
                stadium TEXT,
                attendance INTEGER,
                data_source TEXT,
                ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_stats (
                player_id TEXT,
                game_id TEXT,
                team TEXT,
                position TEXT,
                at_bats INTEGER,
                hits INTEGER,
                runs INTEGER,
                rbi INTEGER,
                home_runs INTEGER,
                walks INTEGER,
                strikeouts INTEGER,
                ops REAL,
                data_source TEXT,
                ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (player_id, game_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pitching_stats (
                pitcher_id TEXT,
                game_id TEXT,
                team TEXT,
                innings_pitched REAL,
                hits_allowed INTEGER,
                runs_allowed INTEGER,
                earned_runs INTEGER,
                walks INTEGER,
                strikeouts INTEGER,
                home_runs_allowed INTEGER,
                era REAL,
                data_source TEXT,
                ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (pitcher_id, game_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ingestion_logs (
                job_id TEXT PRIMARY KEY,
                data_source TEXT,
                start_date TEXT,
                end_date TEXT,
                records_processed INTEGER,
                status TEXT,
                error_message TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/")
        async def root():
            return {
                "message": "Baseball Data Ingestion API",
                "version": "1.0.0",
                "data_sources": list(self.data_sources.keys())
            }
        
        @self.app.post("/ingest")
        async def ingest_data(request: IngestionRequest, background_tasks: BackgroundTasks):
            """Start data ingestion job."""
            if request.data_source not in self.data_sources:
                raise HTTPException(status_code=400, detail="Unknown data source")
            
            job_id = f"ingest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            job_status = IngestionStatus(
                job_id=job_id,
                status="running",
                progress=0.0,
                records_processed=0,
                start_time=datetime.now()
            )
            
            self.ingestion_jobs[job_id] = job_status
            
            # Start background ingestion task
            background_tasks.add_task(
                self._run_ingestion_job,
                job_id,
                request
            )
            
            return {"job_id": job_id, "status": "started"}
        
        @self.app.get("/ingestion_status/{job_id}")
        async def get_ingestion_status(job_id: str):
            """Get ingestion job status."""
            if job_id not in self.ingestion_jobs:
                raise HTTPException(status_code=404, detail="Job not found")
            
            return self.ingestion_jobs[job_id]
        
        @self.app.get("/sources")
        async def list_data_sources():
            """List available data sources."""
            return {
                "sources": {
                    name: {
                        "endpoint": config.endpoint,
                        "enabled": config.enabled,
                        "rate_limit": config.rate_limit
                    }
                    for name, config in self.data_sources.items()
                }
            }
        
        @self.app.post("/sources")
        async def register_data_source(config: DataSourceConfig):
            """Register a new data source."""
            self.data_sources[config.name] = config
            return {"status": "registered", "source": config.name}
        
        @self.app.get("/data/games")
        async def get_game_data(
            start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
            end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
            team: Optional[str] = None
        ):
            """Retrieve game data from database."""
            try:
                conn = sqlite3.connect(self.db_path)
                
                query = """
                    SELECT * FROM game_data 
                    WHERE date BETWEEN ? AND ?
                """
                params = [start_date, end_date]
                
                if team:
                    query += " AND (home_team = ? OR away_team = ?)"
                    params.extend([team, team])
                
                df = pd.read_sql_query(query, conn, params=params)
                conn.close()
                
                return df.to_dict('records')
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/data/players")
        async def get_player_stats(
            player_id: Optional[str] = None,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None
        ):
            """Retrieve player statistics."""
            try:
                conn = sqlite3.connect(self.db_path)
                
                query = "SELECT * FROM player_stats WHERE 1=1"
                params = []
                
                if player_id:
                    query += " AND player_id = ?"
                    params.append(player_id)
                
                if start_date and end_date:
                    query += " AND game_id IN (SELECT game_id FROM game_data WHERE date BETWEEN ? AND ?)"
                    params.extend([start_date, end_date])
                
                df = pd.read_sql_query(query, conn, params=params)
                conn.close()
                
                return df.to_dict('records')
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    def _register_default_sources(self):
        """Register default data sources."""
        default_sources = [
            DataSourceConfig(
                name="mlb_stats",
                endpoint="http://statsapi.mlb.com/api/v1/",
                rate_limit=20
            ),
            DataSourceConfig(
                name="baseball_reference",
                endpoint="https://www.baseball-reference.com/",
                rate_limit=5
            ),
            DataSourceConfig(
                name="retrosheet",
                endpoint="https://www.retrosheet.org/",
                rate_limit=10
            )
        ]
        
        for source in default_sources:
            self.data_sources[source.name] = source
    
    async def _run_ingestion_job(self, job_id: str, request: IngestionRequest):
        """Run data ingestion job in background."""
        try:
            logger.info(f"Starting ingestion job {job_id} for {request.data_source}")
            
            # Update job status
            self.ingestion_jobs[job_id].status = "running"
            self.ingestion_jobs[job_id].progress = 0.1
            
            # Simulate data ingestion (replace with actual implementation)
            await asyncio.sleep(2)  # Simulate API calls
            
            records_processed = await self._ingest_from_source(request)
            
            # Update completion status
            self.ingestion_jobs[job_id].status = "completed"
            self.ingestion_jobs[job_id].progress = 1.0
            self.ingestion_jobs[job_id].records_processed = records_processed
            self.ingestion_jobs[job_id].end_time = datetime.now()
            
            # Log to database
            self._log_ingestion(job_id, request, records_processed, "completed")
            
            logger.info(f"Completed ingestion job {job_id}: {records_processed} records")
            
        except Exception as e:
            logger.error(f"Ingestion job {job_id} failed: {e}")
            
            self.ingestion_jobs[job_id].status = "failed"
            self.ingestion_jobs[job_id].error_message = str(e)
            self.ingestion_jobs[job_id].end_time = datetime.now()
            
            self._log_ingestion(job_id, request, 0, "failed", str(e))
    
    async def _ingest_from_source(self, request: IngestionRequest) -> int:
        """Ingest data from specified source."""
        # TODO: Implement actual data ingestion logic
        # This is a mock implementation
        
        if request.data_source == "mlb_stats":
            return await self._ingest_mlb_stats(request)
        elif request.data_source == "baseball_reference":
            return await self._ingest_baseball_reference(request)
        elif request.data_source == "retrosheet":
            return await self._ingest_retrosheet(request)
        else:
            raise ValueError(f"Unsupported data source: {request.data_source}")
    
    async def _ingest_mlb_stats(self, request: IngestionRequest) -> int:
        """Ingest data from MLB Stats API."""
        # Mock implementation - replace with actual API calls
        mock_data = [
            {
                "game_id": "2023_001",
                "date": "2023-03-30",
                "home_team": "NYY",
                "away_team": "BOS", 
                "home_score": 5,
                "away_score": 3,
                "stadium": "Yankee Stadium",
                "attendance": 45000
            }
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for game in mock_data:
            cursor.execute('''
                INSERT OR REPLACE INTO game_data 
                (game_id, date, home_team, away_team, home_score, away_score, stadium, attendance, data_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                game['game_id'], game['date'], game['home_team'], game['away_team'],
                game['home_score'], game['away_score'], game['stadium'], 
                game['attendance'], 'mlb_stats'
            ))
        
        conn.commit()
        conn.close()
        
        return len(mock_data)
    
    async def _ingest_baseball_reference(self, request: IngestionRequest) -> int:
        """Ingest data from Baseball Reference."""
        # TODO: Implement web scraping or use their API
        return 0
    
    async def _ingest_retrosheet(self, request: IngestionRequest) -> int:
        """Ingest data from Retrosheet."""
        # TODO: Implement Retrosheet data parsing
        return 0
    
    def _log_ingestion(self, job_id: str, request: IngestionRequest, 
                      records_processed: int, status: str, error_message: str = None):
        """Log ingestion job to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ingestion_logs 
            (job_id, data_source, start_date, end_date, records_processed, status, error_message, start_time, end_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            job_id, request.data_source, request.start_date, request.end_date,
            records_processed, status, error_message, 
            self.ingestion_jobs[job_id].start_time,
            self.ingestion_jobs[job_id].end_time
        ))
        
        conn.commit()
        conn.close()


if __name__ == "__main__":
    import uvicorn
    
    ingestion_api = DataIngestionAPI()
    uvicorn.run(ingestion_api.app, host="0.0.0.0", port=8001)
