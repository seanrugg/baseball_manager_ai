# baseball_manager_ai/features/feature_engineering.py
"""
Feature engineering pipeline for transforming raw baseball data into ML-ready features.

This module handles:
1. Base state encoding
2. Matchup feature creation
3. Situational feature engineering
4. Recent performance aggregation
5. Environmental factors
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class FeatureConfig:
    """Configuration for feature engineering."""
    include_weather: bool = True
    include_park_factors: bool = True
    include_recent_performance: bool = True
    recent_windows: List[int] = None  # Days: [7, 15, 30]
    min_ab_for_splits: int = 50
    normalize_features: bool = True
    handle_missing: str = 'mean'  # 'mean', 'median', 'forward_fill'
    
    def __post_init__(self):
        if self.recent_windows is None:
            self.recent_windows = [7, 15, 30]


class BaseStateEncoder:
    """Encode base runner configurations."""
    
    @staticmethod
    def encode_bases(bases: Tuple[bool, bool, bool]) -> Dict[str, float]:
        """
        Encode base state as individual features.
        
        Args:
            bases: (first_occupied, second_occupied, third_occupied)
        
        Returns:
            Dictionary with binary features for each base
        """
        return {
            'first_base': float(bases[0]),
            'second_base': float(bases[1]),
            'third_base': float(bases[2]),
            'runners_on_base': float(sum(bases)),
            'scoring_position': float(bases[1] or bases[2]),  # 2nd or 3rd
        }
    
    @staticmethod
    def encode_base_state_categorical(bases: Tuple[bool, bool, bool]) -> Dict[str, int]:
        """
        Encode base state as categorical index (0-7) with one-hot encoding.
        
        Args:
            bases: (first_occupied, second_occupied, third_occupied)
        
        Returns:
            One-hot encoded dictionary (8 features)
        """
        state_idx = sum((1 << i) for i in range(3) if bases[i])
        
        result = {}
        for i in range(8):
            result[f'base_state_{i}'] = 1.0 if i == state_idx else 0.0
        
        return result


class GameStateFeatures:
    """Extract features from game state."""
    
    @staticmethod
    def create_features(
        inning: int,
        outs: int,
        score: List[int],
        bases: Tuple[bool, bool, bool],
        count: Tuple[int, int],
        game_importance: float = 0.5,
        config: Optional[FeatureConfig] = None
    ) -> Dict[str, float]:
        """
        Create game state features.
        
        Args:
            inning: Current inning (1-9+)
            outs: Number of outs (0-2)
            score: [home_runs, away_runs]
            bases: (first, second, third) occupied
            count: (balls, strikes)
            game_importance: 0-1 scale
            config: Feature configuration
        
        Returns:
            Dictionary of game state features
        """
        if config is None:
            config = FeatureConfig()
        
        features = {}
        
        # Inning features
        features['inning'] = float(inning)
        features['inning_normalized'] = float(inning) / 9.0
        features['inning_is_extra'] = 1.0 if inning > 9 else 0.0
        
        # Outs features
        features['outs'] = float(outs)
        features['outs_normalized'] = float(outs) / 2.0
        features['outs_remaining'] = float(3 - outs)
        
        # Score features
        home_score, away_score = score
        score_diff = home_score - away_score
        features['score_diff'] = float(score_diff)
        features['score_diff_sign'] = 1.0 if score_diff > 0 else (-1.0 if score_diff < 0 else 0.0)
        features['score_diff_abs'] = float(abs(score_diff))
        features['home_runs'] = float(home_score)
        features['away_runs'] = float(away_score)
        
        # Count features
        balls, strikes = count
        features['balls'] = float(balls)
        features['strikes'] = float(strikes)
        features['balls_normalized'] = float(balls) / 3.0
        features['strikes_normalized'] = float(strikes) / 2.0
        features['count_is_hitter_friendly'] = 1.0 if balls > strikes else 0.0
        features['count_is_pitcher_friendly'] = 1.0 if strikes > balls else 0.0
        
        # Base state features
        bases_features = BaseStateEncoder.encode_bases(bases)
        features.update(bases_features)
        
        # Game importance
        features['game_importance'] = float(game_importance)
        
        return features
    
    @staticmethod
    def create_situational_features(
        inning: int,
        outs: int,
        score_diff: int,
        runners_on_base: int
    ) -> Dict[str, float]:
        """
        Create higher-level situational features.
        
        Args:
            inning: Current inning
            outs: Number of outs
            score_diff: home - away score
            runners_on_base: 0-3
        
        Returns:
            Dictionary of situational features
        """
        features = {}
        
        # Late-game situation
        features['is_late_game'] = 1.0 if inning >= 7 else 0.0
        features['is_very_late_game'] = 1.0 if inning >= 8 else 0.0
        features['is_extra_inning'] = 1.0 if inning > 9 else 0.0
        
        # Pressure situations
        features['is_close_game'] = 1.0 if abs(score_diff) <= 2 else 0.0
        features['is_tied_game'] = 1.0 if score_diff == 0 else 0.0
        features['is_one_run_game'] = 1.0 if abs(score_diff) == 1 else 0.0
        
        # High leverage combinations
        features['late_close'] = (
            1.0 if (inning >= 7 and abs(score_diff) <= 3) else 0.0
        )
        features['two_outs_close'] = (
            1.0 if (outs == 2 and abs(score_diff) <= 2) else 0.0
        )
        
        # Scoring opportunity
        features['scoring_position'] = 1.0 if runners_on_base >= 1 else 0.0  # Runner on 2nd or 3rd
        features['bases_loaded'] = 1.0 if runners_on_base == 3 else 0.0
        features['multiple_runners'] = 1.0 if runners_on_base >= 2 else 0.0
        
        return features


class PlayerFeatures:
    """Extract and normalize player performance features."""
    
    @staticmethod
    def create_batter_features(
        batter_stats: Dict,
        config: Optional[FeatureConfig] = None
    ) -> Dict[str, float]:
        """
        Create feature vector from batter stats.
        
        Args:
            batter_stats: Dictionary with batter statistics
            config: Feature configuration
        
        Returns:
            Feature dictionary
        """
        if config is None:
            config = FeatureConfig()
        
        features = {}
        
        # Career performance (baseline)
        features['career_avg'] = float(batter_stats.get('career_avg', 0.260))
        features['career_obp'] = float(batter_stats.get('career_obp', 0.330))
        features['career_slg'] = float(batter_stats.get('career_slg', 0.420))
        features['career_ops'] = float(batter_stats.get('career_ops', 0.750))
        
        # Season performance
        features['season_avg'] = float(batter_stats.get('season_avg', 0.260))
        features['season_obp'] = float(batter_stats.get('season_obp', 0.330))
        features['season_slg'] = float(batter_stats.get('season_slg', 0.420))
        features['season_ops'] = float(batter_stats.get('season_ops', 0.750))
        
        # Rate stats
        features['strikeout_rate'] = float(batter_stats.get('strikeout_rate', 0.200))
        features['walk_rate'] = float(batter_stats.get('walk_rate', 0.080))
        features['iso'] = float(batter_stats.get('iso', 0.160))  # Isolated power
        
        # Recent form (if available)
        if config.include_recent_performance:
            features['recent_avg'] = float(batter_stats.get('recent_avg', 0.260))
            features['recent_obp'] = float(batter_stats.get('recent_obp', 0.330))
            features['trend'] = (
                float(batter_stats.get('recent_avg', 0.260)) - 
                float(batter_stats.get('season_avg', 0.260))
            )
        
        # Platoon splits (normalized)
        lhp_avg = float(batter_stats.get('vs_lhp_avg', 0.260))
        rhp_avg = float(batter_stats.get('vs_rhp_avg', 0.260))
        features['lhp_avg'] = lhp_avg
        features['rhp_avg'] = rhp_avg
        features['platoon_differential'] = lhp_avg - rhp_avg
        
        # Situational performance
        features['risp_avg'] = float(batter_stats.get('risp_avg', 0.260))
        features['late_close_avg'] = float(batter_stats.get('late_close_avg', 0.260))
        features['high_leverage_avg'] = float(batter_stats.get('high_leverage_avg', 0.260))
        
        # Advanced metrics
        features['barrel_rate'] = float(batter_stats.get('barrel_rate', 0.070))
        features['hard_hit_rate'] = float(batter_stats.get('hard_hit_rate', 0.380))
        features['avg_exit_velocity'] = float(batter_stats.get('avg_exit_velocity', 89.0))
        features['avg_launch_angle'] = float(batter_stats.get('avg_launch_angle', 10.0))
        
        # Defense
        features['drs'] = float(batter_stats.get('drs', 0.0))
        
        return features
    
    @staticmethod
    def create_pitcher_features(
        pitcher_stats: Dict,
        config: Optional[FeatureConfig] = None
    ) -> Dict[str, float]:
        """
        Create feature vector from pitcher stats.
        
        Args:
            pitcher_stats: Dictionary with pitcher statistics
            config: Feature configuration
        
        Returns:
            Feature dictionary
        """
        if config is None:
            config = FeatureConfig()
        
        features = {}
        
        # Career performance
        features['career_era'] = float(pitcher_stats.get('career_era', 4.0))
        features['career_whip'] = float(pitcher_stats.get('career_whip', 1.25))
        features['career_k9'] = float(pitcher_stats.get('career_k9', 8.5))
        features['career_bb9'] = float(pitcher_stats.get('career_bb9', 2.5))
        
        # Season performance
        features['season_era'] = float(pitcher_stats.get('season_era', 4.0))
        features['season_whip'] = float(pitcher_stats.get('season_whip', 1.25))
        features['season_k9'] = float(pitcher_stats.get('season_k9', 8.5))
        features['season_bb9'] = float(pitcher_stats.get('season_bb9', 2.5))
        
        # Recent form
        if config.include_recent_performance:
            features['recent_era'] = float(pitcher_stats.get('recent_era', 4.0))
            features['recent_k9'] = float(pitcher_stats.get('recent_k9', 8.5))
            features['era_trend'] = (
                float(pitcher_stats.get('recent_era', 4.0)) - 
                float(pitcher_stats.get('season_era', 4.0))
            )
        
        # Matchup splits
        features['vs_lhb_era'] = float(pitcher_stats.get('vs_lhb_era', 4.0))
        features['vs_rhb_era'] = float(pitcher_stats.get('vs_rhb_era', 4.0))
        features['vs_lhb_k9'] = float(pitcher_stats.get('vs_lhb_k9', 8.5))
        features['vs_rhb_k9'] = float(pitcher_stats.get('vs_rhb_k9', 8.5))
        
        # Fatigue
        features['pitch_count_today'] = float(pitcher_stats.get('pitch_count_today', 0))
        features['innings_today'] = float(pitcher_stats.get('innings_today', 0.0))
        features['pitches_last_7_days'] = float(pitcher_stats.get('pitches_last_7_days', 0))
        features['games_last_14_days'] = float(pitcher_stats.get('games_last_14_days', 0))
        features['days_rest'] = float(pitcher_stats.get('days_rest', 0))
        features['is_fresh'] = 1.0 if float(pitcher_stats.get('days_rest', 0)) >= 2 else 0.0
        
        # Arsenal
        features['pitch_variety'] = float(pitcher_stats.get('pitch_variety', 3.0))
        features['spin_rate'] = float(pitcher_stats.get('spin_rate', 2300))
        features['avg_pitch_velo'] = float(pitcher_stats.get('avg_pitch_velo', 92.0))
        
        # Role
        features['is_starter'] = 1.0 if pitcher_stats.get('role') == 'starter' else 0.0
        features['is_reliever'] = 1.0 if pitcher_stats.get('role') == 'reliever' else 0.0
        features['is_closer'] = 1.0 if pitcher_stats.get('role') == 'closer' else 0.0
        
        return features


class EnvironmentalFeatures:
    """Extract features from environmental conditions."""
    
    @staticmethod
    def create_weather_features(weather_dict: Dict) -> Dict[str, float]:
        """
        Create weather-related features.
        
        Args:
            weather_dict: Dictionary with temperature, wind, humidity, etc.
        
        Returns:
            Feature dictionary
        """
        features = {}
        
        temp = float(weather_dict.get('temperature', 72.0))
        wind = float(weather_dict.get('wind_speed', 0.0))
        humidity = float(weather_dict.get('humidity', 50.0))
        
        features['temperature'] = temp
        features['temp_normalized'] = (temp - 60.0) / 20.0  # -1 to +2 scale
        
        features['wind_speed'] = wind
        features['is_windy'] = 1.0 if wind > 10 else 0.0
        
        features['humidity'] = humidity
        features['is_humid'] = 1.0 if humidity > 70 else 0.0
        
        # Combined effect (higher temp + wind = more fly ball distance)
        features['ball_carry_factor'] = (temp - 60.0) / 20.0 + (wind / 20.0)
        
        return features
    
    @staticmethod
    def create_park_factors(park_name: str) -> Dict[str, float]:
        """
        Create park-specific factors.
        
        Args:
            park_name: Name of stadium
        
        Returns:
            Feature dictionary with park factors
        """
        # Pre-computed park factors (runs per game vs league average)
        park_factors_db = {
            'Fenway Park': {'hr_factor': 1.08, 'runs_factor': 1.06},
            'Yankee Stadium': {'hr_factor': 1.08, 'runs_factor': 1.05},
            'Rogers Centre': {'hr_factor': 0.98, 'runs_factor': 0.98},
            'Comerica Park': {'hr_factor': 0.94, 'runs_factor': 0.95},
            'Coors Field': {'hr_factor': 1.19, 'runs_factor': 1.20},  # Altitude!
            'Dodger Stadium': {'hr_factor': 0.95, 'runs_factor': 0.94},
            'Oracle Park': {'hr_factor': 0.88, 'runs_factor': 0.88},
        }
        
        features = {}
        
        if park_name in park_factors_db:
            factors = park_factors_db[park_name]
            features['park_hr_factor'] = factors['hr_factor']
            features['park_runs_factor'] = factors['runs_factor']
        else:
            # Default to neutral
            features['park_hr_factor'] = 1.0
            features['park_runs_factor'] = 1.0
        
        features['is_high_altitude'] = 1.0 if park_name == 'Coors Field' else 0.0
        
        return features


class FeatureScaler:
    """Normalize and scale features."""
    
    @staticmethod
    def normalize_features(
        features: Dict[str, float],
        feature_ranges: Optional[Dict[str, Tuple[float, float]]] = None
    ) -> Dict[str, float]:
        """
        Normalize features to 0-1 range.
        
        Args:
            features: Feature dictionary
            feature_ranges: Optional {feature_name: (min, max)} for normalization
        
        Returns:
            Normalized feature dictionary
        """
        if feature_ranges is None:
            return features
        
        normalized = {}
        for name, value in features.items():
            if name in feature_ranges:
                min_val, max_val = feature_ranges[name]
                if max_val > min_val:
                    normalized[name] = (value - min_val) / (max_val - min_val)
                else:
                    normalized[name] = 0.5
            else:
                normalized[name] = value
        
        return normalized


class FeatureEngineer:
    """Main feature engineering orchestrator."""
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        self.config = config or FeatureConfig()
    
    def create_full_feature_set(
        self,
        game_state: Dict,
        batter_stats: Dict,
        pitcher_stats: Dict,
        weather: Optional[Dict] = None,
        park_name: str = 'Unknown'
    ) -> Dict[str, float]:
        """
        Create complete feature vector for a game situation.
        
        Args:
            game_state: Current inning, outs, score, bases, count
            batter_stats: Batter performance statistics
            pitcher_stats: Pitcher performance statistics
            weather: Weather conditions
            park_name: Stadium name
        
        Returns:
            Complete feature dictionary
        """
        features = {}
        
        # Game state features
        gs_features = GameStateFeatures.create_features(
            inning=game_state.get('inning', 1),
            outs=game_state.get('outs', 0),
            score=game_state.get('score', [0, 0]),
            bases=tuple(game_state.get('bases', [False, False, False])),
            count=tuple(game_state.get('count', [0, 0])),
            game_importance=game_state.get('game_importance', 0.5),
            config=self.config
        )
        features.update(gs_features)
        
        # Situational features
        sit_features = GameStateFeatures.create_situational_features(
            inning=game_state.get('inning', 1),
            outs=game_state.get('outs', 0),
            score_diff=game_state.get('score', [0, 0])[0] - game_state.get('score', [0, 0])[1],
            runners_on_base=sum(game_state.get('bases', [False, False, False]))
        )
        features.update(sit_features)
        
        # Player features
        batter_features = PlayerFeatures.create_batter_features(batter_stats, self.config)
        features.update({f'batter_{k}': v for k, v in batter_features.items()})
        
        pitcher_features = PlayerFeatures.create_pitcher_features(pitcher_stats, self.config)
        features.update({f'pitcher_{k}': v for k, v in pitcher_features.items()})
        
        # Environmental features
        if self.config.include_weather and weather:
            weather_features = EnvironmentalFeatures.create_weather_features(weather)
            features.update(weather_features)
        
        if self.config.include_park_factors:
            park_features = EnvironmentalFeatures.create_park_factors(park_name)
            features.update(park_features)
        
        return features
