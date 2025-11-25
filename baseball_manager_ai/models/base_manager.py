"""
Base manager class with common functionality for all decision models.

Provides:
- Model loading/saving
- Feature preparation
- Prediction interface
- Evaluation utilities
"""

import logging
import pickle
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class BaseManager(ABC):
    """Abstract base class for baseball decision managers."""
    
    def __init__(
        self,
        model_name: str,
        model_type: str = 'classifier',
        random_state: int = 42
    ):
        """
        Initialize base manager.
        
        Args:
            model_name: Name of the manager (e.g., 'lineup_optimizer')
            model_type: Type of model ('classifier', 'regressor', 'ranking')
            random_state: Random seed for reproducibility
        """
        self.model_name = model_name
        self.model_type = model_type
        self.random_state = random_state
        
        self.model = None
        self.scaler = None
        self.feature_names = []
        self.is_fitted = False
    
    @abstractmethod
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        **kwargs
    ) -> None:
        """
        Fit the model to training data.
        
        Args:
            X: Training features
            y: Training targets
            **kwargs: Additional training arguments
        """
        pass
    
    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions on new data.
        
        Args:
            X: Features for prediction
        
        Returns:
            Predictions
        """
        pass
    
    def predict_proba(self, X: pd.DataFrame) -> Optional[np.ndarray]:
        """
        Get prediction probabilities (if supported).
        
        Args:
            X: Features for prediction
        
        Returns:
            Probability array or None if not supported
        """
        if hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(self._prepare_features(X))
        return None
    
    def _prepare_features(self, X: pd.DataFrame) -> np.ndarray:
        """
        Prepare features for model input.
        
        Args:
            X: Raw features
        
        Returns:
            Scaled feature array
        """
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        
        # Select only relevant features
        if self.feature_names:
            X = X[self.feature_names]
        
        # Scale features if scaler exists
        if self.scaler is not None:
            return self.scaler.transform(X)
        
        return X.values
    
    def score(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        metric: str = 'accuracy'
    ) -> float:
        """
        Evaluate model performance.
        
        Args:
            X: Test features
            y: Test targets
            metric: Evaluation metric ('accuracy', 'f1', 'roc_auc')
        
        Returns:
            Score value
        """
        if self.model is None:
            logger.warning("Model not fitted")
            return 0.0
        
        predictions = self.predict(X)
        
        if metric == 'accuracy':
            return float(np.mean(predictions == y.values))
        elif metric == 'f1':
            from sklearn.metrics import f1_score
            return float(f1_score(y, predictions, average='weighted'))
        elif metric == 'roc_auc':
            from sklearn.metrics import roc_auc_score
            proba = self.predict_proba(X)
            if proba is not None:
                return float(roc_auc_score(y, proba[:, 1]))
        
        return 0.0
    
    def get_feature_importance(
        self,
        top_n: int = 10
    ) -> Optional[pd.DataFrame]:
        """
        Get feature importance scores.
        
        Args:
            top_n: Number of top features to return
        
        Returns:
            DataFrame with feature importance or None
        """
        if not hasattr(self.model, 'feature_importances_'):
            return None
        
        importances = self.model.feature_importances_
        
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importances
        }).sort_values('importance', ascending=False)
        
        return feature_importance.head(top_n)
    
    def save(self, filepath: Path) -> None:
        """
        Save model and scaler to disk.
        
        Args:
            filepath: Path to save model (without extension)
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Save model
        model_path = filepath.with_suffix('.pkl')
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        logger.info(f"Saved model to {model_path}")
        
        # Save scaler
        if self.scaler is not None:
            scaler_path = filepath.with_stem(f'{filepath.stem}_scaler')
            with open(scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            logger.info(f"Saved scaler to {scaler_path}")
        
        # Save metadata
        metadata = {
            'model_name': self.model_name,
            'model_type': self.model_type,
            'feature_names': self.feature_names,
            'is_fitted': self.is_fitted
        }
        
        metadata_path = filepath.with_suffix('.json')
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved metadata to {metadata_path}")
    
    def load(self, filepath: Path) -> None:
        """
        Load model and scaler from disk.
        
        Args:
            filepath: Path to model files (without extension)
        """
        filepath = Path(filepath)
        
        # Load model
        model_path = filepath.with_suffix('.pkl')
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        logger.info(f"Loaded model from {model_path}")
        
        # Load scaler
        scaler_path = filepath.with_stem(f'{filepath.stem}_scaler')
        if scaler_path.exists():
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            logger.info(f"Loaded scaler from {scaler_path}")
        
        # Load metadata
        metadata_path = filepath.with_suffix('.json')
        if metadata_path.exists():
            import json
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            self.feature_names = metadata.get('feature_names', [])
            self.is_fitted = metadata.get('is_fitted', False)
            logger.info(f"Loaded metadata from {metadata_path}")
    
    def get_params(self) -> Dict[str, Any]:
        """
        Get model parameters.
        
        Returns:
            Dictionary of parameters
        """
        if self.model is None:
            return {}
        
        if hasattr(self.model, 'get_params'):
            return self.model.get_params()
        
        return {}
    
    def set_params(self, **params) -> None:
        """
        Set model parameters.
        
        Args:
            **params: Parameters to set
        """
        if self.model is None:
            logger.warning("Model not initialized")
            return
        
        if hasattr(self.model, 'set_params'):
            self.model.set_params(**params)
    
    def __repr__(self) -> str:
        """String representation."""
        status = "fitted" if self.is_fitted else "not fitted"
        return f"{self.__class__.__name__}({self.model_name}, {status})"
