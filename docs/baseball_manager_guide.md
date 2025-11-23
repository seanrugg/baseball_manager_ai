# Baseball Manager AI - Project Guide

## Project Overview

A comprehensive AI system for baseball game management, combining historical data analysis, machine learning models, and game simulation to optimize in-game decisions.

## Directory Structure Explained

### Core Components

**data/** - Data pipeline and storage
- `raw/` - Original data from Statcast, Retrosheet, and manual annotations
- `processed/` - Clean training data, features, and embeddings
- `external/` - Real-time APIs (MLB StatsAPI, Baseball Reference)

**baseball_manager_ai/** - Main Python package
- `data_processing/` - ETL: loading, parsing, validation, feature engineering
- `models/` - Decision-making models (lineup, in-game, pitching)
- `simulation/` - Game simulation engines for strategy evaluation
- `utils/` - Baseball-specific calculations (win probability, run expectancy)
- `api/` - Flask/FastAPI server, dashboards, data endpoints

**Infrastructure**
- `.github/workflows/` - CI/CD pipelines (tests, training, licensing)
- `tests/` - Unit and integration tests
- `config/` - YAML configurations for models and data sources
- `scripts/` - Standalone runners for download, training, simulation
- `notebooks/` - Jupyter notebooks for exploration and analysis

## Key Responsibilities by Module

| Module | Purpose |
|--------|---------|
| **statcast_loader.py** | Parse and normalize Statcast CSV data (pitch-by-pitch) |
| **retrosheet_parser.py** | Process Retrosheet play-by-play and game logs |
| **feature_engineering.py** | Create batter/pitcher/team features for ML models |
| **lineup_optimizer.py** | Optimize batting order given player matchups |
| **in_game_decider.py** | Real-time decisions (steal, bunt, relief, etc.) |
| **pitching_manager.py** | Pitcher selection and rotation management |
| **game_simulator.py** | Monte Carlo simulation engine for game outcomes |
| **win_probability.py** | Calculate WPA (Win Probability Added) |
| **run_expectancy.py** | Pre-computed run expectancy matrices |

## Data Flow

```
Raw Data Sources
    ↓
[statcast_loader, retrosheet_parser]
    ↓
feature_engineering.py
    ↓
Data Validation
    ↓
ML Models Training
    ↓
Simulation & Evaluation
    ↓
API Server / Dashboard
```

## Getting Started

### 1. Setup Environment
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Download Data
```bash
python scripts/download_data.py --sources statcast retrosheet --season 2024
```

### 3. Train Models
```bash
python scripts/train_model.py --config config/training_config.yaml
```

### 4. Run Simulations
```bash
python scripts/run_simulation.py --team "New York Yankees" --games 1000
```

### 5. Launch API
```bash
python -m baseball_manager_ai.api.model_server
```

## Configuration Files

- **model_config.yaml** - Model hyperparameters, architectures
- **training_config.yaml** - Learning rate, batch size, epochs, validation split
- **simulation_config.yaml** - Monte Carlo iterations, park factors
- **data_sources.yaml** - API credentials, data paths, update schedules

## Testing Strategy

- `test_data_processing.py` - Data loading and transformation tests
- `test_models.py` - Model inference and decision logic
- `test_simulation.py` - Simulation engine correctness
- `test_integration.py` - End-to-end workflows

Run tests: `pytest tests/ -v`

## Development Workflow

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and write tests
3. Run CI checks: `pytest`, `mypy`, `black`
4. Submit PR for review
5. Merge to main → triggers model retraining workflow

## Deployment

See `docs/deployment_guide.md` for containerization with Docker and cloud deployment options.

## Key ML Concepts

- **Win Probability (WP)** - Probability team wins given game state
- **Run Expectancy (RE)** - Expected runs scored from current base state
- **Decision Trees** - Optimal moves under uncertainty
- **Ensemble Methods** - Combine multiple models for robustness
- **Monte Carlo** - Simulate thousands of game scenarios

## Next Steps

1. Populate `data/raw/` with Statcast/Retrosheet CSVs
2. Implement data loaders in `data_processing/`
3. Build feature engineering pipeline
4. Train baseline models
5. Create simulation evaluation framework
6. Deploy API with dashboard
