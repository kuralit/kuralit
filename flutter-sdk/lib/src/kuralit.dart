import 'dart:async';
import 'dart:typed_data';
import 'package:uuid/uuid.dart';
import 'kuralit_config.dart';
import 'kuralit_events.dart';
import 'kuralit_client.dart';
import 'utils/metadata.dart';

/// Main Kuralit SDK class
/// 
/// Usage:
/// ```dart
/// await Kuralit.init(KuralitConfig(
///   serverUrl: 'wss://api.kuralit.com/ws',
///   apiKey: 'your-api-key',
///   appId: 'your-app-id',
///   debug: true,
/// ));
/// 
/// await Kuralit.connect();
/// 
/// Kuralit.events.listen((event) {
///   if (event is KuralitConnectedEvent) {
///     print('Connected!');
///   } else if (event is KuralitServerTextEvent) {
///     print('Reply: ${event.text}');
///   }
/// });
/// 
/// final sessionId = Kuralit.generateSessionId();
/// await Kuralit.sendText(sessionId, 'Hello!');
/// ```
class Kuralit {
  static KuralitClient? _client;
  static bool _isInitialized = false;
  static final _uuid = const Uuid();

  /// Stream of SDK events
  static Stream<KuralitEvent> get events {
    _requireInitialized();
    return _client!.events;
  }

  /// Initialize the SDK with configuration
  /// 
  /// Must be called before any other operations.
  /// 
  /// Throws [StateError] if already initialized.
  static void init(KuralitConfig config) {
    if (_isInitialized) {
      throw StateError('Kuralit SDK is already initialized. Call dispose() first to reinitialize.');
    }

    _client = KuralitClient(config);
    _isInitialized = true;
  }

  /// Connect to the WebSocket server
  /// 
  /// Returns a Future that completes when connection is established or fails.
  static Future<void> connect() async {
    _requireInitialized();
    await _client!.connect();
  }

  /// Disconnect from the WebSocket server
  static void disconnect() {
    _requireInitialized();
    _client!.disconnect();
  }

  /// Send a text message
  /// 
  /// [sessionId] - Session ID for conversation continuity
  /// [text] - Text message to send (max 4KB)
  /// [metadata] - Optional metadata to include (will be merged with device metadata)
  /// 
  /// The message automatically includes device metadata:
  /// - Platform information (iOS/Android/Web)
  /// - OS version
  /// - SDK version
  /// - App state (foreground/background)
  /// - App ID
  /// - User ID (if set via setUser())
  /// 
  /// Returns true if message was sent, false otherwise.
  /// 
  /// Throws [ArgumentError] if text is empty or exceeds 4KB.
  /// 
  /// Example:
  /// ```dart
  /// // Basic usage
  /// Kuralit.sendText(sessionId, 'Hello!');
  /// 
  /// // With custom metadata
  /// Kuralit.sendText(sessionId, 'Hello!', metadata: {
  ///   'custom_field': 'value',
  ///   'source': 'chat_screen',
  /// });
  /// ```
  static bool sendText(
    String sessionId,
    String text, {
    Map<String, dynamic>? metadata,
  }) {
    _requireInitialized();
    
    if (text.isEmpty) {
      throw ArgumentError.value(text, 'text', 'Text cannot be empty');
    }

    if (text.length > 4096) {
      throw ArgumentError.value(text, 'text', 'Text cannot exceed 4KB');
    }

    return _client!.sendText(sessionId, text, metadata: metadata);
  }

  /// Start an audio stream
  /// 
  /// [sessionId] - Session ID for conversation continuity
  /// [sampleRate] - Audio sample rate (default: 16000). Supported: 8000, 16000, 44100, 48000
  /// [encoding] - Audio encoding (default: 'PCM16'). Supported: 'PCM16' or 'PCM8' (uppercase per spec)
  /// [metadata] - Optional metadata to include in the audio start message
  /// 
  /// Returns true if start message was sent, false otherwise.
  static bool startAudioStream(
    String sessionId, {
    int sampleRate = 16000,
    String encoding = 'PCM16',
    Map<String, dynamic>? metadata,
  }) {
    _requireInitialized();
    return _client!.sendAudioStart(sessionId, sampleRate, encoding, metadata: metadata);
  }

  /// Send an audio chunk
  /// 
  /// [sessionId] - Session ID
  /// [chunk] - Audio data as Uint8List
  /// [timestamp] - Optional Unix timestamp in seconds with milliseconds precision
  /// 
  /// Returns true if chunk was sent, false otherwise.
  /// 
  /// Throws [ArgumentError] if chunk is empty.
  static bool sendAudioChunk(
    String sessionId,
    Uint8List chunk, {
    double? timestamp,
  }) {
    _requireInitialized();
    
    if (chunk.isEmpty) {
      throw ArgumentError.value(chunk, 'chunk', 'Chunk cannot be empty');
    }

    return _client!.sendAudioChunk(sessionId, chunk.toList(), timestamp: timestamp);
  }

  /// End an audio stream
  /// 
  /// [sessionId] - Session ID
  /// [finalChunk] - Optional final audio chunk if there's remaining audio data
  /// 
  /// Returns true if end message was sent, false otherwise.
  static bool endAudioStream(
    String sessionId, {
    Uint8List? finalChunk,
  }) {
    _requireInitialized();
    return _client!.sendAudioEnd(
      sessionId,
      finalChunk: finalChunk?.toList(),
    );
  }

  /// Generate a new session ID
  /// 
  /// [prefix] - Optional prefix for the session ID (e.g., user ID or app identifier)
  /// 
  /// Returns a UUID v4 string, optionally prefixed.
  /// 
  /// Example:
  /// ```dart
  /// // Simple UUID
  /// final sessionId = Kuralit.generateSessionId();
  /// 
  /// // With user prefix
  /// final sessionId = Kuralit.generateSessionId(prefix: 'user_123');
  /// // Result: "user_123_550e8400-e29b-41d4-a716-446655440000"
  /// ```
  static String generateSessionId({String? prefix}) {
    final uuid = _uuid.v4();
    if (prefix != null && prefix.isNotEmpty) {
      return '${prefix}_$uuid';
    }
    return uuid;
  }
  
  /// Set app state (foreground/background)
  /// 
  /// This should be called when the app lifecycle changes.
  /// The app state is included in message metadata.
  /// 
  /// [state] - App state: 'foreground' or 'background'
  /// 
  /// Example:
  /// ```dart
  /// // In your app lifecycle observer
  /// AppLifecycleListener(
  ///   onStateChange: (state) {
  ///     if (state == AppLifecycleState.resumed) {
  ///       Kuralit.setAppState('foreground');
  ///     } else {
  ///       Kuralit.setAppState('background');
  ///     }
  ///   },
  /// )
  /// ```
  static void setAppState(String state) {
    _requireInitialized();
    if (state == 'foreground' || state == 'background') {
      MetadataCollector.setAppState(state);
    } else {
      throw ArgumentError.value(state, 'state', 'Must be "foreground" or "background"');
    }
  }

  /// Set user information
  /// 
  /// [userId] - User identifier
  /// [properties] - Optional user properties
  static void setUser(String userId, {Map<String, dynamic>? properties}) {
    _requireInitialized();
    _client!.setUser(userId, properties);
  }

  /// Clear user information
  static void clearUser() {
    _requireInitialized();
    _client!.clearUser();
  }

  /// Check if SDK is connected to the server
  /// 
  /// Returns true if connected, false otherwise.
  static bool isConnected() {
    if (!_isInitialized || _client == null) {
      return false;
    }
    return _client!.isConnected;
  }

  /// Get server-provided session ID (if available)
  /// 
  /// The server sends a session_id in the `server_connected` message upon connection.
  /// This method returns that session ID, or null if not yet received.
  /// 
  /// Returns the server session ID, or null if not available.
  static String? getServerSessionId() {
    _requireInitialized();
    return _client!.serverSessionId;
  }

  /// Dispose SDK resources
  /// 
  /// Call this when you're done using the SDK to free resources.
  /// After calling dispose(), you can call init() again to reinitialize.
  static void dispose() {
    _client?.dispose();
    _client = null;
    _isInitialized = false;
  }

  static void _requireInitialized() {
    if (!_isInitialized || _client == null) {
      throw StateError(
        'Kuralit SDK not initialized. Call Kuralit.init() first.',
      );
    }
  }
}

