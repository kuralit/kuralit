# Kuralit SDK for Flutter

A Flutter SDK for Kuralit realtime communication with WebSocket support for text and audio streaming.

## Features

- 🔌 **WebSocket Communication** - Real-time bidirectional communication
- 💬 **Text Messaging** - Send and receive text messages with streaming support
- 🎤 **Audio Streaming** - Stream audio data with support for multiple sample rates and encodings
- 🔄 **Automatic Reconnection** - Built-in reconnection logic with configurable retry attempts
- 📡 **Event-Driven Architecture** - Reactive event stream for handling all SDK events
- 🎨 **Ready-to-Use Templates** - Pre-built UI components for quick integration
  - Popup Chat Dialog
  - Agent Overlay Interface
- 🛠️ **Tool Call Support** - Handle function/tool calls from the server
- 📊 **Metadata Support** - Attach custom metadata to messages
- 🔍 **Debug Mode** - Comprehensive logging for development

## Installation

Add this to your package's `pubspec.yaml` file:

```yaml
dependencies:
  kuralit_sdk: ^1.0.0
```

Then run:

```bash
flutter pub get
```

## Quick Start

### 1. Initialize the SDK

```dart
import 'package:kuralit_sdk/kuralit.dart';

// Initialize with your configuration
await Kuralit.init(KuralitConfig(
  serverUrl: 'wss://api.kuralit.com/ws',
  apiKey: 'your-api-key',
  appId: 'your-app-id',
  debug: true, // Enable debug logging
));
```

### 2. Connect to Server

```dart
await Kuralit.connect();
```

### 3. Listen to Events

```dart
Kuralit.events.listen((event) {
  if (event is KuralitConnectedEvent) {
    print('Connected to server!');
  } else if (event is KuralitServerTextEvent) {
    print('Server response: ${event.text}');
  } else if (event is KuralitErrorEvent) {
    print('Error: ${event.message}');
  }
});
```

### 4. Send Messages

```dart
// Generate a session ID for conversation continuity
final sessionId = Kuralit.generateSessionId();

// Send text message
await Kuralit.sendText(sessionId, 'Hello, Kuralit!');
```

## Usage Examples

### Basic Text Chat

```dart
import 'package:kuralit_sdk/kuralit.dart';

class ChatService {
  String? _sessionId;
  StreamSubscription<KuralitEvent>? _subscription;

  Future<void> initialize() async {
    // Initialize SDK
    await Kuralit.init(KuralitConfig(
      serverUrl: 'wss://api.kuralit.com/ws',
      apiKey: 'your-api-key',
      appId: 'your-app-id',
    ));

    // Connect
    await Kuralit.connect();

    // Generate session ID
    _sessionId = Kuralit.generateSessionId();

    // Listen to events
    _subscription = Kuralit.events.listen(_handleEvent);
  }

  void _handleEvent(KuralitEvent event) {
    if (event is KuralitServerTextEvent) {
      print('Received: ${event.text}');
    } else if (event is KuralitServerPartialEvent) {
      print('Partial: ${event.text}');
    }
  }

  void sendMessage(String text) {
    if (_sessionId != null) {
      Kuralit.sendText(_sessionId!, text);
    }
  }

  void dispose() {
    _subscription?.cancel();
    Kuralit.disconnect();
    Kuralit.dispose();
  }
}
```

### Audio Streaming

```dart
import 'package:kuralit_sdk/kuralit.dart';
import 'dart:typed_data';

// Start audio stream
final sessionId = Kuralit.generateSessionId();
Kuralit.startAudioStream(
  sessionId,
  sampleRate: 16000,
  encoding: 'PCM16',
);

// Send audio chunks
final audioChunk = Uint8List.fromList([/* your audio data */]);
Kuralit.sendAudioChunk(sessionId, audioChunk);

// End audio stream
Kuralit.endAudioStream(sessionId);
```

### Using Pre-built Templates

#### Popup Chat Dialog

```dart
import 'package:kuralit_sdk/kuralit.dart';

// Show popup chat dialog
KuralitPopupChat.show(
  context,
  sessionId: Kuralit.generateSessionId(),
  config: KuralitPopupChatConfig(
    title: 'Chat Assistant',
    // Customize appearance and behavior
  ),
);
```

#### Agent Overlay

```dart
import 'package:kuralit_sdk/kuralit.dart';

// Add agent overlay to your app
KuralitAgentOverlay(
  sessionId: Kuralit.generateSessionId(),
  // Customize as needed
)
```

## Configuration

### KuralitConfig Options

```dart
KuralitConfig(
  serverUrl: 'wss://api.kuralit.com/ws',  // Required: WebSocket server URL
  apiKey: 'your-api-key',                  // Required: API key
  appId: 'your-app-id',                    // Required: Application ID
  debug: false,                            // Enable debug logging
  reconnectEnabled: true,                   // Enable automatic reconnection
  maxReconnectAttempts: 10,                // Maximum reconnection attempts
  reconnectDelayMs: 1000,                   // Delay between reconnection attempts
  heartbeatIntervalMs: 30000,              // Heartbeat interval (0 to disable)
)
```

### Factory Constructors

```dart
// Production configuration
KuralitConfig.production(
  serverUrl: 'wss://api.kuralit.com/ws',
  apiKey: 'your-api-key',
  appId: 'your-app-id',
);

// Development configuration
KuralitConfig.development(
  serverUrl: 'wss://api.kuralit.com/ws',
  apiKey: 'your-api-key',
  appId: 'your-app-id',
);
```

## Events

The SDK provides a stream of events that you can listen to:

- `KuralitConnectedEvent` - WebSocket connected
- `KuralitDisconnectedEvent` - WebSocket disconnected
- `KuralitServerConnectedEvent` - Server confirmed connection
- `KuralitServerTextEvent` - Complete text response from server
- `KuralitServerPartialEvent` - Partial/streaming text response
- `KuralitServerSttEvent` - Speech-to-text transcription
- `KuralitServerToolCallEvent` - Tool/function call from server
- `KuralitServerToolResultEvent` - Tool execution result
- `KuralitErrorEvent` - Error occurred

## API Reference

### Core Methods

- `Kuralit.init(KuralitConfig)` - Initialize the SDK
- `Kuralit.connect()` - Connect to WebSocket server
- `Kuralit.disconnect()` - Disconnect from server
- `Kuralit.dispose()` - Clean up resources
- `Kuralit.generateSessionId()` - Generate a unique session ID

### Text Messaging

- `Kuralit.sendText(sessionId, text, {metadata})` - Send text message

### Audio Streaming

- `Kuralit.startAudioStream(sessionId, {sampleRate, encoding, metadata})` - Start audio stream
- `Kuralit.sendAudioChunk(sessionId, chunk, {timestamp})` - Send audio chunk
- `Kuralit.endAudioStream(sessionId, {finalChunk})` - End audio stream

### Audio Recording (Helper Classes)

- `AudioRecorderService` - Record audio from device microphone
- `AudioStreamer` - Stream audio data to server

## Requirements

- Dart SDK: `>=2.17.0 <4.0.0`
- Flutter: `>=3.0.0`

## Dependencies

- `web_socket_channel` - WebSocket communication
- `uuid` - Unique identifier generation
- `record` - Audio recording capabilities
- `permission_handler` - Handle device permissions

## Examples

Check out the `example/` directory for complete working examples:

- **basic** - Basic text chat implementation
- **popup_chat** - Popup chat dialog example
- **agent_overlay** - Agent overlay interface example
- **protocol** - Low-level protocol usage example

## License

This package is licensed under the Personal Use License. See [LICENSE](LICENSE) for details.

**Important**: This SDK is free for personal and non-commercial use. Commercial use requires a separate license. Please contact us at [https://kuralit.com](https://kuralit.com) for commercial licensing.

## Contributing

Contributions are welcome! However, please note that this package is subject to the Personal Use License for non-commercial contributions.

## Support

For issues, questions, or commercial licensing inquiries:

- Website: [https://kuralit.com](https://kuralit.com)
- GitHub: [https://github.com/kuralit/kuralit_sdk](https://github.com/kuralit/kuralit_sdk)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.

