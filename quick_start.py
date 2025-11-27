#!/usr/bin/env python
"""
Quick Start Script for Baseball Manager AI

This script helps you get started by:
1. Checking dependencies
2. Verifying configuration
3. Setting up the database
4. Creating sample data for testing
"""

import sys
import os
from pathlib import Path
import subprocess

def check_dependencies():
    """Check if required packages are installed."""
    print("Checking dependencies...")

    required_packages = [
        'numpy', 'pandas', 'scikit-learn', 'fastapi',
        'uvicorn', 'pyyaml'
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (missing)")
            missing.append(package)

    if missing:
        print(f"\nInstall missing packages with:")
        print(f"  pip install {' '.join(missing)}")
        return False

    print("✓ All dependencies installed\n")
    return True

def check_config():
    """Check if configuration files exist."""
    print("Checking configuration...")

    config_files = [
        'config/model_config.yaml',
        'config/training_config.yaml',
        'config/simulation_config.yaml',
        'config/data_sources.yaml'
    ]

    all_exist = True
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"  ✓ {config_file}")
        else:
            print(f"  ✗ {config_file} (missing)")
            all_exist = False

    if all_exist:
        print("✓ All configuration files present\n")
    else:
        print("✗ Some configuration files missing\n")

    return all_exist

def check_env():
    """Check environment variables."""
    print("Checking environment variables...")

    env_file = Path('.env')
    if not env_file.exists():
        print("  ⚠ .env file not found")
        print("  Copy .env.example to .env and fill in your Supabase credentials:")
        print("    cp .env.example .env")
        print("")
        return False

    print("  ✓ .env file exists")

    # Check for required variables
    from dotenv import load_dotenv
    load_dotenv()

    required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
    missing = []

    for var in required_vars:
        if os.getenv(var):
            print(f"  ✓ {var} set")
        else:
            print(f"  ✗ {var} not set")
            missing.append(var)

    if missing:
        print(f"\n  Set these variables in your .env file\n")
        return False

    print("✓ Environment configured\n")
    return True

def create_sample_data():
    """Create sample data for testing."""
    print("Creating sample data...")

    import pandas as pd
    import numpy as np

    # Create sample player data
    players = pd.DataFrame({
        'player_id': [f'player_{i:03d}' for i in range(1, 21)],
        'name': [f'Player {i}' for i in range(1, 21)],
        'position': np.random.choice(['P', 'C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF'], 20),
        'season_avg': np.random.uniform(0.200, 0.350, 20),
        'season_ops': np.random.uniform(0.600, 0.950, 20),
        'season_era': np.where(
            np.random.choice(['P', 'C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF'], 20) == 'P',
            np.random.uniform(2.5, 5.0, 20),
            np.nan
        )
    })

    # Save to data directory
    data_dir = Path('data/processed')
    data_dir.mkdir(parents=True, exist_ok=True)

    players.to_csv(data_dir / 'sample_players.csv', index=False)
    print(f"  ✓ Created sample player data ({len(players)} players)")

    # Create sample training data
    training_data = pd.DataFrame({
        'feature_1': np.random.randn(100),
        'feature_2': np.random.randn(100),
        'feature_3': np.random.randn(100),
        'target': np.random.choice([0, 1], 100)
    })

    training_dir = data_dir / 'training_examples'
    training_dir.mkdir(parents=True, exist_ok=True)

    training_data.to_csv(training_dir / 'examples.csv', index=False)
    print(f"  ✓ Created sample training data ({len(training_data)} examples)")

    print("✓ Sample data created\n")
    return True

def print_next_steps():
    """Print next steps for the user."""
    print("=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("""
1. Configure your environment:
   - Copy .env.example to .env
   - Add your Supabase credentials to .env

2. Set up the database:
   - Create tables in Supabase for games, players, decisions
   - Use the Supabase dashboard or CLI

3. Test the API:
   - Run: python -m baseball_manager_ai.api.model_server
   - Visit: http://localhost:8000/health

4. Download real data (optional):
   - python scripts/download_data.py --sources statcast --seasons 2024

5. Train models (after getting data):
   - python scripts/train_model.py --model all

6. Run simulations:
   - python scripts/run_simulation.py --home-team NYY --away-team BOS --games 100

For more information, check the README.md file.
""")

def main():
    """Main entry point."""
    print("=" * 60)
    print("BASEBALL MANAGER AI - QUICK START")
    print("=" * 60)
    print()

    # Run checks
    deps_ok = check_dependencies()
    config_ok = check_config()

    # Try to check env (may fail if python-dotenv not installed)
    try:
        env_ok = check_env()
    except ImportError:
        print("⚠ python-dotenv not installed (optional)")
        print("  Install with: pip install python-dotenv")
        env_ok = False

    # Create sample data
    sample_ok = create_sample_data()

    # Print status
    print("=" * 60)
    print("SETUP STATUS")
    print("=" * 60)
    print(f"Dependencies:   {'✓' if deps_ok else '✗'}")
    print(f"Configuration:  {'✓' if config_ok else '✗'}")
    print(f"Environment:    {'✓' if env_ok else '⚠'}")
    print(f"Sample Data:    {'✓' if sample_ok else '✗'}")
    print()

    if deps_ok and config_ok:
        print("✓ Basic setup complete!")
        print_next_steps()
    else:
        print("✗ Setup incomplete. Please address the issues above.")
        sys.exit(1)

if __name__ == '__main__':
    main()
