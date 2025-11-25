"""
Decision Evaluator - Evaluates quality of manager decisions through simulation.

Provides:
- Decision outcome analysis
- Win Probability Added (WPA) calculation
- Decision vs alternative comparison
- Historical decision tracking
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Decision:
    """Represents a single managerial decision."""
    timestamp: datetime
    game_id: str
    inning: int
    outs: int
    score_diff: int
    decision_type: str
    player_involved: str
    
    # Context
    win_prob_before: float
    
    # Outcome
    outcome: Optional[str] = None  # 'success', 'failure', 'neutral'
    win_prob_after: Optional[float] = None
    runs_impact: int = 0
    
    # Evaluation
    wpa: float = 0.0  # Win Probability Added
    
    def calculate_wpa(self) -> float:
        """Calculate WPA for this decision."""
        if self.win_prob_after is not None:
            self.wpa = self.win_prob_after - self.win_prob_before
        return self.wpa


@dataclass
class DecisionComparison:
    """Comparison between two decision alternatives."""
    decision_a: str
    decision_b: str
    
    a_success_rate: float
    b_success_rate: float
    
    a_avg_outcome: float
    b_avg_outcome: float
    
    a_wpa: float
    b_wpa: float
    
    simulations: int
    
    def recommend(self) -> str:
        """Get recommendation based on comparison."""
        if self.a_wpa > self.b_wpa:
            return self.decision_a
        elif self.b_wpa > self.a_wpa:
            return self.decision_b
        else:
            return "equivalent"


class DecisionEvaluator:
    """Evaluate quality of manager decisions."""
    
    def __init__(self):
        """Initialize decision evaluator."""
        self.decisions: List[Decision] = []
        self.decision_history = pd.DataFrame()
    
    def record_decision(
        self,
        game_id: str,
        inning: int,
        outs: int,
        score_diff: int,
        decision_type: str,
        player_involved: str,
        win_prob_before: float
    ) -> Decision:
        """
        Record a decision for later evaluation.
        
        Args:
            game_id: Game identifier
            inning: Inning number
            outs: Current outs
            score_diff: Score differential (home - away)
            decision_type: Type of decision
            player_involved: Player ID involved
            win_prob_before: Win probability before decision
        
        Returns:
            Decision object
        """
        decision = Decision(
            timestamp=datetime.now(),
            game_id=game_id,
            inning=inning,
            outs=outs,
            score_diff=score_diff,
            decision_type=decision_type,
            player_involved=player_involved,
            win_prob_before=win_prob_before
        )
        
        self.decisions.append(decision)
        return decision
    
    def record_outcome(
        self,
        decision: Decision,
        outcome: str,
        win_prob_after: float,
        runs_impact: int = 0
    ) -> None:
        """
        Record outcome of a decision.
        
        Args:
            decision: Decision object
            outcome: Outcome type ('success', 'failure', 'neutral')
            win_prob_after: Win probability after outcome
            runs_impact: Runs scored/prevented by decision
        """
        decision.outcome = outcome
        decision.win_prob_after = win_prob_after
        decision.runs_impact = runs_impact
        decision.calculate_wpa()
        
        logger.info(
            f"Decision outcome: {decision.decision_type} - {outcome} "
            f"(WPA: {decision.wpa:+.3f})"
        )
    
    def evaluate_decision_vs_alternative(
        self,
        decision_simulator,
        game_state: Dict,
        decision_a: str,
        decision_b: str,
        roster: List[Dict],
        simulations: int = 100
    ) -> DecisionComparison:
        """
        Compare two decision alternatives through simulation.
        
        Args:
            decision_simulator: GameSimulator instance
            game_state: Current game state
            decision_a: First decision alternative
            decision_b: Second decision alternative
            roster: Team roster
            simulations: Number of simulations per decision
        
        Returns:
            DecisionComparison object
        """
        logger.info(
            f"Comparing decisions: {decision_a} vs {decision_b} "
            f"({simulations} simulations each)"
        )
        
        # Simulate outcomes with decision A
        results_a = self._simulate_decision_outcomes(
            decision_simulator,
            game_state,
            decision_a,
            roster,
            simulations
        )
        
        # Simulate outcomes with decision B
        results_b = self._simulate_decision_outcomes(
            decision_simulator,
            game_state,
            decision_b,
            roster,
            simulations
        )
        
        # Create comparison
        comparison = DecisionComparison(
            decision_a=decision_a,
            decision_b=decision_b,
            a_success_rate=results_a['success_rate'],
            b_success_rate=results_b['success_rate'],
            a_avg_outcome=results_a['avg_outcome'],
            b_avg_outcome=results_b['avg_outcome'],
            a_wpa=results_a['avg_wpa'],
            b_wpa=results_b['avg_wpa'],
            simulations=simulations
        )
        
        logger.info(
            f"Comparison results:\n"
            f"  {decision_a}: {comparison.a_success_rate:.1%} success, "
            f"{comparison.a_wpa:+.3f} WPA\n"
            f"  {decision_b}: {comparison.b_success_rate:.1%} success, "
            f"{comparison.b_wpa:+.3f} WPA\n"
            f"  Recommendation: {comparison.recommend()}"
        )
        
        return comparison
    
    def _simulate_decision_outcomes(
        self,
        game_simulator,
        game_state: Dict,
        decision: str,
        roster: List[Dict],
        simulations: int
    ) -> Dict:
        """
        Simulate outcomes for a specific decision.
        
        Args:
            game_simulator: GameSimulator instance
            game_state: Current game state
            decision: Decision type
            roster: Team roster
            simulations: Number of simulations
        
        Returns:
            Outcome statistics dictionary
        """
        outcomes = []
        wpa_values = []
        
        for _ in range(simulations):
            # Apply decision to game state
            modified_state = self._apply_decision(game_state, decision)
            
            # Simulate forward from this point
            outcome = self._simulate_from_state(game_simulator, modified_state)
            
            outcomes.append(outcome)
            wpa_values.append(outcome.get('wpa', 0.0))
        
        success_count = sum(
            1 for o in outcomes
            if o.get('success', False)
        )
        
        return {
            'success_rate': success_count / simulations,
            'avg_outcome': np.mean([o.get('outcome_value', 0) for o in outcomes]),
            'avg_wpa': np.mean(wpa_values),
            'std_wpa': np.std(wpa_values),
            'outcomes': outcomes
        }
    
    def _apply_decision(
        self,
        game_state: Dict,
        decision: str
    ) -> Dict:
        """
        Apply a decision to game state.
        
        Args:
            game_state: Current game state
            decision: Decision type
        
        Returns:
            Modified game state
        """
        modified_state = game_state.copy()
        
        # Decision-specific modifications
        if decision == 'steal_attempt':
            modified_state['attempted_steal'] = True
        elif decision == 'sacrifice_bunt':
            modified_state['sacrifice_bunt'] = True
        elif decision == 'aggressive_baserun':
            modified_state['aggressive_baserunning'] = True
        elif decision == 'pitch_around':
            modified_state['pitch_around_batter'] = True
        
        return modified_state
    
    def _simulate_from_state(
        self,
        game_simulator,
        game_state: Dict
    ) -> Dict:
        """
        Simulate game forward from current state.
        
        Args:
            game_simulator: GameSimulator instance
            game_state: Current game state
        
        Returns:
            Outcome dictionary
        """
        # Placeholder simulation
        # In practice, this would resume from current game state
        outcome_value = np.random.random()
        success = outcome_value > 0.5
        
        wpa = 0.05 if success else -0.05
        
        return {
            'success': success,
            'outcome_value': outcome_value,
            'wpa': wpa
        }
    
    def get_decision_statistics(
        self,
        decision_type: Optional[str] = None
    ) -> Dict:
        """
        Get statistics for recorded decisions.
        
        Args:
            decision_type: Filter by decision type (None = all)
        
        Returns:
            Statistics dictionary
        """
        if not self.decisions:
            return {}
        
        decisions = self.decisions
        if decision_type:
            decisions = [d for d in decisions if d.decision_type == decision_type]
        
        if not decisions:
            return {}
        
        # Filter to completed decisions
        completed = [d for d in decisions if d.outcome is not None]
        
        if not completed:
            return {'error': 'No completed decisions'}
        
        wpa_values = [d.wpa for d in completed]
        outcomes = [d.outcome for d in completed]
        
        success_count = sum(1 for o in outcomes if o == 'success')
        
        stats = {
            'total_decisions': len(completed),
            'success_count': success_count,
            'success_rate': success_count / len(completed),
            'avg_wpa': np.mean(wpa_values),
            'std_wpa': np.std(wpa_values),
            'max_wpa': np.max(wpa_values),
            'min_wpa': np.min(wpa_values),
            'avg_runs_impact': np.mean([d.runs_impact for d in completed])
        }
        
        return stats
    
    def get_decision_by_type(self) -> pd.DataFrame:
        """
        Get decisions aggregated by type.
        
        Returns:
            DataFrame with decision statistics by type
        """
        if not self.decisions:
            return pd.DataFrame()
        
        completed = [d for d in self.decisions if d.outcome is not None]
        
        data = []
        for decision_type in set(d.decision_type for d in completed):
            type_decisions = [d for d in completed if d.decision_type == decision_type]
            
            wpa_values = [d.wpa for d in type_decisions]
            success_count = sum(1 for d in type_decisions if d.outcome == 'success')
            
            data.append({
                'decision_type': decision_type,
                'count': len(type_decisions),
                'success_rate': success_count / len(type_decisions),
                'avg_wpa': np.mean(wpa_values),
                'std_wpa': np.std(wpa_values)
            })
        
        return pd.DataFrame(data).sort_values('avg_wpa', ascending=False)
    
    def export_decisions(self, filepath: str) -> None:
        """
        Export decision history to CSV.
        
        Args:
            filepath: Path to save decisions
        """
        if not self.decisions:
            logger.warning("No decisions to export")
            return
        
        data = []
        for d in self.decisions:
            data.append({
                'timestamp': d.timestamp,
                'game_id': d.game_id,
                'inning': d.inning,
                'outs': d.outs,
                'score_diff': d.score_diff,
                'decision_type': d.decision_type,
                'player': d.player_involved,
                'wp_before': d.win_prob_before,
                'wp_after': d.win_prob_after,
                'outcome': d.outcome,
                'wpa': d.wpa,
                'runs_impact': d.runs_impact
            })
        
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        logger.info(f"Exported {len(data)} decisions to {filepath}")
    
    def clear_history(self) -> None:
        """Clear decision history."""
        self.decisions = []
        self.decision_history = pd.DataFrame()
        logger.info("Cleared decision history")
