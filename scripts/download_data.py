#!/usr/bin/env python
"""
Download baseball data from multiple sources.

Supported sources:
- Statcast (pitch-by-pitch data from Baseball Savant)
- Retrosheet (game logs and play-by-play)
- MLB Stats API (real-time data)
- Baseball Reference (historical player stats)

Usage:
    python scripts/download_data.py --sources statcast retrosheet --seasons 2020 2021 2022
    python scripts/download_data.py --sources all --seasons 2024
"""

import argparse
import logging
from pathlib import Path
from typing import List, Optional
import requests
import pandas as pd
from datetime import datetime
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/download_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataDownloader:
    """Download baseball data from multiple sources."""
    
    def __init__(self, data_dir: Path = Path('data')):
        """
        Initialize downloader.
        
        Args:
            data_dir: Base directory for data storage
        """
        self.data_dir = data_dir
        self.raw_dir = data_dir / 'raw'
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        for subdir in ['statcast', 'retrosheet', 'baseball_reference']:
            (self.raw_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    def download_statcast(
        self,
        seasons: List[int],
        verify_ssl: bool = True,
        timeout: int = 30
    ) -> None:
        """
        Download Statcast data from Baseball Savant.
        
        Args:
            seasons: List of seasons to download (e.g., [2020, 2021])
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
        """
        logger.info(f"Downloading Statcast data for seasons: {seasons}")
        
        for season in seasons:
            try:
                # Use pybaseball if available, otherwise construct URL
                output_path = self.raw_dir / 'statcast' / f'statcast_{season}.csv'
                
                if output_path.exists():
                    logger.info(f"Statcast {season} already exists at {output_path}")
                    continue
                
                logger.info(f"Downloading Statcast data for {season}...")
                
                # Try importing pybaseball
                try:
                    from pybaseball import statcast
                    
                    df = statcast(start_dt=f'{season}-03-01', end_dt=f'{season}-11-30')
                    
                    if df is not None and len(df) > 0:
                        df.to_csv(output_path, index=False)
                        logger.info(f"✓ Downloaded {len(df)} pitches for {season}")
                    else:
                        logger.warning(f"No data returned for Statcast {season}")
                
                except ImportError:
                    logger.error(
                        "pybaseball not installed. Install with: pip install pybaseball"
                    )
                    logger.info(
                        f"Alternatively, download manually from: "
                        f"https://baseballsavant.mlb.com/statcast"
                    )
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Failed to download Statcast {season}: {e}")
    
    def download_retrosheet(
        self,
        seasons: List[int],
        include_events: bool = True,
        include_game_logs: bool = True
    ) -> None:
        """
        Download Retrosheet data.
        
        Args:
            seasons: List of seasons to download
            include_events: Download event files (play-by-play)
            include_game_logs: Download game logs
        """
        logger.info(f"Downloading Retrosheet data for seasons: {seasons}")
        
        for season in seasons:
            try:
                if include_game_logs:
                    self._download_retrosheet_game_logs(season)
                
                if include_events:
                    self._download_retrosheet_events(season)
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Failed to download Retrosheet {season}: {e}")
    
    def _download_retrosheet_game_logs(self, season: int) -> None:
        """Download Retrosheet game logs for a season."""
        output_path = self.raw_dir / 'retrosheet' / f'gamelogs_{season}.csv'
        
        if output_path.exists():
            logger.info(f"Retrosheet game logs {season} already exists")
            return
        
        logger.info(f"Downloading Retrosheet game logs for {season}...")
        
        try:
            from pybaseball import playerid_reverse_lookup
            # Alternative: use Retrosheet directly
            logger.info(
                "Download game logs manually from: "
                f"https://www.retrosheet.org/gamelogs/index.html"
            )
        except Exception as e:
            logger.warning(f"Could not auto-download game logs: {e}")
    
    def _download_retrosheet_events(self, season: int) -> None:
        """Download Retrosheet event files for a season."""
        output_path = self.raw_dir / 'retrosheet' / f'events_{season}.csv'
        
        if output_path.exists():
            logger.info(f"Retrosheet events {season} already exists")
            return
        
        logger.info(f"Downloading Retrosheet events for {season}...")
        logger.info(
            "Download event files manually from: "
            f"https://www.retrosheet.org/game.htm"
        )
    
    def download_baseball_reference(
        self,
        season: int,
        include_batting: bool = True,
        include_pitching: bool = True,
        include_fielding: bool = False
    ) -> None:
        """
        Download player stats from Baseball Reference.
        
        Args:
            season: Season to download
            include_batting: Download batting stats
            include_pitching: Download pitching stats
            include_fielding: Download fielding stats
        """
        logger.info(f"Downloading Baseball Reference data for {season}")
        
        try:
            from pybaseball import playerid_reverse_lookup, statcast_pitcher
            
            if include_batting:
                logger.info(f"Downloading batting stats for {season}...")
                batting_path = self.raw_dir / 'baseball_reference' / f'batting_{season}.csv'
                
                if not batting_path.exists():
                    # Placeholder - actual implementation depends on pybaseball version
                    logger.info(
                        "Download batting stats manually from: "
                        f"https://www.baseball-reference.com/leagues/majors/{season}/"
                    )
            
            if include_pitching:
                logger.info(f"Downloading pitching stats for {season}...")
                pitching_path = self.raw_dir / 'baseball_reference' / f'pitching_{season}.csv'
                
                if not pitching_path.exists():
                    logger.info(
                        "Download pitching stats manually from: "
                        f"https://www.baseball-reference.com/leagues/majors/{season}/"
                    )
        
        except Exception as e:
            logger.error(f"Failed to download Baseball Reference data: {e}")
    
    def download_mlb_statsapi(self, season: int) -> None:
        """
        Download current season data from MLB Stats API.
        
        Args:
            season: Season to download
        """
        logger.info(f"Downloading MLB Stats API data for {season}")
        
        try:
            output_dir = self.raw_dir / 'mlb_statsapi'
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Schedule data
            schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&season={season}"
            response = requests.get(schedule_url, timeout=30)
            response.raise_for_status()
            
            schedule_data = response.json()
            schedule_path = output_dir / f'schedule_{season}.json'
            
            with open(schedule_path, 'w') as f:
                json.dump(schedule_data, f, indent=2)
            
            logger.info(f"✓ Downloaded schedule for {season}")
        
        except Exception as e:
            logger.error(f"Failed to download MLB Stats API data: {e}")
    
    def validate_downloads(self) -> None:
        """Validate downloaded files and report status."""
        logger.info("Validating downloaded data...")
        
        manifest = {
            'timestamp': datetime.now().isoformat(),
            'directories': {}
        }
        
        for subdir in self.raw_dir.iterdir():
            if subdir.is_dir():
                files = list(subdir.glob('*'))
                manifest['directories'][subdir.name] = {
                    'file_count': len(files),
                    'files': [f.name for f in files],
                    'total_size_mb': sum(f.stat().st_size for f in files) / (1024 * 1024)
                }
                logger.info(
                    f"{subdir.name}: {len(files)} files, "
                    f"{manifest['directories'][subdir.name]['total_size_mb']:.1f} MB"
                )
        
        manifest_path = self.data_dir / 'manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"✓ Validation complete. Manifest saved to {manifest_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Download baseball data from multiple sources'
    )
    
    parser.add_argument(
        '--sources',
        nargs='+',
        choices=['statcast', 'retrosheet', 'baseball_reference', 'mlb_statsapi', 'all'],
        default=['all'],
        help='Data sources to download'
    )
    
    parser.add_argument(
        '--seasons',
        nargs='+',
        type=int,
        default=[2024],
        help='Seasons to download (e.g., 2020 2021 2022)'
    )
    
    parser.add_argument(
        '--data-dir',
        type=Path,
        default=Path('data'),
        help='Base data directory'
    )
    
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate existing downloads'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("BASEBALL MANAGER AI - DATA DOWNLOADER")
    logger.info("=" * 60)
    
    downloader = DataDownloader(args.data_dir)
    
    # Expand 'all' to all sources
    sources = args.sources
    if 'all' in sources:
        sources = ['statcast', 'retrosheet', 'baseball_reference', 'mlb_statsapi']
    
    if args.validate_only:
        logger.info("Validation mode - checking existing downloads")
        downloader.validate_downloads()
    else:
        logger.info(f"Downloading from: {sources}")
        logger.info(f"Seasons: {args.seasons}")
        
        if 'statcast' in sources:
            downloader.download_statcast(args.seasons)
        
        if 'retrosheet' in sources:
            downloader.download_retrosheet(args.seasons)
        
        if 'baseball_reference' in sources:
            for season in args.seasons:
                downloader.download_baseball_reference(season)
        
        if 'mlb_statsapi' in sources:
            for season in args.seasons:
                downloader.download_mlb_statsapi(season)
        
        downloader.validate_downloads()
    
    logger.info("=" * 60)
    logger.info("Download complete!")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
