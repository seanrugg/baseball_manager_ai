#!/usr/bin/env python
"""
Train machine learning models for baseball decision making.

Supports training multiple model types:
- Lineup optimizer
- In-game decision maker
- Pitching manager
- Ensemble models

Usage:
    python scripts/train_model.py --model lineup_optimizer --config config/training_config.yaml
    python scripts/train_model.py --model in_game_decider --seasons 2020 2021 2022
    python scripts/train_model.py --model all --validate
"""

import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, List
import yaml
import json
from datetime import datetime
import pickle

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
import xgboost as xgb

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/train_model.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ModelTrainer:
    """Train baseball decision-making models."""
    
    def __init__(
        self,
        config_path: Path = Path('config/training_config.yaml'),
        data_dir: Path = Path('data'),
        model_dir: Path = Path('models')
    ):
        """
        Initialize model trainer.
        
        Args:
            config_path: Path to training configuration file
            data_dir: Path to data directory
            model_dir: Path to save trained models
        """
        self.config_path = config_path
        self.data_dir = data_dir
        self.model_dir = model_dir
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Model registry
        self.models = {}
        self.scalers = {}
        self.feature_names = {}
    
    def _load_config(self, config_path: Path) -> Dict:
        """Load training configuration from YAML."""
        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}")
            return {}
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Loaded configuration from {config_path}")
        return config
    
    def prepare_training_data(
        self,
        data_path: Path,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> tuple:
        """
        Prepare data for model training.
        
        Args:
            data_path: Path to preprocessed training data
            test_size: Proportion of data for testing
            random_state: Random seed for reproducibility
        
        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        logger.info(f"Loading training data from {data_path}")
        
        if not data_path.exists():
            raise FileNotFoundError(f"Training data not found: {data_path}")
        
        if data_path.suffix == '.csv':
            df = pd.read_csv(data_path)
        elif data_path.suffix == '.parquet':
            df = pd.read_parquet(data_path)
        else:
            raise ValueError(f"Unsupported file format: {data_path.suffix}")
        
        logger.info(f"Loaded {len(df)} training examples")
        
        # Separate features and target
        target_col = self.config.get('target_column', 'target')
        
        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found in data")
        
        X = df.drop(columns=[target_col])
        y = df[target_col]
        
        # Store feature names for later use
        self.feature_names['all'] = X.columns.tolist()
        
        logger.info(f"Features: {len(X.columns)}")
        logger.info(f"Target distribution:\n{y.value_counts()}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=random_state,
            stratify=y if len(np.unique(y)) > 1 else None
        )
        
        logger.info(f"Train set: {len(X_train)} samples")
        logger.info(f"Test set: {len(X_test)} samples")
        
        return X_train, X_test, y_train, y_test
    
    def train_lineup_optimizer(
        self,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        y_train: pd.Series,
        y_test: pd.Series
    ) -> Dict:
        """
        Train lineup optimization model.
        
        Predicts optimal batting order given player matchups and game context.
        
        Args:
            X_train, X_test: Training and test features
            y_train, y_test: Training and test targets
        
        Returns:
            Dictionary with model performance metrics
        """
        logger.info("Training Lineup Optimizer model...")
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        self.scalers['lineup_optimizer'] = scaler
        
        # Train model
        model_config = self.config.get('lineup_optimizer', {})
        
        if model_config.get('model_type') == 'xgboost':
            model = xgb.XGBClassifier(
                n_estimators=model_config.get('n_estimators', 100),
                max_depth=model_config.get('max_depth', 6),
                learning_rate=model_config.get('learning_rate', 0.1),
                random_state=42
            )
        else:
            model = GradientBoostingClassifier(
                n_estimators=model_config.get('n_estimators', 100),
                max_depth=model_config.get('max_depth', 6),
                learning_rate=model_config.get('learning_rate', 0.1),
                random_state=42
            )
        
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = model.score(X_train_scaled, y_train)
        test_score = model.score(X_test_scaled, y_test)
        
        logger.info(f"Lineup Optimizer - Train accuracy: {train_score:.4f}")
        logger.info(f"Lineup Optimizer - Test accuracy: {test_score:.4f}")
        
        self.models['lineup_optimizer'] = model
        
        return {
            'model': 'lineup_optimizer',
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'n_features': X_train.shape[1],
            'n_samples': len(X_train)
        }
    
    def train_in_game_decider(
        self,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        y_train: pd.Series,
        y_test: pd.Series
    ) -> Dict:
        """
        Train in-game decision model.
        
        Predicts optimal decisions (steal, bunt, sacrifice, etc.) based on game state.
        
        Args:
            X_train, X_test: Training and test features
            y_train, y_test: Training and test targets
        
        Returns:
            Dictionary with model performance metrics
        """
        logger.info("Training In-Game Decider model...")
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        self.scalers['in_game_decider'] = scaler
        
        # Train with Random Forest for interpretability
        model_config = self.config.get('in_game_decider', {})
        
        model = RandomForestClassifier(
            n_estimators=model_config.get('n_estimators', 200),
            max_depth=model_config.get('max_depth', 10),
            min_samples_split=model_config.get('min_samples_split', 5),
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = model.score(X_train_scaled, y_train)
        test_score = model.score(X_test_scaled, y_test)
        
        logger.info(f"In-Game Decider - Train accuracy: {train_score:.4f}")
        logger.info(f"In-Game Decider - Test accuracy: {test_score:.4f}")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': X_train.columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        logger.info("Top 10 important features:")
        for idx, row in feature_importance.head(10).iterrows():
            logger.info(f"  {row['feature']}: {row['importance']:.4f}")
        
        self.models['in_game_decider'] = model
        
        return {
            'model': 'in_game_decider',
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'n_features': X_train.shape[1],
            'n_samples': len(X_train),
            'top_features': feature_importance.head(10).to_dict('records')
        }
    
    def train_pitching_manager(
        self,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        y_train: pd.Series,
        y_test: pd.Series
    ) -> Dict:
        """
        Train pitching management model.
        
        Predicts pitcher changes and rotation management decisions.
        
        Args:
            X_train, X_test: Training and test features
            y_train, y_test: Training and test targets
        
        Returns:
            Dictionary with model performance metrics
        """
        logger.info("Training Pitching Manager model...")
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        self.scalers['pitching_manager'] = scaler
        
        # XGBoost for complex decision boundaries
        model_config = self.config.get('pitching_manager', {})
        
        model = xgb.XGBClassifier(
            n_estimators=model_config.get('n_estimators', 150),
            max_depth=model_config.get('max_depth', 8),
            learning_rate=model_config.get('learning_rate', 0.1),
            subsample=0.8,
            random_state=42
        )
        
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = model.score(X_train_scaled, y_train)
        test_score = model.score(X_test_scaled, y_test)
        
        logger.info(f"Pitching Manager - Train accuracy: {train_score:.4f}")
        logger.info(f"Pitching Manager - Test accuracy: {test_score:.4f}")
        
        self.models['pitching_manager'] = model
        
        return {
            'model': 'pitching_manager',
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'n_features': X_train.shape[1],
            'n_samples': len(X_train)
        }
    
    def save_models(self, tag: str = 'latest') -> None:
        """
        Save trained models and scalers to disk.
        
        Args:
            tag: Version tag for models (e.g., 'v1.0', 'latest')
        """
        logger.info(f"Saving models with tag: {tag}")
        
        for model_name, model in self.models.items():
            model_path = self.model_dir / f'{model_name}_{tag}.pkl'
            
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            
            logger.info(f"✓ Saved {model_name} to {model_path}")
            
            # Save scaler if exists
            if model_name in self.scalers:
                scaler_path = self.model_dir / f'{model_name}_scaler_{tag}.pkl'
                
                with open(scaler_path, 'wb') as f:
                    pickle.dump(self.scalers[model_name], f)
                
                logger.info(f"✓ Saved {model_name} scaler to {scaler_path}")
        
        # Save feature names
        features_path = self.model_dir / f'feature_names_{tag}.json'
        with open(features_path, 'w') as f:
            json.dump(self.feature_names, f, indent=2)
        
        logger.info(f"✓ Saved feature names to {features_path}")
    
    def generate_training_report(self, results: List[Dict]) -> None:
        """
        Generate training report.
        
        Args:
            results: List of training results from each model
        """
        logger.info("=" * 60)
        logger.info("TRAINING REPORT")
        logger.info("=" * 60)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'config_path': str(self.config_path),
            'models': results
        }
        
        for result in results:
            logger.info(f"\n{result['model'].upper()}")
            logger.info(f"  Train Accuracy: {result.get('train_accuracy', 'N/A'):.4f}")
            logger.info(f"  Test Accuracy:  {result.get('test_accuracy', 'N/A'):.4f}")
            logger.info(f"  Samples:        {result.get('n_samples', 'N/A')}")
            logger.info(f"  Features:       {result.get('n_features', 'N/A')}")
        
        report_path = self.model_dir / f'training_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n✓ Report saved to {report_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Train baseball decision-making models'
    )
    
    parser.add_argument(
        '--model',
        choices=['lineup_optimizer', 'in_game_decider', 'pitching_manager', 'all'],
        default='all',
        help='Model to train'
    )
    
    parser.add_argument(
        '--config',
        type=Path,
        default=Path('config/training_config.yaml'),
        help='Training configuration file'
    )
    
    parser.add_argument(
        '--data-dir',
        type=Path,
        default=Path('data'),
        help='Data directory'
    )
    
    parser.add_argument(
        '--model-dir',
        type=Path,
        default=Path('models'),
        help='Model output directory'
    )
    
    parser.add_argument(
        '--training-data',
        type=Path,
        help='Path to preprocessed training data (CSV or Parquet)'
    )
    
    parser.add_argument(
        '--tag',
        default='latest',
        help='Version tag for saved models'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate models after training'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("BASEBALL MANAGER AI - MODEL TRAINER")
    logger.info("=" * 60)
    
    trainer = ModelTrainer(
        config_path=args.config,
        data_dir=args.data_dir,
        model_dir=args.model_dir
    )
    
    # Load training data
    if args.training_data:
        training_data_path = args.training_data
    else:
        # Default to processed training examples
        training_data_path = args.data_dir / 'processed' / 'training_examples' / 'examples.csv'
    
    if not training_data_path.exists():
        logger.error(f"Training data not found: {training_data_path}")
        logger.info("Generate training data with: python scripts/process_data.py")
        return
    
    X_train, X_test, y_train, y_test = trainer.prepare_training_data(training_data_path)
    
    # Train models
    results = []
    models_to_train = args.model if args.model != 'all' else [
        'lineup_optimizer', 'in_game_decider', 'pitching_manager'
    ]
    
    if args.model == 'all':
        models_to_train = ['lineup_optimizer', 'in_game_decider', 'pitching_manager']
    else:
        models_to_train = [args.model]
    
    for model_name in models_to_train:
        try:
            if model_name == 'lineup_optimizer':
                result = trainer.train_lineup_optimizer(X_train, X_test, y_train, y_test)
            elif model_name == 'in_game_decider':
                result = trainer.train_in_game_decider(X_train, X_test, y_train, y_test)
            elif model_name == 'pitching_manager':
                result = trainer.train_pitching_manager(X_train, X_test, y_train, y_test)
            
            results.append(result)
        
        except Exception as e:
            logger.error(f"Failed to train {model_name}: {e}")
    
    # Save models
    trainer.save_models(tag=args.tag)
    
    # Generate report
    trainer.generate_training_report(results)
    
    logger.info("=" * 60)
    logger.info("Training complete!")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
