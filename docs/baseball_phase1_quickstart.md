# Phase 1: Data Collection & Foundation - Quick Start

## Overview

Phase 1 establishes the data infrastructure and foundational models for your Baseball Manager AI. This phase focuses on:

1. **Data Collection** - Gathering Statcast, Retrosheet, and player stats
2. **Data Modeling** - Creating robust data structures for game state and analytics
3. **Data Validation** - Ensuring data quality and consistency
4. **Feature Engineering** - Building inputs for machine learning models

## Installation

### Prerequisites
- Python 3.9+
- pip or conda
- ~50GB disk space for historical data

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/baseball_manager_ai.git
cd baseball_manager_ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run Phase 1 setup
python scripts/setup_phase1.py
```

## Core Data Models

### GameState

The central model representing the current state of a baseball game:

```python
from baseball_manager_ai.core.data_models import GameState, HandednessType

# Create a game state
state = GameState(
    game_id="gid_2024_08_15_nynmlb_bosalb_1",
    date=datetime.now(),
    home_team="BOS",
    away_team="NYY",
    inning=5,
    outs=1,
    score=[2, 1],
    bases=[True, False, True],  # Runners on 1st and 3rd
    count=(1, 1),               # 1 ball, 1 strike
    batter_hand=HandednessType.LEFT,
    pitcher_hand=HandednessType.RIGHT,
    batter_id="troutm001",
    pitcher_id="kershc001"
)

# Useful methods
state.get_bases_occupied()     # Returns "1-3"
state.get_runners_on_base()    # Returns 2
state.get_base_state_index()   # Returns 5 (for lookup tables)
state.to_dict()                # Serialize for storage
```

### BatterStats & PitcherStats

Individual player performance data:

```python
from baseball_manager_ai.core.data_models import BatterStats, PitcherStats

# Batter statistics
batter = BatterStats(
    player_id="troutm001",
    name="Mike Trout",
    hand=HandednessType.RIGHT,
    career_avg=0.305,
    season_avg=0.310,
    vs_lhp_avg=0.298,  # vs Left-handed pitchers
    vs_rhp_avg=0.315,  # vs Right-handed pitchers
    risp_avg=0.328,    # Runners in scoring position
    late_close_avg=0.301,
    strikeout_rate=0.195,
    walk_rate=0.085,
    barrel_rate=0.089,
    avg_exit_velocity=91.2,
    position=DefensivePosition.CENTER_FIELD
)

# Pitcher statistics
pitcher = PitcherStats(
    player_id="kershc001",
    name="Clayton Kershaw",
    hand=HandednessType.LEFT,
    role="starter",
    season_era=3.45,
    season_k9=9.2,
    season_bb9=1.8,
    pitch_types=["4-seam", "slider", "curveball", "changeup"],
    vs_lhb_era=4.12,   # vs Left-handed batters
    vs_rhb_era=3.01,   # vs Right-handed batters
    days_rest=3,
    pitch_count_today=87,
    is_injured=False
)
```

## Data Sources

### 1. Statcast Data (Pitch-by-Pitch)

Download from Baseball Savant or use pybaseball library:

```python
from baseball_manager_ai.data_processing.data_loaders import StatcastLoader
from pathlib import Path

# Load Statcast data for a season
data_dir = Path("data/raw/statcast")
statcast_df = StatcastLoader.load_season(data_dir, season=2024)

# Extract play outcomes
from baseball_manager_ai.core.data_models import PlayOutcome
outcomes = StatcastLoader.extract_play_outcomes(statcast_df)

print(f"Loaded {len(outcomes)} plays from 2024")
```

**Key columns:**
- `game_pk` - Game ID
- `inning`, `outs_when_up` - Game state
- `pitcher`, `batter` - Player IDs
- `release_speed`, `exit_velocity` - Physical metrics
- `events`, `description` - Outcome

### 2. Retrosheet Data (Game Logs)

Historical game-level data and manager decisions:

```python
from baseball_manager_ai.data_processing.data_loaders import RetroSheetParser

# Load game logs
game_logs = RetroSheetParser.load_game_log(
    Path("data/raw/retrosheet/gamelogs_2024.csv")
)

# Access manager IDs, game results, attendance
print(game_logs[['date', 'away_team', 'home_team', 'away_manager', 'home_manager']])
```

### 3. Player Stats

Load batter and pitcher statistics:

```python
from baseball_manager_ai.data_processing.data_loaders import PlayerStatsLoader

# Load player statistics
batter_stats = PlayerStatsLoader.load_batter_stats(
    Path("data/raw/baseball_reference/batters_2024.csv")
)

pitcher_stats = PlayerStatsLoader.load_pitcher_stats(
    Path("data/raw/baseball_reference/pitchers_2024.csv")
)

# Access individual player
mike_trout = batter_stats.get("troutm001")
if mike_trout:
    print(f"{mike_trout.name}: .{int(mike_trout.season_avg*1000)}")
```

## Data Validation

Ensure data integrity before processing:

```python
from baseball_manager_ai.data_processing.data_loaders import DataValidator

# Validate game state
state = GameState(inning=5, outs=2, bases=[True, False, True])
is_valid, errors = DataValidator.validate_game_state(state)

if not is_valid:
    print(f"Validation errors: {errors}")

# Validate Statcast data
valid, errors = DataValidator.validate_statcast(statcast_df)
if not valid:
    for error in errors:
        print(f"ERROR: {error}")
```

## File Structure After Phase 1

```
baseball_manager_ai/
├── core/
│   └── data_models.py          # GameState, BatterStats, etc.
├── data_processing/
│   ├── data_loaders.py         # Statcast, Retrosheet parsers
│   └── data_validators.py      # Data quality checks
├── data/
│   ├── raw/
│   │   ├── statcast/           # Pitch-by-pitch CSVs
│   │   ├── retrosheet/         # Game logs
│   │   └── baseball_reference/ # Player stats
│   ├── processed/
│   │   ├── training_examples/
│   │   └── feature_sets/
│   └── manifest.json           # Data inventory
├── config/
│   ├── data_sources.yaml       # Data endpoints
│   └── data_processing_config.yaml
└── scripts/
    ├── setup_phase1.py         # Initial setup
    └── download_data.py        # Data acquisition
```

## Common Tasks

### Load and Explore Statcast Data

```python
import pandas as pd
from baseball_manager_ai.data_processing.data_loaders import StatcastLoader

# Load data
df = StatcastLoader.load_season(Path("data/raw/statcast"), 2024)

# Explore
print(f"Loaded {len(df)} pitches")
print(f"Columns: {df.columns.tolist()}")

# Filter to specific matchup
trout_vs_kershaw = df[
    (df['batter'] == 545361) & (df['pitcher'] == 477132)
]
print(f"Trout vs Kershaw: {len(trout_vs_kershaw)} at-bats")

# Exit velocity analysis
exit_velos = df['exit_velocity'].dropna()
print(f"Average exit velocity: {exit_velos.mean():.1f} mph")
```

### Create a Test Game State

```python
from baseball_manager_ai.core.data_models import (
    GameState, HandednessType, Weather, DefensiveAlignment
)

# Create realistic game scenario
state = GameState(
    game_id="test_game_001",
    date=datetime(2024, 8, 15),
    home_team="BOS",
    away_team="NYY",
    inning=9,
    outs=2,
    score=[2, 2],  # Tied in 9th
    bases=[False, True, True],  # Runners on 2nd and 3rd
    count=(1, 2),  # 1-2 count
    batter_hand=HandednessType.RIGHT,
    pitcher_hand=HandednessType.RIGHT,
    batter_id="troutm001",
    pitcher_id="rosim002",
    ballpark="Fenway Park",
    weather=Weather(
        temperature=75.0,
        wind_speed=12.0,
        wind_direction="SW",
        precipitation=0.0,
        sky_condition="Clear",
        humidity=65.0
    ),
    game_importance=0.95  # Late-inning, tied game
)

# Use the state
print(f"Inning {state.inning}, {state.outs} outs")
print(f"Score: Home {state.score[0]}, Away {state.score[1]}")
print(f"Bases: {state.get_bases_occupied()}")
print(f"Base state index (for lookups): {state.get_base_state_index()}")
```

### Validate and Clean Data

```python
from baseball_manager_ai.data_processing.data_loaders import (
    StatcastLoader, DataValidator
)

# Load raw data
df = StatcastLoader.load_season(Path("data/raw/statcast"), 2024)

# Validate
valid, errors = DataValidator.validate_statcast(df)

if valid:
    print("✓ Statcast data passes validation")
else:
    print("Validation errors:")
    for error in errors:
        print(f"  - {error}")

# Summary statistics
print(f"\nData Summary:")
print(f"  Pitches: {len(df)}")
print(f"  Unique games: {df['game_pk'].nunique()}")
print(f"  Missing exit velocity: {df['exit_velocity'].isna().sum()} ({df['exit_velocity'].isna().sum()/len(df)*100:.1f}%)")
```

## Next Phase

Phase 2 will focus on:
- Feature engineering (matchup metrics, situational factors)
- Building win probability models
- Creating run expectancy matrices
- Training baseline decision models

## Resources

- **Baseball Savant**: https://baseballsavant.mlb.com/statcast
- **Retrosheet**: https://www.retrosheet.org/
- **MLB Stats API**: https://statsapi.mlb.com/api/v1
- **pybaseball**: https://github.com/jldbc/pybaseball
- **Baseball Stats Glossary**: https://www.baseball-reference.com/about/glossary.html

## Troubleshooting

**Issue**: "Statcast data not found"
- Solution: Download from Baseball Savant or use `scripts/download_data.py`

**Issue**: "Invalid column error"
- Solution: Ensure CSV has all required columns; check `data_sources.yaml`

**Issue**: Memory error loading large datasets
- Solution: Process by season; use `dtype` optimization in pandas

## Support

For issues or questions:
1. Check data/manifest.json for data inventory
2. Review logs/ directory for processing errors
3. Validate data with DataValidator class
