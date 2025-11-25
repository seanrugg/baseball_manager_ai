"""
Lineup Optimizer - Optimizes batting order based on player matchups and context.

Predicts optimal batting positions for given players considering:
- Player strengths and weaknesses
- Pitcher matchups
- Game situation
- Team composition
"""

import logging
from typing import List, Dict, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler

from .base_manager import BaseManager

logger = logging.getLogger(__name__)


class LineupOptimizer(BaseManager):
    """Optimize batting lineups for maximum run production."""
    
    def __init__(self, random_state: int = 42):
        """
        Initialize Lineup Optimizer.
        
        Args:
            random_state: Random seed for reproducibility
        """
        super().__init__(
            model_name='lineup_optimizer',
            model_type='classifier',
            random_state=random_state
        )
        
        # Model configuration
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=random_state,
            verbose=0
        )
        
        self.scaler = StandardScaler()
    
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        validation_split: float = 0.2,
        **kwargs
    ) -> None:
        """
        Fit lineup optimizer to training data.
        
        Expected features include:
        - Player stats (AVG, OBP, SLG, strikeout rate, etc.)
        - Pitcher stats (ERA, handedness, etc.)
        - Game context (inning, score diff, etc.)
        
        Expected target: optimal batting position (1-9)
        
        Args:
            X: Training features
            y: Training targets (batting positions)
            validation_split: Proportion for validation
            **kwargs: Additional training arguments
        """
        logger.info(f"Fitting {self.model_name} with {len(X)} samples")
        
        # Store feature names
        self.feature_names = X.columns.tolist()
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Fit model
        self.model.fit(X_scaled, y)
        
        self.is_fitted = True
        
        # Log training summary
        train_score = self.model.score(X_scaled, y)
        logger.info(f"Training accuracy: {train_score:.4f}")
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict optimal batting positions.
        
        Args:
            X: Player and game features
        
        Returns:
            Predicted batting positions (1-9)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        X_prepared = self._prepare_features(X)
        predictions = self.model.predict(X_prepared)
        
        # Ensure valid positions (1-9)
        predictions = np.clip(predictions, 1, 9).astype(int)
        
        return predictions
    
    def optimize_lineup(
        self,
        players: List[Dict],
        opposing_pitcher: Dict,
        game_context: Dict
    ) -> List[Tuple[str, int]]:
        """
        Generate optimal batting order for given players.
        
        Args:
            players: List of player stats dictionaries
            opposing_pitcher: Opposing pitcher stats
            game_context: Game situation (inning, score, etc.)
        
        Returns:
            List of (player_id, position) tuples in optimal order
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before optimization")
        
        # Create feature matrix for each player
        feature_list = []
        player_ids = []
        
        for player in players:
            features = self._create_player_features(
                player,
                opposing_pitcher,
                game_context
            )
            feature_list.append(features)
            player_ids.append(player.get('player_id', 'unknown'))
        
        X = pd.DataFrame(feature_list)
        
        # Get predicted positions
        positions = self.predict(X)
        
        # Create lineup (sort by predicted position)
        lineup = list(zip(player_ids, positions))
        lineup.sort(key=lambda x: x[1])
        
        logger.info("Generated optimized lineup:")
        for idx, (player_id, pos) in enumerate(lineup, 1):
            logger.info(f"  {idx}. {player_id} (predicted pos: {pos})")
        
        return lineup
    
    def _create_player_features(
        self,
        player: Dict,
        opposing_pitcher: Dict,
        game_context: Dict
    ) -> Dict:
        """
        Create feature vector for a player in context.
        
        Args:
            player: Player statistics
            opposing_pitcher: Opposing pitcher stats
            game_context: Game situation
        
        Returns:
            Feature dictionary
        """
        features = {}
        
        # Player offensive stats
        features['avg'] = float(player.get('season_avg', 0.260))
        features['obp'] = float(player.get('season_obp', 0.330))
        features['slg'] = float(player.get('season_slg', 0.420))
        features['ops'] = float(player.get('season_ops', 0.750))
        features['strikeout_rate'] = float(player.get('strikeout_rate', 0.200))
        features['walk_rate'] = float(player.get('walk_rate', 0.080))
        features['iso'] = float(player.get('iso', 0.160))
        
        # Handedness matchup
        player_hand = player.get('hand', 'R')
        pitcher_hand = opposing_pitcher.get('hand', 'R')
        
        if player_hand == 'L' and pitcher_hand == 'R':
            features['vs_pitcher_avg'] = float(player.get('vs_rhp_avg', 0.260))
            features['vs_pitcher_obp'] = float(player.get('vs_rhp_obp', 0.330))
        elif player_hand == 'R' and pitcher_hand == 'L':
            features['vs_pitcher_avg'] = float(player.get('vs_lhp_avg', 0.260))
            features['vs_pitcher_obp'] = float(player.get('vs_lhp_obp', 0.330))
        else:
            features['vs_pitcher_avg'] = float(player.get('season_avg', 0.260))
            features['vs_pitcher_obp'] = float(player.get('season_obp', 0.330))
        
        # Recent performance
        features['recent_avg'] = float(player.get('recent_avg', 0.260))
        features['trend'] = (
            float(player.get('recent_avg', 0.260)) - 
            float(player.get('season_avg', 0.260))
        )
        
        # Situational stats
        features['risp_avg'] = float(player.get('risp_avg', 0.260))
        
        # Game context
        features['game_importance'] = float(game_context.get('game_importance', 0.5))
        features['is_home'] = 1.0 if game_context.get('is_home', False) else 0.0
        
        # Pitcher stats
        features['pitcher_era'] = float(opposing_pitcher.get('season_era', 4.0))
        features['pitcher_k9'] = float(opposing_pitcher.get('season_k9', 8.5))
        
        return features
    
    def suggest_leadoff_hitter(
        self,
        players: List[Dict],
        opposing_pitcher: Dict
    ) -> str:
        """
        Identify best leadoff hitter from roster.
        
        Leadoff should have: high OBP, speed, ability to get on base
        
        Args:
            players: List of player stats
            opposing_pitcher: Opposing pitcher stats
        
        Returns:
            Player ID of recommended leadoff hitter
        """
        if not self.is_fitted:
            logger.warning("Model not fitted; using heuristic")
            return self._heuristic_leadoff(players, opposing_pitcher)
        
        # Calculate leadoff score (OBP weight heavily)
        leadoff_scores = []
        
        for player in players:
            obp = float(player.get('season_obp', 0.330))
            avg = float(player.get('season_avg', 0.260))
            walk_rate = float(player.get('walk_rate', 0.080))
            
            # Leadoff score: prioritize OBP and walk rate
            score = (obp * 0.5) + (walk_rate * 0.3) + (avg * 0.2)
            
            leadoff_scores.append((player.get('player_id'), score))
        
        leadoff_scores.sort(key=lambda x: x[1], reverse=True)
        
        if leadoff_scores:
            best_leadoff = leadoff_scores[0][0]
            logger.info(f"Recommended leadoff: {best_leadoff}")
            return best_leadoff
        
        return players[0].get('player_id', 'unknown')
    
    def _heuristic_leadoff(
        self,
        players: List[Dict],
        opposing_pitcher: Dict
    ) -> str:
        """
        Heuristic-based leadoff recommendation.
        
        Args:
            players: List of player stats
            opposing_pitcher: Opposing pitcher stats
        
        Returns:
            Player ID
        """
        # Sort by OBP
        sorted_players = sorted(
            players,
            key=lambda p: float(p.get('season_obp', 0.330)),
            reverse=True
        )
        
        if sorted_players:
            return sorted_players[0].get('player_id', 'unknown')
        
        return 'unknown'
    
    def suggest_cleanup_hitter(
        self,
        players: List[Dict],
        opposing_pitcher: Dict
    ) -> str:
        """
        Identify best cleanup hitter (4th spot).
        
        Cleanup should have: high power, high RBI potential
        
        Args:
            players: List of player stats
            opposing_pitcher: Opposing pitcher stats
        
        Returns:
            Player ID of recommended cleanup hitter
        """
        # Calculate cleanup score (SLG and ISO weight heavily)
        cleanup_scores = []
        
        for player in players:
            slg = float(player.get('season_slg', 0.420))
            iso = float(player.get('iso', 0.160))
            risp_avg = float(player.get('risp_avg', 0.260))
            
            # Cleanup score: prioritize power
            score = (slg * 0.5) + (iso * 0.35) + (risp_avg * 0.15)
            
            cleanup_scores.append((player.get('player_id'), score))
        
        cleanup_scores.sort(key=lambda x: x[1], reverse=True)
        
        if cleanup_scores:
            best_cleanup = cleanup_scores[0][0]
            logger.info(f"Recommended cleanup: {best_cleanup}")
            return best_cleanup
        
        return players[0].get('player_id', 'unknown')
