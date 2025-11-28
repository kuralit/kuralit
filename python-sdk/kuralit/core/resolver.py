"""Plugin resolver for string-based plugin specification.

This module provides functionality to resolve string-based plugin specifications
(e.g., "deepgram/nova-2:en" or "gemini/gemini-2.0-flash-001") into actual
plugin instances.
"""

import logging
from typing import Any, Optional, Tuple

from kuralit.core.plugin_registry import PluginRegistry
from kuralit.core.interfaces import LLMPlugin, STTPlugin, VADPlugin, TurnDetectorPlugin

logger = logging.getLogger(__name__)


class PluginResolver:
    """Resolves string-based plugin specifications to plugin instances.
    
    Supports LiveKit-style specifications:
    - STT: "provider/model:language" (e.g., "deepgram/nova-2:en")
    - LLM: "provider/model" (e.g., "gemini/gemini-2.0-flash-001")
    - VAD: "provider/model" (e.g., "silero/v3")
    - Turn Detector: "provider/model" (e.g., "multilingual/v1")
    """
    
    @staticmethod
    def parse_stt_spec(spec: str) -> Tuple[str, Optional[str], Optional[str]]:
        """Parse STT specification string.
        
        Format: "provider/model:language" or "provider/model" or "provider"
        
        Args:
            spec: STT specification string
            
        Returns:
            Tuple of (provider, model, language)
            
        Examples:
            "deepgram/nova-2:en" -> ("deepgram", "nova-2", "en")
            "deepgram/nova-2" -> ("deepgram", "nova-2", None)
            "deepgram" -> ("deepgram", None, None)
        """
        if not spec or not isinstance(spec, str):
            raise ValueError(f"Invalid STT spec: {spec}")
        
        # Split by colon for language
        parts = spec.split(":", 1)
        main_part = parts[0].strip()
        language = parts[1].strip() if len(parts) > 1 else None
        
        # Split by slash for provider/model
        provider_parts = main_part.split("/", 1)
        provider = provider_parts[0].strip().lower()
        model = provider_parts[1].strip() if len(provider_parts) > 1 else None
        
        return provider, model, language
    
    @staticmethod
    def parse_llm_spec(spec: str) -> Tuple[str, Optional[str]]:
        """Parse LLM specification string.
        
        Format: "provider/model" or "provider"
        
        Args:
            spec: LLM specification string
            
        Returns:
            Tuple of (provider, model)
            
        Examples:
            "gemini/gemini-2.0-flash-001" -> ("gemini", "gemini-2.0-flash-001")
            "gemini" -> ("gemini", None)
        """
        if not spec or not isinstance(spec, str):
            raise ValueError(f"Invalid LLM spec: {spec}")
        
        parts = spec.split("/", 1)
        provider = parts[0].strip().lower()
        model = parts[1].strip() if len(parts) > 1 else None
        
        return provider, model
    
    @staticmethod
    def parse_plugin_spec(spec: str) -> Tuple[str, Optional[str]]:
        """Parse generic plugin specification string.
        
        Format: "provider/model" or "provider"
        
        Used for VAD and Turn Detector plugins.
        
        Args:
            spec: Plugin specification string
            
        Returns:
            Tuple of (provider, model)
        """
        if not spec or not isinstance(spec, str):
            raise ValueError(f"Invalid plugin spec: {spec}")
        
        parts = spec.split("/", 1)
        provider = parts[0].strip().lower()
        model = parts[1].strip() if len(parts) > 1 else None
        
        return provider, model
    
    @staticmethod
    def resolve_stt(spec: str, config: Any) -> Any:
        """Resolve STT specification to STT handler instance.
        
        Args:
            spec: STT specification (e.g., "deepgram/nova-2:en")
            config: STT configuration object (STTConfig)
            
        Returns:
            STT handler instance
            
        Raises:
            ValueError: If plugin not found or invalid spec
        """
        provider, model, language = PluginResolver.parse_stt_spec(spec)
        
        # Get plugin from registry
        plugin = PluginRegistry.get_stt_plugin(provider)
        if not plugin:
            available = ", ".join(PluginRegistry.list_stt_plugins())
            raise ValueError(
                f"STT plugin '{provider}' not found. "
                f"Available plugins: {available or 'none'}"
            )
        
        # Update config with model and language if provided
        if model:
            config.model = model
        if language:
            config.language_code = language
        
        # Validate config
        plugin.validate_config(config)
        
        # Create handler
        handler = plugin.create_handler(config)
        logger.debug(f"Resolved STT spec '{spec}' to handler: {type(handler).__name__}")
        
        return handler
    
    @staticmethod
    def resolve_llm(spec: str, config: Any) -> Any:
        """Resolve LLM specification to Model instance.
        
        Args:
            spec: LLM specification (e.g., "gemini/gemini-2.0-flash-001")
            config: LLM configuration object (LLMConfig)
            
        Returns:
            Model instance
            
        Raises:
            ValueError: If plugin not found or invalid spec
        """
        provider, model = PluginResolver.parse_llm_spec(spec)
        
        # Get plugin from registry
        plugin = PluginRegistry.get_llm_plugin(provider)
        if not plugin:
            available = ", ".join(PluginRegistry.list_llm_plugins())
            raise ValueError(
                f"LLM plugin '{provider}' not found. "
                f"Available plugins: {available or 'none'}"
            )
        
        # Update config with model if provided
        if model:
            config.model_id = model
        
        # Validate config
        plugin.validate_config(config)
        
        # Create model
        model_instance = plugin.create_model(config)
        logger.debug(f"Resolved LLM spec '{spec}' to model: {type(model_instance).__name__}")
        
        return model_instance
    
    @staticmethod
    def resolve_vad(spec: str, config: Any) -> Any:
        """Resolve VAD specification to VAD handler instance.
        
        Args:
            spec: VAD specification (e.g., "silero/v3")
            config: VAD configuration object (VADConfig)
            
        Returns:
            VAD handler instance
            
        Raises:
            ValueError: If plugin not found or invalid spec
        """
        provider, model = PluginResolver.parse_plugin_spec(spec)
        
        # Get plugin from registry
        plugin = PluginRegistry.get_vad_plugin(provider)
        if not plugin:
            available = ", ".join(PluginRegistry.list_vad_plugins())
            raise ValueError(
                f"VAD plugin '{provider}' not found. "
                f"Available plugins: {available or 'none'}"
            )
        
        # Update config with model if provided
        if model:
            config.model = model
        
        # Validate config
        plugin.validate_config(config)
        
        # Create handler
        handler = plugin.create_handler(config)
        logger.debug(f"Resolved VAD spec '{spec}' to handler: {type(handler).__name__}")
        
        return handler
    
    @staticmethod
    def resolve_turn_detector(spec: str, config: Any) -> Any:
        """Resolve Turn Detector specification to handler instance.
        
        Args:
            spec: Turn Detector specification (e.g., "multilingual/v1")
            config: Turn Detector configuration object (TurnDetectorConfig)
            
        Returns:
            Turn Detector handler instance
            
        Raises:
            ValueError: If plugin not found or invalid spec
        """
        provider, model = PluginResolver.parse_plugin_spec(spec)
        
        # Get plugin from registry
        plugin = PluginRegistry.get_turn_detector_plugin(provider)
        if not plugin:
            available = ", ".join(PluginRegistry.list_turn_detector_plugins())
            raise ValueError(
                f"Turn Detector plugin '{provider}' not found. "
                f"Available plugins: {available or 'none'}"
            )
        
        # Update config with model if provided
        if model:
            config.model = model
        
        # Validate config
        plugin.validate_config(config)
        
        # Create handler
        handler = plugin.create_handler(config)
        logger.debug(f"Resolved Turn Detector spec '{spec}' to handler: {type(handler).__name__}")
        
        return handler

