"""VAD plugins for Kuralit.

This module provides access to all VAD plugins.
"""

# Import plugins to trigger auto-registration
from kuralit.plugins.vad import silero

__all__ = ["silero"]

