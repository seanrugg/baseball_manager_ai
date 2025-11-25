"""
Ensemble Manager - Combines multiple models for robust decisions.

Integrates:
- Lineup Optimizer
- In-Game Decider
- Pitching Manager

Provides:
- Weighted model predictions
- Conflict resolution
- Confidence estimation
- Decision justification
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import json
import numpy as np
import pandas as pd

from .lineup_optimizer import LineupOptimizer
from .in_game_decider import InGameDecider
from .pitching_manager import PitchingManager

logger = logging.getLogger(__name__)


class EnsembleManager:
    """Ensemble of baseball decision models."""
    
    def __init__(
        self,
        lineup_weight: float = 0.3,
        decision_weight: float = 0.4,
        pitching_weight: float = 0.3
    ):
        """
        Initialize Ensemble Manager.
        
        Args:
            lineup_weight: Weight for lineup optimizer
            decision_weight: Weight for in-game decider
            pitching_weight: Weight for pitching manager
        """
        self.lineup_weight = lineup_weight
        self.decision_weight = decision_weight
        self.pitching_weight = pitching_weight
        
        # Initialize component managers
        self.lineup_optimizer = LineupOptimizer()
        self.in_game_decider = InGameDecider()
        self.pitching_manager = PitchingManager()
        
        # Track predictions for analysis
        self.prediction_history = []
    
    def load_models(self, model_dir: Path) -> None:
        """
        Load all component models.
        
        Args:
            model_dir: Directory containing model files
        """
        logger.info(f"Loading ensemble models from {model_dir}")
        
        try:
            self.lineup_optimizer.load(model_dir / 'lineup_optimizer_latest')
            logger.info("✓ Loaded lineup optimizer")
        except Exception as e:
            logger.warning(f"Could not load lineup optimizer: {e}")
        
        try:
            self.in_game_decider.load(model_dir / 'in_game_decider_latest')
            logger.info("✓ Loaded in-game decider")
        except Exception as e:
            logger.warning(f"Could not load in-game decider: {e}")
        
        try:
            self.pitching_manager.load(model_dir / 'pitching_manager_latest')
            logger.info("✓ Loaded pitching manager")
        except Exception as e:
            logger.warning(f"Could not load pitching manager: {e}")
    
    def save_models(self, model_dir: Path) -> None:
        """
        Save all component models.
        
        Args:
            model_dir: Directory to save models
        """
        logger.info(f"Saving ensemble models to {model_dir}")
        
        self.lineup_optimizer.save(model_dir / 'lineup_optimizer')
        self.in_game_decider.save(model_dir / 'in_game_decider')
        self.pitching_manager.save(model_dir / 'pitching_manager')
        
        logger.info("✓ All models saved")
    
    def get_game_plan(
        self,
        team_roster: List[Dict],
        opposing_pitcher: Dict,
        game_context: Dict
    ) -> Dict[str, Any]:
        """
        Generate comprehensive game plan.
        
        Args:
            team_roster: Team's roster
            opposing_pitcher: Opposing pitcher stats
            game_context: Game context
        
        Returns:
            Dictionary with complete game plan
        """
        logger.info("Generating game plan...")
        
        game_plan = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'lineup': None,
            'pitching_plan': None,
            'key_decisions': [],
            'contingencies': []
        }
        
        # Generate lineup
        try:
            if self.lineup_optimizer.is_fitted:
                lineup = self.lineup_optimizer.optimize_lineup(
                    team_roster,
                    opposing_pitcher,
                    game_context
                )
                game_plan['lineup'] = [
                    {'position': pos, 'player_id': pid}
                    for pid, pos in lineup
                ]
                logger.info(f"✓ Generated lineup ({len(lineup)} batters)")
        except Exception as e:
            logger.error(f"Failed to generate lineup: {e}")
        
        # Generate pitching plan
        try:
            starters = [p for p in team_roster if p.get('role') == 'starter']
            if starters:
                bullpen = [p for p in team_roster if p.get('role') != 'starter']
                game_plan['pitching_plan'] = {
                    'starter': starters[0].get('player_id'),
                    'starter_name': starters[0].get('name'),
                    'bullpen_depth': len(bullpen)
                }
                logger.info(f"✓ Generated pitching plan (starter: {starters[0].get('name')})")
        except Exception as e:
            logger.error(f"Failed to generate pitching plan: {e}")
        
        return game_plan
    
    def recommend_decision(
        self,
        game_state: Dict,
        team_roster: List[Dict],
        opposing_roster: List[Dict]
    ) -> Dict[str, Any]:
        """
        Get ensemble recommendation for current situation.
        
        Args:
            game_state: Current game state
            team_roster: Team roster
            opposing_roster: Opposing team roster
        
        Returns:
            Ensemble recommendation with justification
        """
        logger.info("Getting ensemble recommendation...")
        
        recommendation = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'primary_recommendation': None,
            'alternatives': [],
            'confidence': 0.0,
            'reasoning': [],
            'individual_recommendations': {}
        }
        
        # Get individual model recommendations
        
        # 1. In-game decision
        try:
            if self.in_game_decider.is_fitted:
                batter = opposing_roster[0] if opposing_roster else {}
                runner = game_state.get('runner_stats', {})
                pitcher = opposing_roster[0] if opposing_roster else {}
                
                decision, conf = self.in_game_decider.recommend_decision(
                    game_state,
                    batter,
                    runner,
                    pitcher
                )
                
                recommendation['individual_recommendations']['in_game_decider'] = {
                    'decision': decision,
                    'confidence': conf
                }
        except Exception as e:
            logger.warning(f"In-game decider failed: {e}")
        
        # 2. Pitching decision
        try:
            if self.pitching_manager.is_fitted:
                current_pitcher = game_state.get('current_pitcher', {})
                batter = opposing_roster[0] if opposing_roster else {}
                bullpen = [p for p in team_roster if p.get('role') != 'starter']
                
                should_replace, pitcher_id, conf = self.pitching_manager.should_replace_pitcher(
                    current_pitcher,
                    batter,
                    game_state,
                    bullpen
                )
                
                recommendation['individual_recommendations']['pitching_manager'] = {
                    'should_replace': should_replace,
                    'recommended_pitcher': pitcher_id,
                    'confidence': conf
                }
        except Exception as e:
            logger.warning(f"Pitching manager failed: {e}")
        
        # Aggregate recommendations
        self._aggregate_recommendations(recommendation)
        
        # Store in history
        self.prediction_history.append(recommendation)
        
        return recommendation
    
    def _aggregate_recommendations(self, recommendation: Dict) -> None:
        """
        Aggregate individual model recommendations into ensemble decision.
        
        Args:
            recommendation: Recommendation dictionary to populate
        """
        # Find most common recommendation
        recommendations = []
        confidences = []
        
        for model_name, pred in recommendation['individual_recommendations'].items():
            if 'decision' in pred:
                recommendations.append((model_name, pred['decision']))
                confidences.append(pred['confidence'])
            elif 'should_replace' in pred:
                recommendations.append((
                    model_name,
                    'replace_pitcher' if pred['should_replace'] else 'keep_pitcher'
                ))
                confidences.append(pred['confidence'])
        
        if recommendations:
            # Primary recommendation is from highest confidence model
            primary_idx = np.argmax(confidences)
            model_name, decision = recommendations[primary_idx]
            confidence = confidences[primary_idx]
            
            recommendation['primary_recommendation'] = decision
            recommendation['confidence'] = float(confidence)
            recommendation['reasoning'].append(
                f"Primary recommendation from {model_name}: {decision} "
                f"(confidence: {confidence:.2%})"
            )
            
            # Add alternative recommendations
            for (model, dec), conf in sorted(
                zip(recommendations, confidences),
                key=lambda x: x[1],
                reverse=True
            )[1:]:
                recommendation['alternatives'].append({
                    'model': model,
                    'recommendation': dec,
                    'confidence': float(conf)
                })
    
    def explain_decision(
        self,
        recommendation: Dict,
        max_reasons: int = 3
    ) -> str:
        """
        Generate human-readable explanation for ensemble decision.
        
        Args:
            recommendation: Ensemble recommendation
            max_reasons: Maximum number of reasons to include
        
        Returns:
            Explanation text
        """
        explanation = []
        
        # Primary recommendation
        if recommendation.get('primary_recommendation'):
            primary = recommendation['primary_recommendation']
            confidence = recommendation.get('confidence', 0.0)
            explanation.append(
                f"RECOMMENDATION: {primary.upper()}\n"
                f"Confidence: {confidence:.0%}\n"
            )
        
        # Reasoning
        if recommendation.get('reasoning'):
            explanation.append("REASONING:")
            for reason in recommendation['reasoning'][:max_reasons]:
                explanation.append(f"  • {reason}")
        
        # Alternatives
        if recommendation.get('alternatives'):
            explanation.append("\nALTERNATIVE OPTIONS:")
            for alt in recommendation['alternatives']:
                explanation.append(
                    f"  • {alt['recommendation']} ({alt['confidence']:.0%}) - {alt['model']}"
                )
        
        return "\n".join(explanation)
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """
        Get ensemble performance metrics.
        
        Returns:
            Dictionary of performance metrics
        """
        if not self.prediction_history:
            return {}
        
        metrics = {
            'total_predictions': len(self.prediction_history),
            'avg_confidence': np.mean([
                p.get('confidence', 0) for p in self.prediction_history
            ]),
            'high_confidence_predictions': sum(
                1 for p in self.prediction_history
                if p.get('confidence', 0) > 0.75
            ),
            'low_confidence_predictions': sum(
                1 for p in self.prediction_history
                if p.get('confidence', 0) < 0.50
            )
        }
        
        metrics['high_confidence_rate'] = (
            metrics['high_confidence_predictions'] / metrics['total_predictions']
        )
        
        return metrics
    
    def clear_history(self) -> None:
        """Clear prediction history."""
        self.prediction_history = []
        logger.info("Cleared prediction history")
    
    def export_predictions(self, filepath: Path) -> None:
        """
        Export prediction history to JSON.
        
        Args:
            filepath: Path to save predictions
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(self.prediction_history, f, indent=2, default=str)
        
        logger.info(f"Exported {len(self.prediction_history)} predictions to {filepath}")
    
    def __repr__(self) -> str:
        """String representation."""
        fitted_models = sum([
            self.lineup_optimizer.is_fitted,
            self.in_game_decider.is_fitted,
            self.pitching_manager.is_fitted
        ])
        
        return (
            f"EnsembleManager("
            f"models_fitted={fitted_models}/3, "
            f"predictions={len(self.prediction_history)}"
            f")"
        )
