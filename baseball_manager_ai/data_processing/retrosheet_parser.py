"""
Retrosheet data parser.
Handles Retrosheet event file parsing and processing.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class RetrosheetParser:
    """Parser for Retrosheet event files"""
    
    def __init__(self, data_dir: str = "data/raw/retrosheet"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Retrosheet event codes
        self.event_codes = {
            'S': 'single', 'D': 'double', 'T': 'triple', 'H': 'home_run',
            'W': 'walk', 'K': 'strikeout', 'E': 'error', 'FC': 'fielders_choice',
            'SB': 'stolen_base', 'CS': 'caught_stealing'
        }
    
    def parse_event_file(self, filepath: str) -> pd.DataFrame:
        """
        Parse a Retrosheet .EVA or .EVN file.
        
        Args:
            filepath: Path to Retrosheet event file
            
        Returns:
            DataFrame with parsed event data
        """
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()
            
            events = []
            current_game = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('id,'):
                    # New game
                    if current_game:
                        events.extend(self._process_game_events(current_game))
                    current_game = {'id': line.split(',')[1], 'events': []}
                elif line.startswith('play,'):
                    # Play event
                    current_game['events'].append(line)
                elif line.startswith('info,'):
                    # Game info
                    parts = line.split(',')
                    if len(parts) >= 3:
                        current_game[parts[1]] = parts[2]
            
            # Process final game
            if current_game:
                events.extend(self._process_game_events(current_game))
            
            df = pd.DataFrame(events)
            logger.info(f"Parsed {len(df)} events from {filepath}")
            return df
            
        except Exception as e:
            logger.error(f"Error parsing Retrosheet file {filepath}: {e}")
            return pd.DataFrame()
    
    def _process_game_events(self, game_data: Dict) -> List[Dict]:
        """Process all events for a single game"""
        events = []
        
        for event_line in game_data.get('events', []):
            event = self._parse_play_event(event_line, game_data)
            if event:
                events.append(event)
        
        return events
    
    def _parse_play_event(self, event_line: str, game_data: Dict) -> Optional[Dict]:
        """Parse a single play event line"""
        try:
            parts = event_line.split(',')
            if len(parts) < 6:
                return None
            
            event_data = {
                'game_id': game_data.get('id', ''),
                'inning': parts[1],
                'team': parts[2],
                'batter_id': parts[3],
                'count': parts[4],
                'pitches': parts[5],
                'event': parts[6] if len(parts) > 6 else '',
                'runners': parts[7] if len(parts) > 7 else ''
            }
            
            # Add game context
            event_data.update({
                'home_team': game_data.get('hometeam', ''),
                'away_team': game_data.get('visteam', ''),
                'date': game_data.get('date', ''),
                'start_time': game_data.get('starttime', ''),
            })
            
            # Parse event details
            event_data.update(self._parse_event_details(event_data['event']))
            
            return event_data
            
        except Exception as e:
            logger.warning(f"Error parsing event line: {event_line}, error: {e}")
            return None
    
    def _parse_event_details(self, event_str: str) -> Dict:
        """Parse event string for detailed event information"""
        details = {}
        
        # Basic event type
        if event_str in self.event_codes:
            details['event_type'] = self.event_codes[event_str]
        else:
            details['event_type'] = 'other'
        
        # Parse modifiers (e.g., SB2 = stolen base 2nd, HR9 = home run to center?)
        if event_str.startswith('SB'):
            details['event_type'] = 'stolen_base'
            details['stolen_base'] = '2B' if '2' in event_str else 'base'
        elif event_str.startswith('CS'):
            details['event_type'] = 'caught_stealing'
        elif event_str.startswith('WP') or event_str.startswith('PB'):
            details['event_type'] = 'wild_pitch' if event_str.startswith('WP') else 'passed_ball'
        
        return details
    
    def load_season_data(self, year: int) -> pd.DataFrame:
        """
        Load and parse Retrosheet data for a full season.
        
        Args:
            year: Season year
            
        Returns:
            DataFrame with season event data
        """
        events = []
        
        # Look for event files for the given year
        pattern = f"*{year}*.EV*"
        event_files = list(self.data_dir.glob(pattern))
        
        for filepath in event_files:
            logger.info(f"Parsing Retrosheet file: {filepath}")
            df = self.parse_event_file(str(filepath))
            events.append(df)
        
        if events:
            combined_df = pd.concat(events, ignore_index=True)
            logger.info(f"Loaded {len(combined_df)} events for {year} season")
            return combined_df
        else:
            logger.warning(f"No Retrosheet files found for {year}")
            return pd.DataFrame()
