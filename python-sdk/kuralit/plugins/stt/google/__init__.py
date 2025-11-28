"""Google STT Plugin for KuralIt.

This module provides the Google STT plugin and auto-registers it with the plugin registry.
"""

from kuralit.core.plugin_registry import PluginRegistry
from kuralit.plugins.stt.google.handler import GoogleSTTHandler
from kuralit.plugins.stt.google.plugin import GoogleSTTPlugin

# Create plugin instance
_plugin = GoogleSTTPlugin()

# Auto-register plugin
PluginRegistry.register_stt_plugin(_plugin)

# Export for direct imports
__all__ = ["GoogleSTTHandler", "GoogleSTTPlugin"]

