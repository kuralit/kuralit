"""Plugin registry for managing and discovering plugins.

The PluginRegistry is a centralized system for registering and retrieving
plugins. Plugins can be registered manually or automatically on import.
"""

import logging
from typing import Dict, List, Optional

from kuralit.core.interfaces import (
    LLMPlugin,
    STTPlugin,
    VADPlugin,
    TurnDetectorPlugin,
)

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Centralized registry for all plugins.
    
    This class provides a singleton-like interface for registering and
    retrieving plugins. Plugins are organized by type (LLM, STT, VAD, etc.)
    and can be retrieved by name.
    """
    
    # Class-level storage for plugins
    _llm_plugins: Dict[str, LLMPlugin] = {}
    _stt_plugins: Dict[str, STTPlugin] = {}
    _vad_plugins: Dict[str, VADPlugin] = {}
    _turn_detector_plugins: Dict[str, TurnDetectorPlugin] = {}
    
    @classmethod
    def register_llm_plugin(cls, plugin: LLMPlugin) -> None:
        """Register an LLM plugin.
        
        Args:
            plugin: LLM plugin instance
            
        Raises:
            ValueError: If plugin name is already registered
        """
        name = plugin.name.lower()
        if name in cls._llm_plugins:
            logger.warning(
                f"LLM plugin '{name}' is already registered. "
                f"Overwriting with new plugin."
            )
        cls._llm_plugins[name] = plugin
        logger.debug(f"Registered LLM plugin: {name} ({plugin.provider})")
    
    @classmethod
    def register_stt_plugin(cls, plugin: STTPlugin) -> None:
        """Register an STT plugin.
        
        Args:
            plugin: STT plugin instance
            
        Raises:
            ValueError: If plugin name is already registered
        """
        name = plugin.name.lower()
        if name in cls._stt_plugins:
            logger.warning(
                f"STT plugin '{name}' is already registered. "
                f"Overwriting with new plugin."
            )
        cls._stt_plugins[name] = plugin
        logger.debug(f"Registered STT plugin: {name} ({plugin.provider})")
    
    @classmethod
    def register_vad_plugin(cls, plugin: VADPlugin) -> None:
        """Register a VAD plugin.
        
        Args:
            plugin: VAD plugin instance
        """
        name = plugin.name.lower()
        if name in cls._vad_plugins:
            logger.warning(
                f"VAD plugin '{name}' is already registered. "
                f"Overwriting with new plugin."
            )
        cls._vad_plugins[name] = plugin
        logger.debug(f"Registered VAD plugin: {name} ({plugin.provider})")
    
    @classmethod
    def register_turn_detector_plugin(cls, plugin: TurnDetectorPlugin) -> None:
        """Register a Turn Detector plugin.
        
        Args:
            plugin: Turn Detector plugin instance
        """
        name = plugin.name.lower()
        if name in cls._turn_detector_plugins:
            logger.warning(
                f"Turn Detector plugin '{name}' is already registered. "
                f"Overwriting with new plugin."
            )
        cls._turn_detector_plugins[name] = plugin
        logger.debug(f"Registered Turn Detector plugin: {name} ({plugin.provider})")
    
    @classmethod
    def get_llm_plugin(cls, name: str) -> Optional[LLMPlugin]:
        """Get an LLM plugin by name.
        
        Args:
            name: Plugin name (case-insensitive)
            
        Returns:
            LLM plugin instance or None if not found
        """
        return cls._llm_plugins.get(name.lower())
    
    @classmethod
    def get_stt_plugin(cls, name: str) -> Optional[STTPlugin]:
        """Get an STT plugin by name.
        
        Args:
            name: Plugin name (case-insensitive)
            
        Returns:
            STT plugin instance or None if not found
        """
        return cls._stt_plugins.get(name.lower())
    
    @classmethod
    def get_vad_plugin(cls, name: str) -> Optional[VADPlugin]:
        """Get a VAD plugin by name.
        
        Args:
            name: Plugin name (case-insensitive)
            
        Returns:
            VAD plugin instance or None if not found
        """
        return cls._vad_plugins.get(name.lower())
    
    @classmethod
    def get_turn_detector_plugin(cls, name: str) -> Optional[TurnDetectorPlugin]:
        """Get a Turn Detector plugin by name.
        
        Args:
            name: Plugin name (case-insensitive)
            
        Returns:
            Turn Detector plugin instance or None if not found
        """
        return cls._turn_detector_plugins.get(name.lower())
    
    @classmethod
    def list_llm_plugins(cls) -> List[str]:
        """List all registered LLM plugin names.
        
        Returns:
            List of plugin names
        """
        return list(cls._llm_plugins.keys())
    
    @classmethod
    def list_stt_plugins(cls) -> List[str]:
        """List all registered STT plugin names.
        
        Returns:
            List of plugin names
        """
        return list(cls._stt_plugins.keys())
    
    @classmethod
    def list_vad_plugins(cls) -> List[str]:
        """List all registered VAD plugin names.
        
        Returns:
            List of plugin names
        """
        return list(cls._vad_plugins.keys())
    
    @classmethod
    def list_turn_detector_plugins(cls) -> List[str]:
        """List all registered Turn Detector plugin names.
        
        Returns:
            List of plugin names
        """
        return list(cls._turn_detector_plugins.keys())
    
    @classmethod
    def clear_all(cls) -> None:
        """Clear all registered plugins (useful for testing)."""
        cls._llm_plugins.clear()
        cls._stt_plugins.clear()
        cls._vad_plugins.clear()
        cls._turn_detector_plugins.clear()
        logger.debug("Cleared all plugins from registry")

