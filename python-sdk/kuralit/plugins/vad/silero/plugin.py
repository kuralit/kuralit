"""Silero VAD Plugin for Kuralit.

This plugin provides Silero Voice Activity Detection integration as a plugin.
"""

import logging
from typing import List

from kuralit.core.interfaces import VADPlugin
from kuralit.config.schema import VADConfig
from kuralit.plugins.vad.silero.handler import SileroVADHandler

logger = logging.getLogger(__name__)


class SileroVADPlugin(VADPlugin):
    """Plugin for Silero VAD provider."""
    
    @property
    def name(self) -> str:
        """Return the plugin name."""
        return "silero"
    
    @property
    def provider(self) -> str:
        """Return the provider name."""
        return "Silero"
    
    def create_handler(self, config: VADConfig) -> SileroVADHandler:
        """Create a Silero VAD handler instance from configuration.
        
        Args:
            config: VAD configuration object (VADConfig)
            
        Returns:
            SileroVADHandler instance that implements process_audio_frame()
        """
        return SileroVADHandler(config)
    
    def validate_config(self, config: VADConfig) -> bool:
        """Validate configuration for Silero VAD plugin.
        
        Args:
            config: VAD configuration object (VADConfig)
            
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        if config.provider.lower() != "silero":
            raise ValueError(f"Provider mismatch: expected 'silero', got '{config.provider}'")
        
        if config.sample_rate not in [8000, 16000]:
            raise ValueError("Sample rate must be 8000 or 16000 Hz")
        
        if not (0.0 <= config.activation_threshold <= 1.0):
            raise ValueError("activation_threshold must be between 0.0 and 1.0")
        
        return True
    
    def get_required_env_vars(self) -> List[str]:
        """Get list of required environment variable names.
        
        Returns:
            List of environment variable names (empty for VAD)
        """
        return []  # VAD doesn't require API keys

