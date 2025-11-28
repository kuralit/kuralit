"""Core plugin infrastructure for KuralIt."""

from kuralit.core.interfaces import (
    LLMPlugin,
    STTPlugin,
    VADPlugin,
    TurnDetectorPlugin,
)
from kuralit.core.plugin_registry import PluginRegistry
from kuralit.core.resolver import PluginResolver

__all__ = [
    "LLMPlugin",
    "STTPlugin",
    "VADPlugin",
    "TurnDetectorPlugin",
    "PluginRegistry",
    "PluginResolver",
]

