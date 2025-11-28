"""Turn Detector handler using English Turn Detector model."""

import logging
import math
import os
from typing import Dict, List, Optional

try:
    import onnxruntime as ort
    from transformers import AutoTokenizer
    TURN_DETECTOR_AVAILABLE = True
except ImportError:
    TURN_DETECTOR_AVAILABLE = False
    ort = None
    AutoTokenizer = None

from kuralit.config.schema import TurnDetectorConfig
from kuralit.server.exceptions import AudioProcessingError

logger = logging.getLogger(__name__)

# Model configuration
HG_MODEL = "livekit/turn-detector"
MODEL_REVISION = "v1.2.2-en"  # English model revision
ONNX_FILENAME = "model_q8.onnx"

# Model limits
MAX_HISTORY_TOKENS = 128
MAX_HISTORY_TURNS = 6


class MultilingualTurnDetectorHandler:
    """Multilingual Turn Detector Model - Standalone Implementation"""
    
    def __init__(
        self,
        config: TurnDetectorConfig,
        force_cpu: bool = True
    ):
        """Initialize the turn detector model.
        
        Args:
            config: Turn Detector configuration object (TurnDetectorConfig)
            force_cpu: Force CPU execution
        
        Raises:
            AudioProcessingError: If model cannot be loaded
        """
        if not TURN_DETECTOR_AVAILABLE:
            raise AudioProcessingError(
                "Turn Detector dependencies not available. Install with: pip install onnxruntime transformers huggingface-hub",
                retriable=False
            )
        
        threshold = config.threshold
        model_path = config.model_path
        tokenizer_path = config.tokenizer_path
        
        if not (0.0 <= threshold <= 1.0):
            raise ValueError("threshold must be between 0.0 and 1.0")
        
        self._threshold = threshold
        
        # Download model if not provided
        # Handle empty string as None (already handled in config loader)
        
        if model_path is None:
            try:
                from huggingface_hub import hf_hub_download
                logger.info(f"Downloading Turn Detector model from Hugging Face: {HG_MODEL} (revision: {MODEL_REVISION})")
                model_path = hf_hub_download(
                    repo_id=HG_MODEL,
                    filename=ONNX_FILENAME,
                    subfolder="onnx",
                    revision=MODEL_REVISION,
                )
                logger.info(f"Downloaded ONNX model to: {model_path}")
            except Exception as e:
                raise AudioProcessingError(
                    f"Failed to download Turn Detector model: {str(e)}",
                    retriable=False
                ) from e
        else:
            if not os.path.exists(model_path):
                raise AudioProcessingError(
                    f"Turn Detector model file not found: {model_path}",
                    retriable=False
                )
        
        # Load ONNX model
        try:
            sess_options = ort.SessionOptions()
            sess_options.intra_op_num_threads = max(1, min(math.ceil((os.cpu_count() or 1) // 2), 4))
            sess_options.inter_op_num_threads = 1
            sess_options.add_session_config_entry("session.dynamic_block_base", "4")
            
            providers = ["CPUExecutionProvider"] if force_cpu else None
            self._session = ort.InferenceSession(
                model_path,
                providers=providers,
                sess_options=sess_options
            )
            logger.info(f"Successfully loaded Turn Detector ONNX model from: {model_path}")
        except Exception as e:
            raise AudioProcessingError(
                f"Failed to load Turn Detector ONNX model: {str(e)}",
                retriable=False
            ) from e
        
        # Load tokenizer
        try:
            if tokenizer_path is None:
                logger.info(f"Loading Turn Detector tokenizer from Hugging Face: {HG_MODEL} (revision: {MODEL_REVISION})")
                self._tokenizer = AutoTokenizer.from_pretrained(
                    HG_MODEL,
                    revision=MODEL_REVISION,
                    local_files_only=False,
                    truncation_side="left",
                )
            else:
                self._tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
            logger.info("Successfully loaded Turn Detector tokenizer")
        except Exception as e:
            raise AudioProcessingError(
                f"Failed to load Turn Detector tokenizer: {str(e)}",
                retriable=False
            ) from e
    
    @property
    def threshold(self) -> float:
        """End-of-turn probability threshold"""
        return self._threshold
    
    @threshold.setter
    def threshold(self, value: float) -> None:
        """Set end-of-turn probability threshold"""
        if not (0.0 <= value <= 1.0):
            raise ValueError("threshold must be between 0.0 and 1.0")
        self._threshold = value
    
    def _format_chat_context(self, chat_ctx: List[Dict[str, str]]) -> str:
        """Format conversation history for the model.
        
        Args:
            chat_ctx: List of messages with "role" and "content" keys
                    Example: [{"role": "user", "content": "Hello"}, ...]
        
        Returns:
            Formatted text string for tokenization
        """
        # Combine adjacent messages with same role
        new_chat_ctx = []
        last_msg = None
        
        for msg in chat_ctx:
            if not msg.get("content"):
                continue
            
            content = msg["content"]
            
            # Combine adjacent turns together to match training data
            if last_msg and last_msg["role"] == msg["role"]:
                last_msg["content"] += f" {content}"
            else:
                new_chat_ctx.append(msg.copy())
                last_msg = new_chat_ctx[-1]
        
        # Apply chat template
        convo_text = self._tokenizer.apply_chat_template(
            new_chat_ctx,
            add_generation_prompt=False,
            add_special_tokens=False,
            tokenize=False
        )
        
        # Remove the EOU token from current utterance
        ix = convo_text.rfind("<|im_end|>")
        text = convo_text[:ix] if ix != -1 else convo_text
        
        return text
    
    def predict_end_of_turn(self, conversation_history: List[Dict[str, str]]) -> float:
        """Predict the probability that the user has finished their turn.
        
        Args:
            conversation_history: List of messages with "role" and "content"
                Example: [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"},
                    {"role": "user", "content": "How are you?"}
                ]
        
        Returns:
            Probability score (0.0 to 1.0) indicating likelihood of end-of-turn
            Higher values = more likely the user has finished speaking
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if not conversation_history:
            logger.warning("[TurnDetector] Empty conversation history, returning 0.0")
            return 0.0
        
        try:
            # Limit to last N turns
            chat_ctx = conversation_history[-MAX_HISTORY_TURNS:]
            
            logger.debug(f"[TurnDetector] Processing {len(chat_ctx)} messages from history (total: {len(conversation_history)})")
            
            # Format the conversation
            text = self._format_chat_context(chat_ctx)
            
            if not text or len(text.strip()) == 0:
                logger.warning("[TurnDetector] Formatted text is empty, returning 0.0")
                return 0.0
            
            logger.debug(f"[TurnDetector] Formatted text length: {len(text)} chars")
            
            # Tokenize
            inputs = self._tokenizer(
                text,
                add_special_tokens=False,
                return_tensors="np",
                max_length=MAX_HISTORY_TOKENS,
                truncation=True,
            )
            
            if inputs["input_ids"].size == 0:
                logger.warning("[TurnDetector] Tokenized input is empty, returning 0.0")
                return 0.0
            
            logger.debug(f"[TurnDetector] Tokenized input shape: {inputs['input_ids'].shape}")
            
            # Run inference
            outputs = self._session.run(
                None,
                {"input_ids": inputs["input_ids"].astype("int64")}
            )
            
            if outputs is None or len(outputs) == 0:
                logger.warning("[TurnDetector] Model output is empty, returning 0.0")
                return 0.0
            
            # Extract probability (last value from output)
            output_flat = outputs[0].flatten()
            if len(output_flat) == 0:
                logger.warning("[TurnDetector] Model output is empty after flattening, returning 0.0")
                return 0.0
            
            eou_probability = float(output_flat[-1])
            
            logger.debug(f"[TurnDetector] EOU probability: {eou_probability:.3f}")
            
            return eou_probability
            
        except Exception as e:
            logger.error(f"[TurnDetector] Error predicting end of turn: {e}", exc_info=True)
            return 0.0
    
    def is_end_of_turn(self, conversation_history: List[Dict[str, str]]) -> bool:
        """Check if the conversation indicates end-of-turn.
        
        Args:
            conversation_history: List of messages with "role" and "content"
        
        Returns:
            True if end-of-turn is detected (probability > threshold)
        """
        probability = self.predict_end_of_turn(conversation_history)
        return probability > self._threshold
    
    def convert_message_history(self, messages: List) -> List[Dict[str, str]]:
        """Convert message objects to Turn Detector format.
        
        Args:
            messages: List of Message objects (from session.conversation_history)
        
        Returns:
            List of dicts with "role" and "content" keys
        """
        result = []
        for msg in messages:
            # Handle Message objects with to_dict() method
            if hasattr(msg, 'to_dict'):
                msg_dict = msg.to_dict()
                role = msg_dict.get("role", "")
                content = msg_dict.get("content", "")
            # Handle dict-like objects
            elif isinstance(msg, dict):
                role = msg.get("role", "")
                content = msg.get("content", "")
            else:
                # Try to access attributes directly
                role = getattr(msg, "role", "")
                content = getattr(msg, "content", "")
            
            # Convert content to string if needed
            if content is not None:
                content = str(content)
            else:
                content = ""
            
            if role and content:
                result.append({
                    "role": role,
                    "content": content
                })
        
        return result

