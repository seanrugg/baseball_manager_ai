"""
Baseball Manager AI API Module

Provides REST API endpoints for model serving, data ingestion, and web dashboard.
"""

__version__ = "1.0.0"
__author__ = "Baseball Manager AI Team"

from .model_server import ModelServer
from .data_ingestion import DataIngestionAPI
from .web_dashboard import WebDashboard

__all__ = ['ModelServer', 'DataIngestionAPI', 'WebDashboard']
