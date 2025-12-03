# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-XX

### Added

#### Python SDK
- Initial release of Kuralit Python SDK
- World's 1<sup>st</sup> AI agent for mobile apps with no external dependencies
- Agent system with customizable instructions and tool support
- Tool system with Functions and Toolkits
- Plugin architecture for LLM, STT, VAD, and turn detection
- WebSocket server with FastAPI integration
- REST API toolkit generation from Postman collections
- Speech-to-Text support for multiple providers:
  - Deepgram STT integration
  - Google Cloud Speech-to-Text integration
- Voice Activity Detection (VAD) with Silero
- Multilingual turn detection
- Real-time audio streaming and processing
- Type-safe implementation with full type hints and Pydantic validation
- Comprehensive examples:
  - Minimal server example
  - Simple tools demo
  - WebSocket demo
  - Voice assistant demo
  - Postman API demo
  - Customer support agent example
  - Audio client example

#### Flutter SDK
- Initial release of Kuralit SDK for Flutter
- WebSocket-based real-time communication
- Text messaging with streaming support
- Audio streaming with multiple sample rate and encoding support
- Automatic reconnection with configurable retry logic
- Event-driven architecture with comprehensive event types
- Pre-built UI templates:
  - `KuralitPopupChat` - Popup chat dialog component
  - `KuralitAgentOverlay` - Agent overlay interface
- Audio recording service (`AudioRecorderService`)
- Audio streaming helper (`AudioStreamer`)
- Tool/function call support
- Metadata support for messages
- Debug logging mode
- Session management
- Heartbeat mechanism for connection health
- Comprehensive error handling with error codes
- Support for partial/streaming text responses
- Speech-to-text (STT) event support
- Multiple configuration presets (production, development, defaults)
- Example applications:
  - Basic chat example
  - Popup chat example
  - Agent overlay example
  - Protocol-level example

#### Documentation
- Comprehensive documentation site built with Mintlify
- Getting started guides for both Python and Flutter SDKs
- API reference documentation
- Integration guides for LLM, STT, VAD, and turn detection providers
- Example code and tutorials
- Architecture documentation
- Configuration guides
- Troubleshooting guides

### Features

#### Core Framework
- **Standalone**: No dependencies on other agent frameworks
- **Simple**: Easy to understand and extend
- **Flexible**: Works with any model that supports function calling
- **Extensible**: Easy to add new tool types and plugins
- **Type-Safe**: Full type hints and Pydantic validation
- **Production-Ready**: WebSocket server with real-time audio support
- **Multi-Platform**: Python server and Flutter client support

#### Python SDK Features
- Core dependencies: `pydantic`, `docstring-parser`
- Optional feature groups: `gemini`, `websocket`, `stt`, `vad`, `rest`
- Plugin system for easy integration of new providers
- REST API tools from Postman collections
- Real-time audio processing pipeline

#### Flutter SDK Features
- Minimum Dart SDK: 2.17.0
- Minimum Flutter: 3.0.0
- WebSocket protocol implementation
- Support for PCM16 and PCM8 audio encoding
- Sample rates: 8000, 16000, 44100, 48000 Hz
- Maximum text message size: 4KB
- UUID-based session ID generation

### Technical Details

- **Python Requirements**: Python 3.10+
- **Flutter Requirements**: Dart SDK >=2.17.0 <4.0.0, Flutter >=3.0.0
- **License**: Non-Commercial License
- **Repository**: https://github.com/kuralit/kuralit

---

## [Unreleased]

### Planned
- Additional UI templates for Flutter SDK
- Enhanced error recovery mechanisms
- Performance optimizations
- Additional audio format support
- Offline message queuing
- Message history persistence
- Additional LLM provider integrations
- Enhanced documentation and examples
- Testing framework and test coverage improvements

---

[0.1.0]: https://github.com/kuralit/kuralit/releases/tag/v0.1.0

