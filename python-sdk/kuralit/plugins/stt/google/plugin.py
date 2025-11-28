"""Google STT Plugin for KuralIt.

This plugin provides Google Cloud Speech-to-Text integration as a plugin.
"""

import logging
from typing import List

from kuralit.core.interfaces import STTPlugin
from kuralit.config.schema import STTConfig
from kuralit.plugins.stt.google.handler import GoogleSTTHandler

logger = logging.getLogger(__name__)


class GoogleSTTPlugin(STTPlugin):
    """Plugin for Google Cloud Speech-to-Text provider."""
    
    @property
    def name(self) -> str:
        """Return the plugin name."""
        return "google"
    
    @property
    def provider(self) -> str:
        """Return the provider name."""
        return "Google"
    
    def create_handler(self, config: STTConfig) -> GoogleSTTHandler:
        """Create a Google STT handler instance from configuration.
        
        Args:
            config: STT configuration object (STTConfig)
            
        Returns:
            GoogleSTTHandler instance that implements stream_transcribe()
        """
        return GoogleSTTHandler(config)
    
    def validate_config(self, config: STTConfig) -> bool:
        """Validate configuration for Google STT plugin.
        
        Args:
            config: STT configuration object (STTConfig)
            
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        if config.provider.lower() != "google":
            raise ValueError(f"Provider mismatch: expected 'google', got '{config.provider}'")
        
        if not config.api_key and not config.credentials_path:
            raise ValueError(
                "Google STT credentials are required. "
                "Set GOOGLE_STT_API_KEY or GOOGLE_STT_CREDENTIALS environment variable."
            )
        
        return True
    
    def get_required_env_vars(self) -> List[str]:
        """Get list of required environment variable names.
        
        Returns:
            List of environment variable names
        """
        return ["GOOGLE_STT_API_KEY", "GOOGLE_STT_CREDENTIALS"]  # Either one works

