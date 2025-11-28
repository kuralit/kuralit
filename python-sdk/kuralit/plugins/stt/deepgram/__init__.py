"""Deepgram STT Plugin for KuralIt.

This module provides the Deepgram STT plugin and auto-registers it with the plugin registry.
"""

from kuralit.core.plugin_registry import PluginRegistry
from kuralit.plugins.stt.deepgram.handler import DeepgramSTTHandler
from kuralit.plugins.stt.deepgram.plugin import DeepgramSTTPlugin

# Create plugin instance
_plugin = DeepgramSTTPlugin()

# Auto-register plugin
PluginRegistry.register_stt_plugin(_plugin)

# Export for direct imports
__all__ = ["DeepgramSTTHandler", "DeepgramSTTPlugin"]

