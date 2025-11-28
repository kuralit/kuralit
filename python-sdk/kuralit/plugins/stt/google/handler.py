"""Speech-to-Text (STT) integration using Google Cloud Speech-to-Text API."""

import asyncio
import io
from typing import AsyncIterator, Optional

from kuralit.config.schema import STTConfig
from kuralit.server.exceptions import STTError

try:
    from google.cloud import speech_v1
    from google.cloud.speech_v1 import types as speech_types
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False
    speech_v1 = None
    speech_types = None


class GoogleSTTHandler:
    """Handles Speech-to-Text transcription using Google Cloud Speech-to-Text API."""
    
    def __init__(self, config: STTConfig):
        """Initialize STT handler.
        
        Args:
            config: STT configuration
        """
        self.config = config
        self.client: Optional[speech_v1.SpeechClient] = None
        
        if not STT_AVAILABLE:
            raise STTError("google-cloud-speech not installed. Install with: pip install google-cloud-speech")
        
        # Initialize client
        try:
            if config.credentials_path:
                from pathlib import Path
                import os
                
                # Resolve credentials path
                creds_path = Path(config.credentials_path)
                
                # If relative path, try to resolve it
                if not creds_path.is_absolute():
                    # Try relative to project root
                    project_root = Path(__file__).parent.parent.parent.parent
                    resolved_path = project_root / creds_path
                    
                    if not resolved_path.exists():
                        # Try relative to current working directory
                        resolved_path = Path.cwd() / creds_path
                    
                    if resolved_path.exists():
                        creds_path = resolved_path.resolve()
                    else:
                        raise STTError(
                            f"STT credentials file not found: {config.credentials_path}. "
                            f"Tried: {project_root / config.credentials_path}, "
                            f"{Path.cwd() / config.credentials_path}",
                            retriable=False
                        )
                else:
                    # Absolute path - check if exists
                    if not creds_path.exists():
                        raise STTError(
                            f"STT credentials file not found: {creds_path}",
                            retriable=False
                        )
                    creds_path = creds_path.resolve()
                
                # Set environment variable for Google Cloud client
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(creds_path)
            
            self.client = speech_v1.SpeechClient()
        except STTError:
            # Re-raise STT errors as-is
            raise
        except Exception as e:
            raise STTError(f"Failed to initialize STT client: {str(e)}", retriable=False)
    
    def validate_audio_format(
        self,
        audio_bytes: bytes,
        sample_rate: int,
        encoding: str
    ) -> bool:
        """Validate audio format.
        
        Args:
            audio_bytes: Audio data bytes
            sample_rate: Sample rate in Hz
            encoding: Encoding format (PCM16, etc.)
            
        Returns:
            True if format is valid
        """
        if not audio_bytes:
            return False
        
        if sample_rate not in [8000, 16000, 44100, 48000]:
            return False
        
        if encoding not in ["PCM16", "PCM8"]:
            return False
        
        # Check minimum size (at least 1 frame)
        min_size = 2 if encoding == "PCM16" else 1
        if len(audio_bytes) < min_size:
            return False
        
        return True
    
    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        sample_rate: int = 16000,
        encoding: str = "PCM16",
        language_code: Optional[str] = None,
    ) -> tuple[str, Optional[float]]:
        """Transcribe audio bytes to text.
        
        Args:
            audio_bytes: Audio data bytes (PCM16)
            sample_rate: Sample rate in Hz
            encoding: Encoding format
            language_code: Language code (defaults to config)
            
        Returns:
            Tuple of (transcribed_text, confidence_score)
        """
        if not self.client:
            raise STTError("STT client not initialized", retriable=False)
        
        if not self.validate_audio_format(audio_bytes, sample_rate, encoding):
            raise STTError("Invalid audio format", retriable=False)
        
        try:
            # Map encoding to Speech API encoding
            encoding_map = {
                "PCM16": speech_types.RecognitionConfig.AudioEncoding.LINEAR16,
                "PCM8": speech_types.RecognitionConfig.AudioEncoding.LINEAR16,  # Fallback
            }
            speech_encoding = encoding_map.get(encoding, speech_types.RecognitionConfig.AudioEncoding.LINEAR16)
            
            # Configure recognition
            config = speech_types.RecognitionConfig(
                encoding=speech_encoding,
                sample_rate_hertz=sample_rate,
                language_code=language_code or self.config.language_code,
                enable_automatic_punctuation=True,
                model="latest_long",  # Best for longer audio
            )
            
            audio = speech_types.RecognitionAudio(content=audio_bytes)
            
            # Perform recognition
            response = self.client.recognize(config=config, audio=audio)
            
            # Extract results
            if not response.results:
                return "", None
            
            # Get the first result (most confident)
            result = response.results[0]
            if not result.alternatives:
                return "", None
            
            alternative = result.alternatives[0]
            text = alternative.transcript
            confidence = alternative.confidence if hasattr(alternative, "confidence") else None
            
            return text, confidence
            
        except Exception as e:
            raise STTError(f"STT transcription failed: {str(e)}", retriable=True)
    
    async def stream_transcribe(
        self,
        audio_stream: AsyncIterator[bytes],
        sample_rate: int = 16000,
        encoding: str = "PCM16",
        language_code: Optional[str] = None,
    ) -> AsyncIterator[tuple[str, bool, Optional[float]]]:
        """
        Stream audio and yield (transcript, is_final, confidence).
        
        Uses Google Cloud Speech-to-Text streaming_recognize API.
        Yields interim transcripts as they become available, followed by final transcripts.
        
        Args:
            audio_stream: Async iterator of audio chunks
            sample_rate: Sample rate in Hz
            encoding: Encoding format
            language_code: Language code (defaults to config)
            
        Yields:
            Tuples of (transcript, is_final, confidence)
            - transcript: Transcribed text
            - is_final: True if this is a final transcript, False for interim
            - confidence: Confidence score (only available for final transcripts)
        """
        if not self.client:
            raise STTError("STT client not initialized", retriable=False)
        
        try:
            # Map encoding to Speech API encoding
            encoding_map = {
                "PCM16": speech_types.RecognitionConfig.AudioEncoding.LINEAR16,
                "PCM8": speech_types.RecognitionConfig.AudioEncoding.LINEAR16,
            }
            speech_encoding = encoding_map.get(encoding, speech_types.RecognitionConfig.AudioEncoding.LINEAR16)
            
            # Configure streaming recognition
            streaming_config = speech_types.StreamingRecognitionConfig(
                config=speech_types.RecognitionConfig(
                    encoding=speech_encoding,
                    sample_rate_hertz=sample_rate,
                    language_code=language_code or self.config.language_code,
                    enable_automatic_punctuation=True,
                    model="latest_long",
                ),
                interim_results=True,  # Enable interim transcripts
            )
            
            # Since Google's streaming_recognize is synchronous, we need to run it in executor
            # and handle the async audio stream properly
            import queue
            import threading
            
            audio_queue = queue.Queue()
            stop_event = threading.Event()
            
            def complete_request_generator():
                """Generator that yields streaming recognize requests (config + audio)."""
                import logging
                log = logging.getLogger(__name__)
                
                try:
                    # FIRST: Yield the config request (REQUIRED as first request)
                    log.info(f"[STT] Yielding initial config request")
                    yield speech_types.StreamingRecognizeRequest(streaming_config=streaming_config)
                    
                    # THEN: Yield audio requests
                    request_count = 0
                    while not stop_event.is_set():
                        try:
                            chunk = audio_queue.get(timeout=0.1)
                            if chunk is None:  # Sentinel to stop
                                log.info(f"[STT] Received stop sentinel, sent {request_count} audio requests")
                                break
                            request_count += 1
                            if request_count == 1:
                                log.info(f"[STT] Sending first audio request ({len(chunk)} bytes)")
                            if request_count % 50 == 0:  # Log every 50 requests
                                log.info(f"[STT] Sent {request_count} audio requests to Google API")
                            yield speech_types.StreamingRecognizeRequest(audio_content=chunk)
                        except queue.Empty:
                            continue
                except Exception as gen_error:
                    log.error(f"[STT] Error in request generator: {gen_error}", exc_info=True)
                    raise
            
            # Start audio forwarding task
            async def forward_audio():
                """Forward audio from async stream to sync queue."""
                import logging
                log = logging.getLogger(__name__)
                chunk_count = 0
                try:
                    log.info(f"[STT] Starting audio forwarding from async stream to sync queue")
                    async for chunk in audio_stream:
                        chunk_count += 1
                        audio_queue.put(chunk)
                        if chunk_count % 50 == 0:  # Log every 50 chunks
                            log.debug(f"[STT] Forwarded {chunk_count} chunks to Google API, queue_size={audio_queue.qsize()}")
                except Exception as e:
                    # Log error but don't raise - let the streaming continue
                    log.error(f"[STT] Error forwarding audio after {chunk_count} chunks: {e}")
                finally:
                    audio_queue.put(None)  # Signal end of audio
                    log.info(f"[STT] Audio forwarding complete: {chunk_count} chunks forwarded")
            
            forward_task = asyncio.create_task(forward_audio())
            
            try:
                # Run streaming recognition in executor (it's synchronous)
                loop = asyncio.get_event_loop()
                
                import logging
                log = logging.getLogger(__name__)
                log.info(f"[STT] Calling Google streaming_recognize API (will run in thread)")
                
                # Since Google's API is synchronous and returns a generator that must be
                # consumed in the same thread, we run everything in a thread and collect results
                def run_streaming_recognition():
                    """Run streaming recognition entirely in thread pool."""
                    import logging
                    thread_log = logging.getLogger(__name__)
                    results = []
                    
                    try:
                        thread_log.info(f"[STT-Thread] Starting streaming_recognize...")
                        # streaming_recognize takes ONE generator that yields:
                        # 1. First request with streaming_config
                        # 2. Subsequent requests with audio_content
                        thread_log.info(f"[STT-Thread] Calling streaming_recognize with request generator...")
                        responses = self.client.streaming_recognize(complete_request_generator())
                        thread_log.info(f"[STT-Thread] Got response stream, iterating...")
                        
                        response_count = 0
                        for response in responses:
                            response_count += 1
                            if response_count == 1:
                                thread_log.info(f"[STT-Thread] Received first response!")
                            if response_count % 5 == 0:
                                thread_log.info(f"[STT-Thread] Processed {response_count} responses so far...")
                            
                            if not response.results:
                                continue
                            
                            result = response.results[0]
                            if not result.alternatives:
                                continue
                            
                            alternative = result.alternatives[0]
                            transcript = alternative.transcript
                            is_final = result.is_final
                            confidence = alternative.confidence if hasattr(alternative, 'confidence') else None
                            
                            if transcript:
                                thread_log.info(f"[STT-Thread] Got transcript: '{transcript[:30]}...' (final={is_final})")
                                results.append((transcript, is_final, confidence))
                        
                        thread_log.info(f"[STT-Thread] Stream ended: {response_count} responses, {len(results)} transcripts")
                        return results
                    
                    except Exception as e:
                        thread_log.error(f"[STT-Thread] Error: {e}", exc_info=True)
                        raise
                
                # Run in executor and get all results
                try:
                    all_results = await loop.run_in_executor(None, run_streaming_recognition)
                    log.info(f"[STT] Got {len(all_results)} transcripts from Google, yielding them...")
                    
                    # Yield all collected results
                    for transcript, is_final, confidence in all_results:
                        yield (transcript, is_final, confidence)
                
                except Exception as api_error:
                    log.error(f"[STT] Streaming recognition failed: {api_error}", exc_info=True)
                    raise STTError(f"Google STT failed: {str(api_error)}", retriable=True)
            
            finally:
                # Cleanup
                stop_event.set()
                audio_queue.put(None)
                await forward_task
                    
        except Exception as e:
            raise STTError(f"STT streaming transcription failed: {str(e)}", retriable=True)

