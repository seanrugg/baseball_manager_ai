# Baseball Manager AI ⚾🤖

[![Apache License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

An AI-powered assistant for baseball team management, providing data-driven recommendations for lineups, in-game strategy, and player management.

## Features

- **📊 Lineup Optimization**: Generate optimal batting orders based on matchups and analytics
- **🎯 In-Game Decision Support**: Real-time recommendations for substitutions, bunts, steals, etc.
- **⚡ Pitching Management**: Bullpen usage optimization and starter management  
- **🧪 Simulation Engine**: Test strategies through game simulation
- **📈 Performance Analytics**: Track decision quality and strategy effectiveness

## Quick Start

```bash
# Clone repository
git clone https://github.com/seanrugg/baseball_manager_ai
cd baseball_manager_ai

# Install package
pip install -e .

# Download sample data
python scripts/download_data.py

# Train initial model
python scripts/train_model.py

# Start web dashboard
streamlit run src/api/web_dashboard.py
