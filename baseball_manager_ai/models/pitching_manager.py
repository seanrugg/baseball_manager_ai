"""
Pitching Manager - Pitcher selection and rotation management.

Makes decisions on:
- When to replace pitcher
- Which reliever to use
- Rest and recovery management
- Rotation planning
- Matchup optimization (pitcher vs batter)
"""

import logging
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler

from .base_manager import BaseManager

logger = logging.getLogger(__name__)


class PitchingManager(BaseManager):
    """Manage pitching decisions and rotation."""
    
    # Pitcher roles
    ROLES = ['starter', 'reliever', 'closer', 'long_relief', 'middle_relief', 'setup']
    
    def __init__(self, random_state: int = 42):
        """
        Initialize Pitching Manager.
        
        Args:
            random_state: Random seed
        """
        super().__init__(
            model_name='pitching_manager',
            model_type='classifier',
            random_state=random_state
        )
        
        self.model = GradientBoostingClassifier(
            n_estimators=150,
            max_depth=8,
            learning_rate=0.1,
            subsample=0.8,
            random_state=random_state
        )
        
        self.scaler = StandardScaler()
    
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        **kwargs
    ) -> None:
        """
        Fit pitching manager model.
        
        Expected features:
        - Pitcher stats (ERA, K/9, BB/9, recent performance)
        - Fatigue metrics (pitch count, recent usage, rest)
        - Game state (inning, score, runners, outs)
        - Batter stats and matchup history
        - Team bullpen depth
        
        Expected target: pitcher change decision (0=keep, 1=replace)
        
        Args:
            X: Training features
            y: Training targets
            **kwargs: Additional training arguments
        """
        logger.info(f"Fitting {self.model_name} with {len(X)} samples")
        
        self.feature_names = X.columns.tolist()
        
        X_scaled = self.scaler.fit_transform(X)
        
        self.model.fit(X_scaled, y)
        
        self.is_fitted = True
        
        train_score = self.model.score(X_scaled, y)
        logger.info(f"Training accuracy: {train_score:.4f}")
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict pitcher change decisions.
        
        Args:
            X: Pitcher and game state features
        
        Returns:
            Binary predictions (0=keep pitcher, 1=replace)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        X_prepared = self._prepare_features(X)
        predictions = self.model.predict(X_prepared)
        
        return predictions
    
    def should_replace_pitcher(
        self,
        current_pitcher: Dict,
        batter: Dict,
        game_state: Dict,
        bullpen: List[Dict],
        recent_performance: Optional[Dict] = None
    ) -> Tuple[bool, Optional[str], float]:
        """
        Determine if current pitcher should be replaced.
        
        Args:
            current_pitcher: Current pitcher stats
            batter: Upcoming batter stats
            game_state: Game state
            bullpen: List of available relievers
            recent_performance: Recent pitcher performance
        
        Returns:
            Tuple of (should_replace, recommended_pitcher_id, confidence)
        """
        if not self.is_fitted:
            return self._heuristic_replacement(
                current_pitcher, batter, game_state, bullpen
            )
        
        # Create feature vector
        features = self._create_pitcher_features(
            current_pitcher,
            batter,
            game_state,
            recent_performance
        )
        
        X = pd.DataFrame([features])
        
        # Get prediction
        replace = self.predict(X)[0] == 1
        
        # Get confidence
        probas = self.predict_proba(X)
        if probas is not None:
            confidence = float(probas[0][1]) if replace else float(probas[0][0])
        else:
            confidence = 0.5
        
        recommended_pitcher = None
        if replace and bullpen:
            recommended_pitcher = self.select_reliever(
                batter,
                game_state,
                bullpen
            )
            logger.info(
                f"Replace pitcher with {recommended_pitcher} "
                f"(confidence: {confidence:.2%})"
            )
        
        return replace, recommended_pitcher, confidence
    
    def _create_pitcher_features(
        self,
        current_pitcher: Dict,
        batter: Dict,
        game_state: Dict,
        recent_performance: Optional[Dict] = None
    ) -> Dict:
        """
        Create feature vector for pitcher replacement decision.
        
        Args:
            current_pitcher: Current pitcher stats
            batter: Upcoming batter
            game_state: Game state
            recent_performance: Recent pitcher performance
        
        Returns:
            Feature dictionary
        """
        features = {}
        
        # Pitcher stats
        features['pitcher_era'] = float(current_pitcher.get('season_era', 4.0))
        features['pitcher_k9'] = float(current_pitcher.get('season_k9', 8.5))
        features['pitcher_bb9'] = float(current_pitcher.get('season_bb9', 2.5))
        
        # Matchup
        pitcher_hand = current_pitcher.get('hand', 'R')
        batter_hand = batter.get('hand', 'R')
        features['same_handedness'] = 1.0 if pitcher_hand == batter_hand else 0.0
        
        if pitcher_hand == 'R' and batter_hand == 'L':
            features['vs_matchup_avg'] = float(current_pitcher.get('vs_lhb_era', 4.0))
        elif pitcher_hand == 'L' and batter_hand == 'R':
            features['vs_matchup_avg'] = float(current_pitcher.get('vs_rhb_era', 4.0))
        else:
            features['vs_matchup_avg'] = float(current_pitcher.get('season_era', 4.0))
        
        # Fatigue
        features['pitch_count'] = float(current_pitcher.get('pitch_count_today', 0))
        features['innings_pitched'] = float(current_pitcher.get('innings_today', 0.0))
        features['games_last_14'] = float(current_pitcher.get('games_last_14_days', 0))
        
        # Game state
        features['inning'] = float(game_state.get('inning', 1))
        features['outs'] = float(game_state.get('outs', 0))
        features['score_diff'] = float(game_state.get('score_diff', 0))
        features['runners_on'] = float(sum(game_state.get('bases', [False, False, False])))
        
        # Recent performance
        if recent_performance:
            features['recent_era'] = float(recent_performance.get('recent_era', 4.0))
            features['recent_k9'] = float(recent_performance.get('recent_k9', 8.5))
            features['last_game_earned_runs'] = float(
                recent_performance.get('last_game_earned_runs', 0)
            )
        else:
            features['recent_era'] = float(current_pitcher.get('season_era', 4.0))
            features['recent_k9'] = float(current_pitcher.get('season_k9', 8.5))
            features['last_game_earned_runs'] = 0.0
        
        # Pitcher role
        role = current_pitcher.get('role', 'reliever')
        features['is_starter'] = 1.0 if role == 'starter' else 0.0
        features['is_reliever'] = 1.0 if role == 'reliever' else 0.0
        features['is_closer'] = 1.0 if role == 'closer' else 0.0
        
        return features
    
    def _heuristic_replacement(
        self,
        current_pitcher: Dict,
        batter: Dict,
        game_state: Dict,
        bullpen: List[Dict]
    ) -> Tuple[bool, Optional[str], float]:
        """
        Heuristic pitcher replacement recommendation.
        
        Args:
            current_pitcher: Current pitcher
            batter: Upcoming batter
            game_state: Game state
            bullpen: Available relievers
        
        Returns:
            Tuple of (should_replace, pitcher_id, confidence)
        """
        pitch_count = current_pitcher.get('pitch_count_today', 0)
        innings = current_pitcher.get('innings_today', 0.0)
        era = current_pitcher.get('season_era', 4.0)
        role = current_pitcher.get('role', 'reliever')
        
        # Always replace if over pitch limit
        if role == 'starter' and pitch_count > 100:
            recommended = self.select_reliever(batter, game_state, bullpen)
            return True, recommended, 0.95
        
        if role == 'reliever' and pitch_count > 40:
            recommended = self.select_reliever(batter, game_state, bullpen)
            return True, recommended, 0.90
        
        # Replace if ERA elevated and runner on third
        if era > 5.0 and game_state.get('bases', [False, False, False])[2]:
            recommended = self.select_reliever(batter, game_state, bullpen)
            return True, recommended, 0.70
        
        return False, None, 0.5
    
    def select_reliever(
        self,
        batter: Dict,
        game_state: Dict,
        bullpen: List[Dict]
    ) -> Optional[str]:
        """
        Select best reliever for current matchup.
        
        Args:
            batter: Upcoming batter
            game_state: Game state
            bullpen: Available relievers
        
        Returns:
            Reliever player ID
        """
        if not bullpen:
            return None
        
        batter_hand = batter.get('hand', 'R')
        inning = game_state.get('inning', 1)
        score_diff = game_state.get('score_diff', 0)
        
        # Find best matchup and availability
        best_reliever = None
        best_score = -float('inf')
        
        for reliever in bullpen:
            # Check availability
            if reliever.get('games_last_14_days', 0) > 5:  # Tired
                continue
            
            if reliever.get('is_injured', False):
                continue
            
            # Matchup score
            pitcher_hand = reliever.get('hand', 'R')
            if pitcher_hand == batter_hand:
                # Same handedness disadvantage
                score = -1.0
            else:
                # Opposite handedness advantage
                score = 1.0
            
            # ERA weight
            era = reliever.get('season_era', 4.0)
            score -= (era - 3.5) * 0.1
            
            # Role appropriateness
            role = reliever.get('role', 'reliever')
            if inning >= 9 and role == 'closer':
                score += 2.0
            elif inning >= 8 and role == 'setup':
                score += 1.5
            elif inning < 8 and role == 'middle_relief':
                score += 1.0
            
            if score > best_score:
                best_score = score
                best_reliever = reliever.get('player_id')
        
        if best_reliever:
            logger.info(f"Selected reliever: {best_reliever}")
        
        return best_reliever
    
    def plan_rotation(
        self,
        team_roster: List[Dict],
        upcoming_opponents: List[Dict],
        days_ahead: int = 14
    ) -> pd.DataFrame:
        """
        Plan pitcher rotation for upcoming games.
        
        Args:
            team_roster: List of pitcher stats
            upcoming_opponents: List of opponents
            days_ahead: Number of days to plan for
        
        Returns:
            Rotation schedule DataFrame
        """
        rotation = []
        
        # Filter to starters
        starters = [p for p in team_roster if p.get('role') == 'starter']
        
        if not starters:
            logger.warning("No starters found in roster")
            return pd.DataFrame()
        
        # Assign starters to games
        starter_idx = 0
        
        for game_idx, opponent in enumerate(upcoming_opponents[:days_ahead]):
            starter = starters[starter_idx % len(starters)]
            
            rotation.append({
                'game': game_idx + 1,
                'opponent': opponent.get('team_id', 'unknown'),
                'starter_id': starter.get('player_id'),
                'starter_name': starter.get('name'),
                'pitcher_era': starter.get('season_era', 4.0),
                'vs_opponent_era': starter.get('vs_opponent_era', 4.0),
            })
            
            starter_idx += 1
        
        logger.info(f"Planned rotation for {len(rotation)} games")
        
        return pd.DataFrame(rotation)
