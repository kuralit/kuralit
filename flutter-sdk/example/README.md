# Kuralit Flutter SDK Examples

Quick start examples for the Kuralit Flutter SDK. Each example is minimal, easy to understand, and ready to run.

## 📋 Examples Overview

### 1. **Basic Text Chat** (`basic/`)
- **What it does**: Simple text messaging - send and receive messages
- **Best for**: Understanding the core SDK functionality
- **Features**: Connection, text sending, event handling
- **Lines of code**: ~150

### 2. **Popup Chat Template** (`popup_chat/`)
- **What it does**: Uses the ready-made `KuralitPopupChat` widget
- **Best for**: Quick integration - just one button to open chat
- **Features**: Full chat UI with text + audio, no custom UI needed
- **Lines of code**: ~100

### 3. **Agent Overlay** (`agent_overlay/`)
- **What it does**: Uses the full-screen `KuralitAgentOverlay` widget
- **Best for**: Voice-first interactions with beautiful animations
- **Features**: Full-screen overlay, voice input, animated UI
- **Lines of code**: ~100

### 4. **WebSocket Protocol** (`protocol/`)
- **What it does**: Shows actual WebSocket message formats
- **Best for**: Understanding the protocol and debugging
- **Features**: Message format display, event logging, audio streaming format
- **Lines of code**: ~300

## 🚀 Quick Start

### Prerequisites
- Flutter SDK installed (>=3.0.0)
- Android Studio / VS Code with Flutter extensions
- Your Kuralit API credentials:
  - Server URL (e.g., `wss://api.kuralit.com/ws`)
  - API Key
  - App ID

### Running an Example

1. **Choose an example**:
   ```bash
   cd example/basic        # or popup_chat, agent_overlay, protocol
   ```

2. **Update API credentials**:
   - Open `main.dart`
   - Find these lines (around line 15-17):
     ```dart
     const serverUrl = 'wss://api.kuralit.com/ws';
     const apiKey = 'your-api-key-here';
     const appId = 'your-app-id-here';
     ```
   - Replace with your actual values

3. **Install dependencies**:
   ```bash
   flutter pub get
   ```

4. **Run the example**:
   ```bash
   flutter run
   ```

## 📱 Platform Requirements

### Android
- Minimum SDK: 21 (Android 5.0)
- Permissions: Microphone (for audio examples)
- Add to `android/app/src/main/AndroidManifest.xml`:
  ```xml
  <uses-permission android:name="android.permission.RECORD_AUDIO" />
  ```

### iOS
- Minimum version: iOS 12.0
- Permissions: Microphone (for audio examples)
- Add to `ios/Runner/Info.plist`:
  ```xml
  <key>NSMicrophoneUsageDescription</key>
  <string>This app needs microphone access for voice chat</string>
  ```

## 📖 Example Details

### Basic Text Chat
**File**: `example/basic/main.dart`

Shows:
- ✅ SDK initialization
- ✅ WebSocket connection
- ✅ Sending text messages
- ✅ Receiving responses
- ✅ Event handling
- ✅ Connection status

**Use this when**: You want to build your own custom UI.

### Popup Chat Template
**File**: `example/popup_chat/main.dart`

Shows:
- ✅ Using `KuralitPopupChat.show()`
- ✅ One-line integration
- ✅ Ready-made chat UI
- ✅ Text + audio modes
- ✅ Tool calls display

**Use this when**: You want a quick chat dialog without building UI.

### Agent Overlay
**File**: `example/agent_overlay/main.dart`

Shows:
- ✅ Using `KuralitAgentOverlay.show()`
- ✅ Full-screen animated overlay
- ✅ Voice-first interaction
- ✅ Beautiful animations

**Use this when**: You want a premium voice-first experience.

### WebSocket Protocol
**File**: `example/protocol/main.dart`

Shows:
- ✅ Text message format: `{"type": "client_text", ...}`
- ✅ Audio start format: `{"type": "client_audio_start", ...}`
- ✅ Audio chunk format: `{"type": "client_audio_chunk", ...}`
- ✅ Audio end format: `{"type": "client_audio_end", ...}`
- ✅ All response event types
- ✅ Real-time message logging

**Use this when**: You need to understand the protocol or debug messages.

## 🔧 Troubleshooting

### Connection Issues
- Check your server URL is correct
- Verify API key and App ID
- Check network connectivity
- Enable debug mode: `debug: true` in `KuralitConfig`

### Audio Not Working
- Check microphone permissions are granted
- Verify platform-specific permissions are set (see above)
- Test on a physical device (emulators may not support audio)

### Build Errors
- Run `flutter clean` then `flutter pub get`
- Ensure Flutter SDK version is >=3.0.0
- Check that all dependencies are installed

## 📚 Next Steps

1. **Start with Basic**: Understand the core concepts
2. **Try Templates**: See how easy it is to use ready-made widgets
3. **Explore Protocol**: Understand the WebSocket messages
4. **Build Your App**: Use these examples as a starting point

## 💡 Tips

- **Enable debug mode**: Set `debug: true` in `KuralitConfig` to see detailed logs
- **Session IDs**: Each conversation needs a unique session ID - use `Kuralit.generateSessionId()`
- **Event handling**: Listen to `Kuralit.events` stream to handle all responses
- **Connection status**: Check `Kuralit.isConnected()` before sending messages

## 📝 Code Structure

Each example follows this pattern:

```dart
// 1. Import SDK
import 'package:kuralit_sdk/kuralit.dart';

// 2. Initialize (in main or initState)
Kuralit.init(KuralitConfig(...));

// 3. Connect
await Kuralit.connect();

// 4. Listen to events
Kuralit.events.listen((event) {
  // Handle events
});

// 5. Send messages
Kuralit.sendText(sessionId, "Hello");
```

## 🤝 Need Help?

- Check the main SDK README: `../README.md`
- Review the example code comments
- Enable debug logging to see what's happening

---

**Happy coding! 🚀**

