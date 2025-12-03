"""Silero VAD Plugin for Kuralit.

This module provides the Silero VAD plugin and auto-registers it with the plugin registry.
"""

from kuralit.core.plugin_registry import PluginRegistry
from kuralit.plugins.vad.silero.handler import SileroVADHandler
from kuralit.plugins.vad.silero.plugin import SileroVADPlugin

# Create plugin instance
_plugin = SileroVADPlugin()

# Auto-register plugin
PluginRegistry.register_vad_plugin(_plugin)

# Export for direct imports
__all__ = ["SileroVADHandler", "SileroVADPlugin"]

