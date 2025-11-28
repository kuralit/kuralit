import 'dart:convert';
import 'dart:typed_data';

/// Client message types
enum ClientMessageType {
  /// Text message
  clientText,

  /// Audio stream start
  clientAudioStart,

  /// Audio chunk
  clientAudioChunk,

  /// Audio stream end
  clientAudioEnd;

  /// Converts enum name to snake_case string format expected by backend
  String toSnakeCase() {
    // Convert camelCase to snake_case
    // clientText -> client_text
    // clientAudioStart -> client_audio_start
    final name = this.name;
    final buffer = StringBuffer();
    for (int i = 0; i < name.length; i++) {
      final char = name[i];
      if (i > 0 && char == char.toUpperCase()) {
        buffer.write('_');
      }
      buffer.write(char.toLowerCase());
    }
    return buffer.toString();
  }
}

/// Server message types
enum ServerMessageType {
  /// Connection confirmation
  serverConnected,

  /// STT transcription
  serverStt,

  /// Final text response
  serverText,

  /// Partial/streaming text response
  serverPartial,

  /// Error response
  serverError,

  /// Tool call initiated
  serverToolCall,

  /// Tool call result
  serverToolResult,
}

/// Base message envelope
abstract class Message {
  /// Message type
  String get type;

  /// Session ID
  String get sessionId;

  /// Message data
  Map<String, dynamic> get data;

  /// Converts message to JSON
  Map<String, dynamic> toJson();
}

/// Client message envelope
class ClientMessage implements Message {
  @override
  final String type;

  @override
  final String sessionId;

  @override
  final Map<String, dynamic> data;

  /// Optional metadata
  final Map<String, dynamic>? metadata;

  /// Creates a new ClientMessage
  ClientMessage({
    required this.type,
    required this.sessionId,
    required this.data,
    this.metadata,
  });

  @override
  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{
      'type': type,
      'session_id': sessionId,
      'data': data,
    };
    if (metadata != null && metadata!.isNotEmpty) {
      json['metadata'] = metadata;
    }
    return json;
  }

  /// Converts message to JSON string
  String toJsonString() {
    return jsonEncode(toJson());
  }
}

/// Server message envelope
class ServerMessage implements Message {
  @override
  final String type;

  @override
  final String sessionId;

  @override
  final Map<String, dynamic> data;

  /// Creates a new ServerMessage
  ServerMessage({
    required this.type,
    required this.sessionId,
    required this.data,
  });

  /// Parses a ServerMessage from JSON
  factory ServerMessage.fromJson(Map<String, dynamic> json) {
    return ServerMessage(
      type: json['type'] as String,
      sessionId: json['session_id'] as String,
      data: json['data'] as Map<String, dynamic>,
    );
  }

  /// Parses a ServerMessage from JSON string
  factory ServerMessage.fromJsonString(String jsonString) {
    final json = jsonDecode(jsonString) as Map<String, dynamic>;
    return ServerMessage.fromJson(json);
  }

  @override
  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'session_id': sessionId,
      'data': data,
    };
  }
}

/// Server connected data
class ServerConnectedData {
  final String message;
  final Map<String, dynamic>? metadata;

  ServerConnectedData({
    required this.message,
    this.metadata,
  });

  factory ServerConnectedData.fromJson(Map<String, dynamic> json) {
    return ServerConnectedData(
      message: json['message'] as String? ?? 'Connected successfully',
      metadata: json['metadata'] as Map<String, dynamic>?,
    );
  }
}

/// Server STT (Speech-to-Text) data
class ServerSttData {
  final String text;
  final double? confidence;

  ServerSttData({
    required this.text,
    this.confidence,
  });

  factory ServerSttData.fromJson(Map<String, dynamic> json) {
    return ServerSttData(
      text: json['text'] as String,
      confidence: json['confidence'] as double?,
    );
  }
}

/// Server text data
class ServerTextData {
  final String text;
  final Map<String, dynamic>? metadata;

  ServerTextData({
    required this.text,
    this.metadata,
  });

  factory ServerTextData.fromJson(Map<String, dynamic> json) {
    return ServerTextData(
      text: json['text'] as String,
      metadata: json['metadata'] as Map<String, dynamic>?,
    );
  }
}

/// Server partial data
class ServerPartialData {
  final String text;
  final bool isFinal;
  final Map<String, dynamic>? metadata;

  ServerPartialData({
    required this.text,
    this.isFinal = false,
    this.metadata,
  });

  factory ServerPartialData.fromJson(Map<String, dynamic> json) {
    return ServerPartialData(
      text: json['text'] as String,
      isFinal: json['is_final'] as bool? ?? false,
      metadata: json['metadata'] as Map<String, dynamic>?,
    );
  }
}

/// Server error data
class ServerErrorData {
  final String code;
  final String message;
  final bool retriable;

  ServerErrorData({
    required this.code,
    required this.message,
    this.retriable = false,
  });

  factory ServerErrorData.fromJson(Map<String, dynamic> json) {
    return ServerErrorData(
      code: json['code'] as String,
      message: json['message'] as String,
      retriable: json['retriable'] as bool? ?? false,
    );
  }
}

/// Server tool call data
class ServerToolCallData {
  final String toolName;
  final String toolCallId;
  final String status;
  final Map<String, dynamic> arguments;

  ServerToolCallData({
    required this.toolName,
    required this.toolCallId,
    required this.status,
    required this.arguments,
  });

  factory ServerToolCallData.fromJson(Map<String, dynamic> json) {
    return ServerToolCallData(
      toolName: json['tool_name'] as String,
      toolCallId: json['tool_call_id'] as String,
      status: json['status'] as String,
      arguments: json['arguments'] as Map<String, dynamic>? ?? {},
    );
  }
}

/// Server tool result data
class ServerToolResultData {
  final String toolName;
  final String toolCallId;
  final String status;
  final dynamic result; // Can be any type (object, string, etc.)
  final String? error; // Error message if status is "failed"

  ServerToolResultData({
    required this.toolName,
    required this.toolCallId,
    required this.status,
    this.result,
    this.error,
  });

  factory ServerToolResultData.fromJson(Map<String, dynamic> json) {
    return ServerToolResultData(
      toolName: json['tool_name'] as String,
      toolCallId: json['tool_call_id'] as String? ?? '',
      status: json['status'] as String,
      result: json['result'],
      error: json['error'] as String?,
    );
  }
}

/// Message validation utilities
class MessageValidator {
  /// Maximum text message size (4KB)
  static const int maxTextSize = 4096;

  /// Validates text message size
  static bool isValidTextSize(String text) {
    return text.length <= maxTextSize;
  }

  /// Validates session ID
  static bool isValidSessionId(String sessionId) {
    return sessionId.isNotEmpty;
  }

  /// Validates audio chunk
  static bool isValidAudioChunk(Uint8List chunk) {
    return chunk.isNotEmpty;
  }
}

