/// Kuralit SDK for Flutter
/// 
/// A Flutter SDK for Kuralit realtime communication with WebSocket support
/// for text and audio streaming.
/// 
/// ## Quick Start
/// 
/// ```dart
/// import 'package:kuralit_sdk/kuralit.dart';
/// 
/// // Initialize
/// await Kuralit.init(KuralitConfig(
///   serverUrl: 'wss://api.kuralit.com/ws',
///   apiKey: 'your-api-key',
///   appId: 'your-app-id',
///   debug: true,
/// ));
/// 
/// // Connect
/// await Kuralit.connect();
/// 
/// // Listen to events
/// Kuralit.events.listen((event) {
///   if (event is KuralitConnectedEvent) {
///     print('Connected!');
///   } else if (event is KuralitServerTextEvent) {
///     print('Reply: ${event.text}');
///   }
/// });
/// 
/// // Send text
/// final sessionId = Kuralit.generateSessionId();
/// await Kuralit.sendText(sessionId, 'Hello!');
/// ```
library kuralit_sdk;

// Export public API
export 'src/kuralit.dart' show Kuralit;
export 'src/kuralit_config.dart' show KuralitConfig;
export 'src/kuralit_events.dart'
    show
        KuralitEvent,
        KuralitConnectedEvent,
        KuralitDisconnectedEvent,
        KuralitServerConnectedEvent,
        KuralitServerSttEvent,
        KuralitServerTextEvent,
        KuralitServerPartialEvent,
        KuralitServerToolCallEvent,
        KuralitServerToolResultEvent,
        KuralitErrorEvent,
        KuralitErrorCode;
export 'src/audio/audio_streamer.dart' show AudioStreamer;
export 'src/audio/audio_recorder_service.dart' show AudioRecorderService;

// Export templates
export 'templates/popup_chat/kuralit_popup_chat.dart' show KuralitPopupChat;
export 'templates/popup_chat/kuralit_popup_chat_config.dart' show KuralitPopupChatConfig;
export 'templates/popup_chat/models/chat_message.dart' show ChatMessage;
export 'templates/popup_chat/models/tool_call_info.dart' show ToolCallInfo;
export 'templates/agent_overlay/kuralit_agent_overlay.dart' show KuralitAgentOverlay;

