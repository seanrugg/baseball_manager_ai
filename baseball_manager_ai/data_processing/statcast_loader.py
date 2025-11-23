"""
Statcast data loader and processor.
Handles MLB Statcast data downloading and initial processing.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import requests
import time
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

class StatcastLoader:
    """Loader for MLB Statcast data"""
    
    def __init__(self, data_dir: str = "data/raw/statcast"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def download_statcast_data(self, start_date: str, end_date: str, 
                             save: bool = True) -> pd.DataFrame:
        """
        Download Statcast data for a date range.
        
        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            save: Whether to save to disk
            
        Returns:
            DataFrame with Statcast data
        """
        try:
            from pybaseball import statcast
            logger.info(f"Downloading Statcast data from {start_date} to {end_date}")
            
            df = statcast(start_dt=start_date, end_dt=end_date)
            
            if save:
                filename = f"statcast_{start_date}_{end_date}.parquet"
                filepath = self.data_dir / filename
                df.to_parquet(filepath)
                logger.info(f"Saved Statcast data to {filepath}")
            
            return df
            
        except ImportError:
            logger.error("pybaseball not installed. Install with: pip install pybaseball")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error downloading Statcast data: {e}")
            return pd.DataFrame()
    
    def load_statcast_data(self, filepath: str) -> pd.DataFrame:
        """Load Statcast data from file"""
        try:
            df = pd.read_parquet(filepath)
            logger.info(f"Loaded Statcast data from {filepath}")
            return df
        except Exception as e:
            logger.error(f"Error loading Statcast data: {e}")
            return pd.DataFrame()
    
    def preprocess_statcast_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess raw Statcast data.
        
        Args:
            df: Raw Statcast DataFrame
            
        Returns:
            Preprocessed DataFrame
        """
        if df.empty:
            return df
            
        # Create copy to avoid warnings
        df_clean = df.copy()
        
        # Convert date columns
        date_columns = ['game_date', 'at_bat_date']
        for col in date_columns:
            if col in df_clean.columns:
                df_clean[col] = pd.to_datetime(df_clean[col])
        
        # Create game state features
        df_clean = self._create_game_state_features(df_clean)
        
        # Clean player names
        df_clean = self._clean_player_names(df_clean)
        
        # Add derived metrics
        df_clean = self._add_derived_metrics(df_clean)
        
        logger.info(f"Preprocessed Statcast data: {len(df_clean)} rows")
        return df_clean
    
    def _create_game_state_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create game state features from raw data"""
        df_copy = df.copy()
        
        # Base runners
        df_copy['on_1b'] = df_copy['on_1b'].notna().astype(int)
        df_copy['on_2b'] = df_copy['on_2b'].notna().astype(int)
        df_copy['on_3b'] = df_copy['on_3b'].notna().astype(int)
        
        # Count features
        df_copy['is_full_count'] = ((df_copy['balls'] == 3) & (df_copy['strikes'] == 2)).astype(int)
        df_copy['is_three_ball_count'] = (df_copy['balls'] == 3).astype(int)
        df_copy['is_two_strike_count'] = (df_copy['strikes'] == 2).astype(int)
        
        # Inning features
        df_copy['is_late_inning'] = (df_copy['inning'] >= 7).astype(int)
        df_copy['is_high_leverage'] = self._calculate_leverage_index(df_copy)
        
        return df_copy
    
    def _clean_player_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize player names"""
        df_copy = df.copy()
        
        # Remove extra whitespace from names
        name_columns = ['player_name', 'batter', 'pitcher', 'fielder_2', 'fielder_3', 
                       'fielder_4', 'fielder_5', 'fielder_6', 'fielder_7', 
                       'fielder_8', 'fielder_9']
        
        for col in name_columns:
            if col in df_copy.columns:
                df_copy[col] = df_copy[col].astype(str).str.strip()
        
        return df_copy
    
    def _add_derived_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived baseball metrics"""
        df_copy = df.copy()
        
        # Pitch metrics
        if 'release_speed' in df_copy.columns and 'release_spin_rate' in df_copy.columns:
            df_copy['velocity_spin_ratio'] = df_copy['release_speed'] / (df_copy['release_spin_rate'] + 1)
        
        # Batter performance
        if 'events' in df_copy.columns:
            df_copy['is_hit'] = df_copy['events'].isin(['single', 'double', 'triple', 'home_run']).astype(int)
            df_copy['is_hr'] = (df_copy['events'] == 'home_run').astype(int)
            df_copy['is_ab'] = df_copy['events'].notna().astype(int)
        
        return df_copy
    
    def _calculate_leverage_index(self, df: pd.DataFrame) -> pd.Series:
        """Calculate simple leverage index based on inning, score, and outs"""
        # Simplified leverage calculation
        # In reality, you'd want a more sophisticated WPA-based approach
        inning_weight = np.minimum(df['inning'] / 9, 1.0)
        score_diff = np.abs(df['home_score'] - df['away_score'])
        score_weight = 1 / (1 + score_diff / 4)  # Close games have higher leverage
        outs_weight = (df['outs_when_up'] + 1) / 3  # More outs = higher leverage
        
        leverage = inning_weight * score_weight * outs_weight
        return (leverage > 0.5).astype(int)  # Binary high/low leverage
