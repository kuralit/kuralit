"""STT plugins for KuralIt.

This module provides access to all STT plugins.
"""

# Import plugins to trigger auto-registration
from kuralit.plugins.stt import deepgram, google

__all__ = ["deepgram", "google"]

