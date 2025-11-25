"""
Win Probability utilities and models.

Calculate win probability from game state using empirical data
and statistical models.
"""

import logging
import numpy as np
from typing import Tuple, Optional, Dict
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)


class WinProbabilityModel:
    """
    Win probability model based on game state.
    
    Uses historical MLB data to estimate probability that home team wins
    from any given game state.
    """
    
    # Pre-computed Win Probability lookup table
    # [inning-1, outs, score_diff + 10] -> WP
    # Score diff range: -10 to +10 (20 values)
    WP_TABLE = np.array([
        # Inning 1 (index 0)
        [
            # 0 outs
            [0.008, 0.012, 0.016, 0.021, 0.028, 0.037, 0.048, 0.060, 0.074, 0.091,
             0.500, 0.909, 0.926, 0.940, 0.952, 0.963, 0.972, 0.979, 0.984, 0.988],
            # 1 out
            [0.010, 0.015, 0.020, 0.026, 0.034, 0.044, 0.056, 0.070, 0.087, 0.107,
             0.500, 0.893, 0.913, 0.930, 0.944, 0.956, 0.966, 0.975, 0.982, 0.985],
            # 2 outs
            [0.018, 0.025, 0.033, 0.043, 0.056, 0.073, 0.093, 0.116, 0.145, 0.179,
             0.500, 0.821, 0.855, 0.884, 0.907, 0.927, 0.942, 0.957, 0.967, 0.975],
        ],
        # Inning 4 (index 3)
        [
            [0.025, 0.035, 0.048, 0.063, 0.082, 0.104, 0.130, 0.160, 0.194, 0.232,
             0.500, 0.768, 0.806, 0.840, 0.869, 0.895, 0.917, 0.936, 0.952, 0.965],
            [0.028, 0.038, 0.051, 0.067, 0.087, 0.110, 0.138, 0.170, 0.206, 0.246,
             0.500, 0.754, 0.794, 0.828, 0.857, 0.882, 0.904, 0.923, 0.939, 0.952],
            [0.045, 0.060, 0.078, 0.100, 0.127, 0.160, 0.199, 0.244, 0.293, 0.347,
             0.500, 0.653, 0.707, 0.756, 0.800, 0.840, 0.875, 0.904, 0.929, 0.950],
        ],
        # Inning 7 (index 6)
        [
            [0.058, 0.076, 0.098, 0.124, 0.155, 0.191, 0.232, 0.276, 0.323, 0.372,
             0.500, 0.628, 0.677, 0.724, 0.768, 0.809, 0.845, 0.876, 0.902, 0.924],
            [0.063, 0.082, 0.104, 0.132, 0.164, 0.201, 0.243, 0.288, 0.335, 0.385,
             0.500, 0.615, 0.665, 0.712, 0.755, 0.796, 0.832, 0.864, 0.891, 0.913],
            [0.095, 0.119, 0.147, 0.181, 0.220, 0.266, 0.317, 0.371, 0.427, 0.483,
             0.500, 0.517, 0.573, 0.629, 0.683, 0.734, 0.781, 0.822, 0.858, 0.889],
        ],
        # Inning 9 (index 8)
        [
            [0.103, 0.133, 0.167, 0.207, 0.252, 0.301, 0.354, 0.409, 0.465, 0.520,
             0.500, 0.480, 0.535, 0.591, 0.646, 0.699, 0.748, 0.793, 0.833, 0.867],
            [0.110, 0.141, 0.176, 0.217, 0.264, 0.315, 0.369, 0.425, 0.481, 0.536,
             0.500, 0.464, 0.519, 0.575, 0.631, 0.684, 0.733, 0.778, 0.819, 0.853],
            [0.145, 0.180, 0.220, 0.266, 0.318, 0.375, 0.434, 0.492, 0.548, 0.602,
             0.500, 0.398, 0.452, 0.508, 0.566, 0.625, 0.680, 0.734, 0.782, 0.820],
        ],
    ])
    
    # Inning indices for WP_TABLE (sparse: only selected innings)
    INNING_INDICES = [0, 3, 6, 8]  # Innings 1, 4, 7, 9
    INNING_MAPPING = {1: 0, 4: 3, 7: 6, 9: 8}
    
    def __init__(self):
        """Initialize Win Probability Model."""
        pass
    
    @staticmethod
    def calculate_wp(
        inning: int,
        outs: int,
        score_diff: int,
        is_home_team: bool = True
    ) -> float:
        """
        Calculate win probability for home team.
        
        Args:
            inning: Current inning (1-9+)
            outs: Current outs (0-2)
            score_diff: Score differential (home - away)
            is_home_team: Calculate for home team (True) or away (False)
        
        Returns:
            Win probability (0.0 to 1.0)
        """
        # Clamp inputs to valid ranges
        inning = min(max(1, inning), 9)
        outs = max(0, min(2, outs))
        score_diff = max(-10, min(10, score_diff))
        
        # Find nearest inning in table
        if inning <= 1:
            table_inning = 1
        elif inning <= 4:
            table_inning = 4
        elif inning <= 7:
            table_inning = 7
        else:
            table_inning = 9
        
        inning_idx = WinProbabilityModel.INNING_MAPPING.get(table_inning, 2)
        
        # Score diff index (offset by 10 to handle negatives)
        score_idx = score_diff + 10
        
        # Look up win probability
        try:
            wp = WinProbabilityModel.WP_TABLE[inning_idx, outs, score_idx]
        except IndexError:
            logger.warning(f"Index out of bounds: {inning_idx}, {outs}, {score_idx}")
            wp = 0.5
        
        # Interpolate for innings between table values
        if inning not in WinProbabilityModel.INNING_MAPPING:
            # Linear interpolation
            if inning < 4:
                wp1 = WinProbabilityModel.WP_TABLE[0, outs, score_idx]
                wp2 = WinProbabilityModel.WP_TABLE[1, outs, score_idx]
                t = (inning - 1) / 3.0
                wp = wp1 + t * (wp2 - wp1)
        
        # Adjust for away team
        if not is_home_team:
            wp = 1.0 - wp
        
        return np.clip(float(wp), 0.0, 1.0)


def calculate_win_probability(
    inning: int,
    outs: int,
    score_diff: int,
    runners_on_base: int = 0,
    is_home_team: bool = True,
    custom_model: Optional[any] = None
) -> float:
    """
    Calculate win probability given game state.
    
    Args:
        inning: Current inning (1-9+)
        outs: Current outs (0-2)
        score_diff: Score differential (home - away)
        runners_on_base: Number of runners on base (0-3)
        is_home_team: True for home team win probability
        custom_model: Optional custom model (callable)
    
    Returns:
        Win probability (0.0 to 1.0)
    """
    if custom_model is not None:
        return custom_model(inning, outs, score_diff, is_home_team)
    
    # Use standard model
    model = WinProbabilityModel()
    wp = model.calculate_wp(inning, outs, score_diff, is_home_team)
    
    # Slight adjustment for runners on base
    if runners_on_base > 0 and is_home_team:
        runners_factor = 1.0 + (runners_on_base * 0.01)
        wp *= runners_factor
        wp = np.clip(wp, 0.0, 1.0)
    
    return wp


def calculate_leverage_index(
    inning: int,
    outs: int,
    score_diff: int,
    wp: Optional[float] = None
) -> float:
    """
    Calculate leverage index for current situation.
    
    Leverage measures how much a single play can swing win probability.
    Higher values indicate more critical situations.
    
    Args:
        inning: Current inning
        outs: Current outs
        score_diff: Score differential
        wp: Current win probability (calculated if not provided)
    
    Returns:
        Leverage index (typically 0.5 to 2.0+)
    """
    if wp is None:
        wp = calculate_win_probability(inning, outs, score_diff)
    
    # Base leverage from WP uncertainty
    # Maximize around 0.5 (most uncertain)
    wp_uncertainty = 1.0 - abs(wp - 0.5) * 2.0
    
    # Inning weighting (more critical late in game)
    if inning <= 3:
        inning_weight = 0.5
    elif inning <= 6:
        inning_weight = 0.75
    elif inning <= 8:
        inning_weight = 1.0
    else:
        inning_weight = 1.5
    
    # Outs weighting (more outs = more leverage)
    outs_weight = 1.0 + (outs * 0.3)
    
    # Combine
    leverage = wp_uncertainty * inning_weight * outs_weight
    
    return np.clip(leverage, 0.5, 3.0)


def calculate_win_expectancy_index(
    home_wp: float,
    away_wp: Optional[float] = None
) -> float:
    """
    Calculate Win Expectancy Index (WEI).
    
    Measures deviation from even odds (0.5-0.5).
    WEI = 0 means completely uncertain
    WEI = +1 means certainty for home team
    WEI = -1 means certainty for away team
    
    Args:
        home_wp: Home team win probability
        away_wp: Away team win probability (calculated if not provided)
    
    Returns:
        WEI value (-1.0 to 1.0)
    """
    if away_wp is None:
        away_wp = 1.0 - home_wp
    
    wei = home_wp - away_wp
    
    return np.clip(wei, -1.0, 1.0)


def calculate_win_probability_added(
    wp_before: float,
    wp_after: float,
    is_batter: bool = True
) -> float:
    """
    Calculate Win Probability Added (WPA).
    
    Measures how much a single play changed team's win probability.
    
    Args:
        wp_before: Win probability before play
        wp_after: Win probability after play
        is_batter: True if from batter's perspective (affects sign)
    
    Returns:
        WPA value (typically -0.1 to +0.1)
    """
    wpa = wp_after - wp_before
    
    if not is_batter:
        wpa = -wpa
    
    return np.clip(wpa, -1.0, 1.0)


def estimate_wp_from_score(
    score_diff: int,
    inning: int = 5  # Mid-game
) -> float:
    """
    Quick estimate of win probability from score alone.
    
    Assumes mid-game situation with 0 outs.
    
    Args:
        score_diff: Score differential (home - away)
        inning: Inning number (default 5)
    
    Returns:
        Estimated win probability
    """
    return calculate_win_probability(
        inning=inning,
        outs=0,
        score_diff=score_diff,
        is_home_team=True
    )


def get_wp_swing(
    home_wp_before: float,
    home_wp_after: float,
    away_wp_before: Optional[float] = None,
    away_wp_after: Optional[float] = None
) -> Dict[str, float]:
    """
    Get win probability swings for both teams.
    
    Args:
        home_wp_before: Home WP before play
        home_wp_after: Home WP after play
        away_wp_before: Away WP before play (calculated if not provided)
        away_wp_after: Away WP after play (calculated if not provided)
    
    Returns:
        Dictionary with WPA for both teams
    """
    if away_wp_before is None:
        away_wp_before = 1.0 - home_wp_before
    if away_wp_after is None:
        away_wp_after = 1.0 - home_wp_after
    
    return {
        'home_wpa': home_wp_after - home_wp_before,
        'away_wpa': away_wp_after - away_wp_before,
        'total_swing': abs((home_wp_after - home_wp_before)) * 2
    }


class WinProbabilityTracker:
    """Track win probability throughout game."""
    
    def __init__(self):
        """Initialize tracker."""
        self.history = []
    
    def record_state(
        self,
        timestamp: int,
        inning: int,
        outs: int,
        score_diff: int,
        home_wp: Optional[float] = None
    ) -> None:
        """
        Record game state and WP.
        
        Args:
            timestamp: Play number or timestamp
            inning: Current inning
            outs: Current outs
            score_diff: Score differential
            home_wp: Home team WP (calculated if not provided)
        """
        if home_wp is None:
            home_wp = calculate_win_probability(inning, outs, score_diff)
        
        self.history.append({
            'timestamp': timestamp,
            'inning': inning,
            'outs': outs,
            'score_diff': score_diff,
            'home_wp': home_wp,
            'away_wp': 1.0 - home_wp
        })
    
    def get_wpa_for_play(self, play_index: int) -> float:
        """
        Get WPA for specific play.
        
        Args:
            play_index: Index in history
        
        Returns:
            WPA for that play
        """
        if play_index <= 0 or play_index >= len(self.history):
            return 0.0
        
        before = self.history[play_index - 1]
        after = self.history[play_index]
        
        return after['home_wp'] - before['home_wp']
    
    def get_total_wpa(self) -> float:
        """Get total WPA for game."""
        if len(self.history) < 2:
            return 0.0
        
        return self.history[-1]['home_wp'] - self.history[0]['home_wp']
    
    def get_history_dataframe(self):
        """Get history as pandas DataFrame."""
        import pandas as pd
        return pd.DataFrame(self.history)
