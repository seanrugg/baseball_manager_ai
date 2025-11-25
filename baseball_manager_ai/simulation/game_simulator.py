"""
Game Simulator - Simulates complete baseball games with realistic outcomes.

Provides:
- At-bat outcome simulation
- Inning simulation
- Full game simulation
- Realistic probability distributions
- Game state tracking
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


class AtBatOutcome(Enum):
    """At-bat outcome types."""
    STRIKEOUT = 'strikeout'
    WALK = 'walk'
    SINGLE = 'single'
    DOUBLE = 'double'
    TRIPLE = 'triple'
    HOME_RUN = 'home_run'
    OUT = 'out'
    ERROR = 'error'


@dataclass
class InningState:
    """State tracking for half-inning."""
    inning: int
    team: str
    outs: int = 0
    bases: List[bool] = field(default_factory=lambda: [False, False, False])
    batter_index: int = 0
    runs_scored: int = 0
    pitches_thrown: int = 0
    plays: List[Dict] = field(default_factory=list)


@dataclass
class GameState:
    """Complete game state."""
    home_team: str
    away_team: str
    home_score: int = 0
    away_score: int = 0
    inning: int = 1
    outs: int = 0
    bases: List[bool] = field(default_factory=lambda: [False, False, False])
    current_batter: str = ''
    current_pitcher: str = ''
    game_log: List[Dict] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def advance_runners(self, bases_to_advance: int) -> int:
        """
        Advance all runners by specified bases.
        
        Args:
            bases_to_advance: Number of bases to advance
        
        Returns:
            Runs scored
        """
        runs = 0
        new_bases = [False, False, False]
        
        # Advance existing runners
        for base_idx in range(2, -1, -1):
            if self.bases[base_idx]:
                new_position = base_idx + bases_to_advance
                if new_position >= 3:
                    runs += 1
                else:
                    new_bases[new_position] = True
        
        self.bases = new_bases
        return runs
    
    def get_bases_string(self) -> str:
        """Get bases string representation (e.g., '1-3', '-2-')."""
        return ''.join(
            str(i + 1) if self.bases[i] else '-' for i in range(3)
        )


class GameSimulator:
    """Simulate baseball games with realistic outcomes."""
    
    def __init__(
        self,
        seed: Optional[int] = None,
        park_factor: float = 1.0
    ):
        """
        Initialize game simulator.
        
        Args:
            seed: Random seed for reproducibility
            park_factor: Park run environment factor (1.0 = neutral)
        """
        if seed is not None:
            np.random.seed(seed)
        
        self.park_factor = park_factor
        self.simulations_run = 0
    
    def simulate_game(
        self,
        home_team: str,
        away_team: str,
        home_lineup: List[Dict],
        away_lineup: List[Dict],
        home_pitcher: Dict,
        away_pitcher: Dict,
        max_innings: int = 9,
        verbose: bool = False
    ) -> GameState:
        """
        Simulate a complete baseball game.
        
        Args:
            home_team: Home team ID
            away_team: Away team ID
            home_lineup: Home team batting lineup
            away_lineup: Away team batting lineup
            home_pitcher: Home team pitcher stats
            away_pitcher: Away team pitcher stats
            max_innings: Maximum innings (9 or more for extras)
            verbose: Log detailed play-by-play
        
        Returns:
            GameState with final result
        """
        game = GameState(
            home_team=home_team,
            away_team=away_team
        )
        
        inning = 1
        
        while inning <= max_innings:
            # Away team bats (top of inning)
            runs = self._simulate_half_inning(
                game,
                away_team,
                away_lineup,
                home_pitcher,
                inning,
                is_home=False,
                verbose=verbose
            )
            game.away_score += runs
            
            # Check for walk-off (though away team can't walk off)
            game.outs = 0
            game.bases = [False, False, False]
            
            # Home team bats (bottom of inning)
            # Skip home team's last at-bat in 9+ innings if ahead
            if inning < max_innings or game.away_score > game.home_score:
                runs = self._simulate_half_inning(
                    game,
                    home_team,
                    home_lineup,
                    away_pitcher,
                    inning,
                    is_home=True,
                    verbose=verbose
                )
                game.home_score += runs
            
            # Check for walk-off in regulation
            if inning == 9 and game.home_score > game.away_score:
                break
            
            # Reset for next inning
            game.outs = 0
            game.bases = [False, False, False]
            inning += 1
        
        game.inning = inning
        self.simulations_run += 1
        
        return game
    
    def _simulate_half_inning(
        self,
        game: GameState,
        batting_team: str,
        lineup: List[Dict],
        pitcher: Dict,
        inning: int,
        is_home: bool = True,
        verbose: bool = False
    ) -> int:
        """
        Simulate one half-inning.
        
        Args:
            game: Current game state
            batting_team: Team batting
            lineup: Batting lineup
            pitcher: Pitcher stats
            inning: Current inning number
            is_home: True if home team batting
            verbose: Log details
        
        Returns:
            Runs scored in inning
        """
        inning_state = InningState(
            inning=inning,
            team=batting_team
        )
        
        pitcher_hand = pitcher.get('hand', 'R')
        
        while inning_state.outs < 3:
            # Get batter
            batter = lineup[inning_state.batter_index % len(lineup)]
            inning_state.batter_index += 1
            
            # Simulate at-bat
            outcome = self._simulate_at_bat(
                batter,
                pitcher,
                game.bases,
                inning_state.outs
            )
            
            # Process outcome
            runs = self._process_at_bat_outcome(
                game,
                outcome,
                inning_state
            )
            inning_state.runs_scored += runs
            
            if verbose:
                logger.info(
                    f"Inning {inning}: {batter.get('name', 'Unknown')} - "
                    f"{outcome.value} ({inning_state.runs_scored} runs)"
                )
            
            inning_state.pitches_thrown += np.random.randint(3, 7)
        
        game.game_log.append({
            'inning': inning,
            'team': batting_team,
            'runs': inning_state.runs_scored,
            'pitches': inning_state.pitches_thrown,
            'bases_at_end': game.get_bases_string()
        })
        
        return inning_state.runs_scored
    
    def _simulate_at_bat(
        self,
        batter: Dict,
        pitcher: Dict,
        bases: List[bool],
        outs: int,
        count: Tuple[int, int] = (0, 0)
    ) -> AtBatOutcome:
        """
        Simulate a single at-bat.
        
        Args:
            batter: Batter stats
            pitcher: Pitcher stats
            bases: Current base state
            outs: Current outs
            count: Current count (balls, strikes)
        
        Returns:
            At-bat outcome
        """
        # Extract key stats
        batter_ops = batter.get('season_ops', 0.750)
        batter_k_rate = batter.get('strikeout_rate', 0.215)
        batter_bb_rate = batter.get('walk_rate', 0.085)
        
        pitcher_era = pitcher.get('season_era', 4.0)
        pitcher_k9 = pitcher.get('season_k9', 8.5)
        
        # Normalize quality metrics
        batter_quality = (batter_ops / 0.750) if batter_ops > 0 else 1.0
        pitcher_quality = (4.0 / pitcher_era) if pitcher_era > 0 else 1.0
        
        # Calculate outcome probabilities
        # Strikeout rate increases with pitcher quality
        k_prob = batter_k_rate * pitcher_quality
        k_prob = min(0.40, k_prob)  # Cap at 40%
        
        # Walk rate increases with batter quality
        bb_prob = batter_bb_rate * batter_quality
        bb_prob = min(0.15, bb_prob)  # Cap at 15%
        
        # Contact rate = 1 - K rate
        contact_prob = 1.0 - k_prob
        
        # Hit probability on contact
        avg = batter.get('season_avg', 0.260)
        contact_hit_rate = avg / contact_prob if contact_prob > 0 else 0.3
        hit_prob = contact_prob * contact_hit_rate
        
        # Normalize to sum to 1
        total = k_prob + bb_prob + hit_prob
        if total > 1.0:
            k_prob /= total
            bb_prob /= total
            hit_prob /= total
            out_prob = 0.0
        else:
            out_prob = 1.0 - total
        
        # Determine outcome
        rand = np.random.random()
        
        if rand < k_prob:
            return AtBatOutcome.STRIKEOUT
        elif rand < k_prob + bb_prob:
            return AtBatOutcome.WALK
        elif rand < k_prob + bb_prob + hit_prob:
            # Hit type distribution
            hit_rand = np.random.random()
            iso = batter.get('iso', 0.160)
            
            if hit_rand < 0.65:
                return AtBatOutcome.SINGLE
            elif hit_rand < 0.85:
                return AtBatOutcome.DOUBLE
            elif hit_rand < 0.95:
                return AtBatOutcome.TRIPLE
            else:
                return AtBatOutcome.HOME_RUN
        else:
            return AtBatOutcome.OUT
    
    def _process_at_bat_outcome(
        self,
        game: GameState,
        outcome: AtBatOutcome,
        inning_state: InningState
    ) -> int:
        """
        Process at-bat outcome and update game state.
        
        Args:
            game: Current game state
            outcome: At-bat outcome
            inning_state: Inning state
        
        Returns:
            Runs scored from this play
        """
        runs = 0
        
        if outcome == AtBatOutcome.STRIKEOUT:
            inning_state.outs += 1
        
        elif outcome == AtBatOutcome.WALK:
            # Advance runners if bases loaded
            if all(game.bases):
                runs += 1
            
            # Move runners
            game.bases[2] = game.bases[1]
            game.bases[1] = game.bases[0]
            game.bases[0] = True
        
        elif outcome == AtBatOutcome.HOME_RUN:
            # Score all runners plus batter
            runs = 1 + sum(game.bases)
            game.bases = [False, False, False]
        
        elif outcome in [AtBatOutcome.SINGLE, AtBatOutcome.DOUBLE, AtBatOutcome.TRIPLE]:
            # Advance runners by hit distance
            bases_advance = {
                AtBatOutcome.SINGLE: 1,
                AtBatOutcome.DOUBLE: 2,
                AtBatOutcome.TRIPLE: 3
            }[outcome]
            
            # Score runners from 2nd and 3rd
            for base_idx in range(2, -1, -1):
                if game.bases[base_idx]:
                    if base_idx + bases_advance >= 3:
                        runs += 1
                    game.bases[base_idx] = False
            
            # Place batter on base
            if bases_advance < 3:
                game.bases[bases_advance - 1] = True
            else:
                runs += 1
        
        else:  # OUT or ERROR
            if outcome == AtBatOutcome.OUT:
                inning_state.outs += 1
            else:  # ERROR
                # Advance runners on error
                game.bases[2] = game.bases[1]
                game.bases[1] = game.bases[0]
                game.bases[0] = True
        
        return runs
    
    def simulate_multiple_games(
        self,
        home_team: str,
        away_team: str,
        home_lineup: List[Dict],
        away_lineup: List[Dict],
        home_pitcher: Dict,
        away_pitcher: Dict,
        num_games: int = 100,
        verbose: bool = False
    ) -> Dict:
        """
        Simulate multiple games and aggregate statistics.
        
        Args:
            home_team: Home team ID
            away_team: Away team ID
            home_lineup: Home lineup
            away_lineup: Away lineup
            home_pitcher: Home pitcher
            away_pitcher: Away pitcher
            num_games: Number of games to simulate
            verbose: Log details
        
        Returns:
            Aggregated statistics
        """
        logger.info(f"Simulating {num_games} games: {away_team} @ {home_team}")
        
        results = {
            'home_wins': 0,
            'away_wins': 0,
            'home_runs': [],
            'away_runs': [],
            'games': []
        }
        
        for game_num in range(num_games):
            game = self.simulate_game(
                home_team,
                away_team,
                home_lineup,
                away_lineup,
                home_pitcher,
                away_pitcher,
                verbose=verbose
            )
            
            if game.home_score > game.away_score:
                results['home_wins'] += 1
            else:
                results['away_wins'] += 1
            
            results['home_runs'].append(game.home_score)
            results['away_runs'].append(game.away_score)
            results['games'].append({
                'home_score': game.home_score,
                'away_score': game.away_score,
                'winner': 'home' if game.home_score > game.away_score else 'away',
                'innings': game.inning
            })
            
            if (game_num + 1) % max(1, num_games // 10) == 0:
                logger.info(f"  Completed {game_num + 1}/{num_games} simulations")
        
        # Calculate statistics
        results['home_win_percentage'] = results['home_wins'] / num_games
        results['away_win_percentage'] = results['away_wins'] / num_games
        results['avg_home_runs'] = np.mean(results['home_runs'])
        results['avg_away_runs'] = np.mean(results['away_runs'])
        results['std_home_runs'] = np.std(results['home_runs'])
        results['std_away_runs'] = np.std(results['away_runs'])
        
        logger.info(
            f"Results: {home_team} {results['home_wins']}-{results['away_wins']} "
            f"({results['home_win_percentage']:.1%})"
        )
        
        return results
