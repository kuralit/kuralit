"""Gemini LLM Plugin for KuralIt.

This module provides the Gemini plugin and auto-registers it with the plugin registry.
"""

from kuralit.core.plugin_registry import PluginRegistry
from kuralit.plugins.llm.gemini.model import Gemini
from kuralit.plugins.llm.gemini.plugin import GeminiPlugin

# Create plugin instance
_plugin = GeminiPlugin()

# Auto-register plugin
PluginRegistry.register_llm_plugin(_plugin)

# Export for direct imports
__all__ = ["Gemini", "GeminiPlugin"]

