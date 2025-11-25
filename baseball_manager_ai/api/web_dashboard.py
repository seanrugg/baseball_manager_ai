"""
Web dashboard API for baseball manager AI.

Provides real-time dashboard with:
- Live game monitoring
- Player performance tracking
- Strategy recommendations
- Decision analytics
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import json
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

# Dashboard models
class DashboardMetrics(BaseModel):
    """Real-time dashboard metrics."""
    timestamp: datetime
    game_win_probability: float
    recommended_strategy: str
    player_performance: Dict[str, float]
    key_metrics: Dict[str, Any]
    alerts: List[str]

class Alert(BaseModel):
    """Dashboard alert."""
    id: str
    severity: str  # info, warning, critical
    message: str
    timestamp: datetime
    acknowledged: bool = False

class StrategyUpdate(BaseModel):
    """Strategy update from dashboard."""
    strategy_id: str
    new_strategy: str
    rationale: str
    user: str

class WebDashboard:
    """
    Web dashboard for real-time baseball management.
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8002):
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="Baseball Manager AI Dashboard",
            description="Real-time web dashboard for baseball management",
            version="1.0.0"
        )
        
        # WebSocket connections
        self.active_connections: List[WebSocket] = []
        self.dashboard_data: Dict[str, Any] = {}
        self.alerts: List[Alert] = []
        self.metric_history: List[DashboardMetrics] = []
        
        # Setup static files and CORS
        self._setup_middleware()
        self._setup_routes()
        self._initialize_sample_data()
        
        logger.info(f"Web dashboard initialized on {host}:{port}")
    
    def _setup_middleware(self):
        """Setup CORS and static files."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Create static directory
        static_dir = Path("static")
        static_dir.mkdir(exist_ok=True)
        
        # Serve static files
        self.app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    def _setup_routes(self):
        """Setup dashboard routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            """Serve main dashboard page."""
            return self._get_dashboard_html()
        
        @self.app.get("/dashboard")
        async def dashboard_data():
            """Get current dashboard data."""
            return {
                "metrics": self.dashboard_data,
                "alerts": [alert.dict() for alert in self.alerts if not alert.acknowledged],
                "history": self.metric_history[-50:]  # Last 50 data points
            }
        
        @self.app.get("/alerts")
        async def get_alerts(acknowledged: bool = False):
            """Get dashboard alerts."""
            return [alert.dict() for alert in self.alerts if alert.acknowledged == acknowledged]
        
        @self.app.post("/alerts/{alert_id}/acknowledge")
        async def acknowledge_alert(alert_id: str):
            """Acknowledge an alert."""
            for alert in self.alerts:
                if alert.id == alert_id:
                    alert.acknowledged = True
                    return {"status": "acknowledged"}
            raise HTTPException(status_code=404, detail="Alert not found")
        
        @self.app.post("/strategy/update")
        async def update_strategy(update: StrategyUpdate):
            """Update game strategy from dashboard."""
            # Broadcast strategy update to all connected clients
            await self._broadcast_strategy_update(update)
            
            # Log the update
            logger.info(f"Strategy updated by {update.user}: {update.new_strategy}")
            
            return {"status": "updated", "strategy_id": update.strategy_id}
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await self._handle_websocket_connection(websocket)
        
        @self.app.get("/metrics/history")
        async def get_metric_history(
            metric: str = Query(..., description="Metric name"),
            hours: int = Query(24, description="Hours of history")
        ):
            """Get historical metric data."""
            cutoff_time = datetime.now() - timedelta(hours=hours)
            filtered_data = [
                {
                    "timestamp": m.timestamp,
                    "value": m.key_metrics.get(metric, 0)
                }
                for m in self.metric_history
                if m.timestamp >= cutoff_time
            ]
            return filtered_data
        
        @self.app.get("/player/{player_id}/performance")
        async def get_player_performance(player_id: str):
            """Get player performance data."""
            # Mock implementation - replace with actual data
            return {
                "player_id": player_id,
                "recent_performance": {
                    "last_10_games": {
                        "batting_average": 0.285,
                        "ops": 0.832,
                        "home_runs": 3,
                        "rbi": 8
                    }
                },
                "trends": {
                    "batting_average": "improving",
                    "power": "stable"
                }
            }
    
    def _get_dashboard_html(self) -> str:
        """Generate dashboard HTML."""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Baseball Manager AI Dashboard</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .dashboard {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    max-width: 1200px;
                    margin: 0 auto;
                }
                .card {
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .metrics-grid {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 10px;
                }
                .metric {
                    text-align: center;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                .alert {
                    padding: 10px;
                    margin: 5px 0;
                    border-radius: 4px;
                    border-left: 4px solid;
                }
                .alert-warning {
                    background: #fff3cd;
                    border-color: #ffc107;
                }
                .alert-critical {
                    background: #f8d7da;
                    border-color: #dc3545;
                }
                .chart-container {
                    position: relative;
                    height: 200px;
                    width: 100%;
                }
            </style>
        </head>
        <body>
            <h1>Baseball Manager AI Dashboard</h1>
            <div class="dashboard">
                <div class="card">
                    <h2>Game Overview</h2>
                    <div id="gameOverview">
                        Loading game data...
                    </div>
                </div>
                
                <div class="card">
                    <h2>Win Probability</h2>
                    <div class="chart-container">
                        <canvas id="winProbabilityChart"></canvas>
                    </div>
                </div>
                
                <div class="card">
                    <h2>Strategy Recommendations</h2>
                    <div id="strategyRecommendations">
                        Loading strategies...
                    </div>
                </div>
                
                <div class="card">
                    <h2>Player Performance</h2>
                    <div class="chart-container">
                        <canvas id="performanceChart"></canvas>
                    </div>
                </div>
                
                <div class="card">
                    <h2>Alerts</h2>
                    <div id="alertsContainer">
                        Loading alerts...
                    </div>
                </div>
                
                <div class="card">
                    <h2>Real-time Metrics</h2>
                    <div class="metrics-grid" id="metricsGrid">
                        Loading metrics...
                    </div>
                </div>
            </div>

            <script>
                const ws = new WebSocket(`ws://${window.location.host}/ws`);
                let winProbabilityChart, performanceChart;

                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    updateDashboard(data);
                };

                function updateDashboard(data) {
                    // Update game overview
                    if (data.game_win_probability) {
                        document.getElementById('gameOverview').innerHTML = `
                            <p><strong>Win Probability:</strong> ${(data.game_win_probability * 100).toFixed(1)}%</p>
                            <p><strong>Recommended Strategy:</strong> ${data.recommended_strategy || 'N/A'}</p>
                        `;
                    }

                    // Update metrics grid
                    if (data.key_metrics) {
                        const metricsGrid = document.getElementById('metricsGrid');
                        metricsGrid.innerHTML = Object.entries(data.key_metrics)
                            .map(([key, value]) => `
                                <div class="metric">
                                    <strong>${key}</strong><br>
                                    ${typeof value === 'number' ? value.toFixed(3) : value}
                                </div>
                            `).join('');
                    }

                    // Update alerts
                    if (data.alerts) {
                        const alertsContainer = document.getElementById('alertsContainer');
                        alertsContainer.innerHTML = data.alerts.map(alert => `
                            <div class="alert alert-${alert.severity}">
                                ${alert.message}
                            </div>
                        `).join('');
                    }
                }

                // Initialize charts
                window.addEventListener('load', function() {
                    const winProbCtx = document.getElementById('winProbabilityChart').getContext('2d');
                    winProbabilityChart = new Chart(winProbCtx, {
                        type: 'line',
                        data: {
                            labels: [],
                            datasets: [{
                                label: 'Win Probability',
                                data: [],
                                borderColor: 'rgb(75, 192, 192)',
                                tension: 0.1
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false
                        }
                    });

                    const performanceCtx = document.getElementById('performanceChart').getContext('2d');
                    performanceChart = new Chart(performanceCtx, {
                        type: 'bar',
                        data: {
                            labels: ['OPS', 'BA', 'HR', 'RBI'],
                            datasets: [{
                                label: 'Player Performance',
                                data: [0.8, 0.25, 0, 0],
                                backgroundColor: 'rgba(54, 162, 235, 0.5)'
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false
                        }
                    });
                });

                // Fetch initial data
                fetch('/dashboard')
                    .then(response => response.json())
                    .then(data => updateDashboard(data.metrics));
            </script>
        </body>
        </html>
        """
    
    async def _handle_websocket_connection(self, websocket: WebSocket):
        """Handle WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        try:
            # Send initial data
            await websocket.send_json({
                "type": "initial_data",
                "data": self.dashboard_data
            })
            
            while True:
                # Keep connection alive and handle incoming messages
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif message.get("type") == "strategy_update":
                    # Handle strategy updates from client
                    await self._handle_client_strategy_update(message)
                    
        except WebSocketDisconnect:
            self.active_connections.remove(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            self.active_connections.remove(websocket)
    
    async def _broadcast_strategy_update(self, update: StrategyUpdate):
        """Broadcast strategy update to all connected clients."""
        message = {
            "type": "strategy_update",
            "data": update.dict()
        }
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.active_connections.remove(connection)
    
    async def _handle_client_strategy_update(self, message: dict):
        """Handle strategy update from client."""
        # This would typically validate and process the strategy update
        logger.info(f"Received strategy update: {message}")
    
    def _initialize_sample_data(self):
        """Initialize sample dashboard data."""
        self.dashboard_data = {
            "game_win_probability": 0.65,
            "recommended_strategy": "aggressive_baserunning",
            "player_performance": {
                "player_001": 0.85,
                "player_002": 0.72,
                "player_003": 0.91
            },
            "key_metrics": {
                "run_expectancy": 0.483,
                "wpa": 0.034,
                "leverage_index": 1.2,
                "defensive_efficiency": 0.712
            }
        }
        
        # Add sample alerts
        self.alerts = [
            Alert(
                id=str(uuid.uuid4()),
                severity="warning",
                message="High leverage situation: consider bullpen change",
                timestamp=datetime.now() - timedelta(minutes=5)
            ),
            Alert(
                id=str(uuid.uuid4()),
                severity="info", 
                message="Opponent bringing in left-handed reliever",
                timestamp=datetime.now() - timedelta(minutes=2)
            )
        ]
    
    def update_metrics(self, metrics: DashboardMetrics):
        """Update dashboard metrics (called from external systems)."""
        self.metric_history.append(metrics)
        self.dashboard_data.update(metrics.dict())
        
        # Broadcast update to all connected clients
        asyncio.create_task(self._broadcast_metrics_update(metrics))
    
    async def _broadcast_metrics_update(self, metrics: DashboardMetrics):
        """Broadcast metrics update to all connected clients."""
        message = {
            "type": "metrics_update",
            "data": metrics.dict()
        }
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.active_connections.remove(connection)
    
    def add_alert(self, alert: Alert):
        """Add a new alert to the dashboard."""
        self.alerts.append(alert)
        
        # Broadcast alert to all connected clients
        asyncio.create_task(self._broadcast_alert(alert))
    
    async def _broadcast_alert(self, alert: Alert):
        """Broadcast alert to all connected clients."""
        message = {
            "type": "alert",
            "data": alert.dict()
        }
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.active_connections.remove(connection)
    
    def run(self, reload: bool = False):
        """Run the web dashboard."""
        import uvicorn
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            reload=reload,
            log_level="info"
        )


# Example usage
if __name__ == "__main__":
    dashboard = WebDashboard()
    
    # Example: Simulate real-time updates
    async def simulate_updates():
        import random
        while True:
            await asyncio.sleep(10)  # Update every 10 seconds
            
            metrics = DashboardMetrics(
                timestamp=datetime.now(),
                game_win_probability=random.uniform(0.3, 0.8),
                recommended_strategy=random.choice(["aggressive", "conservative", "balanced"]),
                player_performance={"player_001": random.uniform(0.6, 0.95)},
                key_metrics={
                    "run_expectancy": random.uniform(0.4, 0.6),
                    "wpa": random.uniform(-0.1, 0.1),
                    "leverage_index": random.uniform(0.5, 2.0)
                },
                alerts=[]
            )
            
            dashboard.update_metrics(metrics)
    
    # Start simulation in background
    asyncio.create_task(simulate_updates())
    
    dashboard.run()
