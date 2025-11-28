"""Audio Recognition Handler - Coordinates VAD, STT, and Turn Detector.

Based on LiveKit's AudioRecognition architecture adapted for WebSocket server.
Supports both Google STT and Deepgram STT providers.
"""

import asyncio
import logging
import time
from typing import AsyncIterator, Callable, Optional, Union

logger = logging.getLogger(__name__)


class AudioRecognitionHandler:
    """
    Coordinates VAD, STT, and Turn Detector similar to LiveKit's AudioRecognition.
    
    This handler manages the complete audio processing pipeline:
    1. Streams audio continuously to STT (not buffered chunks)
    2. Receives VAD events in parallel (for user state tracking)
    3. Accumulates STT transcripts during a turn
    4. Runs turn detector to determine end-of-turn
    5. Applies dynamic endpointing delays based on EOU probability
    6. Commits user turn when conditions are met
    """
    
    def __init__(
        self,
        stt_handler,
        vad_handler: Optional[object],
        turn_detector_handler: Optional[object],
        min_endpointing_delay: float,
        max_endpointing_delay: float,
        on_transcript_callback: Callable,
        on_turn_end_callback: Callable,
        conversation_history_callback: Callable,
    ):
        """
        Initialize Audio Recognition Handler.
        
        Args:
            stt_handler: STTHandler instance for streaming transcription
            vad_handler: Optional VADHandler for parallel event detection
            turn_detector_handler: Optional TurnDetectorHandler for EOU detection
            min_endpointing_delay: Minimum delay after EOU before committing turn
            max_endpointing_delay: Maximum delay to wait for more speech
            on_transcript_callback: Called when transcript is received (interim or final)
            on_turn_end_callback: Called when user turn is committed
            conversation_history_callback: Called to get conversation history for turn detector
        """
        self._stt = stt_handler
        self._vad = vad_handler
        self._turn_detector = turn_detector_handler
        self._min_delay = min_endpointing_delay
        self._max_delay = max_endpointing_delay
        
        # Callbacks
        self._on_transcript = on_transcript_callback
        self._on_turn_end = on_turn_end_callback
        self._get_conversation_history = conversation_history_callback
        
        # State tracking (similar to LiveKit's AudioRecognition)
        self._audio_transcript = ""  # Accumulated final transcripts
        self._audio_interim_transcript = ""  # Current interim transcript
        self._speaking = False  # Whether user is currently speaking (from VAD)
        self._last_final_transcript_time: Optional[float] = None
        
        # Async tasks
        self._stt_stream_task: Optional[asyncio.Task] = None
        self._eou_detection_task: Optional[asyncio.Task] = None
        
        # Audio queue for streaming to STT
        self._audio_queue: asyncio.Queue[Optional[bytes]] = asyncio.Queue()
        self._closing = False
    
    async def start(self, sample_rate: int, encoding: str) -> None:
        """
        Start the audio recognition handler.
        
        Spawns the STT streaming task that continuously processes audio.
        
        Args:
            sample_rate: Audio sample rate in Hz
            encoding: Audio encoding format (e.g., "PCM16")
        """
        logger.info(f"Starting AudioRecognitionHandler: sample_rate={sample_rate}, encoding={encoding}")
        self._stt_stream_task = asyncio.create_task(
            self._stt_streaming_task(sample_rate, encoding),
            name="stt_streaming_task"
        )
    
    async def push_audio_frame(self, frame: bytes) -> None:
        """
        Push audio frame to be processed by STT.
        
        Audio is queued and processed continuously by the STT streaming task.
        
        Args:
            frame: Audio frame as bytes (PCM16)
        """
        if not self._closing:
            await self._audio_queue.put(frame)
            logger.debug(f"[AudioRecognition] Pushed audio frame: {len(frame)} bytes, queue_size={self._audio_queue.qsize()}")
    
    async def handle_vad_event(self, event_type: str, probability: float) -> None:
        """
        Handle VAD events (START_OF_SPEECH, END_OF_SPEECH).
        
        VAD runs in parallel and provides signals about user speaking state.
        When END_OF_SPEECH is detected, we trigger turn detection if we have
        accumulated transcripts.
        
        Args:
            event_type: "START_OF_SPEECH", "END_OF_SPEECH", or "CONTINUING"
            probability: VAD probability score
        """
        logger.info(f"[AudioRecognition] VAD event: {event_type}, prob={probability:.3f}, speaking={self._speaking}, transcript_length={len(self._audio_transcript)}")
        
        if event_type == "START_OF_SPEECH":
            self._speaking = True
            logger.info(f"[AudioRecognition] User started speaking (VAD prob={probability:.3f})")
            
            # Cancel any pending EOU detection when user starts speaking again
            if self._eou_detection_task and not self._eou_detection_task.done():
                self._eou_detection_task.cancel()
                logger.info("[AudioRecognition] Cancelled pending EOU detection (user started speaking)")
        
        elif event_type == "END_OF_SPEECH":
            self._speaking = False
            logger.info(f"[AudioRecognition] User stopped speaking (VAD prob={probability:.3f})")
            
            # Trigger EOU detection when user stops speaking (if we have transcript)
            if self._audio_transcript:
                logger.info(f"[AudioRecognition] Triggering EOU detection (transcript accumulated: '{self._audio_transcript[:50]}...')")
                await self._run_eou_detection()
            else:
                logger.info("[AudioRecognition] No transcript accumulated yet, waiting for STT")
    
    async def _stt_streaming_task(self, sample_rate: int, encoding: str) -> None:
        """
        Continuously stream audio to STT and process transcripts.
        
        This task runs for the lifetime of the audio stream, processing:
        - Interim transcripts (partial results as user speaks)
        - Final transcripts (complete utterances from STT)
        
        Args:
            sample_rate: Audio sample rate
            encoding: Audio encoding format
        """
        logger.info("[AudioRecognition] STT streaming task started")
        
        async def audio_generator() -> AsyncIterator[bytes]:
            """Generator that yields audio frames from queue."""
            frame_count = 0
            while True:
                frame = await self._audio_queue.get()
                if frame is None:  # Sentinel to stop
                    logger.debug(f"[AudioRecognition] Audio generator received stop sentinel (processed {frame_count} frames)")
                    break
                frame_count += 1
                if frame_count % 50 == 0:  # Log every 50 frames (~1 second at 20ms frames)
                    logger.debug(f"[AudioRecognition] Audio generator yielding frame #{frame_count} ({len(frame)} bytes)")
                yield frame
        
        try:
            logger.debug(f"[AudioRecognition] Starting STT stream_transcribe loop")
            # Stream audio to STT and process results
            async for transcript, is_final, confidence in \
                    self._stt.stream_transcribe(audio_generator(), sample_rate, encoding):
                
                logger.debug(f"[AudioRecognition] Received from STT: transcript='{transcript[:50]}...', is_final={is_final}")
                
                if is_final:
                    # Final transcript: accumulate and trigger EOU if not speaking
                    confidence_str = f"{confidence:.2f}" if confidence is not None else "N/A"
                    logger.info(f"[AudioRecognition] Final transcript: '{transcript}' (confidence={confidence_str})")
                    
                    # Accumulate the final transcript
                    self._audio_transcript += f" {transcript}"
                    self._audio_transcript = self._audio_transcript.strip()
                    self._audio_interim_transcript = ""
                    self._last_final_transcript_time = time.time()
                    
                    # Send final transcript to client
                    await self._on_transcript(transcript, is_final, confidence)
                    
                    # CRITICAL: Always re-trigger EOU detection when a new final transcript arrives
                    # This ensures we use the latest accumulated transcript, even if user is speaking
                    # If user starts speaking again, the EOU task will be cancelled
                    if self._audio_transcript:
                        logger.debug(f"[AudioRecognition] New final transcript received, re-triggering EOU detection with updated transcript: '{self._audio_transcript[:50]}...'")
                        await self._run_eou_detection()
                else:
                    # Interim transcript: update and send to client
                    logger.debug(f"[AudioRecognition] Interim transcript: '{transcript}'")
                    self._audio_interim_transcript = transcript
                    await self._on_transcript(transcript, is_final, confidence)
        
        except asyncio.CancelledError:
            logger.info("[AudioRecognition] STT streaming task cancelled")
            raise
        except Exception as e:
            logger.error(f"[AudioRecognition] STT streaming task error: {e}", exc_info=True)
            raise
    
    async def _run_eou_detection(self) -> None:
        """
        Run turn detector and apply endpointing delay.
        
        This method is called when:
        1. VAD detects END_OF_SPEECH and we have accumulated transcript
        2. STT provides FINAL_TRANSCRIPT and user is not speaking
        
        It spawns a task that:
        1. Calls turn detector to get EOU probability
        2. Adjusts endpointing delay based on probability
        3. Waits for the delay
        4. Commits the user turn
        """
        # Cancel any existing EOU detection task
        if self._eou_detection_task and not self._eou_detection_task.done():
            self._eou_detection_task.cancel()
            try:
                await self._eou_detection_task
            except asyncio.CancelledError:
                pass
        
        # Spawn new EOU detection task
        self._eou_detection_task = asyncio.create_task(
            self._eou_detection_with_delay(),
            name="eou_detection_task"
        )
    
    async def _eou_detection_with_delay(self) -> None:
        """
        Turn detection with dynamic endpointing delay.
        
        This is the core of LiveKit's turn detection logic:
        1. Get EOU probability from turn detector
        2. If probability < threshold: use max_delay (3.0s) - wait longer
        3. If probability >= threshold: use min_delay (0.5s) - proceed faster
        4. Wait for the calculated delay
        5. Commit user turn
        """
        endpointing_delay = self._min_delay
        eou_probability = 0.0
        
        if self._turn_detector and self._audio_transcript:
            try:
                # Capture transcript at this moment (in case it changes during delay)
                current_transcript = self._audio_transcript
                
                # Get conversation history (callback should return turn detector format)
                conversation_history = self._get_conversation_history()
                
                # Ensure conversation_history is a list of dicts with "role" and "content"
                if conversation_history:
                    # Check if already in correct format (list of dicts)
                    if not (isinstance(conversation_history[0], dict) and "role" in conversation_history[0]):
                        # Convert from Message objects to dict format
                        if hasattr(self._turn_detector, 'convert_message_history'):
                            conversation_history = self._turn_detector.convert_message_history(conversation_history)
                        else:
                            # Fallback: try to convert manually
                            converted = []
                            for msg in conversation_history:
                                if isinstance(msg, dict):
                                    converted.append(msg)
                                elif hasattr(msg, 'role') and hasattr(msg, 'content'):
                                    converted.append({"role": msg.role, "content": str(msg.content)})
                            conversation_history = converted
                
                # Build temporary conversation with current user transcript
                # (similar to LiveKit's chat_ctx.copy() + add_message)
                temp_history = conversation_history + [
                    {"role": "user", "content": current_transcript}
                ]
                
                logger.info(f"[AudioRecognition] Running turn detector with {len(temp_history)} messages (history: {len(conversation_history)}, current: 1), last user message: '{current_transcript[:50]}...'")
                if conversation_history:
                    logger.debug(f"[AudioRecognition] Conversation history sample: {conversation_history[-2:] if len(conversation_history) >= 2 else conversation_history}")
                
                # Get EOU probability from turn detector
                eou_probability = self._turn_detector.predict_end_of_turn(temp_history)
                threshold = self._turn_detector.threshold
                
                logger.info(f"[AudioRecognition] Turn detector returned EOU probability: {eou_probability:.3f}, threshold: {threshold:.3f}")
                
                # Dynamic delay based on probability (LiveKit's approach)
                if eou_probability < threshold:
                    endpointing_delay = self._max_delay
                    logger.info(
                        f"[AudioRecognition] Low EOU probability ({eou_probability:.3f} < {threshold:.3f}), "
                        f"using max delay ({self._max_delay}s)"
                    )
                else:
                    endpointing_delay = self._min_delay
                    logger.info(
                        f"[AudioRecognition] High EOU probability ({eou_probability:.3f} >= {threshold:.3f}), "
                        f"using min delay ({self._min_delay}s)"
                    )
            
            except Exception as e:
                logger.warning(f"[AudioRecognition] Turn detector error: {e}, using min delay", exc_info=True)
                endpointing_delay = self._min_delay
                eou_probability = 0.0  # Set to 0 on error
        else:
            # No turn detector or no transcript yet
            if not self._turn_detector:
                logger.debug("[AudioRecognition] No turn detector configured, using min delay")
            if not self._audio_transcript:
                logger.debug("[AudioRecognition] No transcript accumulated yet")
        
        # Wait for endpointing delay
        # During this delay, new final transcripts may arrive and update self._audio_transcript
        # We'll capture the transcript right before committing to get the latest version
        logger.debug(f"[AudioRecognition] Waiting {endpointing_delay}s before committing turn...")
        try:
            await asyncio.sleep(endpointing_delay)
        except asyncio.CancelledError:
            logger.debug("[AudioRecognition] EOU detection cancelled during delay (likely new transcript arrived)")
            raise
        
        # Commit user turn - capture transcript at commit time to get latest accumulated version
        # This ensures we don't lose transcripts that arrived during the delay
        transcript = self._audio_transcript
        if transcript:
            logger.info(f"[AudioRecognition] Committing user turn: '{transcript}'")
            
            # Clear transcript state BEFORE calling callback (to prevent race conditions)
            self._audio_transcript = ""
            self._audio_interim_transcript = ""
            self._last_final_transcript_time = None
            
            # Call the turn end callback with the complete accumulated transcript
            await self._on_turn_end(transcript)
        else:
            logger.debug("[AudioRecognition] No transcript to commit (may have been cleared)")
    
    def clear_user_turn(self) -> None:
        """Clear accumulated transcript and interim state."""
        logger.debug("[AudioRecognition] Clearing user turn state")
        self._audio_transcript = ""
        self._audio_interim_transcript = ""
        self._last_final_transcript_time = None
    
    async def stop(self) -> None:
        """
        Stop the audio recognition handler.
        
        Stops streaming tasks and cleans up resources.
        """
        logger.info("[AudioRecognition] Stopping audio recognition handler")
        self._closing = True
        
        # Stop STT streaming task
        if self._stt_stream_task:
            await self._audio_queue.put(None)  # Send sentinel
            try:
                await asyncio.wait_for(self._stt_stream_task, timeout=2.0)
            except asyncio.TimeoutError:
                logger.warning("[AudioRecognition] STT streaming task did not stop in time, cancelling")
                self._stt_stream_task.cancel()
                try:
                    await self._stt_stream_task
                except asyncio.CancelledError:
                    pass
        
        # Cancel EOU detection task
        if self._eou_detection_task and not self._eou_detection_task.done():
            self._eou_detection_task.cancel()
            try:
                await self._eou_detection_task
            except asyncio.CancelledError:
                pass
        
        logger.info("[AudioRecognition] Audio recognition handler stopped")
    
    @property
    def current_transcript(self) -> str:
        """
        Get current transcript including interim if available.
        
        Returns:
            Complete transcript (final + interim)
        """
        if self._audio_interim_transcript:
            return f"{self._audio_transcript} {self._audio_interim_transcript}".strip()
        return self._audio_transcript

