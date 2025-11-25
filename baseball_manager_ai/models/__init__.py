"""
Baseball Manager AI - Models Package

Machine learning models for baseball decision making:
- Lineup optimization
- In-game tactical decisions
- Pitching management
- Ensemble predictions
"""

from .base_manager import BaseManager
from .lineup_optimizer import LineupOptimizer
from .in_game_decider import InGameDecider
from .pitching_manager import PitchingManager
from .ensemble import EnsembleManager

__all__ = [
    'BaseManager',
    'LineupOptimizer',
    'InGameDecider',
    'PitchingManager',
    'EnsembleManager',
]

__version__ = '0.1.0'
