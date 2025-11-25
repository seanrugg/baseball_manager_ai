"""
In-Game Decider - Real-time tactical decision making.

Recommends in-game decisions:
- Steal attempts
- Sacrifice bunts
- Hit and run
- Pitch to or walk
- Defensive positioning
- Aggressive baserunning
"""

import logging
from typing import Dict, Tuple, List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from .base_manager import BaseManager

logger = logging.getLogger(__name__)


class InGameDecider(BaseManager):
    """Make optimal tactical decisions during games."""
    
    # Decision types
    DECISION_TYPES = [
        'steal_attempt',
        'sacrifice_bunt',
        'hit_and_run',
        'play_it_safe',
        'aggressive_baserun',
        'pitch_around',
        'intentional_walk',
        'full_count_approach'
    ]
    
    def __init__(self, random_state: int = 42):
        """
        Initialize In-Game Decider.
        
        Args:
            random_state: Random seed
        """
        super().__init__(
            model_name='in_game_decider',
            model_type='classifier',
            random_state=random_state
        )
        
        # Use Random Forest for interpretability
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            random_state=random_state,
            n_jobs=-1
        )
        
        self.scaler = StandardScaler()
    
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        **kwargs
    ) -> None:
        """
        Fit in-game decision model.
        
        Expected features:
        - Game state (inning, outs, score, bases, count)
        - Player stats (speed, power, discipline)
        - Win probability context
        - Historical decision success rates
        
        Expected target: decision type (0-7)
        
        Args:
            X: Training features
            y: Training targets (decision types)
            **kwargs: Additional training arguments
        """
        logger.info(f"Fitting {self.model_name} with {len(X)} samples")
        
        self.feature_names = X.columns.tolist()
        
        X_scaled = self.scaler.fit_transform(X)
        
        self.model.fit(X_scaled, y)
        
        self.is_fitted = True
        
        train_score = self.model.score(X_scaled, y)
        logger.info(f"Training accuracy: {train_score:.4f}")
        
        # Log feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        logger.info("Top 10 important features:")
        for _, row in feature_importance.head(10).iterrows():
            logger.info(f"  {row['feature']}: {row['importance']:.4f}")
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict optimal decision for game situation.
        
        Args:
            X: Game state features
        
        Returns:
            Decision type indices (0-7)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        X_prepared = self._prepare_features(X)
        predictions = self.model.predict(X_prepared)
        
        return predictions
    
    def recommend_decision(
        self,
        game_state: Dict,
        batter_stats: Dict,
        runner_stats: Dict,
        pitcher_stats: Dict,
        historical_success: Optional[Dict] = None
    ) -> Tuple[str, float]:
        """
        Recommend tactical decision for current situation.
        
        Args:
            game_state: Current game state
            batter_stats: Batter statistics
            runner_stats: Baserunner statistics
            pitcher_stats: Pitcher statistics
            historical_success: Success rates for different decisions
        
        Returns:
            Tuple of (recommended_decision, confidence)
        """
        if not self.is_fitted:
            logger.warning("Model not fitted; using heuristic")
            return self._heuristic_decision(game_state, batter_stats, runner_stats)
        
        # Create feature vector
        features = self._create_decision_features(
            game_state,
            batter_stats,
            runner_stats,
            pitcher_stats,
            historical_success
        )
        
        X = pd.DataFrame([features])
        
        # Get prediction and probability
        decision_idx = self.predict(X)[0]
        decision_name = self.DECISION_TYPES[decision_idx]
        
        # Get confidence
        probas = self.predict_proba(X)
        if probas is not None:
            confidence = float(probas[0][decision_idx])
        else:
            confidence = 0.5
        
        logger.info(f"Recommended decision: {decision_name} (confidence: {confidence:.2%})")
        
        return decision_name, confidence
    
    def _create_decision_features(
        self,
        game_state: Dict,
        batter_stats: Dict,
        runner_stats: Dict,
        pitcher_stats: Dict,
        historical_success: Optional[Dict] = None
    ) -> Dict:
        """
        Create feature vector for decision recommendation.
        
        Args:
            game_state: Game state
            batter_stats: Batter stats
            runner_stats: Baserunner stats
            pitcher_stats: Pitcher stats
            historical_success: Success rate history
        
        Returns:
            Feature dictionary
        """
        features = {}
        
        # Game state features
        features['inning'] = float(game_state.get('inning', 1))
        features['outs'] = float(game_state.get('outs', 0))
        features['score_diff'] = float(game_state.get('score_diff', 0))
        features['is_tied'] = 1.0 if game_state.get('score_diff', 0) == 0 else 0.0
        
        # Base state
        bases = game_state.get('bases', [False, False, False])
        features['runner_on_first'] = 1.0 if bases[0] else 0.0
        features['runner_on_second'] = 1.0 if bases[1] else 0.0
        features['runner_on_third'] = 1.0 if bases[2] else 0.0
        features['bases_loaded'] = 1.0 if all(bases) else 0.0
        
        # Count
        count = game_state.get('count', (0, 0))
        features['balls'] = float(count[0])
        features['strikes'] = float(count[1])
        features['is_full_count'] = 1.0 if count == (3, 2) else 0.0
        
        # Batter features
        features['batter_avg'] = float(batter_stats.get('season_avg', 0.260))
        features['batter_obp'] = float(batter_stats.get('season_obp', 0.330))
        features['batter_slg'] = float(batter_stats.get('season_slg', 0.420))
        features['batter_strikeout_rate'] = float(batter_stats.get('strikeout_rate', 0.200))
        features['batter_walk_rate'] = float(batter_stats.get('walk_rate', 0.080))
        
        # Runner features (if on base)
        if runner_stats:
            features['runner_speed'] = float(runner_stats.get('speed_score', 5.0))
            features['runner_stolen_base_rate'] = float(
                runner_stats.get('sb_percentage', 0.700)
            )
            features['runner_is_aggressive'] = float(
                runner_stats.get('aggressive_score', 0.5)
            )
        else:
            features['runner_speed'] = 0.0
            features['runner_stolen_base_rate'] = 0.0
            features['runner_is_aggressive'] = 0.0
        
        # Pitcher features
        features['pitcher_era'] = float(pitcher_stats.get('season_era', 4.0))
        features['pitcher_pickoff_rate'] = float(
            pitcher_stats.get('pickoff_rate', 0.05)
        )
        features['pitcher_holds_runners'] = float(
            pitcher_stats.get('hold_runners_rating', 0.5)
        )
        
        # Historical success (if provided)
        if historical_success:
            features['steal_success_rate'] = float(
                historical_success.get('steal_success_rate', 0.65)
            )
            features['sac_bunt_success_rate'] = float(
                historical_success.get('sac_bunt_success_rate', 0.65)
            )
        else:
            features['steal_success_rate'] = 0.65
            features['sac_bunt_success_rate'] = 0.65
        
        # Situational context
        features['game_importance'] = float(game_state.get('game_importance', 0.5))
        features['is_late_game'] = 1.0 if game_state.get('inning', 1) >= 7 else 0.0
        
        return features
    
    def _heuristic_decision(
        self,
        game_state: Dict,
        batter_stats: Dict,
        runner_stats: Dict
    ) -> Tuple[str, float]:
        """
        Heuristic-based decision recommendation.
        
        Args:
            game_state: Game state
            batter_stats: Batter stats
            runner_stats: Baserunner stats
        
        Returns:
            Tuple of (decision, confidence)
        """
        bases = game_state.get('bases', [False, False, False])
        outs = game_state.get('outs', 0)
        count = game_state.get('count', (0, 0))
        score_diff = game_state.get('score_diff', 0)
        
        runner_speed = runner_stats.get('speed_score', 5.0) if runner_stats else 0
        
        # Steal attempt: runner on 1st, fast runner, <2 outs, favorable count
        if bases[0] and outs < 2 and runner_speed > 6 and count[0] >= count[1]:
            return ('steal_attempt', 0.65)
        
        # Sacrifice bunt: runner on 1st, 0-1 outs, trailing
        if bases[0] and outs <= 1 and score_diff < 0:
            return ('sacrifice_bunt', 0.60)
        
        # Hit and run: runner on 1st, favorable count
        if bases[0] and count[0] > count[1]:
            return ('hit_and_run', 0.70)
        
        # Pitch around: pitcher ahead in count, bases loaded
        if all(bases) and count[1] >= 2:
            return ('pitch_around', 0.55)
        
        # Default: play it safe
        return ('play_it_safe', 0.50)
    
    def evaluate_decision_outcome(
        self,
        decision: str,
        outcome: str,
        runs_gained: int = 0,
        runner_advancement: int = 0
    ) -> Dict:
        """
        Evaluate the outcome of a decision.
        
        Args:
            decision: Decision that was made
            outcome: Outcome ('success', 'failure', 'mixed')
            runs_gained: Runs scored from decision
            runner_advancement: Bases advanced
        
        Returns:
            Evaluation dictionary
        """
        evaluation = {
            'decision': decision,
            'outcome': outcome,
            'success': outcome == 'success',
            'runs_gained': runs_gained,
            'runner_advancement': runner_advancement,
            'value': self._calculate_decision_value(decision, outcome, runs_gained)
        }
        
        return evaluation
    
    def _calculate_decision_value(
        self,
        decision: str,
        outcome: str,
        runs_gained: int
    ) -> float:
        """
        Calculate value of decision outcome.
        
        Args:
            decision: Decision type
            outcome: Success/failure
            runs_gained: Runs resulting from decision
        
        Returns:
            Value score
        """
        base_value = {
            'steal_attempt': 0.3,
            'sacrifice_bunt': 0.2,
            'hit_and_run': 0.25,
            'play_it_safe': 0.0,
            'aggressive_baserun': 0.35,
            'pitch_around': -0.1,
            'intentional_walk': 0.0,
            'full_count_approach': 0.1
        }
        
        value = base_value.get(decision, 0.0)
        
        if outcome == 'success':
            value *= 1.5
        elif outcome == 'failure':
            value *= -1.0
        
        value += (runs_gained * 0.1)
        
        return float(value)
