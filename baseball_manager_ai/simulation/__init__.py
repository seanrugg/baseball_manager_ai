"""
Baseball Manager AI - Simulation Package

Game simulation and strategy evaluation:
- Complete game simulation
- Decision evaluation and outcome tracking
- Monte Carlo scenario analysis
"""

from .game_simulator import GameSimulator
from .decision_evaluator import DecisionEvaluator
from .monte_carlo import MonteCarloSimulator

__all__ = [
    'GameSimulator',
    'DecisionEvaluator',
    'MonteCarloSimulator',
]

__version__ = '0.1.0'
