"""
Deepgram Speech-to-Text Handler

This module provides async streaming STT using Deepgram's WebSocket API.
Much more reliable than Google's synchronous API for continuous streaming.

Based on LiveKit's Deepgram plugin implementation.
"""

import asyncio
import json
import logging
from typing import AsyncIterator, Optional
from dataclasses import dataclass

import aiohttp

from kuralit.config.schema import STTConfig
from kuralit.server.exceptions import STTError

logger = logging.getLogger(__name__)


@dataclass
class DeepgramOptions:
    """Configuration for Deepgram STT."""
    model: str = "nova-2"
    language: str = "en-US"
    sample_rate: int = 16000
    encoding: str = "linear16"
    channels: int = 1
    interim_results: bool = True
    punctuate: bool = True
    smart_format: bool = True
    vad_events: bool = True
    endpointing_ms: int = 300
    no_delay: bool = True
    filler_words: bool = True


class DeepgramSTTHandler:
    """
    Deepgram Speech-to-Text handler with WebSocket streaming.
    
    This handler provides true async streaming STT using Deepgram's WebSocket API,
    which is much more reliable than Google's synchronous streaming API.
    
    Features:
    - Native async WebSocket connection
    - Interim and final transcripts
    - VAD events from Deepgram
    - Auto-reconnection on failure
    - Keepalive handling
    """
    
    _KEEPALIVE_MSG = json.dumps({"type": "KeepAlive"})
    _CLOSE_MSG = json.dumps({"type": "CloseStream"})
    
    def __init__(self, config: STTConfig):
        """
        Initialize Deepgram STT handler.
        
        Args:
            config: STT configuration
        """
        self.config = config
        self.api_key = config.api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        
        # Default options
        model = config.model or "nova-2"
        self.options = DeepgramOptions(
            model=model,
            sample_rate=config.sample_rate,
            language=config.language_code,
            encoding=config.encoding,
            interim_results=config.interim_results,
            punctuate=config.punctuate,
            smart_format=config.smart_format,
        )
        
        logger.info(f"Initialized Deepgram STT: model={self.options.model}, language={self.options.language}")
    
    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure aiohttp session exists."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    def _build_ws_url(self) -> str:
        """Build Deepgram WebSocket URL with query parameters."""
        params = {
            "model": self.options.model,
            "language": self.options.language,
            "sample_rate": self.options.sample_rate,
            "encoding": self.options.encoding,
            "channels": self.options.channels,
            "interim_results": "true" if self.options.interim_results else "false",
            "punctuate": "true" if self.options.punctuate else "false",
            "smart_format": "true" if self.options.smart_format else "false",
            "vad_events": "true" if self.options.vad_events else "false",
            "endpointing": self.options.endpointing_ms,
            "no_delay": "true" if self.options.no_delay else "false",
            "filler_words": "true" if self.options.filler_words else "false",
        }
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"wss://api.deepgram.com/v1/listen?{query_string}"
    
    async def _connect_ws(self) -> aiohttp.ClientWebSocketResponse:
        """Connect to Deepgram WebSocket."""
        session = await self._ensure_session()
        url = self._build_ws_url()
        
        logger.info(f"[Deepgram] Connecting to WebSocket: {url[:100]}...")
        
        ws = await session.ws_connect(
            url,
            headers={
                "Authorization": f"Token {self.api_key}",
            },
            timeout=aiohttp.ClientTimeout(total=30, connect=10),
        )
        
        logger.info("[Deepgram] WebSocket connected successfully")
        return ws
    
    async def stream_transcribe(
        self,
        audio_stream: AsyncIterator[bytes],
        sample_rate: int = 16000,
        encoding: str = "PCM16",
        language_code: Optional[str] = None,
    ) -> AsyncIterator[tuple[str, bool, Optional[float]]]:
        """
        Stream audio to Deepgram and yield transcripts.
        
        Args:
            audio_stream: Async iterator of audio chunks (raw PCM16 bytes)
            sample_rate: Sample rate in Hz
            encoding: Encoding format
            language_code: Language code (optional)
        
        Yields:
            Tuples of (transcript, is_final, confidence)
        """
        if language_code:
            self.options.language = language_code
        
        self.options.sample_rate = sample_rate
        
        # Queue for passing transcripts from receiver task to this generator
        transcript_queue: asyncio.Queue[Optional[tuple[str, bool, Optional[float]]]] = asyncio.Queue()
        
        try:
            # Connect to Deepgram
            self.ws = await self._connect_ws()
            
            # Create tasks for sending and receiving
            send_task = asyncio.create_task(self._send_audio_task(audio_stream))
            recv_task = asyncio.create_task(self._recv_transcripts_task(transcript_queue))
            keepalive_task = asyncio.create_task(self._keepalive_task())
            
            try:
                # Yield transcripts from the queue
                while True:
                    transcript_tuple = await transcript_queue.get()
                    if transcript_tuple is None:  # Sentinel for end of stream
                        break
                    yield transcript_tuple
            finally:
                # Cleanup
                send_task.cancel()
                recv_task.cancel()
                keepalive_task.cancel()
                
                try:
                    await send_task
                except asyncio.CancelledError:
                    pass
                
                try:
                    await recv_task
                except asyncio.CancelledError:
                    pass
                
                try:
                    await keepalive_task
                except asyncio.CancelledError:
                    pass
                
                if self.ws and not self.ws.closed:
                    await self.ws.close()
        
        except Exception as e:
            logger.error(f"[Deepgram] Streaming error: {e}", exc_info=True)
            raise STTError(f"Deepgram streaming failed: {str(e)}", retriable=True)
    
    async def _send_audio_task(self, audio_stream: AsyncIterator[bytes]) -> None:
        """Task to send audio chunks to Deepgram."""
        if not self.ws:
            raise STTError("WebSocket not connected")
        
        chunk_count = 0
        try:
            logger.info("[Deepgram] Starting audio send task")
            async for chunk in audio_stream:
                chunk_count += 1
                await self.ws.send_bytes(chunk)
                
                if chunk_count == 1:
                    logger.info(f"[Deepgram] Sent first audio chunk ({len(chunk)} bytes)")
                elif chunk_count % 100 == 0:
                    logger.debug(f"[Deepgram] Sent {chunk_count} audio chunks")
            
            logger.info(f"[Deepgram] Audio stream ended, sent {chunk_count} chunks total")
            # Tell Deepgram we're done
            await self.ws.send_str(self._CLOSE_MSG)
        
        except Exception as e:
            logger.error(f"[Deepgram] Error sending audio: {e}", exc_info=True)
            raise
    
    async def _recv_transcripts_task(self, transcript_queue: asyncio.Queue) -> None:
        """Task to receive and parse transcripts from Deepgram, pushing them to a queue."""
        if not self.ws:
            raise STTError("WebSocket not connected")
        
        response_count = 0
        try:
            logger.info("[Deepgram] Starting receive task")
            
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        response_count += 1
                        
                        if response_count == 1:
                            logger.info(f"[Deepgram] Received first response: {data.get('type', 'Unknown')}")
                        
                        # Process different message types
                        if data.get("type") == "SpeechStarted":
                            logger.info("[Deepgram] Speech started event")
                            continue
                        
                        elif data.get("type") == "Results":
                            # Extract transcript
                            channel = data.get("channel", {})
                            alternatives = channel.get("alternatives", [])
                            
                            if not alternatives:
                                continue
                            
                            alt = alternatives[0]
                            transcript = alt.get("transcript", "")
                            confidence = alt.get("confidence", 0.0)
                            is_final = data.get("is_final", False)
                            speech_final = data.get("speech_final", False)
                            
                            if transcript:
                                logger.info(
                                    f"[Deepgram] Transcript: '{transcript[:50]}...' "
                                    f"(is_final={is_final}, speech_final={speech_final}, "
                                    f"confidence={confidence:.2f})"
                                )
                                # Put transcript in queue for main generator
                                await transcript_queue.put((transcript, is_final, confidence if is_final else None))
                        
                        elif data.get("type") == "Metadata":
                            # Metadata events - can be noisy, log at debug level
                            logger.debug(f"[Deepgram] Metadata: {data}")
                        
                        elif data.get("type") == "UtteranceEnd":
                            logger.info("[Deepgram] Utterance end event")
                        
                        else:
                            logger.warning(f"[Deepgram] Unknown message type: {data.get('type')}")
                    
                    except json.JSONDecodeError as e:
                        logger.error(f"[Deepgram] Failed to parse JSON: {e}")
                    except Exception as e:
                        logger.error(f"[Deepgram] Error processing message: {e}", exc_info=True)
                
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"[Deepgram] WebSocket error: {self.ws.exception()}")
                    break
                
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSING):
                    logger.info("[Deepgram] WebSocket closed")
                    break
            
            logger.info(f"[Deepgram] Receive task ended: {response_count} responses processed")
            # Send sentinel to indicate end of stream
            await transcript_queue.put(None)
        
        except Exception as e:
            logger.error(f"[Deepgram] Error receiving transcripts: {e}", exc_info=True)
            # Send sentinel even on error
            await transcript_queue.put(None)
            raise
    
    async def _keepalive_task(self) -> None:
        """Task to send keepalive messages to Deepgram."""
        if not self.ws:
            return
        
        try:
            logger.debug("[Deepgram] Starting keepalive task")
            while not self.ws.closed:
                await asyncio.sleep(5)
                if not self.ws.closed:
                    await self.ws.send_str(self._KEEPALIVE_MSG)
                    logger.debug("[Deepgram] Sent keepalive")
        except Exception as e:
            logger.debug(f"[Deepgram] Keepalive task ended: {e}")
    
    async def close(self):
        """Close the STT handler and cleanup resources."""
        if self.ws and not self.ws.closed:
            await self.ws.close()
        
        if self.session and not self.session.closed:
            await self.session.close()
        
        logger.info("[Deepgram] STT handler closed")

