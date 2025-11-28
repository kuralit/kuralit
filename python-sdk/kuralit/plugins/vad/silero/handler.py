"""Voice Activity Detection (VAD) handler using Silero VAD model."""

import logging
from typing import Any, Dict, Literal, Optional

try:
    import numpy as np
    import onnxruntime
    VAD_AVAILABLE = True
except ImportError:
    VAD_AVAILABLE = False
    np = None
    onnxruntime = None

from kuralit.config.schema import VADConfig
from kuralit.server.exceptions import AudioProcessingError

logger = logging.getLogger(__name__)

# Supported sample rates
SUPPORTED_SAMPLE_RATES = [8000, 16000]


class SileroVADModel:
    """Silero VAD Model - Standalone Implementation
    
    Processes audio frames to detect speech activity.
    """
    
    def __init__(self, onnx_session: onnxruntime.InferenceSession, sample_rate: int):
        """Initialize VAD model.
        
        Args:
            onnx_session: Loaded ONNX inference session
            sample_rate: Audio sample rate (8000 or 16000 Hz)
        """
        if sample_rate not in SUPPORTED_SAMPLE_RATES:
            raise ValueError(f"Silero VAD only supports {SUPPORTED_SAMPLE_RATES} Hz sample rates")
        
        self._sess = onnx_session
        self._sample_rate = sample_rate
        
        # Window size depends on sample rate
        if sample_rate == 8000:
            self._window_size_samples = 256  # 32ms at 8kHz
            self._context_size = 32
        elif sample_rate == 16000:
            self._window_size_samples = 512  # 32ms at 16kHz
            self._context_size = 64
        
        # Initialize RNN state and context buffers
        self._sample_rate_nd = np.array(sample_rate, dtype=np.int64)
        self._context = np.zeros((1, self._context_size), dtype=np.float32)
        self._rnn_state = np.zeros((2, 1, 128), dtype=np.float32)
        self._input_buffer = np.zeros(
            (1, self._context_size + self._window_size_samples),
            dtype=np.float32
        )
    
    @property
    def window_size_samples(self) -> int:
        """Number of audio samples per inference window"""
        return self._window_size_samples
    
    @property
    def sample_rate(self) -> int:
        """Audio sample rate"""
        return self._sample_rate
    
    def __call__(self, audio_samples: np.ndarray) -> float:
        """Run inference on audio samples.
        
        Args:
            audio_samples: Audio samples as float32 array
                          Shape: (window_size_samples,)
                          Values should be normalized to [-1.0, 1.0]
        
        Returns:
            Probability score (0.0 to 1.0) indicating speech likelihood
            Higher values = more likely to be speech
        """
        # Prepare input buffer with context from previous inference
        # Context is the last N samples from previous window
        self._input_buffer[:, :self._context_size] = self._context
        self._input_buffer[:, self._context_size:] = audio_samples
        
        # Prepare ONNX inputs
        ort_inputs = {
            "input": self._input_buffer,      # Audio input with context
            "state": self._rnn_state,        # RNN hidden state
            "sr": self._sample_rate_nd,      # Sample rate
        }
        
        # Run inference
        outputs = self._sess.run(None, ort_inputs)
        out, self._rnn_state = outputs[0], outputs[1]
        
        # Update context for next inference (last N samples of current buffer)
        self._context = self._input_buffer[:, -self._context_size:]
        
        # Return probability score
        return float(out.item())
    
    def reset(self) -> None:
        """Reset RNN state and context buffers."""
        self._context = np.zeros((1, self._context_size), dtype=np.float32)
        self._rnn_state = np.zeros((2, 1, 128), dtype=np.float32)


def load_vad_model(onnx_file_path: Optional[str] = None, force_cpu: bool = True) -> onnxruntime.InferenceSession:
    """Load the Silero VAD ONNX model.
    
    Args:
        onnx_file_path: Path to ONNX model file (if None, tries to use embedded model or auto-download)
        force_cpu: Force CPU execution
    
    Returns:
        onnxruntime.InferenceSession: Loaded ONNX session
    
    Raises:
        AudioProcessingError: If model cannot be loaded
    """
    if not VAD_AVAILABLE:
        raise AudioProcessingError(
            "VAD dependencies not available. Install with: pip install onnxruntime numpy",
            retriable=False
        )
    
    # Normalize empty strings to None (safety check - config should handle this, but be defensive)
    if onnx_file_path is not None and isinstance(onnx_file_path, str) and onnx_file_path.strip() == "":
        onnx_file_path = None
    
    # Try to load from embedded model first
    if onnx_file_path is None:
        try:
            # Try to import from livekit.plugins.silero if available
            import importlib.resources
            try:
                res = importlib.resources.files("livekit.plugins.silero.resources") / "silero_vad.onnx"
                with importlib.resources.as_file(res) as path:
                    onnx_file_path = str(path)
                logger.info("Using embedded Silero VAD model from livekit.plugins.silero")
            except (ImportError, ModuleNotFoundError, FileNotFoundError):
                # Fallback: try to find model in common locations
                from pathlib import Path
                possible_paths = [
                    Path.home() / ".cache" / "silero_vad" / "silero_vad.onnx",
                    Path.cwd() / "silero_vad.onnx",
                ]
                for path in possible_paths:
                    if path.exists():
                        onnx_file_path = str(path)
                        logger.info(f"Using Silero VAD model from: {onnx_file_path}")
                        break
                
                # If not found, try to auto-download from Hugging Face or GitHub
                if onnx_file_path is None:
                    try:
                        logger.info("Silero VAD model not found locally. Attempting to download...")
                        cache_dir = Path.home() / ".cache" / "silero_vad"
                        cache_dir.mkdir(parents=True, exist_ok=True)
                        cached_model_path = cache_dir / "silero_vad.onnx"
                        
                        # Check if already cached
                        if cached_model_path.exists():
                            onnx_file_path = str(cached_model_path)
                            logger.info(f"Using cached Silero VAD model from: {onnx_file_path}")
                        else:
                            # Try Hugging Face first
                            try:
                                from huggingface_hub import hf_hub_download
                                
                                # Try snakers4/silero-vad repository
                                try:
                                    onnx_file_path = hf_hub_download(
                                        repo_id="snakers4/silero-vad",
                                        filename="silero_vad.onnx",
                                        cache_dir=str(cache_dir),
                                    )
                                    logger.info(f"Downloaded Silero VAD model from Hugging Face to: {onnx_file_path}")
                                except Exception:
                                    # If Hugging Face fails, try direct download from GitHub
                                    import urllib.request
                                    
                                    model_url = "https://github.com/snakers4/silero-vad/raw/master/src/silero_vad/data/silero_vad.onnx"
                                    logger.info(f"Downloading Silero VAD model from GitHub...")
                                    urllib.request.urlretrieve(model_url, str(cached_model_path))
                                    onnx_file_path = str(cached_model_path)
                                    logger.info(f"Downloaded Silero VAD model to: {onnx_file_path}")
                            except ImportError:
                                # huggingface-hub not available, try direct download
                                import urllib.request
                                
                                model_url = "https://github.com/snakers4/silero-vad/raw/master/src/silero_vad/data/silero_vad.onnx"
                                logger.info(f"Downloading Silero VAD model from GitHub (huggingface-hub not available)...")
                                urllib.request.urlretrieve(model_url, str(cached_model_path))
                                onnx_file_path = str(cached_model_path)
                                logger.info(f"Downloaded Silero VAD model to: {onnx_file_path}")
                    except Exception as download_error:
                        raise AudioProcessingError(
                            f"Silero VAD model not found and auto-download failed: {str(download_error)}. "
                            "Please provide onnx_file_path via KURALIT_VAD_MODEL_PATH, install livekit-plugins-silero, "
                            "or ensure internet connection for auto-download.",
                            retriable=False
                        ) from download_error
        except Exception as e:
            if isinstance(e, AudioProcessingError):
                raise
            raise AudioProcessingError(
                f"Failed to locate Silero VAD model: {str(e)}",
                retriable=False
            )
    else:
        # onnx_file_path was provided - use it
        from pathlib import Path
        onnx_file_path = Path(onnx_file_path)
        if not onnx_file_path.exists():
            raise AudioProcessingError(
                f"VAD model file not found: {onnx_file_path}",
                retriable=False
            )
        onnx_file_path = str(onnx_file_path)
    
    # Configure ONNX Runtime session options
    opts = onnxruntime.SessionOptions()
    opts.add_session_config_entry("session.intra_op.allow_spinning", "0")
    opts.add_session_config_entry("session.inter_op.allow_spinning", "0")
    opts.inter_op_num_threads = 1
    opts.intra_op_num_threads = 1
    opts.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL
    
    # Create inference session
    try:
        if force_cpu and "CPUExecutionProvider" in onnxruntime.get_available_providers():
            session = onnxruntime.InferenceSession(
                onnx_file_path,
                providers=["CPUExecutionProvider"],
                sess_options=opts
            )
        else:
            session = onnxruntime.InferenceSession(onnx_file_path, sess_options=opts)
        
        logger.info(f"Successfully loaded Silero VAD model from: {onnx_file_path}")
        return session
    except Exception as e:
        raise AudioProcessingError(
            f"Failed to load VAD model: {str(e)}",
            retriable=False
        ) from e


class SileroVADHandler:
    """Complete Silero VAD handler implementation"""
    
    def __init__(
        self,
        config: VADConfig,
        force_cpu: bool = True
    ):
        """Initialize VAD handler.
        
        Args:
            config: VAD configuration object (VADConfig)
            force_cpu: Force CPU execution
        
        Raises:
            AudioProcessingError: If VAD cannot be initialized
        """
        sample_rate = config.sample_rate
        activation_threshold = config.activation_threshold
        onnx_file_path = config.model_path
        if not VAD_AVAILABLE:
            raise AudioProcessingError(
                "VAD dependencies not available. Install with: pip install onnxruntime numpy",
                retriable=False
            )
        
        if sample_rate not in SUPPORTED_SAMPLE_RATES:
            raise ValueError(f"Sample rate must be one of {SUPPORTED_SAMPLE_RATES}")
        
        if not (0.0 <= activation_threshold <= 1.0):
            raise ValueError("activation_threshold must be between 0.0 and 1.0")
        
        # Load model
        try:
            self._session = load_vad_model(onnx_file_path, force_cpu)
            self._model = SileroVADModel(self._session, sample_rate)
        except AudioProcessingError:
            raise
        except Exception as e:
            raise AudioProcessingError(
                f"Failed to initialize VAD: {str(e)}",
                retriable=False
            ) from e
        
        self._sample_rate = sample_rate
        self._activation_threshold = activation_threshold
        self._is_speaking = False
        self._last_event: Optional[Literal["START_OF_SPEECH", "END_OF_SPEECH", "CONTINUING"]] = None
    
    @property
    def sample_rate(self) -> int:
        """Audio sample rate"""
        return self._sample_rate
    
    @property
    def window_size_samples(self) -> int:
        """Number of audio samples per inference window"""
        return self._model.window_size_samples
    
    def process_audio_frame(self, audio_frame: np.ndarray) -> Dict[str, Any]:
        """Process a single audio frame.
        
        Args:
            audio_frame: Audio samples as int16 array
                        Should be exactly window_size_samples long
                        (256 for 8kHz, 512 for 16kHz)
        
        Returns:
            dict with:
                - is_speech: bool - Whether frame contains speech
                - probability: float - Speech probability (0.0 to 1.0)
                - is_speaking: bool - Current speaking state
                - event: str - Event type: "START_OF_SPEECH", "END_OF_SPEECH", or "CONTINUING"
        """
        if len(audio_frame) != self._model.window_size_samples:
            raise ValueError(
                f"Audio frame must be exactly {self._model.window_size_samples} samples "
                f"({self._model.window_size_samples / self._sample_rate * 1000:.0f}ms at {self._sample_rate}Hz)"
            )
        
        # Convert int16 to float32 and normalize to [-1.0, 1.0]
        audio_f32 = audio_frame.astype(np.float32) / np.iinfo(np.int16).max
        
        # Run inference
        probability = self._model(audio_f32)
        
        # Determine if this frame is speech
        is_speech = probability >= self._activation_threshold
        
        # Update speaking state and detect events
        if is_speech and not self._is_speaking:
            self._is_speaking = True
            event = "START_OF_SPEECH"
        elif not is_speech and self._is_speaking:
            self._is_speaking = False
            event = "END_OF_SPEECH"
        else:
            event = "CONTINUING"
        
        self._last_event = event
        
        return {
            "is_speech": is_speech,
            "probability": probability,
            "is_speaking": self._is_speaking,
            "event": event
        }
    
    def process_audio_chunk(self, audio_chunk: bytes) -> Dict[str, Any]:
        """Process an audio chunk (PCM16 bytes).
        
        Args:
            audio_chunk: Audio chunk as PCM16 bytes
        
        Returns:
            dict with processing results (same format as process_audio_frame)
        """
        if len(audio_chunk) < 2:
            return {
                "is_speech": False,
                "probability": 0.0,
                "is_speaking": self._is_speaking,
                "event": "CONTINUING"
            }
        
        # Convert bytes to numpy array
        audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
        
        # Process frame-by-frame if chunk is larger than window size
        if len(audio_array) >= self._model.window_size_samples:
            # Process the last complete frame
            frame = audio_array[-self._model.window_size_samples:]
            return self.process_audio_frame(frame)
        else:
            # Chunk is smaller than window size, pad with zeros
            frame = np.zeros(self._model.window_size_samples, dtype=np.int16)
            frame[:len(audio_array)] = audio_array
            return self.process_audio_frame(frame)
    
    def reset(self) -> None:
        """Reset VAD state (speaking state and model buffers)."""
        self._is_speaking = False
        self._last_event = None
        self._model.reset()
    
    def is_speaking(self) -> bool:
        """Get current speaking state."""
        return self._is_speaking

