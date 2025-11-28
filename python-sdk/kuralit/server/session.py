"""Session management for WebSocket connections."""

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from uuid import uuid4

from kuralit.models.message import Message

from kuralit.server.audio_buffer import AudioBuffer
from kuralit.server.config import ServerConfig
from kuralit.server.metrics import SessionMetrics

logger = logging.getLogger(__name__)


@dataclass
class Session:
    """Manages session state for a WebSocket connection."""
    
    session_id: str
    config: ServerConfig
    conversation_history: List[Message] = field(default_factory=list)
    audio_buffer: AudioBuffer = field(init=False)
    is_audio_active: bool = False
    current_audio_stream_id: Optional[str] = None
    user_metadata: Dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    metrics: SessionMetrics = field(default_factory=SessionMetrics)
    
    # Optional handlers from AgentSession (plugin instances)
    _vad_handler: Optional[object] = field(default=None)
    _turn_detector_handler: Optional[object] = field(default=None)
    
    # VAD and Turn Detector handlers (optional) - public interface
    vad_handler: Optional[object] = field(default=None, init=False)
    turn_detector_handler: Optional[object] = field(default=None, init=False)
    
    # Audio Recognition Handler (coordinates VAD, STT, Turn Detector)
    audio_recognition_handler: Optional[object] = field(default=None, init=False)
    
    # VAD initialization state (internal)
    _vad_handler_class: Optional[type] = field(default=None, init=False)
    _vad_initialized: bool = field(default=False, init=False)
    
    def __post_init__(self):
        """Initialize audio buffer and optional handlers after object creation."""
        # Audio buffer will get VAD handler after VAD is initialized in start_audio_stream
        self.audio_buffer = AudioBuffer(self.config, vad_handler=None)
        
        # If handlers were provided (from AgentSession), use them
        if self._turn_detector_handler:
            self.turn_detector_handler = self._turn_detector_handler
            logger.debug(f"Turn Detector handler provided for session {self.session_id}")
        elif hasattr(self.config, 'turn_detector_enabled') and self.config.turn_detector_enabled:
            # Use plugin registry to create Turn Detector handler
            try:
                from kuralit.core.plugin_registry import PluginRegistry
                from kuralit.config.schema import TurnDetectorConfig
                
                turn_detector_plugin = PluginRegistry.get_turn_detector_plugin("multilingual")
                if turn_detector_plugin:
                    turn_detector_model_path = getattr(self.config, 'turn_detector_model_path', None)
                    turn_detector_threshold = getattr(self.config, 'turn_detector_threshold', 0.6)
                    
                    turn_detector_config = TurnDetectorConfig(
                        enabled=True,
                        provider="multilingual",
                        model_path=turn_detector_model_path,
                        threshold=turn_detector_threshold,
                    )
                    self.turn_detector_handler = turn_detector_plugin.create_handler(turn_detector_config)
                    logger.debug(f"Turn Detector handler initialized for session {self.session_id}")
                else:
                    logger.warning("Turn Detector plugin not found. Turn Detector will be disabled.")
                    self.turn_detector_handler = None
            except Exception as e:
                logger.warning(f"Failed to initialize Turn Detector handler: {e}. Turn Detector will be disabled.")
                self.turn_detector_handler = None
        
        # VAD handler will be initialized in start_audio_stream (needs sample_rate)
        # If handler was provided, store it for later use
        if self._vad_handler:
            # VAD handler provided - will be set in start_audio_stream
            self._vad_initialized = False
        elif hasattr(self.config, 'vad_enabled') and self.config.vad_enabled:
            # Use plugin registry - VAD will be initialized when audio stream starts (needs sample_rate)
            try:
                from kuralit.core.plugin_registry import PluginRegistry
                vad_plugin = PluginRegistry.get_vad_plugin("silero")
                if vad_plugin:
                    # Store plugin reference for later initialization
                    self._vad_plugin = vad_plugin
                    self._vad_initialized = False
                else:
                    logger.warning("VAD plugin not found. VAD will be disabled.")
                    self._vad_plugin = None
                    self._vad_initialized = False
            except Exception as e:
                logger.warning(f"Failed to get VAD plugin: {e}. VAD will be disabled.")
                self._vad_plugin = None
                self._vad_initialized = False
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()
        self.metrics.update_activity()
    
    def start_audio_stream(self, sample_rate: int, encoding: str, stream_id: Optional[str] = None) -> None:
        """Start an audio stream.
        
        Args:
            sample_rate: Audio sample rate
            encoding: Audio encoding format
            stream_id: Optional stream identifier
        """
        self.is_audio_active = True
        self.current_audio_stream_id = stream_id or str(uuid4())
        self.audio_buffer.set_audio_config(sample_rate, encoding)
        
        # Initialize VAD handler if enabled and not already initialized
        if not self._vad_initialized:
            if self._vad_handler:
                # Use provided VAD handler (from AgentSession)
                self.vad_handler = self._vad_handler
                # Update audio buffer with VAD handler
                self.audio_buffer.vad_handler = self.vad_handler
                self._vad_initialized = True
                logger.debug(f"VAD handler provided for session {self.session_id} (sample_rate={sample_rate})")
            elif hasattr(self.config, 'vad_enabled') and self.config.vad_enabled and hasattr(self, '_vad_plugin') and self._vad_plugin:
                # Use plugin to create VAD handler
                try:
                    from kuralit.config.schema import VADConfig
                    
                    vad_activation_threshold = getattr(self.config, 'vad_activation_threshold', 0.5)
                    vad_model_path = getattr(self.config, 'vad_model_path', None)
                    
                    vad_config = VADConfig(
                        enabled=True,
                        provider="silero",
                        model_path=vad_model_path,
                        activation_threshold=vad_activation_threshold,
                        sample_rate=sample_rate,
                    )
                    self.vad_handler = self._vad_plugin.create_handler(vad_config)
                    # Update audio buffer with VAD handler
                    self.audio_buffer.vad_handler = self.vad_handler
                    self._vad_initialized = True
                    logger.debug(f"VAD handler initialized for session {self.session_id} (sample_rate={sample_rate})")
                except Exception as e:
                    logger.warning(f"Failed to initialize VAD handler: {e}. VAD will be disabled for this session.")
                    self.vad_handler = None
        
        self.update_activity()
    
    def end_audio_stream(self) -> bytes:
        """End the current audio stream and return accumulated audio.
        
        Returns:
            Accumulated audio bytes
        """
        self.is_audio_active = False
        accumulated = self.audio_buffer.flush()
        self.current_audio_stream_id = None
        self.update_activity()
        return accumulated
    
    def add_audio_chunk(self, chunk: bytes, timestamp: Optional[float] = None) -> tuple[bool, bytes]:
        """Add audio chunk to buffer.
        
        Args:
            chunk: Audio chunk bytes
            timestamp: Optional timestamp
            
        Returns:
            Tuple of (should_process, accumulated_audio)
        """
        if not self.is_audio_active:
            raise ValueError("Audio stream not active")
        
        should_process, accumulated = self.audio_buffer.add_chunk(chunk, timestamp)
        self.update_activity()
        return should_process, accumulated
    
    def add_message(self, message: Message) -> None:
        """Add message to conversation history.
        
        Args:
            message: Message to add
        """
        self.conversation_history.append(message)
        self.update_activity()
    
    def get_conversation_history(self) -> List[Message]:
        """Get conversation history."""
        return self.conversation_history.copy()
    
    def set_user(self, user_id: str, properties: Dict) -> None:
        """Set user information.
        
        Args:
            user_id: User identifier
            properties: User properties
        """
        self.user_metadata = {
            "user_id": user_id,
            "properties": properties,
        }
        self.update_activity()
    
    def clear_user(self) -> None:
        """Clear user information."""
        self.user_metadata = {}
    
    def is_expired(self, timeout_seconds: int) -> bool:
        """Check if session has expired.
        
        Args:
            timeout_seconds: Session timeout in seconds
            
        Returns:
            True if session is expired
        """
        inactive_time = time.time() - self.last_activity
        return inactive_time > timeout_seconds
    
    def reset(self) -> None:
        """Reset session state (keep session_id)."""
        self.conversation_history.clear()
        self.audio_buffer.reset()
        self.is_audio_active = False
        self.current_audio_stream_id = None
        
        # Reset VAD handler if initialized
        if self.vad_handler:
            self.vad_handler.reset()
        
        # Clear audio recognition handler state
        if self.audio_recognition_handler:
            self.audio_recognition_handler.clear_user_turn()
        
        self.update_activity()
    
    def get_conversation_history_for_turn_detector(self) -> List[Dict[str, str]]:
        """Convert conversation history to Turn Detector format.
        
        Returns:
            List of dicts with "role" and "content" keys for Turn Detector
        """
        if not self.turn_detector_handler:
            return []
        
        return self.turn_detector_handler.convert_message_history(self.conversation_history)

