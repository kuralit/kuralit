# KuralIt Server Architecture

## Overview

The KuralIt server provides a WebSocket-based interface for real-time voice agent interactions. It implements a continuous streaming audio pipeline inspired by LiveKit's proven architecture, coordinating Voice Activity Detection (VAD), Speech-to-Text (STT), Turn Detection, and Large Language Model (LLM) processing.

## Architecture Components

### 1. AudioRecognitionHandler (`audio_recognition.py`)

The core orchestrator that coordinates the entire audio pipeline:

- **Continuous STT Streaming**: Audio frames are streamed immediately to STT (no buffering)
- **Parallel VAD Processing**: VAD runs in parallel to detect START_OF_SPEECH and END_OF_SPEECH events
- **Transcript Accumulation**: Final transcripts are accumulated during a user's turn
- **Turn Detection**: When VAD signals END_OF_SPEECH or STT provides final transcripts while not speaking, turn detection is triggered
- **Dynamic Endpointing**: Adjusts delay based on end-of-turn probability:
  - High probability (>= threshold) → min_delay (0.5s) - proceed faster
  - Low probability (< threshold) → max_delay (3.0s) - wait longer for more speech

**Key Methods**:
- `start()`: Initializes STT streaming task
- `push_audio_frame()`: Queues audio for STT processing
- `handle_vad_event()`: Processes VAD events (START/END_OF_SPEECH)
- `_run_eou_detection()`: Triggers turn detector with dynamic endpointing

### 2. STTHandler (`stt_handler.py`)

Provides Speech-to-Text transcription using Google Cloud Speech-to-Text API:

- **Streaming API**: `stream_transcribe()` uses Google's streaming_recognize with interim results
- **Interim Transcripts**: Provides partial results as the user speaks
- **Final Transcripts**: Delivers complete utterance transcriptions
- **Async Processing**: Handles audio stream asynchronously with proper threading for Google's sync API

### 3. VADHandler (`vad_handler.py`)

Silero VAD implementation for voice activity detection:

- **Frame-by-frame Processing**: Analyzes audio frames to detect speech
- **Event Generation**: Produces START_OF_SPEECH, END_OF_SPEECH, and CONTINUING events
- **Probability Scores**: Provides confidence scores for speech detection
- **State Tracking**: Maintains speaking state across frames

### 4. TurnDetectorHandler (`turn_detector_handler.py`)

Language-aware turn detection using Hugging Face ONNX model:

- **Contextual Analysis**: Analyzes conversation history + current transcript
- **EOU Probability**: Predicts end-of-turn probability (0.0-1.0)
- **Threshold-based Decision**: Configurable threshold for turn completion
- **Message Formatting**: Converts conversation history to model input format

### 5. Session (`session.py`)

Manages per-connection state:

- **Conversation History**: Stores user and assistant messages
- **Handler References**: Maintains references to VAD, STT, Turn Detector, and AudioRecognitionHandler
- **Audio Configuration**: Tracks sample rate and encoding
- **Lifecycle Management**: Handles initialization, reset, and cleanup

### 6. AudioBuffer (`audio_buffer.py`)

Simplified to frame pass-through in new architecture:

- **No Buffering**: Audio is streamed continuously, not buffered
- **Legacy Compatibility**: Maintains interface for backward compatibility
- **Config Storage**: Stores audio configuration (sample rate, encoding)

### 7. WebSocket Server (`websocket_server.py`)

FastAPI-based WebSocket server:

- **Protocol Handling**: Parses and validates client messages
- **Audio Stream Management**: Coordinates audio start/chunk/end flow
- **Error Handling**: Graceful error recovery with client notifications
- **Keepalive**: Maintains connection during long LLM operations

## Audio Processing Flow

```
┌─────────────────┐
│ Audio Chunk     │
│ (from client)   │
└────────┬────────┘
         │
         ├──────────────────────────────────┐
         │                                  │
         v                                  v
┌────────────────────┐           ┌──────────────────┐
│ AudioRecognition   │           │ VAD Handler      │
│ Handler            │           │ (parallel)       │
│ - push_audio_frame()│           │ - process_frame()│
└────────┬───────────┘           └────────┬─────────┘
         │                                 │
         v                                 │
┌────────────────────┐                    │
│ STT Streaming      │                    │
│ - stream_transcribe│                    │
│   • interim results│                    │
│   • final results  │                    │
└────────┬───────────┘                    │
         │                                 │
         ├─────────────────────────────────┘
         │
         v
┌────────────────────────────────────────────────┐
│ AudioRecognitionHandler State Management       │
│ - Accumulate final transcripts                │
│ - Track user speaking state (from VAD)        │
│ - Trigger EOU detection when:                 │
│   • VAD END_OF_SPEECH + transcript exists     │
│   • STT final transcript + not speaking       │
└────────┬───────────────────────────────────────┘
         │
         v
┌────────────────────────────────────────────────┐
│ Turn Detector                                  │
│ - Analyze conversation + current transcript    │
│ - Predict EOU probability                      │
│ - Apply dynamic endpointing delay:             │
│   • Low prob → max_delay (3.0s)               │
│   • High prob → min_delay (0.5s)              │
└────────┬───────────────────────────────────────┘
         │
         v
┌────────────────────────────────────────────────┐
│ User Turn Committed                            │
│ - Callback to websocket handler                │
│ - Process with LLM Agent                       │
│ - Stream responses to client                   │
└────────────────────────────────────────────────┘
```

## Key Differences from Previous Architecture

| Aspect | Old (Buffered) | New (Streaming) |
|--------|---------------|-----------------|
| **Audio Flow** | Buffered until silence/threshold | Continuous streaming |
| **STT** | Batch processing on chunks | Continuous streaming with interim results |
| **VAD Role** | Triggers STT processing, overrides turn detector | Parallel events only, informs turn detector |
| **Turn Detection** | Once per buffer, can be overridden by VAD | Primary decision maker with dynamic endpointing |
| **Coordination** | Mixed in websocket_server | Encapsulated in AudioRecognitionHandler |
| **Latency** | High (buffering delays) | Low (immediate streaming) |

## Configuration

### Environment Variables

```bash
# Endpointing delays (LiveKit defaults)
KURALIT_MIN_ENDPOINTING_DELAY=0.5  # seconds
KURALIT_MAX_ENDPOINTING_DELAY=3.0  # seconds

# Turn Detector
KURALIT_TURN_DETECTOR_ENABLED=true
KURALIT_TURN_DETECTOR_THRESHOLD=0.5
KURALIT_TURN_DETECTOR_MODEL_PATH=  # Optional, downloads from HuggingFace if not set

# VAD
KURALIT_VAD_ENABLED=true
KURALIT_VAD_ACTIVATION_THRESHOLD=0.5
KURALIT_VAD_MODEL_PATH=  # Optional, downloads from HuggingFace if not set

# STT
KURALIT_STT_ENABLED=true
GOOGLE_STT_CREDENTIALS=/path/to/credentials.json
KURALIT_STT_LANGUAGE=en-US
```

## Usage Example

```python
from kuralit.server import WebSocketServer
from kuralit.server.config import ServerConfig

config = ServerConfig(
    host="0.0.0.0",
    port=8000,
    stt_enabled=True,
    vad_enabled=True,
    turn_detector_enabled=True,
    min_endpointing_delay=0.5,
    max_endpointing_delay=3.0,
    api_key_validator=lambda key: key == "your-api-key"
)

server = WebSocketServer(config)
server.start()
```

## Best Practices

1. **Enable All Components**: For best results, enable STT, VAD, and Turn Detector together
2. **Tune Thresholds**: Adjust VAD and Turn Detector thresholds based on your use case
3. **Monitor Latency**: Use built-in metrics to track STT and agent latency
4. **Handle Errors**: Implement proper error handling for STT/LLM failures
5. **Test Streaming**: Verify interim transcripts are working for real-time feedback

## Troubleshooting

### Issue: Turn detection too aggressive (cuts off user mid-sentence)
- **Solution**: Increase `turn_detector_threshold` (e.g., 0.6 or 0.7)
- **Solution**: Increase `max_endpointing_delay` to wait longer

### Issue: Turn detection too conservative (delays after user finishes)
- **Solution**: Decrease `turn_detector_threshold` (e.g., 0.4 or 0.3)
- **Solution**: Decrease `min_endpointing_delay` for faster response

### Issue: VAD not detecting speech
- **Solution**: Lower `vad_activation_threshold` (e.g., 0.3 or 0.4)
- **Solution**: Check audio format (must be PCM16, 16kHz recommended)

### Issue: STT streaming errors
- **Solution**: Verify Google Cloud credentials are valid
- **Solution**: Check network connectivity to Google API
- **Solution**: Ensure audio format matches STT config

### Issue: High latency
- **Solution**: Check STT API response times
- **Solution**: Reduce `max_endpointing_delay` if appropriate
- **Solution**: Monitor network latency to client

## References

- LiveKit Agents: [https://github.com/livekit/agents](https://github.com/livekit/agents)
- LiveKit Turn Detector Guide: See `TURN_DETECTOR_GUIDE.md` in livekit repo
- Google Cloud Speech-to-Text: [https://cloud.google.com/speech-to-text](https://cloud.google.com/speech-to-text)
- Silero VAD: [https://github.com/snakers4/silero-vad](https://github.com/snakers4/silero-vad)
