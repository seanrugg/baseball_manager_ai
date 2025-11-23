#!/usr/bin/env python
"""
Run game simulations to evaluate manager decisions and strategies.

Simulates baseball games using trained models to:
- Evaluate decision quality (WPA - Win Probability Added)
- Compare different strategies
- Test lineup optimizations
- Benchmark against historical managers

Usage:
    python scripts/run_simulation.py --home-team NYY --away-team BOS --games 1000
    python scripts/run_simulation.py --scenario game_state.json --iterations 10000
    python scripts/run_simulation.py --strategy comparison --output results/
"""

import argparse
import logging
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import json
import yaml
from datetime import datetime
import pickle

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/run_simulation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GameSimulator:
    """Simulate baseball games."""
    
    def __init__(
        self,
        config_path: Path = Path('config/simulation_config.yaml'),
        model_dir: Path = Path('models')
    ):
        """
        Initialize game simulator.
        
        Args:
            config_path: Path to simulation configuration
            model_dir: Path to trained models directory
        """
        self.config_path = config_path
        self.model_dir = model_dir
        self.config = self._load_config(config_path)
        self.models = {}
        self.scalers = {}
        
        self._load_models()
    
    def _load_config(self, config_path: Path) -> Dict:
        """Load simulation configuration."""
        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}")
            return {}
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Loaded simulation config from {config_path}")
        return config
    
    def _load_models(self) -> None:
        """Load trained models from disk."""
        logger.info("Loading trained models...")
        
        model_files = list(self.model_dir.glob('*_latest.pkl'))
        
        if not model_files:
            logger.warning("No trained models found in model directory")
            logger.info("Train models with: python scripts/train_model.py")
            return
        
        for model_file in model_files:
            model_name = model_file.stem.replace('_latest', '')
            
            try:
                with open(model_file, 'rb') as f:
                    model = pickle.load(f)
                
                self.models[model_name] = model
                logger.info(f"✓ Loaded {model_name}")
                
                # Load corresponding scaler
                scaler_file = self.model_dir / f'{model_name}_scaler_latest.pkl'
                if scaler_file.exists():
                    with open(scaler_file, 'rb') as f:
                        scaler = pickle.load(f)
                    
                    self.scalers[model_name] = scaler
            
            except Exception as e:
                logger.error(f"Failed to load {model_name}: {e}")
    
    def simulate_at_bat(
        self,
        batter_stats: Dict,
        pitcher_stats: Dict,
        bases: Tuple[bool, bool, bool],
        outs: int,
        count: Tuple[int, int] = (0, 0)
    ) -> Dict:
        """
        Simulate a single at-bat outcome.
        
        Args:
            batter_stats: Batter statistics
            pitcher_stats: Pitcher statistics
            bases: (first, second, third) occupied
            outs: Current outs (0-2)
            count: (balls, strikes)
        
        Returns:
            Dictionary with at-bat outcome
        """
        # Simplified outcome probabilities based on matchup
        batter_ops = batter_stats.get('season_ops', 0.750)
        pitcher_era = pitcher_stats.get('season_era', 4.0)
        
        # Normalize
        batter_quality = (batter_ops / 0.750) if batter_ops > 0 else 1.0
        pitcher_quality = (4.0 / pitcher_era) if pitcher_era > 0 else 1.0
        
        # Base outcome probabilities
        k_prob = 0.215 * pitcher_quality
        bb_prob = 0.085 * batter_quality
        hit_prob = 0.246 * batter_quality / pitcher_quality
        
        # Normalize
        total = k_prob + bb_prob + hit_prob
        k_prob /= total
        bb_prob /= total
        hit_prob /= total
        
        # Determine outcome
        rand = np.random.random()
        
        if rand < k_prob:
            outcome = 'strikeout'
            runners_advanced = 0
        elif rand < k_prob + bb_prob:
            outcome = 'walk'
            runners_advanced = 0
        elif rand < k_prob + bb_prob + hit_prob:
            # Hit type distribution
            hit_rand = np.random.random()
            if hit_rand < 0.65:
                outcome = 'single'
                runners_advanced = 1
            elif hit_rand < 0.85:
                outcome = 'double'
                runners_advanced = 2
            elif hit_rand < 0.95:
                outcome = 'triple'
                runners_advanced = 3
            else:
                outcome = 'home_run'
                runners_advanced = 4
        else:
            outcome = 'out'
            runners_advanced = 0
        
        return {
            'outcome': outcome,
            'runners_advanced': runners_advanced,
            'runs_scored': 0  # Simplified; would calculate properly
        }
    
    def simulate_inning(
        self,
        team_id: str,
        lineup: List[str],
        opposing_pitcher: Dict,
        bases: Tuple[bool, bool, bool],
        outs: int,
        player_stats: Dict[str, Dict]
    ) -> Tuple[int, Tuple[bool, bool, bool], int]:
        """
        Simulate a half-inning.
        
        Args:
            team_id: Team identifier
            lineup: List of batter IDs in order
            opposing_pitcher: Pitcher statistics
            bases: (first, second, third) occupied
            outs: Current outs
            player_stats: Dictionary of all player statistics
        
        Returns:
            Tuple of (runs_scored, final_bases, final_outs)
        """
        runs_scored = 0
        current_bases = list(bases)
        current_outs = outs
        lineup_position = 0
        
        while current_outs < 3 and lineup_position < len(lineup):
            batter_id = lineup[lineup_position]
            batter_stats = player_stats.get(batter_id, {})
            
            # Simulate at-bat
            ab_result = self.simulate_at_bat(
                batter_stats,
                opposing_pitcher,
                tuple(current_bases),
                current_outs
            )
            
            # Process outcome
            if ab_result['outcome'] == 'strikeout':
                current_outs += 1
            elif ab_result['outcome'] == 'walk':
                # Move runners
                if current_bases[2]:
                    runs_scored += 1
                current_bases[2] = current_bases[1]
                current_bases[1] = current_bases[0]
                current_bases[0] = True
            elif ab_result['outcome'] == 'home_run':
                # Score everyone
                runs_scored += 1 + sum(current_bases)
                current_bases = [False, False, False]
            elif ab_result['outcome'] in ['single', 'double', 'triple']:
                # Advance runners
                runners_adv = ab_result['runners_advanced']
                
                for base in range(2, -1, -1):
                    if current_bases[base]:
                        new_base = base + runners_adv
                        if new_base >= 3:
                            runs_scored += 1
                        else:
                            current_bases[new_base] = True
                        current_bases[base] = False
                
                current_bases[runners_adv - 1] = True
            else:  # out (non-strikeout)
                current_outs += 1
            
            lineup_position += 1
        
        return runs_scored, tuple(current_bases), current_outs
    
    def simulate_game(
        self,
        home_team: str,
        away_team: str,
        player_stats: Dict[str, Dict],
        home_lineup: List[str],
        away_lineup: List[str]
    ) -> Dict:
        """
        Simulate a complete baseball game.
        
        Args:
            home_team: Home team ID
            away_team: Away team ID
            player_stats: Dictionary of all player statistics
            home_lineup: Home team batting order
            away_lineup: Away team batting order
        
        Returns:
            Game result dictionary
        """
        home_score = 0
        away_score = 0
        inning = 1
        max_innings = 9
        
        # Use dummy pitcher stats for simulation
        dummy_pitcher = {'season_era': 4.0}
        
        game_log = []
        
        while inning <= max_innings:
            # Away team bats
            runs, _, _ = self.simulate_inning(
                away_team,
                away_lineup,
                dummy_pitcher,
                (False, False, False),
                0,
                player_stats
            )
            away_score += runs
            
            # Home team bats (only if not already winning in 9th)
            if inning < 9 or away_score <= home_score:
                runs, _, _ = self.simulate_inning(
                    home_team,
                    home_lineup,
                    dummy_pitcher,
                    (False, False, False),
                    0,
                    player_stats
                )
                home_score += runs
            
            game_log.append({
                'inning': inning,
                'home_score': home_score,
                'away_score': away_score
            })
            
            # Check for winner
            if inning >= 9 and home_score != away_score:
                break
            
            inning += 1
        
        winner = 'home' if home_score > away_score else 'away'
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_score': home_score,
            'away_score': away_score,
            'winner': winner,
            'innings_played': inning,
            'game_log': game_log
        }
    
    def run_simulation_series(
        self,
        home_team: str,
        away_team: str,
        num_games: int = 1000,
        player_stats: Optional[Dict] = None
    ) -> Dict:
        """
        Run multiple game simulations.
        
        Args:
            home_team: Home team ID
            away_team: Away team ID
            num_games: Number of games to simulate
            player_stats: Player statistics dictionary
        
        Returns:
            Dictionary with simulation results
        """
        logger.info(f"Simulating {num_games} games: {away_team} @ {home_team}")
        
        if player_stats is None:
            player_stats = {}
        
        # Generate dummy lineups
        home_lineup = [f'{home_team}_batter_{i}' for i in range(9)]
        away_lineup = [f'{away_team}_batter_{i}' for i in range(9)]
        
        results = {
            'home_wins': 0,
            'away_wins': 0,
            'total_home_runs': 0,
            'total_away_runs': 0,
            'games': []
        }
        
        for game_num in range(num_games):
            game_result = self.simulate_game(
                home_team,
                away_team,
                player_stats,
                home_lineup,
                away_lineup
            )
            
            if game_result['winner'] == 'home':
                results['home_wins'] += 1
            else:
                results['away_wins'] += 1
            
            results['total_home_runs'] += game_result['home_score']
            results['total_away_runs'] += game_result['away_score']
            
            if game_num % 100 == 0:
                logger.info(f"  Completed {game_num}/{num_games} simulations")
        
        # Calculate statistics
        results['home_win_percentage'] = results['home_wins'] / num_games
        results['away_win_percentage'] = results['away_wins'] / num_games
        results['avg_home_runs'] = results['total_home_runs'] / num_games
        results['avg_away_runs'] = results['total_away_runs'] / num_games
        
        return results
    
    def save_results(self, results: Dict, output_dir: Path) -> None:
        """
        Save simulation results to disk.
        
        Args:
            results: Simulation results dictionary
            output_dir: Output directory
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f'simulation_results_{timestamp}.json'
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"✓ Results saved to {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run game simulations to evaluate manager decisions'
    )
    
    parser.add_argument(
        '--home-team',
        default='HOME',
        help='Home team ID'
    )
    
    parser.add_argument(
        '--away-team',
        default='AWAY',
        help='Away team ID'
    )
    
    parser.add_argument(
        '--games',
        type=int,
        default=1000,
        help='Number of games to simulate'
    )
    
    parser.add_argument(
        '--config',
        type=Path,
        default=Path('config/simulation_config.yaml'),
        help='Simulation configuration file'
    )
    
    parser.add_argument(
        '--model-dir',
        type=Path,
        default=Path('models'),
        help='Trained models directory'
    )
    
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('results'),
        help='Output directory for results'
    )
    
    parser.add_argument(
        '--player-stats',
        type=Path,
        help='Path to player statistics file (JSON)'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("BASEBALL MANAGER AI - SIMULATION ENGINE")
    logger.info("=" * 60)
    
    simulator = GameSimulator(
        config_path=args.config,
        model_dir=args.model_dir
    )
    
    # Load player statistics if provided
    player_stats = {}
    if args.player_stats and args.player_stats.exists():
        with open(args.player_stats, 'r') as f:
            player_stats = json.load(f)
        logger.info(f"Loaded stats for {len(player_stats)} players")
    
    # Run simulation
    results = simulator.run_simulation_series(
        home_team=args.home_team,
        away_team=args.away_team,
        num_games=args.games,
        player_stats=player_stats
    )
    
    # Display summary
    logger.info("=" * 60)
    logger.info("SIMULATION RESULTS")
    logger.info("=" * 60)
    logger.info(f"{args.home_team}: {results['home_wins']} wins ({results['home_win_percentage']:.1%})")
    logger.info(f"{args.away_team}: {results['away_wins']} wins ({results['away_win_percentage']:.1%})")
    logger.info(f"Avg runs per game: {results['avg_home_runs']:.2f} (home) vs {results['avg_away_runs']:.2f} (away)")
    logger.info("=" * 60)
    
    # Save results
    simulator.save_results(results, args.output)
    
    logger.info("Simulation complete!")


if __name__ == '__main__':
    main()
