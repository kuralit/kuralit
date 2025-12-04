# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2025-12-04

### Changed
- Updated dependency sorting in pubspec.yaml
- Minor code improvements and cleanup

## [0.1.0] - 2025-11-28

### Added
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

### Features
- **Core SDK**: Main `Kuralit` class with initialization, connection, and messaging
- **Configuration**: Flexible `KuralitConfig` with factory constructors
- **Events**: Complete event system for all SDK operations
- **Templates**: Ready-to-use UI components for quick integration
- **Audio**: Full audio recording and streaming capabilities
- **Reconnection**: Automatic reconnection with exponential backoff
- **Documentation**: Comprehensive API documentation and examples

### Technical Details
- Minimum Dart SDK: 2.17.0
- Minimum Flutter: 3.0.0
- WebSocket protocol implementation
- Support for PCM16 and PCM8 audio encoding
- Sample rates: 8000, 16000, 44100, 48000 Hz
- Maximum text message size: 4KB
- UUID-based session ID generation

---

## [Unreleased]

### Planned
- Additional UI templates
- Enhanced error recovery
- Performance optimizations
- Additional audio format support
- Offline message queuing
- Message history persistence

---

[0.1.0]: https://github.com/kuralit/kuralit_sdk/releases/tag/v0.1.0

