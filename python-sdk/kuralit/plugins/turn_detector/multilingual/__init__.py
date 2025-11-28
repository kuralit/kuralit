"""Multilingual Turn Detector Plugin for KuralIt.

This module provides the Turn Detector plugin and auto-registers it with the plugin registry.
"""

from kuralit.core.plugin_registry import PluginRegistry
from kuralit.plugins.turn_detector.multilingual.handler import MultilingualTurnDetectorHandler
from kuralit.plugins.turn_detector.multilingual.plugin import MultilingualTurnDetectorPlugin

# Create plugin instance
_plugin = MultilingualTurnDetectorPlugin()

# Auto-register plugin
PluginRegistry.register_turn_detector_plugin(_plugin)

# Export for direct imports
__all__ = ["MultilingualTurnDetectorHandler", "MultilingualTurnDetectorPlugin"]

