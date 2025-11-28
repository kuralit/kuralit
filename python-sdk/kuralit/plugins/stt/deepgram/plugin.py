"""Deepgram STT Plugin for KuralIt.

This plugin provides Deepgram Speech-to-Text integration as a plugin.
"""

import logging
from typing import List

from kuralit.core.interfaces import STTPlugin
from kuralit.config.schema import STTConfig
from kuralit.plugins.stt.deepgram.handler import DeepgramSTTHandler

logger = logging.getLogger(__name__)


class DeepgramSTTPlugin(STTPlugin):
    """Plugin for Deepgram STT provider."""
    
    @property
    def name(self) -> str:
        """Return the plugin name."""
        return "deepgram"
    
    @property
    def provider(self) -> str:
        """Return the provider name."""
        return "Deepgram"
    
    def create_handler(self, config: STTConfig) -> DeepgramSTTHandler:
        """Create a Deepgram STT handler instance from configuration.
        
        Args:
            config: STT configuration object (STTConfig)
            
        Returns:
            DeepgramSTTHandler instance that implements stream_transcribe()
        """
        return DeepgramSTTHandler(config)
    
    def validate_config(self, config: STTConfig) -> bool:
        """Validate configuration for Deepgram plugin.
        
        Args:
            config: STT configuration object (STTConfig)
            
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        if config.provider.lower() != "deepgram":
            raise ValueError(f"Provider mismatch: expected 'deepgram', got '{config.provider}'")
        
        if not config.api_key:
            raise ValueError(
                "Deepgram API key is required. "
                "Set DEEPGRAM_API_KEY environment variable."
            )
        
        return True
    
    def get_required_env_vars(self) -> List[str]:
        """Get list of required environment variable names.
        
        Returns:
            List of environment variable names
        """
        return ["DEEPGRAM_API_KEY"]

