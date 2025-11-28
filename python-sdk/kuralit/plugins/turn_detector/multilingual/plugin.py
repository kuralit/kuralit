"""Multilingual Turn Detector Plugin for KuralIt.

This plugin provides Turn Detector integration as a plugin.
"""

import logging
from typing import List

from kuralit.core.interfaces import TurnDetectorPlugin
from kuralit.config.schema import TurnDetectorConfig
from kuralit.plugins.turn_detector.multilingual.handler import MultilingualTurnDetectorHandler

logger = logging.getLogger(__name__)


class MultilingualTurnDetectorPlugin(TurnDetectorPlugin):
    """Plugin for Multilingual Turn Detector provider."""
    
    @property
    def name(self) -> str:
        """Return the plugin name."""
        return "multilingual"
    
    @property
    def provider(self) -> str:
        """Return the provider name."""
        return "LiveKit"
    
    def create_handler(self, config: TurnDetectorConfig) -> MultilingualTurnDetectorHandler:
        """Create a Turn Detector handler instance from configuration.
        
        Args:
            config: Turn Detector configuration object (TurnDetectorConfig)
            
        Returns:
            MultilingualTurnDetectorHandler instance that implements predict_end_of_turn()
        """
        return MultilingualTurnDetectorHandler(config)
    
    def validate_config(self, config: TurnDetectorConfig) -> bool:
        """Validate configuration for Turn Detector plugin.
        
        Args:
            config: Turn Detector configuration object (TurnDetectorConfig)
            
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        if config.provider.lower() not in ["multilingual", "english"]:
            raise ValueError(f"Provider mismatch: expected 'multilingual' or 'english', got '{config.provider}'")
        
        if not (0.0 <= config.threshold <= 1.0):
            raise ValueError("threshold must be between 0.0 and 1.0")
        
        return True
    
    def get_required_env_vars(self) -> List[str]:
        """Get list of required environment variable names.
        
        Returns:
            List of environment variable names (empty for Turn Detector)
        """
        return []  # Turn Detector doesn't require API keys

