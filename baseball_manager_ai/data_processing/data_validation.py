"""
Data validation for baseball data.
Ensures data quality and consistency.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DataValidator:
    """Validates baseball data quality and consistency"""
    
    def __init__(self):
        self.validation_rules = self._initialize_validation_rules()
    
    def validate_statcast_data(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Validate Statcast data quality.
        
        Args:
            df: Statcast DataFrame to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'summary': {}
        }
        
        if df.empty:
            validation_results['is_valid'] = False
            validation_results['errors'].append("DataFrame is empty")
            return validation_results
        
        # Check required columns
        required_columns = ['game_date', 'batter', 'pitcher', 'events', 'description']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            validation_results['is_valid'] = False
            validation_results['errors'].append(f"Missing required columns: {missing_columns}")
        
        # Validate data types
        type_issues = self._validate_data_types(df)
        validation_results['warnings'].extend(type_issues)
        
        # Check for missing values
        missing_stats = self._check_missing_values(df)
        validation_results['summary']['missing_values'] = missing_stats
        
        # Validate value ranges
        range_issues = self._validate_value_ranges(df)
        validation_results['warnings'].extend(range_issues)
        
        # Check data consistency
        consistency_issues = self._check_consistency(df)
        validation_results['warnings'].extend(consistency_issues)
        
        # Generate summary statistics
        validation_results['summary'].update(self._generate_summary_stats(df))
        
        logger.info(f"Data validation completed: {len(validation_results['errors'])} errors, "
                   f"{len(validation_results['warnings'])} warnings")
        
        return validation_results
    
    def validate_retrosheet_data(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Validate Retrosheet data quality.
        
        Args:
            df: Retrosheet DataFrame to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'summary': {}
        }
        
        if df.empty:
            validation_results['is_valid'] = False
            validation_results['errors'].append("DataFrame is empty")
            return validation_results
        
        # Retrosheet-specific validation
        required_columns = ['game_id', 'inning', 'batter_id', 'event']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            validation_results['is_valid'] = False
            validation_results['errors'].append(f"Missing required columns: {missing_columns}")
        
        # Validate event codes
        event_issues = self._validate_retrosheet_events(df)
        validation_results['warnings'].extend(event_issues)
        
        # Validate game sequences
        sequence_issues = self._validate_game_sequences(df)
        validation_results['warnings'].extend(sequence_issues)
        
        validation_results['summary'].update(self._generate_summary_stats(df))
        
        return validation_results
    
    def _initialize_validation_rules(self) -> Dict:
        """Initialize validation rules for different data types"""
        return {
            'numeric_ranges': {
                'inning': (1, 20),  # Extra innings possible
                'balls': (0, 3),
                'strikes': (0, 2),
                'outs_when_up': (0, 2),
                'on_1b': (0, 1),
                'on_2b': (0, 1),
                'on_3b': (0, 1),
            },
            'required_columns': {
                'statcast': ['game_date', 'batter', 'pitcher', 'events', 'description'],
                'retrosheet': ['game_id', 'inning', 'batter_id', 'event']
            }
        }
    
    def _validate_data_types(self, df: pd.DataFrame) -> List[str]:
        """Validate data types of columns"""
        issues = []
        
        # Check date columns
        date_columns = ['game_date', 'at_bat_date']
        for col in date_columns:
            if col in df.columns and not pd.api.types.is_datetime64_any_dtype(df[col]):
                issues.append(f"Column {col} should be datetime type")
        
        # Check numeric columns
        numeric_columns = ['inning', 'balls', 'strikes', 'outs_when_up', 'on_1b', 'on_2b', 'on_3b']
        for col in numeric_columns:
            if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
                issues.append(f"Column {col} should be numeric type")
        
        return issues
    
    def _check_missing_values(self, df: pd.DataFrame) -> Dict[str, int]:
        """Check for missing values in important columns"""
        important_columns = ['game_date', 'batter', 'pitcher', 'events', 'inning']
        missing_counts = {}
        
        for col in important_columns:
            if col in df.columns:
                missing_count = df[col].isna().sum()
                if missing_count > 0:
                    missing_counts[col] = missing_count
        
        return missing_counts
    
    def _validate_value_ranges(self, df: pd.DataFrame) -> List[str]:
        """Validate that values are within expected ranges"""
        issues = []
        rules = self.validation_rules['numeric_ranges']
        
        for col, (min_val, max_val) in rules.items():
            if col in df.columns:
                out_of_range = ((df[col] < min_val) | (df[col] > max_val)).sum()
                if out_of_range > 0:
                    issues.append(f"Column {col} has {out_of_range} values outside range [{min_val}, {max_val}]")
        
        return issues
    
    def _check_consistency(self, df: pd.DataFrame) -> List[str]:
        """Check data consistency"""
        issues = []
        
        # Check that outs don't exceed 2
        if 'outs_when_up' in df.columns:
            invalid_outs = (df['outs_when_up'] > 2).sum()
            if invalid_outs > 0:
                issues.append(f"Found {invalid_outs} records with outs > 2")
        
        # Check that balls + strikes don't exceed at-bat limits
        if all(col in df.columns for col in ['balls', 'strikes']):
            invalid_counts = ((df['balls'] + df['strikes']) > 5).sum()
            if invalid_counts > 0:
                issues.append(f"Found {invalid_counts} records with balls+strikes > 5")
        
        return issues
    
    def _validate_retrosheet_events(self, df: pd.DataFrame) -> List[str]:
        """Validate Retrosheet event codes"""
        issues = []
        
        if 'event' in df.columns:
            # Check for unknown event codes
            valid_events = ['S', 'D', 'T', 'H', 'W', 'K', 'E', 'FC', 'SB', 'CS', 'WP', 'PB']
            unknown_events = df[~df['event'].isin(valid_events)]['event'].unique()
            
            if len(unknown_events) > 0:
                issues.append(f"Found unknown event codes: {unknown_events}")
        
        return issues
    
    def _validate_game_sequences(self, df: pd.DataFrame) -> List[str]:
        """Validate that game events are in proper sequence"""
        issues = []
        
        if 'game_id' in df.columns and 'inning' in df.columns:
            # Check for duplicate game-inning combinations
            game_inning_counts = df.groupby(['game_id', 'inning']).size()
            unusual_counts = game_inning_counts[game_inning_counts > 6]  # More than 6 half-innings
            
            if len(unusual_counts) > 0:
                issues.append(f"Found {len(unusual_counts)} game-inning combinations with unusual event counts")
        
        return issues
    
    def _generate_summary_stats(self, df: pd.DataFrame) -> Dict[str, any]:
        """Generate summary statistics for the dataset"""
        stats = {
            'total_records': len(df),
            'date_range': None,
            'unique_games': 0,
            'unique_players': 0
        }
        
        # Date range
        if 'game_date' in df.columns:
            dates = pd.to_datetime(df['game_date'], errors='coerce')
            valid_dates = dates[dates.notna()]
            if len(valid_dates) > 0:
                stats['date_range'] = {
                    'start': valid_dates.min().strftime('%Y-%m-%d'),
                    'end': valid_dates.max().strftime('%Y-%m-%d')
                }
        
        # Unique games
        if 'game_id' in df.columns:
            stats['unique_games'] = df['game_id'].nunique()
        
        # Unique players
        player_columns = [col for col in ['batter', 'pitcher', 'batter_id'] if col in df.columns]
        if player_columns:
            all_players = pd.concat([df[col] for col in player_columns if col in df.columns])
            stats['unique_players'] = all_players.nunique()
        
        return stats
