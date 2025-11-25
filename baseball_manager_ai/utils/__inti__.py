"""
Baseball Manager AI - Utils Package

Utilities and calculations:
- Baseball constants and definitions
- Win probability models
- Run expectancy matrices
- Visualization tools
"""

from .baseball_constants import (
    TEAMS,
    POSITIONS,
    PLAYER_ROLES,
    DECISION_TYPES,
    GAME_STATES,
    BASE_STATES,
    get_base_state_name,
    get_position_name
)

from .win_probability import (
    WinProbabilityModel,
    calculate_win_probability,
    calculate_leverage_index
)

from .run_expectancy import (
    RunExpectancyMatrix,
    get_expected_runs,
    calculate_wpa
)

from .visualization import (
    plot_game_timeline,
    plot_win_probability_chart,
    plot_decision_comparison,
    plot_lineup_heatmap
)

__all__ = [
    # Constants
    'TEAMS',
    'POSITIONS',
    'PLAYER_ROLES',
    'DECISION_TYPES',
    'GAME_STATES',
    'BASE_STATES',
    'get_base_state_name',
    'get_position_name',
    
    # Win Probability
    'WinProbabilityModel',
    'calculate_win_probability',
    'calculate_leverage_index',
    
    # Run Expectancy
    'RunExpectancyMatrix',
    'get_expected_runs',
    'calculate_wpa',
    
    # Visualization
    'plot_game_timeline',
    'plot_win_probability_chart',
    'plot_decision_comparison',
    'plot_lineup_heatmap',
]

__version__ = '0.1.0'
