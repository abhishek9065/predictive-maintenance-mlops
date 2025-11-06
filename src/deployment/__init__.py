"""Deployment package initialization."""

from .api import app
from .model_loader import ModelLoader

__all__ = ['app', 'ModelLoader']
