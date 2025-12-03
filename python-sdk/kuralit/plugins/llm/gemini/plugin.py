"""Gemini LLM Plugin for Kuralit.

This plugin provides Google Gemini model integration as a plugin.
"""

import logging
from typing import List

from kuralit.core.interfaces import LLMPlugin
from kuralit.config.schema import LLMConfig
from kuralit.plugins.llm.gemini.model import Gemini

logger = logging.getLogger(__name__)


class GeminiPlugin(LLMPlugin):
    """Plugin for Google Gemini LLM provider."""
    
    @property
    def name(self) -> str:
        """Return the plugin name."""
        return "gemini"
    
    @property
    def provider(self) -> str:
        """Return the provider name."""
        return "Google"
    
    def create_model(self, config: LLMConfig) -> Gemini:
        """Create a Gemini model instance from configuration.
        
        Args:
            config: LLM configuration object (LLMConfig)
            
        Returns:
            Gemini model instance
        """
        # Map LLMConfig to Gemini model parameters
        model = Gemini(
            id=config.model_id,
            name="Gemini",
            provider="Google",
            api_key=config.api_key,
            temperature=config.temperature,
            max_output_tokens=config.max_tokens,
        )
        
        # Apply any provider-specific settings
        if config.provider_settings:
            for key, value in config.provider_settings.items():
                if hasattr(model, key):
                    setattr(model, key, value)
        
        return model
    
    def validate_config(self, config: LLMConfig) -> bool:
        """Validate configuration for Gemini plugin.
        
        Args:
            config: LLM configuration object (LLMConfig)
            
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        if config.provider.lower() != "gemini":
            raise ValueError(f"Provider mismatch: expected 'gemini', got '{config.provider}'")
        
        if not config.api_key:
            raise ValueError(
                "Gemini API key is required. "
                "Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable."
            )
        
        if not config.model_id:
            raise ValueError("Model ID is required for Gemini plugin")
        
        return True
    
    def get_required_env_vars(self) -> List[str]:
        """Get list of required environment variable names.
        
        Returns:
            List of environment variable names
        """
        return ["GEMINI_API_KEY", "GOOGLE_API_KEY"]  # Either one works

