"""Configuration schema for Kuralit.

This module defines the configuration dataclasses used throughout Kuralit.
Configurations are organized by component (LLM, STT, VAD, etc.) and support
provider-based settings.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, Optional


@dataclass
class LLMConfig:
    """Configuration for LLM (Language Model) providers.
    
    This configuration is provider-agnostic. Provider-specific settings
    are loaded from environment variables prefixed with the provider name
    (e.g., GEMINI_API_KEY, OPENAI_API_KEY).
    """
    provider: str = "gemini"  # Provider name (e.g., "gemini", "openai")
    model_id: str = "gemini-2.0-flash-001"  # Model identifier
    api_key: Optional[str] = None  # Provider API key
    base_url: Optional[str] = None  # Optional custom base URL
    temperature: float = 0.7  # Temperature for generation
    max_tokens: Optional[int] = None  # Maximum tokens to generate
    timeout: float = 60.0  # Request timeout in seconds
    
    # Provider-specific settings (stored as dict)
    provider_settings: Dict = field(default_factory=dict)


@dataclass
class STTConfig:
    """Configuration for STT (Speech-to-Text) providers.
    
    This configuration is provider-agnostic. Provider-specific settings
    are loaded from environment variables prefixed with the provider name
    (e.g., DEEPGRAM_API_KEY, GOOGLE_STT_API_KEY).
    """
    provider: str = "deepgram"  # Provider name (e.g., "deepgram", "google")
    model: Optional[str] = None  # Model identifier (e.g., "nova-2")
    language_code: str = "en-US"  # Language code
    sample_rate: int = 16000  # Audio sample rate
    encoding: str = "linear16"  # Audio encoding
    api_key: Optional[str] = None  # Provider API key
    credentials_path: Optional[str] = None  # Path to credentials file (Google)
    interim_results: bool = True  # Enable interim results
    punctuate: bool = True  # Enable punctuation
    smart_format: bool = True  # Enable smart formatting
    
    # Provider-specific settings (stored as dict)
    provider_settings: Dict = field(default_factory=dict)


@dataclass
class VADConfig:
    """Configuration for VAD (Voice Activity Detection).
    
    VAD settings are generally provider-agnostic, but some providers
    may have specific model paths or settings.
    """
    enabled: bool = True
    provider: str = "silero"  # Provider name (e.g., "silero")
    model: Optional[str] = None  # Model identifier
    activation_threshold: float = 0.5  # Speech activation threshold
    model_path: Optional[str] = None  # Path to model file
    sample_rate: int = 16000  # Audio sample rate (must match audio)


@dataclass
class TurnDetectorConfig:
    """Configuration for Turn Detector.
    
    Turn Detector settings for end-of-turn detection.
    """
    enabled: bool = True
    provider: str = "multilingual"  # Provider name (e.g., "multilingual", "english")
    model: Optional[str] = None  # Model identifier
    threshold: float = 0.6  # End-of-turn probability threshold
    model_path: Optional[str] = None  # Path to model file
    tokenizer_path: Optional[str] = None  # Path to tokenizer


@dataclass
class AgentConfig:
    """Configuration for Agent settings.
    
    This includes agent name and system instructions.
    """
    name: str = "WebSocket Agent"  # Agent name
    instructions: Optional[str] = None  # System instructions/prompt
    # Instructions can be set via:
    # 1. Direct in AgentSession (highest priority)
    # 2. KURALIT_AGENT_INSTRUCTIONS env var (medium priority)
    # 3. Default generated instructions (lowest priority)


@dataclass
class ToolsConfig:
    """Configuration for REST API Tools (Postman collections).
    """
    postman_collection_path: Optional[str] = None  # Path to Postman collection
    api_base_url: Optional[str] = None  # Base URL for API calls
    api_headers: Optional[Dict[str, str]] = None  # Headers for API calls
    enabled: bool = True  # Enable/disable tools


@dataclass
class ServerConfig:
    """Server-level configuration.
    
    This includes WebSocket server settings, limits, and metrics.
    Note: This is kept separate from the new Config class to maintain
    backward compatibility with existing code.
    """
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"
    
    # Security
    api_key_validator: Optional[Callable[[str], bool]] = None
    require_wss: bool = True
    
    # Audio buffer settings
    silence_threshold: float = 0.01
    silence_duration_ms: int = 500
    max_buffer_duration_ms: int = 3000
    max_buffer_size_bytes: int = 131072  # 128KB
    chunk_size_ms: int = 50
    
    # Endpointing delays
    min_endpointing_delay: float = 0.5  # seconds
    max_endpointing_delay: float = 3.0  # seconds
    
    # Limits
    max_text_size_bytes: int = 4096
    max_audio_chunk_size_bytes: int = 16384  # 16KB
    max_concurrent_connections: int = 1000
    connection_timeout_seconds: int = 300
    
    # Metrics
    enable_metrics: bool = True
    metrics_port: int = 9090


@dataclass
class Config:
    """Main configuration container.
    
    This class contains all component configurations. It can be loaded
    from environment variables or created programmatically.
    """
    # Component configurations
    llm: LLMConfig = field(default_factory=LLMConfig)
    stt: STTConfig = field(default_factory=STTConfig)
    vad: VADConfig = field(default_factory=VADConfig)
    turn_detector: TurnDetectorConfig = field(default_factory=TurnDetectorConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    tools: ToolsConfig = field(default_factory=ToolsConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    
    def validate(self) -> None:
        """Validate configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate LLM config
        if not self.llm.provider:
            raise ValueError("LLM provider must be specified")
        if not self.llm.api_key:
            import warnings
            warnings.warn(
                f"LLM API key not set for provider '{self.llm.provider}'. "
                f"Set {self.llm.provider.upper()}_API_KEY environment variable."
            )
        
        # Validate STT config
        if not self.stt.provider:
            raise ValueError("STT provider must be specified")
        if not self.stt.api_key and not self.stt.credentials_path:
            import warnings
            warnings.warn(
                f"STT credentials not set for provider '{self.stt.provider}'. "
                f"Set {self.stt.provider.upper()}_API_KEY or credentials path."
            )
        
        # Validate VAD config
        if self.vad.enabled and not self.vad.provider:
            raise ValueError("VAD provider must be specified when VAD is enabled")
        
        # Validate Turn Detector config
        if self.turn_detector.enabled and not self.turn_detector.provider:
            raise ValueError("Turn Detector provider must be specified when enabled")

