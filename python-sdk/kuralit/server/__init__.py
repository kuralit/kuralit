"""Kuralit WebSocket Server Package.

This package provides a production-grade WebSocket server for realtime
text and audio communication with Android clients.

Supports multiple STT providers:
- Deepgram (recommended) - Native WebSocket, low latency
- Google Cloud Speech-to-Text (legacy) - For existing users
"""

from kuralit.server.websocket_server import create_app, app
from kuralit.plugins.stt.deepgram import DeepgramSTTHandler
from kuralit.plugins.stt.google import GoogleSTTHandler

# Export plugin classes (backward compatible aliases)
STTHandler = GoogleSTTHandler  # Alias for backward compatibility

__all__ = [
    "create_app",
    "app",
    "DeepgramSTTHandler",
    "GoogleSTTHandler",
    "STTHandler",  # Backward compatibility alias
]

