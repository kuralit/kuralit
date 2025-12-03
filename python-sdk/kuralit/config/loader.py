"""Configuration loader for Kuralit.

This module provides functionality to load configuration from environment
variables, with support for provider-based variable prefixes (e.g., GEMINI_*,
DEEPGRAM_*, etc.).
"""

import os
import logging
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

from kuralit.config.schema import (
    Config,
    ServerConfig,
    LLMConfig,
    STTConfig,
    VADConfig,
    TurnDetectorConfig,
    AgentConfig,
    ToolsConfig,
)

logger = logging.getLogger(__name__)


def _normalize_model_path(path: Optional[str]) -> Optional[str]:
    """Normalize model path: convert empty strings to None."""
    if not path or path.strip() == "":
        return None
    return path.strip()


def _load_env_file(root_path: Optional[str] = None) -> None:
    """Load environment variables from .env file."""
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
    
    # Try root of the project
    project_root = Path(__file__).parent.parent.parent.parent
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        return
    
    # Last resort: try current directory
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        load_dotenv(env_path)


class ConfigManager:
    """Manages loading and validation of Kuralit configuration."""
    
    def __init__(self, load_env: bool = True):
        """Initialize ConfigManager.
        
        Args:
            load_env: Whether to load .env file automatically
        """
        if load_env:
            _load_env_file()
    
    def load_from_env(self) -> Config:
        """Load configuration from environment variables.
        
        Returns:
            Config object with all settings loaded from environment
        """
        config = Config()
        
        # Load component configs
        config.llm = self._load_llm_config()
        config.stt = self._load_stt_config()
        config.vad = self._load_vad_config()
        config.turn_detector = self._load_turn_detector_config()
        config.agent = self._load_agent_config()
        config.tools = self._load_tools_config()
        config.server = self._load_server_config()
        
        return config
    
    def _load_llm_config(self) -> LLMConfig:
        """Load LLM configuration from environment variables.
        
        Supports provider-based variables:
        - KURALIT_LLM_PROVIDER (default: "gemini")
        - {PROVIDER}_API_KEY (e.g., GEMINI_API_KEY, OPENAI_API_KEY)
        - KURALIT_LLM_MODEL_ID (default: "gemini-2.0-flash-001")
        - KURALIT_LLM_TEMPERATURE (default: 0.7)
        """
        provider = os.getenv("KURALIT_LLM_PROVIDER", "gemini").lower()
        
        # Load provider-specific API key
        api_key = None
        provider_upper = provider.upper()
        api_key_var = f"{provider_upper}_API_KEY"
        api_key = os.getenv(api_key_var)
        
        # Fallback to generic GOOGLE_API_KEY for Gemini
        if not api_key and provider == "gemini":
            api_key = os.getenv("GOOGLE_API_KEY")
        
        return LLMConfig(
            provider=provider,
            model_id=os.getenv("KURALIT_LLM_MODEL_ID", "gemini-2.0-flash-001"),
            api_key=api_key,
            base_url=os.getenv("KURALIT_LLM_BASE_URL"),
            temperature=float(os.getenv("KURALIT_LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("KURALIT_LLM_MAX_TOKENS")) if os.getenv("KURALIT_LLM_MAX_TOKENS") else None,
            timeout=float(os.getenv("KURALIT_LLM_TIMEOUT", "60.0")),
        )
    
    def _load_stt_config(self) -> STTConfig:
        """Load STT configuration from environment variables.
        
        Supports provider-based variables:
        - KURALIT_STT_PROVIDER (default: "deepgram")
        - {PROVIDER}_API_KEY (e.g., DEEPGRAM_API_KEY, GOOGLE_STT_API_KEY)
        - KURALIT_STT_MODEL (optional)
        - KURALIT_STT_LANGUAGE (default: "en-US")
        """
        provider = os.getenv("KURALIT_STT_PROVIDER", "deepgram").lower()
        
        # Load provider-specific API key
        api_key = None
        credentials_path = None
        
        if provider == "deepgram":
            api_key = os.getenv("DEEPGRAM_API_KEY")
        elif provider == "google":
            api_key = os.getenv("GOOGLE_STT_API_KEY")
            credentials_path = os.getenv("GOOGLE_STT_CREDENTIALS")
        
        return STTConfig(
            provider=provider,
            model=os.getenv("KURALIT_STT_MODEL"),
            language_code=os.getenv("KURALIT_STT_LANGUAGE", "en-US"),
            sample_rate=int(os.getenv("KURALIT_SAMPLE_RATE", "16000")),
            encoding=os.getenv("KURALIT_STT_ENCODING", "linear16"),
            api_key=api_key,
            credentials_path=credentials_path,
            interim_results=os.getenv("KURALIT_STT_INTERIM_RESULTS", "true").lower() == "true",
            punctuate=os.getenv("KURALIT_STT_PUNCTUATE", "true").lower() == "true",
            smart_format=os.getenv("KURALIT_STT_SMART_FORMAT", "true").lower() == "true",
        )
    
    def _load_vad_config(self) -> VADConfig:
        """Load VAD configuration from environment variables.
        
        Environment variables:
        - KURALIT_VAD_ENABLED (default: "true")
        - KURALIT_VAD_PROVIDER (default: "silero")
        - KURALIT_VAD_ACTIVATION_THRESHOLD (default: 0.5)
        - KURALIT_VAD_MODEL_PATH (optional)
        """
        return VADConfig(
            enabled=os.getenv("KURALIT_VAD_ENABLED", "true").lower() == "true",
            provider=os.getenv("KURALIT_VAD_PROVIDER", "silero").lower(),
            model=os.getenv("KURALIT_VAD_MODEL"),
            activation_threshold=float(os.getenv("KURALIT_VAD_ACTIVATION_THRESHOLD", "0.5")),
            model_path=_normalize_model_path(os.getenv("KURALIT_VAD_MODEL_PATH")),
            sample_rate=int(os.getenv("KURALIT_SAMPLE_RATE", "16000")),
        )
    
    def _load_turn_detector_config(self) -> TurnDetectorConfig:
        """Load Turn Detector configuration from environment variables.
        
        Environment variables:
        - KURALIT_TURN_DETECTOR_ENABLED (default: "true")
        - KURALIT_TURN_DETECTOR_PROVIDER (default: "multilingual")
        - KURALIT_TURN_DETECTOR_THRESHOLD (default: 0.6)
        - KURALIT_TURN_DETECTOR_MODEL_PATH (optional)
        """
        return TurnDetectorConfig(
            enabled=os.getenv("KURALIT_TURN_DETECTOR_ENABLED", "true").lower() == "true",
            provider=os.getenv("KURALIT_TURN_DETECTOR_PROVIDER", "multilingual").lower(),
            model=os.getenv("KURALIT_TURN_DETECTOR_MODEL"),
            threshold=float(os.getenv("KURALIT_TURN_DETECTOR_THRESHOLD", "0.6")),
            model_path=_normalize_model_path(os.getenv("KURALIT_TURN_DETECTOR_MODEL_PATH")),
            tokenizer_path=_normalize_model_path(os.getenv("KURALIT_TURN_DETECTOR_TOKENIZER_PATH")),
        )
    
    def _load_agent_config(self) -> AgentConfig:
        """Load Agent configuration from environment variables.
        
        Environment variables:
        - KURALIT_AGENT_NAME (default: "WebSocket Agent")
        - KURALIT_AGENT_INSTRUCTIONS (optional, can be set in AgentSession)
        """
        return AgentConfig(
            name=os.getenv("KURALIT_AGENT_NAME", "WebSocket Agent"),
            instructions=os.getenv("KURALIT_AGENT_INSTRUCTIONS"),
        )
    
    def _load_tools_config(self) -> ToolsConfig:
        """Load Tools configuration from environment variables.
        
        Environment variables:
        - KURALIT_POSTMAN_COLLECTION (optional)
        - KURALIT_API_BASE_URL (optional)
        - KURALIT_TOOLS_ENABLED (default: "true")
        """
        return ToolsConfig(
            postman_collection_path=os.getenv("KURALIT_POSTMAN_COLLECTION"),
            api_base_url=os.getenv("KURALIT_API_BASE_URL"),
            api_headers=None,  # Can be set programmatically
            enabled=os.getenv("KURALIT_TOOLS_ENABLED", "true").lower() == "true",
        )
    
    def _load_server_config(self) -> ServerConfig:
        """Load Server configuration from environment variables.
        
        This maintains compatibility with the existing ServerConfig structure.
        """
        return ServerConfig(
            host=os.getenv("KURALIT_HOST", "0.0.0.0"),
            port=int(os.getenv("KURALIT_PORT", "8000")),
            debug=os.getenv("KURALIT_DEBUG", "false").lower() == "true",
            log_level=os.getenv("KURALIT_LOG_LEVEL", "INFO"),
            api_key_validator=None,  # Must be set programmatically
            require_wss=os.getenv("KURALIT_REQUIRE_WSS", "true").lower() == "true",
            silence_threshold=float(os.getenv("KURALIT_SILENCE_THRESHOLD", "0.01")),
            silence_duration_ms=int(os.getenv("KURALIT_SILENCE_DURATION_MS", "500")),
            max_buffer_duration_ms=int(os.getenv("KURALIT_MAX_BUFFER_DURATION_MS", "3000")),
            max_buffer_size_bytes=int(os.getenv("KURALIT_MAX_BUFFER_SIZE_BYTES", "131072")),
            chunk_size_ms=int(os.getenv("KURALIT_CHUNK_SIZE_MS", "50")),
            min_endpointing_delay=float(os.getenv("KURALIT_MIN_ENDPOINTING_DELAY", "0.5")),
            max_endpointing_delay=float(os.getenv("KURALIT_MAX_ENDPOINTING_DELAY", "3.0")),
            max_text_size_bytes=int(os.getenv("KURALIT_MAX_TEXT_SIZE", "4096")),
            max_audio_chunk_size_bytes=int(os.getenv("KURALIT_MAX_AUDIO_CHUNK_SIZE", "16384")),
            max_concurrent_connections=int(os.getenv("KURALIT_MAX_CONNECTIONS", "1000")),
            connection_timeout_seconds=int(os.getenv("KURALIT_CONNECTION_TIMEOUT", "300")),
            enable_metrics=os.getenv("KURALIT_ENABLE_METRICS", "true").lower() == "true",
            metrics_port=int(os.getenv("KURALIT_METRICS_PORT", "9090")),
        )
    
    def validate(self, config: Config) -> None:
        """Validate configuration.
        
        Args:
            config: Config object to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        config.validate()

