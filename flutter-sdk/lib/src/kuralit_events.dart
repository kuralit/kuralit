/// Base class for all Kuralit SDK events
abstract class KuralitEvent {
  /// Creates a new KuralitEvent
  const KuralitEvent();
}

/// WebSocket connection established
class KuralitConnectedEvent extends KuralitEvent {
  /// Creates a new KuralitConnectedEvent
  const KuralitConnectedEvent();
}

/// WebSocket connection closed
class KuralitDisconnectedEvent extends KuralitEvent {
  /// Creates a new KuralitDisconnectedEvent
  const KuralitDisconnectedEvent();
}

/// Server connection confirmation with session ID
class KuralitServerConnectedEvent extends KuralitEvent {
  /// Session ID provided by the server
  final String sessionId;

  /// Optional metadata from server
  final Map<String, dynamic>? metadata;

  /// Creates a new KuralitServerConnectedEvent
  const KuralitServerConnectedEvent({
    required this.sessionId,
    this.metadata,
  });
}

/// Server STT (Speech-to-Text) transcription event
class KuralitServerSttEvent extends KuralitEvent {
  /// Session ID
  final String sessionId;

  /// Transcribed text from audio
  final String text;

  /// Confidence score (0.0 to 1.0)
  final double? confidence;

  /// Creates a new KuralitServerSttEvent
  const KuralitServerSttEvent({
    required this.sessionId,
    required this.text,
    this.confidence,
  });
}

/// Final server text reply
class KuralitServerTextEvent extends KuralitEvent {
  /// Session ID
  final String sessionId;

  /// Text content
  final String text;

  /// Optional metadata
  final Map<String, dynamic>? metadata;

  /// Creates a new KuralitServerTextEvent
  const KuralitServerTextEvent({
    required this.sessionId,
    required this.text,
    this.metadata,
  });
}

/// Partial/streaming server text reply
class KuralitServerPartialEvent extends KuralitEvent {
  /// Session ID
  final String sessionId;

  /// Partial text content (incremental chunk)
  final String text;

  /// Whether this is the final partial message
  final bool isFinal;

  /// Optional metadata
  final Map<String, dynamic>? metadata;

  /// Creates a new KuralitServerPartialEvent
  const KuralitServerPartialEvent({
    required this.sessionId,
    required this.text,
    this.isFinal = false,
    this.metadata,
  });
}

/// Error event
class KuralitErrorEvent extends KuralitEvent {
  /// Error code
  final String code;

  /// Error message
  final String message;

  /// Whether the error is retriable
  final bool retriable;

  /// Creates a new KuralitErrorEvent
  const KuralitErrorEvent({
    required this.code,
    required this.message,
    this.retriable = false,
  });
}

/// Server tool call event
class KuralitServerToolCallEvent extends KuralitEvent {
  /// Session ID
  final String sessionId;

  /// Tool name
  final String toolName;

  /// Tool call ID
  final String toolCallId;

  /// Status (e.g., "calling")
  final String status;

  /// Tool arguments
  final Map<String, dynamic> arguments;

  /// Creates a new KuralitServerToolCallEvent
  const KuralitServerToolCallEvent({
    required this.sessionId,
    required this.toolName,
    required this.toolCallId,
    required this.status,
    required this.arguments,
  });
}

/// Server tool result event
class KuralitServerToolResultEvent extends KuralitEvent {
  /// Session ID
  final String sessionId;

  /// Tool name
  final String toolName;

  /// Tool call ID
  final String toolCallId;

  /// Status (e.g., "completed")
  final String status;

  /// Tool result (can be any type: string, object, etc.)
  final dynamic result;

  /// Error message if status is "failed"
  final String? error;

  /// Creates a new KuralitServerToolResultEvent
  const KuralitServerToolResultEvent({
    required this.sessionId,
    required this.toolName,
    required this.toolCallId,
    required this.status,
    this.result,
    this.error,
  });
}

/// Error code constants
class KuralitErrorCode {
  /// Connection error
  static const String connectionError = 'CONNECTION_ERROR';

  /// Send error
  static const String sendError = 'SEND_ERROR';

  /// Parse error
  static const String parseError = 'PARSE_ERROR';

  /// Max reconnect attempts reached
  static const String maxReconnectAttempts = 'MAX_RECONNECT_ATTEMPTS';

  /// Not initialized
  static const String notInitialized = 'NOT_INITIALIZED';

  /// Invalid configuration
  static const String invalidConfig = 'INVALID_CONFIG';

  /// Network error
  static const String networkError = 'NETWORK_ERROR';

  /// Timeout error
  static const String timeoutError = 'TIMEOUT_ERROR';
}

