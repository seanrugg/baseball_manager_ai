"""
Monte Carlo Simulator - Advanced scenario analysis using Monte Carlo methods.

Provides:
- Uncertainty quantification
- Scenario analysis
- Confidence intervals
- Risk assessment
- Strategy optimization
"""

import logging
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy import stats
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class MonteCarloResult:
    """Monte Carlo simulation result."""
    parameter_name: str
    mean: float
    std: float
    confidence_interval: Tuple[float, float]
    percentiles: Dict[str, float]
    samples: np.ndarray
    distribution: str = 'normal'
    
    def __str__(self) -> str:
        """String representation."""
        return (
            f"{self.parameter_name}: {self.mean:.3f} ± {self.std:.3f}\n"
            f"95% CI: [{self.confidence_interval[0]:.3f}, {self.confidence_interval[1]:.3f}]\n"
            f"Percentiles: {json.dumps(self.percentiles, indent=2)}"
        )


class MonteCarloSimulator:
    """Monte Carlo simulation for baseball strategy analysis."""
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize Monte Carlo simulator.
        
        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            np.random.seed(seed)
        
        self.simulations_run = 0
    
    def estimate_win_probability(
        self,
        game_simulator,
        home_team: str,
        away_team: str,
        home_lineup: List[Dict],
        away_lineup: List[Dict],
        home_pitcher: Dict,
        away_pitcher: Dict,
        num_simulations: int = 10000,
        confidence_level: float = 0.95
    ) -> MonteCarloResult:
        """
        Estimate win probability with confidence interval.
        
        Uses Monte Carlo to estimate home team win probability
        and compute confidence interval.
        
        Args:
            game_simulator: GameSimulator instance
            home_team: Home team ID
            away_team: Away team ID
            home_lineup: Home lineup
            away_lineup: Away lineup
            home_pitcher: Home pitcher
            away_pitcher: Away pitcher
            num_simulations: Number of Monte Carlo iterations
            confidence_level: Confidence level for interval (0-1)
        
        Returns:
            MonteCarloResult with win probability estimates
        """
        logger.info(
            f"Estimating win probability ({num_simulations} simulations, "
            f"{confidence_level:.0%} CI)"
        )
        
        wins = 0
        home_scores = []
        
        for i in range(num_simulations):
            game = game_simulator.simulate_game(
                home_team,
                away_team,
                home_lineup,
                away_lineup,
                home_pitcher,
                away_pitcher
            )
            
            if game.home_score > game.away_score:
                wins += 1
            
            home_scores.append(game.home_score)
            
            if (i + 1) % (num_simulations // 10) == 0:
                current_wp = wins / (i + 1)
                logger.info(f"  {i + 1}/{num_simulations}: WP = {current_wp:.3f}")
        
        win_prob = wins / num_simulations
        std = np.sqrt(win_prob * (1 - win_prob) / num_simulations)
        
        # Confidence interval
        z_score = stats.norm.ppf((1 + confidence_level) / 2)
        ci = (
            max(0, win_prob - z_score * std),
            min(1, win_prob + z_score * std)
        )
        
        # Percentiles
        percentiles = {
            'p10': np.percentile(home_scores, 10),
            'p25': np.percentile(home_scores, 25),
            'p50': np.percentile(home_scores, 50),
            'p75': np.percentile(home_scores, 75),
            'p90': np.percentile(home_scores, 90)
        }
        
        result = MonteCarloResult(
            parameter_name=f"P({home_team} wins)",
            mean=win_prob,
            std=std,
            confidence_interval=ci,
            percentiles=percentiles,
            samples=np.array(home_scores)
        )
        
        self.simulations_run += num_simulations
        
        logger.info(f"Result: {win_prob:.3f} [{ci[0]:.3f}, {ci[1]:.3f}]")
        
        return result
    
    def estimate_run_expectancy(
        self,
        game_simulator,
        base_state: Tuple[bool, bool, bool],
        outs: int,
        inning: int,
        batter: Dict,
        pitcher: Dict,
        num_simulations: int = 5000
    ) -> MonteCarloResult:
        """
        Estimate expected runs from current situation.
        
        Args:
            game_simulator: GameSimulator instance
            base_state: (first, second, third) runners
            outs: Current outs
            inning: Current inning
            batter: Batter stats
            pitcher: Pitcher stats
            num_simulations: Number of simulations
        
        Returns:
            MonteCarloResult with run expectancy estimates
        """
        logger.info(
            f"Estimating run expectancy for bases {base_state}, "
            f"{outs} outs ({num_simulations} simulations)"
        )
        
        runs_scored = []
        
        for i in range(num_simulations):
            # Simulate rest of inning
            runs = self._simulate_inning_from_state(
                game_simulator,
                base_state,
                outs,
                batter,
                pitcher
            )
            runs_scored.append(runs)
            
            if (i + 1) % (num_simulations // 10) == 0:
                current_re = np.mean(runs_scored)
                logger.info(f"  {i + 1}/{num_simulations}: RE = {current_re:.3f}")
        
        mean_runs = np.mean(runs_scored)
        std_runs = np.std(runs_scored)
        
        # Confidence interval
        ci = stats.t.interval(
            0.95,
            len(runs_scored) - 1,
            loc=mean_runs,
            scale=std_runs / np.sqrt(len(runs_scored))
        )
        
        percentiles = {
            'p10': np.percentile(runs_scored, 10),
            'p25': np.percentile(runs_scored, 25),
            'p50': np.percentile(runs_scored, 50),
            'p75': np.percentile(runs_scored, 75),
            'p90': np.percentile(runs_scored, 90)
        }
        
        result = MonteCarloResult(
            parameter_name=f"RE({base_state}, {outs} outs)",
            mean=mean_runs,
            std=std_runs,
            confidence_interval=ci,
            percentiles=percentiles,
            samples=np.array(runs_scored)
        )
        
        self.simulations_run += num_simulations
        
        logger.info(f"Result: {mean_runs:.3f} ± {std_runs:.3f} runs")
        
        return result
    
    def sensitivity_analysis(
        self,
        base_function: Callable,
        parameter_ranges: Dict[str, Tuple[float, float]],
        num_samples: int = 1000
    ) -> pd.DataFrame:
        """
        Perform sensitivity analysis on key parameters.
        
        Varies parameters across ranges and evaluates impact on outcome.
        
        Args:
            base_function: Function to evaluate (takes dict of params)
            parameter_ranges: Dict of param_name: (min, max)
            num_samples: Number of samples per parameter
        
        Returns:
            DataFrame with sensitivity results
        """
        logger.info(
            f"Sensitivity analysis on {len(parameter_ranges)} parameters "
            f"({num_samples} samples each)"
        )
        
        results = []
        
        for param_name, (param_min, param_max) in parameter_ranges.items():
            param_values = np.linspace(param_min, param_max, num_samples)
            outcomes = []
            
            for value in param_values:
                params = {param_name: value}
                outcome = base_function(params)
                outcomes.append(outcome)
            
            # Fit relationship
            coefficients = np.polyfit(param_values, outcomes, 2)
            
            results.append({
                'parameter': param_name,
                'min_value': param_min,
                'max_value': param_max,
                'min_outcome': min(outcomes),
                'max_outcome': max(outcomes),
                'outcome_range': max(outcomes) - min(outcomes),
                'linear_coeff': coefficients[1],
                'correlation': np.corrcoef(param_values, outcomes)[0, 1]
            })
        
        df = pd.DataFrame(results).sort_values('outcome_range', ascending=False)
        
        logger.info("Sensitivity ranking (by outcome range):")
        for _, row in df.iterrows():
            logger.info(
                f"  {row['parameter']}: [{row['min_outcome']:.3f}, "
                f"{row['max_outcome']:.3f}] (range: {row['outcome_range']:.3f})"
            )
        
        return df
    
    def scenario_analysis(
        self,
        scenarios: Dict[str, Dict],
        evaluation_func: Callable,
        num_simulations_per_scenario: int = 1000
    ) -> pd.DataFrame:
        """
        Analyze outcomes across multiple scenarios.
        
        Args:
            scenarios: Dict of scenario_name: scenario_params
            evaluation_func: Function to evaluate scenario
            num_simulations_per_scenario: Simulations per scenario
        
        Returns:
            DataFrame with scenario results
        """
        logger.info(
            f"Scenario analysis on {len(scenarios)} scenarios "
            f"({num_simulations_per_scenario} simulations each)"
        )
        
        results = []
        
        for scenario_name, scenario_params in scenarios.items():
            logger.info(f"Evaluating scenario: {scenario_name}")
            
            outcomes = []
            
            for i in range(num_simulations_per_scenario):
                outcome = evaluation_func(scenario_params)
                outcomes.append(outcome)
            
            mean_outcome = np.mean(outcomes)
            std_outcome = np.std(outcomes)
            
            results.append({
                'scenario': scenario_name,
                'mean_outcome': mean_outcome,
                'std_outcome': std_outcome,
                'min_outcome': min(outcomes),
                'max_outcome': max(outcomes),
                'p25': np.percentile(outcomes, 25),
                'p50': np.percentile(outcomes, 50),
                'p75': np.percentile(outcomes, 75)
            })
            
            logger.info(
                f"  {scenario_name}: {mean_outcome:.3f} ± {std_outcome:.3f}"
            )
        
        df = pd.DataFrame(results).sort_values('mean_outcome', ascending=False)
        
        return df
    
    def estimate_value_at_risk(
        self,
        outcomes: np.ndarray,
        confidence_level: float = 0.95
    ) -> Dict[str, float]:
        """
        Calculate Value at Risk (VaR) for outcomes.
        
        Args:
            outcomes: Array of outcome values
            confidence_level: Confidence level (0-1)
        
        Returns:
            Dictionary with VaR estimates
        """
        alpha = 1 - confidence_level
        
        # Parametric VaR (normal distribution)
        mean = np.mean(outcomes)
        std = np.std(outcomes)
        z_score = stats.norm.ppf(alpha)
        parametric_var = mean + z_score * std
        
        # Historical VaR (empirical)
        historical_var = np.percentile(outcomes, alpha * 100)
        
        # Conditional VaR (Expected Shortfall)
        worst_outcomes = outcomes[outcomes <= historical_var]
        cvar = np.mean(worst_outcomes) if len(worst_outcomes) > 0 else historical_var
        
        return {
            'parametric_var': parametric_var,
            'historical_var': historical_var,
            'conditional_var_es': cvar,
            'mean': mean,
            'std': std
        }
    
    def _simulate_inning_from_state(
        self,
        game_simulator,
        base_state: Tuple[bool, bool, bool],
        outs: int,
        batter: Dict,
        pitcher: Dict
    ) -> int:
        """
        Simulate rest of inning from given state.
        
        Args:
            game_simulator: GameSimulator instance
            base_state: Current base state
            outs: Current outs
            batter: Batter stats
            pitcher: Pitcher stats
        
        Returns:
            Runs scored in remainder of inning
        """
        # Simplified inning simulation
        # In practice, would use full game simulator
        runs = 0
        
        # Simulate at-bats until 3 outs
        while outs < 3:
            outcome = game_simulator._simulate_at_bat(
                batter,
                pitcher,
                list(base_state),
                outs
            )
            
            if outcome.value == 'home_run':
                runs += 1 + sum(base_state)
                base_state = (False, False, False)
            elif outcome.value == 'walk':
                base_state = (True, base_state[0], base_state[1])
            elif outcome.value in ['single', 'double', 'triple']:
                advance = {
                    'single': 1,
                    'double': 2,
                    'triple': 3
                }[outcome.value]
                
                if base_state[2]:
                    runs += 1
                base_state = (
                    True if advance >= 1 else False,
                    base_state[0] if advance >= 2 else False,
                    base_state[1] if advance >= 3 else False
                )
            else:  # out/strikeout
                outs += 1
        
        return runs
    
    def get_statistics_summary(self) -> Dict:
        """Get summary of Monte Carlo runs."""
        return {
            'total_simulations': self.simulations_run,
            'timestamp': datetime.now().isoformat()
        }
