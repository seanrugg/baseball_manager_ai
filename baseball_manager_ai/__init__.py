"""
Baseball Manager AI
⚾🤖 AI-powered baseball management assistant

A comprehensive toolkit for data-driven baseball decision making,
including lineup optimization, in-game strategy, and player management.
"""

__version__ = "0.1.0"
__author__ = "Baseball Manager AI Team"
__email__ = "your.email@example.com"

from baseball_manager_ai.data_processing import *
from baseball_manager_ai.models import *
from baseball_manager_ai.simulation import *
from baseball_manager_ai.utils import *

# Core exports
__all__ = [
    "LineupOptimizer",
    "InGameDecider", 
    "PitchingManager",
    "GameSimulator",
    "WinProbability",
    "RunExpectancy",
]
