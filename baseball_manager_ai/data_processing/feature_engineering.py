"""
Feature engineering for baseball data.
Creates features for machine learning models.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class FeatureEngineer:
    """Feature engineering for baseball data"""
    
    def __init__(self):
        self.feature_cache = {}
    
    def create_game_state_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create comprehensive game state features.
        
        Args:
            df: Raw event data
            
        Returns:
            DataFrame with game state features
        """
        if df.empty:
            return df
            
        df_features = df.copy()
        
        # Base state features
        df_features = self._create_base_state_features(df_features)
        
        # Count features
        df_features = self._create_count_features(df_features)
        
        # Game context features
        df_features = self._create_game_context_features(df_features)
        
        # Historical features
        df_features = self._create_historical_features(df_features)
        
        # Matchup features
        df_features = self._create_matchup_features(df_features)
        
        logger.info(f"Created {len([c for c in df_features.columns if 'feature_' in c])} game state features")
        return df_features
    
    def create_player_features(self, df: pd.DataFrame, lookback_days: int = 30) -> pd.DataFrame:
        """
        Create player-specific features.
        
        Args:
            df: Event data with player information
            lookback_days: Number of days to look back for historical stats
            
        Returns:
            DataFrame with player features
        """
        if df.empty:
            return df
            
        df_features = df.copy()
        
        # Batter features
        df_features = self._create_batter_features(df_features, lookback_days)
        
        # Pitcher features
        df_features = self._create_pitcher_features(df_features, lookback_days)
        
        # Platoon features
        df_features = self._create_platoon_features(df_features)
        
        logger.info(f"Created player features for {len(df_features)} events")
        return df_features
    
    def create_strategic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create features for strategic decision making.
        
        Args:
            df: Game state data
            
        Returns:
            DataFrame with strategic features
        """
        if df.empty:
            return df
            
        df_features = df.copy()
        
        # Run expectancy
        df_features = self._create_run_expectancy_features(df_features)
        
        # Win probability
        df_features = self._create_win_probability_features(df_features)
        
        # Leverage index
        df_features = self._create_leverage_features(df_features)
        
        # Strategic context
        df_features = self._create_strategic_context_features(df_features)
        
        logger.info(f"Created strategic features for {len(df_features)} events")
        return df_features
    
    def _create_base_state_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create base runner state features"""
        df_copy = df.copy()
        
        # Base occupancy
        df_copy['feature_bases_occupied'] = (
            df_copy.get('on_1b', 0) + 
            df_copy.get('on_2b', 0) + 
            df_copy.get('on_3b', 0)
        )
        
        # Specific base states
        df_copy['feature_runner_on_1b'] = df_copy.get('on_1b', 0)
        df_copy['feature_runner_on_2b'] = df_copy.get('on_2b', 0)
        df_copy['feature_runner_on_3b'] = df_copy.get('on_3b', 0)
        df_copy['feature_runners_in_scoring_position'] = (
            df_copy.get('on_2b', 0) + df_copy.get('on_3b', 0)
        )
        
        return df_copy
    
    def _create_count_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create count-based features"""
        df_copy = df.copy()
        
        # Current count
        df_copy['feature_balls'] = df_copy.get('balls', 0)
        df_copy['feature_strikes'] = df_copy.get('strikes', 0)
        
        # Count situations
        df_copy['feature_full_count'] = (
            (df_copy.get('balls', 0) == 3) & 
            (df_copy.get('strikes', 0) == 2)
        ).astype(int)
        
        df_copy['feature_hitters_count'] = (
            (df_copy.get('balls', 0) > df_copy.get('strikes', 0)) &
            (df_copy.get('balls', 0) >= 2)
        ).astype(int)
        
        df_copy['feature_pitchers_count'] = (
            (df_copy.get('strikes', 0) > df_copy.get('balls', 0)) &
            (df_copy.get('strikes', 0) >= 2)
        ).astype(int)
        
        return df_copy
    
    def _create_game_context_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create game context features"""
        df_copy = df.copy()
        
        # Inning features
        df_copy['feature_inning'] = df_copy.get('inning', 1)
        df_copy['feature_late_inning'] = (df_copy.get('inning', 1) >= 7).astype(int)
        
        # Score features
        df_copy['feature_score_differential'] = (
            df_copy.get('bat_score', 0) - df_copy.get('fld_score', 0)
        )
        df_copy['feature_abs_score_differential'] = abs(df_copy['feature_score_differential'])
        df_copy['feature_close_game'] = (df_copy['feature_abs_score_differential'] <= 3).astype(int)
        
        # Out features
        df_copy['feature_outs'] = df_copy.get('outs_when_up', 0)
        df_copy['feature_two_outs'] = (df_copy.get('outs_when_up', 0) == 2).astype(int)
        
        return df_copy
    
    def _create_historical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create historical performance features"""
        # This would be implemented with rolling averages
        # For now, placeholder implementation
        df_copy = df.copy()
        
        # Placeholder for historical features
        df_copy['feature_batter_avg_7d'] = 0.25  # Would be calculated from historical data
        df_copy['feature_pitcher_era_7d'] = 4.00  # Would be calculated from historical data
        
        return df_copy
    
    def _create_matchup_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create batter-pitcher matchup features"""
        df_copy = df.copy()
        
        # Platoon advantage
        if 'stand' in df_copy.columns and 'p_throws' in df_copy.columns:
            df_copy['feature_platoon_advantage'] = (
                df_copy['stand'] != df_copy['p_throws']
            ).astype(int)
        
        # Historical matchup data would go here
        df_copy['feature_historical_matchup_avg'] = 0.250  # Placeholder
        
        return df_copy
    
    def _create_run_expectancy_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create run expectancy features"""
        df_copy = df.copy()
        
        # Simple run expectancy matrix (would be more sophisticated in production)
        re_matrix = self._get_run_expectancy_matrix()
        
        # Calculate run expectancy for current state
        df_copy['feature_run_expectancy'] = df_copy.apply(
            lambda row: self._calculate_run_expectancy(row, re_matrix), 
            axis=1
        )
        
        return df_copy
    
    def _create_win_probability_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create win probability features"""
        df_copy = df.copy()
        
        # Simplified win probability calculation
        df_copy['feature_win_probability'] = df_copy.apply(
            self._calculate_win_probability, 
            axis=1
        )
        
        return df_copy
    
    def _create_leverage_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create leverage index features"""
        df_copy = df.copy()
        
        # Leverage index based on game state
        df_copy['feature_leverage_index'] = df_copy.apply(
            self._calculate_leverage_index,
            axis=1
        )
        
        df_copy['feature_high_leverage'] = (df_copy['feature_leverage_index'] > 1.5).astype(int)
        
        return df_copy
    
    def _create_strategic_context_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create strategic context features"""
        df_copy = df.copy()
        
        # Bunt situations
        df_copy['feature_bunt_situation'] = (
            (df_copy.get('outs_when_up', 0) < 2) &
            (df_copy.get('on_1b', 0) == 1) &
            (df_copy.get('on_2b', 0) == 0) &
            (df_copy['feature_close_game'] == 1)
        ).astype(int)
        
        # Steal situations
        df_copy['feature_steal_situation'] = (
            (df_copy.get('on_1b', 0) == 1) &
            (df_copy.get('on_2b', 0) == 0) &
            (df_copy.get('feature_abs_score_differential', 0) <= 2)
        ).astype(int)
        
        # Pinch hit situations
        df_copy['feature_pinch_hit_situation'] = (
            (df_copy['feature_late_inning'] == 1) &
            (df_copy['feature_close_game'] == 1) &
            (df_copy.get('feature_platoon_advantage', 0) == 0)
        ).astype(int)
        
        return df_copy
    
    def _get_run_expectancy_matrix(self) -> Dict[Tuple, float]:
        """Get run expectancy matrix for different base/out states"""
        # Simplified RE matrix - in production, this would be calculated from historical data
        return {
            (0, 0, 0, 0): 0.50,  # bases empty, 0 outs
            (1, 0, 0, 0): 0.90,  # runner on 1st, 0 outs
            (0, 1, 0, 0): 1.10,  # runner on 2nd, 0 outs
            (0, 0, 1, 0): 1.35,  # runner on 3rd, 0 outs
            (1, 1, 0, 0): 1.45,  # runners on 1st and 2nd, 0 outs
            # ... more states
        }
    
    def _calculate_run_expectancy(self, row: pd.Series, re_matrix: Dict) -> float:
        """Calculate run expectancy for current game state"""
        base_state = (
            row.get('on_1b', 0),
            row.get('on_2b', 0), 
            row.get('on_3b', 0),
            row.get('outs_when_up', 0)
        )
        return re_matrix.get(base_state, 0.50)
    
    def _calculate_win_probability(self, row: pd.Series) -> float:
        """Calculate simplified win probability"""
        # This would be a much more sophisticated calculation in production
        inning = row.get('inning', 1)
        score_diff = row.get('feature_score_differential', 0)
        outs = row.get('outs_when_up', 0)
        
        # Very simplified calculation
        base_prob = 0.5
        inning_effect = (inning - 1) / 8 * 0.3  # Later innings matter more
        score_effect = score_diff * 0.05
        out_effect = (2 - outs) / 2 * 0.1  # Fewer outs is better
        
        return max(0.01, min(0.99, base_prob + inning_effect + score_effect + out_effect))
    
    def _calculate_leverage_index(self, row: pd.Series) -> float:
        """Calculate leverage index"""
        wp = row.get('feature_win_probability', 0.5)
        inning = row.get('inning', 1)
        
        # Simplified leverage: higher in close games and late innings
        leverage = (1 - 2 * abs(wp - 0.5)) * (inning / 9)
        return max(0.1, leverage)
