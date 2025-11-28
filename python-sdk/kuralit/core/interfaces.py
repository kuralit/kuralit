"""Plugin interfaces for KuralIt.

This module defines the abstract base classes that all plugins must implement.
These interfaces ensure that plugins provide the required functionality while
allowing flexibility in implementation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

# Type hints for handler classes (will be imported when needed)
STTHandler = Any  # Will be properly typed when handlers are created
VADHandler = Any
TurnDetectorHandler = Any
Model = Any  # From kuralit.models.base.Model


class LLMPlugin(ABC):
    """Base class for LLM (Language Model) plugins.
    
    All LLM plugins must implement this interface to be compatible with
    the KuralIt plugin system.
    
    The plugin creates Model instances that implement the Model interface
    from kuralit.models.base.Model, which includes methods like:
    - invoke()
    - ainvoke_stream()
    - response()
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the plugin name (e.g., 'gemini', 'openai')."""
        pass
    
    @property
    @abstractmethod
    def provider(self) -> str:
        """Return the provider name (e.g., 'Google', 'OpenAI')."""
        pass
    
    @abstractmethod
    def create_model(self, config: Any) -> Model:
        """Create a Model instance from configuration.
        
        Args:
            config: LLM configuration object (LLMConfig)
            
        Returns:
            Model instance that implements kuralit.models.base.Model interface
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Any) -> bool:
        """Validate configuration for this plugin.
        
        Args:
            config: LLM configuration object (LLMConfig)
            
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    def get_required_env_vars(self) -> List[str]:
        """Get list of required environment variable names.
        
        Returns:
            List of environment variable names (e.g., ['GEMINI_API_KEY'])
        """
        pass


class STTPlugin(ABC):
    """Base class for STT (Speech-to-Text) plugins.
    
    All STT plugins must implement this interface. The handler created
    by create_handler() MUST implement the stream_transcribe() method
    with the following signature:
    
    async def stream_transcribe(
        self,
        audio_stream: AsyncIterator[bytes],
        sample_rate: int,
        encoding: str,
        language_code: Optional[str] = None,
    ) -> AsyncIterator[tuple[str, bool, Optional[float]]]:
        \"\"\"Stream audio and yield (transcript, is_final, confidence).\"\"\"
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the plugin name (e.g., 'deepgram', 'google')."""
        pass
    
    @property
    @abstractmethod
    def provider(self) -> str:
        """Return the provider name (e.g., 'Deepgram', 'Google')."""
        pass
    
    @abstractmethod
    def create_handler(self, config: Any) -> STTHandler:
        """Create an STT handler instance from configuration.
        
        Args:
            config: STT configuration object (STTConfig)
            
        Returns:
            STT handler instance that implements stream_transcribe()
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Any) -> bool:
        """Validate configuration for this plugin.
        
        Args:
            config: STT configuration object (STTConfig)
            
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    def get_required_env_vars(self) -> List[str]:
        """Get list of required environment variable names.
        
        Returns:
            List of environment variable names (e.g., ['DEEPGRAM_API_KEY'])
        """
        pass


class VADPlugin(ABC):
    """Base class for VAD (Voice Activity Detection) plugins.
    
    All VAD plugins must implement this interface. The handler created
    by create_handler() MUST implement the process_audio_frame() method
    with the following signature:
    
    def process_audio_frame(self, audio_frame: np.ndarray) -> Dict[str, Any]:
        \"\"\"Process audio frame and return VAD result.
        
        Returns:
            {
                "event": "START_OF_SPEECH" | "END_OF_SPEECH" | "CONTINUING",
                "probability": float
            }
        \"\"\"
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the plugin name (e.g., 'silero')."""
        pass
    
    @property
    @abstractmethod
    def provider(self) -> str:
        """Return the provider name (e.g., 'Silero')."""
        pass
    
    @abstractmethod
    def create_handler(self, config: Any) -> VADHandler:
        """Create a VAD handler instance from configuration.
        
        Args:
            config: VAD configuration object (VADConfig)
            
        Returns:
            VAD handler instance that implements process_audio_frame()
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Any) -> bool:
        """Validate configuration for this plugin.
        
        Args:
            config: VAD configuration object (VADConfig)
            
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    def get_required_env_vars(self) -> List[str]:
        """Get list of required environment variable names.
        
        Returns:
            List of environment variable names (e.g., [])
        """
        pass


class TurnDetectorPlugin(ABC):
    """Base class for Turn Detector plugins.
    
    All Turn Detector plugins must implement this interface. The handler
    created by create_handler() MUST implement the predict_end_of_turn()
    method with the following signature:
    
    def predict_end_of_turn(
        self,
        conversation_history: List[Dict[str, str]]
    ) -> float:
        \"\"\"Predict end-of-turn probability.
        
        Args:
            conversation_history: List of {"role": str, "content": str}
        
        Returns:
            Probability (0.0 to 1.0) that user has finished their turn
        \"\"\"
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the plugin name (e.g., 'multilingual', 'english')."""
        pass
    
    @property
    @abstractmethod
    def provider(self) -> str:
        """Return the provider name (e.g., 'LiveKit', 'Custom')."""
        pass
    
    @abstractmethod
    def create_handler(self, config: Any) -> TurnDetectorHandler:
        """Create a Turn Detector handler instance from configuration.
        
        Args:
            config: Turn Detector configuration object (TurnDetectorConfig)
            
        Returns:
            Turn Detector handler instance that implements predict_end_of_turn()
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Any) -> bool:
        """Validate configuration for this plugin.
        
        Args:
            config: Turn Detector configuration object (TurnDetectorConfig)
            
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    def get_required_env_vars(self) -> List[str]:
        """Get list of required environment variable names.
        
        Returns:
            List of environment variable names (e.g., [])
        """
        pass

