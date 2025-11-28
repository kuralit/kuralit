"""Server configuration module."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Optional

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


def load_env_file(root_path: Optional[str] = None) -> None:
    """Load environment variables from .env file.
    
    Args:
        root_path: Optional root path to search for .env file.
                   If None, searches from current directory up to project root.
    """
    if not DOTENV_AVAILABLE:
        return
    
    if root_path:
        env_path = Path(root_path) / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            return
    
    # Try to find .env file by walking up from current directory
    current = Path.cwd()
    while current != current.parent:
        env_path = current / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            return
        current = current.parent
    
    # Try root of the project (assuming we're in libs/kuralit/server)
    # Go up 3 levels: server -> kuralit -> libs -> root
    project_root = Path(__file__).parent.parent.parent.parent
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        return
    
    # Last resort: try current directory
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        load_dotenv(env_path)


def _normalize_model_path(path: Optional[str]) -> Optional[str]:
    """Normalize model path: convert empty strings to None.
    
    Args:
        path: Model path from environment variable
    
    Returns:
        None if path is empty/whitespace, otherwise the path
    """
    if not path or path.strip() == "":
        return None
    return path.strip()


@dataclass
class ServerConfig:
    """Configuration for WebSocket server."""
    
    def __post_init__(self):
        """Load .env file if not already loaded."""
        # Only load if DOTENV_AVAILABLE and .env not already processed
        if DOTENV_AVAILABLE and not hasattr(ServerConfig, '_env_loaded'):
            load_env_file()
            ServerConfig._env_loaded = True
    
    # Server settings
    host: str = field(default_factory=lambda: os.getenv("KURALIT_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("KURALIT_PORT", "8000")))
    debug: bool = field(default_factory=lambda: os.getenv("KURALIT_DEBUG", "false").lower() == "true")
    log_level: str = field(default_factory=lambda: os.getenv("KURALIT_LOG_LEVEL", "INFO"))
    
    # Security
    api_key_validator: Optional[Callable[[str], bool]] = None
    require_wss: bool = field(default_factory=lambda: os.getenv("KURALIT_REQUIRE_WSS", "true").lower() == "true")
    
    # STT settings
    stt_enabled: bool = field(default_factory=lambda: os.getenv("KURALIT_STT_ENABLED", "true").lower() == "true")
    stt_provider: str = field(default_factory=lambda: os.getenv("KURALIT_STT_PROVIDER", "deepgram"))  # "deepgram" or "google"
    
    # Google STT (legacy)
    stt_api_key: Optional[str] = field(default_factory=lambda: os.getenv("GOOGLE_STT_API_KEY"))
    stt_credentials_path: Optional[str] = field(default_factory=lambda: os.getenv("GOOGLE_STT_CREDENTIALS"))
    
    # Deepgram STT (recommended)
    deepgram_api_key: Optional[str] = field(default_factory=lambda: os.getenv("DEEPGRAM_API_KEY"))
    
    # Common STT settings
    stt_language_code: str = field(default_factory=lambda: os.getenv("KURALIT_STT_LANGUAGE", "en-US"))
    sample_rate: int = field(default_factory=lambda: int(os.getenv("KURALIT_SAMPLE_RATE", "16000")))
    
    # Audio buffer settings
    silence_threshold: float = field(default_factory=lambda: float(os.getenv("KURALIT_SILENCE_THRESHOLD", "0.01")))
    silence_duration_ms: int = field(default_factory=lambda: int(os.getenv("KURALIT_SILENCE_DURATION_MS", "500")))
    max_buffer_duration_ms: int = field(default_factory=lambda: int(os.getenv("KURALIT_MAX_BUFFER_DURATION_MS", "3000")))
    max_buffer_size_bytes: int = field(default_factory=lambda: int(os.getenv("KURALIT_MAX_BUFFER_SIZE_BYTES", "131072")))  # 128KB
    chunk_size_ms: int = field(default_factory=lambda: int(os.getenv("KURALIT_CHUNK_SIZE_MS", "50")))
    
    # VAD (Voice Activity Detection) settings
    vad_enabled: bool = field(default_factory=lambda: os.getenv("KURALIT_VAD_ENABLED", "true").lower() == "true")
    vad_activation_threshold: float = field(default_factory=lambda: float(os.getenv("KURALIT_VAD_ACTIVATION_THRESHOLD", "0.5")))
    vad_model_path: Optional[str] = field(default_factory=lambda: _normalize_model_path(os.getenv("KURALIT_VAD_MODEL_PATH")))
    
    # Turn Detector settings
    turn_detector_enabled: bool = field(default_factory=lambda: os.getenv("KURALIT_TURN_DETECTOR_ENABLED", "true").lower() == "true")
    turn_detector_threshold: float = field(default_factory=lambda: float(os.getenv("KURALIT_TURN_DETECTOR_THRESHOLD", "0.5")))
    turn_detector_model_path: Optional[str] = field(default_factory=lambda: _normalize_model_path(os.getenv("KURALIT_TURN_DETECTOR_MODEL_PATH")))
    
    # Endpointing delays (matching LiveKit defaults)
    # These control how long to wait after turn detector signals end-of-turn before committing the turn
    min_endpointing_delay: float = field(default_factory=lambda: float(os.getenv("KURALIT_MIN_ENDPOINTING_DELAY", "0.5")))  # seconds
    max_endpointing_delay: float = field(default_factory=lambda: float(os.getenv("KURALIT_MAX_ENDPOINTING_DELAY", "3.0")))  # seconds
    
    # Agent settings
    agent_api_key: Optional[str] = field(default_factory=lambda: os.getenv("GOOGLE_API_KEY"))
    agent_model_id: str = field(default_factory=lambda: os.getenv("KURALIT_MODEL_ID", "gemini-2.0-flash-001"))
    
    # REST API Tools settings
    postman_collection_path: Optional[str] = field(default_factory=lambda: os.getenv("KURALIT_POSTMAN_COLLECTION"))
    api_base_url: Optional[str] = field(default_factory=lambda: os.getenv("KURALIT_API_BASE_URL"))
    api_headers: Optional[Dict[str, str]] = field(default_factory=lambda: None)  # Can be set programmatically
    
    # Limits
    max_text_size_bytes: int = field(default_factory=lambda: int(os.getenv("KURALIT_MAX_TEXT_SIZE", "4096")))
    max_audio_chunk_size_bytes: int = field(default_factory=lambda: int(os.getenv("KURALIT_MAX_AUDIO_CHUNK_SIZE", "16384")))  # 16KB
    max_concurrent_connections: int = field(default_factory=lambda: int(os.getenv("KURALIT_MAX_CONNECTIONS", "1000")))
    connection_timeout_seconds: int = field(default_factory=lambda: int(os.getenv("KURALIT_CONNECTION_TIMEOUT", "300")))
    
    # Metrics
    enable_metrics: bool = field(default_factory=lambda: os.getenv("KURALIT_ENABLE_METRICS", "true").lower() == "true")
    metrics_port: int = field(default_factory=lambda: int(os.getenv("KURALIT_METRICS_PORT", "9090")))
    
    def validate(self) -> None:
        """Validate configuration."""
        if not self.api_key_validator:
            raise ValueError("api_key_validator must be provided")
        
        # STT validation - only check if STT is enabled
        if self.stt_enabled:
            if self.stt_provider == "deepgram":
                if not self.deepgram_api_key:
                    import warnings
                    warnings.warn(
                        "STT enabled with Deepgram provider but no API key provided. "
                        "Set DEEPGRAM_API_KEY. STT features will be disabled."
                    )
            elif self.stt_provider == "google":
                if not self.stt_api_key and not self.stt_credentials_path:
                    import warnings
                    warnings.warn(
                        "STT enabled with Google provider but no credentials provided. "
                        "Set GOOGLE_STT_API_KEY or GOOGLE_STT_CREDENTIALS. "
                        "STT features will be disabled."
                    )
            else:
                raise ValueError(f"Unknown STT provider: {self.stt_provider}. Use 'deepgram' or 'google'.")
        
        if not self.agent_api_key:
            raise ValueError("Agent API key required (set GOOGLE_API_KEY)")
        
        # Check if API key looks like a placeholder
        if self.agent_api_key and ("your-" in self.agent_api_key.lower() or "placeholder" in self.agent_api_key.lower()):
            raise ValueError(
                "GOOGLE_API_KEY appears to be a placeholder. "
                "Please set a valid Google Gemini API key in your .env file."
            )

