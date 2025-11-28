"""Audio buffer management - Simple pass-through for continuous streaming."""

import time
from typing import Optional

from kuralit.server.config import ServerConfig


class AudioBuffer:
    """
    Simple audio frame buffer - no processing decisions.
    
    In the new architecture, audio is streamed continuously to STT,
    so the buffer is just a temporary holder with no decision-making logic.
    """
    
    def __init__(self, config: ServerConfig, vad_handler: Optional[object] = None):
        """Initialize audio buffer.
        
        Args:
            config: Server configuration (kept for compatibility)
            vad_handler: Optional VAD handler (kept for compatibility, not used)
        """
        self.config = config
        self.vad_handler = vad_handler  # Kept for compatibility but not used
        self.sample_rate: int = 16000
        self.encoding: str = "PCM16"
        
        # Legacy fields for compatibility
        self._vad_speech_end_time: Optional[float] = None
        self._vad_is_speaking: bool = False
        
    def reset(self) -> None:
        """Reset buffer state."""
        self._vad_speech_end_time = None
        self._vad_is_speaking = False
    
    def set_audio_config(self, sample_rate: int, encoding: str) -> None:
        """Set audio configuration.
        
        Args:
            sample_rate: Audio sample rate
            encoding: Audio encoding format
        """
        self.sample_rate = sample_rate
        self.encoding = encoding
        self.reset()
    
    def add_chunk(self, chunk: bytes, timestamp: Optional[float] = None) -> tuple[bool, bytes]:
        """Add audio chunk - simplified to pass-through.
        
        Args:
            chunk: Audio chunk bytes (PCM16)
            timestamp: Optional timestamp for the chunk (ignored)
            
        Returns:
            Tuple of (False, b"") - no longer makes processing decisions
            Audio is streamed continuously via AudioRecognitionHandler
        """
        # In the new architecture, chunks are forwarded immediately to AudioRecognitionHandler
        # This method is kept for compatibility but no longer accumulates or makes decisions
        return False, b""
    
    def get_buffer_size(self) -> int:
        """Get current buffer size in bytes."""
        return 0  # No buffering in new architecture
    
    def get_buffer_duration_ms(self) -> float:
        """Estimate buffer duration in milliseconds.
        
        Returns:
            Always returns 0.0 (no buffering)
        """
        return 0.0
    
    def flush(self) -> bytes:
        """Flush buffer and return accumulated audio.
        
        Returns:
            Empty bytes (no buffering)
        """
        return b""

