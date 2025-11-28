import 'dart:async';
import 'dart:convert';
import 'dart:io' show WebSocket;
import 'dart:math';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/io.dart' show IOWebSocketChannel;
import 'kuralit_config.dart';
import 'kuralit_events.dart';
import 'kuralit_protocol.dart';
import 'utils/logger.dart';
import 'utils/metadata.dart';

/// WebSocket client for Kuralit SDK
class KuralitClient {
  final KuralitConfig config;
  final KuralitLogger logger;
  final _eventsController = StreamController<KuralitEvent>.broadcast();
  final _pendingMessages = <String>[];
  
  WebSocketChannel? _channel;
  bool _isConnected = false;
  bool _isConnecting = false;
  Timer? _heartbeatTimer;
  Timer? _reconnectTimer;
  int _reconnectAttempts = 0;
  DateTime? _lastRttMeasurement;
  int? _rttMs;

  String? _userId;
  Map<String, dynamic>? _userProperties;
  String? _serverSessionId; // Server-provided session ID from server_connected

  /// Stream of events
  Stream<KuralitEvent> get events => _eventsController.stream;

  /// Get server-provided session ID (if available)
  String? get serverSessionId => _serverSessionId;

  /// Whether the client is connected
  bool get isConnected => _isConnected;

  /// Current RTT in milliseconds (null if not measured)
  int? get rttMs => _rttMs;

  /// Creates a new KuralitClient
  KuralitClient(this.config) : logger = KuralitLogger(enabled: config.debug);

  /// Connects to the WebSocket server
  Future<void> connect() async {
    if (_isConnected || _isConnecting) {
      logger.warn('Already connected or connecting');
      return;
    }

    _isConnecting = true;
    logger.info('Connecting to ${config.serverUrl}');

    try {
      final uri = Uri.parse(config.serverUrl);
      
      // Use platform-specific WebSocket with headers for non-web platforms
      if (kIsWeb) {
        // For web, headers are not supported, so we'll send auth in first message
        // or use query parameters (query params approach for now)
        final uriWithAuth = uri.replace(
          queryParameters: {
            ...uri.queryParameters,
            'x-api-key': config.apiKey,
            'x-app-id': config.appId,
          },
        );
        _channel = WebSocketChannel.connect(uriWithAuth);
      } else {
        // For mobile/desktop, use WebSocket.connect with headers
        // This properly sends headers in the WebSocket handshake
        final ws = await WebSocket.connect(
          uri.toString(),
          headers: {
            'x-api-key': config.apiKey,
            'x-app-id': config.appId,
          },
        );
        
        _channel = IOWebSocketChannel(ws);
      }

      // Set up message handler
      _channel!.stream.listen(
        (message) {
          // First message confirms connection
          if (!_isConnected) {
            _isConnected = true;
            _isConnecting = false;
            _reconnectAttempts = 0;
            logger.info('Connected successfully');
            _eventsController.add(const KuralitConnectedEvent());

            // Start heartbeat if configured
            if (config.heartbeatIntervalMs > 0) {
              _startHeartbeat();
            }

            // Send pending messages
            _flushPendingMessages();
          }
          _handleMessage(message);
        },
        onError: _handleError,
        onDone: _handleDone,
        cancelOnError: false,
      );
      
      // For immediate connection confirmation (if channel is ready)
      // We'll also set connected state after a short delay as fallback
      Future.delayed(const Duration(milliseconds: 1000), () {
        if (_channel != null && !_isConnected && _isConnecting) {
          // Assume connected if no error occurred
          _isConnected = true;
          _isConnecting = false;
          _reconnectAttempts = 0;
          logger.info('Connected (fallback detection)');
          _eventsController.add(const KuralitConnectedEvent());

          if (config.heartbeatIntervalMs > 0) {
            _startHeartbeat();
          }

          _flushPendingMessages();
        }
      });

      // Connection will be confirmed in onOpen handler
      // For now, we'll wait a short time and check if channel is still valid
      await Future.delayed(const Duration(milliseconds: 500));
      
      // If we got here without errors, connection is likely successful
      // The actual connection state will be set in the stream listener
      // when the first message arrives or connection is confirmed
    } catch (e) {
      _isConnecting = false;
      logger.error('Connection failed', e);
      _eventsController.add(KuralitErrorEvent(
        code: KuralitErrorCode.connectionError,
        message: 'Failed to connect: $e',
        retriable: true,
      ));

      if (config.reconnectEnabled) {
        _scheduleReconnect();
      }
    }
  }

  /// Disconnects from the WebSocket server
  void disconnect() {
    logger.info('Disconnecting');
    _stopHeartbeat();
    _cancelReconnect();
    _channel?.sink.close();
    _channel = null;
    _isConnected = false;
    _isConnecting = false;
    _reconnectAttempts = 0;
    _serverSessionId = null; // Clear server session ID on disconnect
    _eventsController.add(const KuralitDisconnectedEvent());
  }

  /// Sends a text message
  bool sendText(String sessionId, String text, {Map<String, dynamic>? metadata}) {
    if (!_isConnected) {
      logger.warn('Not connected, message will be queued');
      _queueMessage(_createTextMessage(sessionId, text, metadata).toJsonString());
      return false;
    }

    if (!MessageValidator.isValidTextSize(text)) {
      logger.error('Text message exceeds maximum size (4KB)');
      _eventsController.add(const KuralitErrorEvent(
        code: KuralitErrorCode.sendError,
        message: 'Text message exceeds maximum size',
        retriable: false,
      ));
      return false;
    }

    final message = _createTextMessage(sessionId, text, metadata);
    return _sendMessage(message);
  }

  /// Sends audio stream start
  bool sendAudioStart(
    String sessionId,
    int sampleRate,
    String encoding, {
    Map<String, dynamic>? metadata,
  }) {
    if (!_isConnected) {
      logger.warn('Not connected, cannot start audio stream');
      return false;
    }

    logger.info('Starting audio stream: sessionId=$sessionId, sampleRate=$sampleRate, encoding=$encoding');

    // Match Python client format exactly: only sample_rate and encoding in data
    final data = <String, dynamic>{
      'sample_rate': sampleRate, // snake_case per spec
      'encoding': encoding,
    };
    
    // Add metadata only if provided (Python client doesn't include it)
    if (metadata != null && metadata.isNotEmpty) {
      data['metadata'] = metadata;
    }

    final message = ClientMessage(
      type: ClientMessageType.clientAudioStart.toSnakeCase(),
      sessionId: sessionId,
      data: data,
      metadata: null, // No top-level metadata per spec
    );

    final sent = _sendMessage(message);
    if (sent) {
      print('✅ [KuralitSDK] Audio stream start sent: sampleRate=$sampleRate, encoding=$encoding');
      logger.info('Audio stream start message sent successfully');
    } else {
      logger.error('Failed to send audio stream start message');
    }
    return sent;
  }

  /// Sends an audio chunk
  bool sendAudioChunk(
    String sessionId,
    List<int> chunk, {
    double? timestamp,
  }) {
    if (!_isConnected) {
      logger.warn('Not connected, cannot send audio chunk');
      return false;
    }

    if (chunk.isEmpty) {
      logger.warn('Empty audio chunk, skipping');
      return false;
    }

    // Encode to base64
    final base64Chunk = base64Encode(chunk);

    final data = <String, dynamic>{
      'chunk': base64Chunk,
    };

    // Add timestamp if provided (Unix timestamp in seconds with milliseconds precision)
    if (timestamp != null) {
      data['timestamp'] = timestamp;
    }

    final message = ClientMessage(
      type: ClientMessageType.clientAudioChunk.toSnakeCase(),
      sessionId: sessionId,
      data: data,
      metadata: null, // No metadata in audio chunks per spec
    );

    final sent = _sendMessage(message);
    if (!sent) {
      logger.error('Failed to send audio chunk');
      throw Exception('Failed to send audio chunk');
    }
    return sent;
  }

  /// Sends audio stream end
  bool sendAudioEnd(
    String sessionId, {
    List<int>? finalChunk,
  }) {
    if (!_isConnected) {
      logger.warn('Not connected');
      return false;
    }

    final data = <String, dynamic>{};

    // Add final_chunk if provided (base64-encoded)
    if (finalChunk != null && finalChunk.isNotEmpty) {
      data['final_chunk'] = base64Encode(finalChunk);
    }

    final message = ClientMessage(
      type: ClientMessageType.clientAudioEnd.toSnakeCase(),
      sessionId: sessionId,
      data: data,
      metadata: null, // No metadata in audio end per spec
    );

    return _sendMessage(message);
  }

  /// Sets user information
  void setUser(String userId, Map<String, dynamic>? properties) {
    _userId = userId;
    _userProperties = properties;
  }

  /// Clears user information
  void clearUser() {
    _userId = null;
    _userProperties = null;
  }

  void _handleMessage(dynamic message) {
    try {
      final messageStr = message.toString();
      logger.debug('Received: ${KuralitLogger.truncateSensitive(messageStr)}');

      final serverMessage = ServerMessage.fromJsonString(messageStr);
      _processServerMessage(serverMessage);
    } catch (e, stackTrace) {
      logger.error('Failed to parse server message', e, stackTrace);
      _eventsController.add(KuralitErrorEvent(
        code: KuralitErrorCode.parseError,
        message: 'Failed to parse message: $e',
        retriable: false,
      ));
    }
  }

  void _processServerMessage(ServerMessage message) {
    final type = message.type.toLowerCase();

    // Handle server_connected message (sent immediately after connection)
    if (type == 'server_connected' || type == ServerMessageType.serverConnected.name.toLowerCase()) {
      _serverSessionId = message.sessionId;
      final connectedData = ServerConnectedData.fromJson(message.data);
      _eventsController.add(KuralitServerConnectedEvent(
        sessionId: message.sessionId,
        metadata: connectedData.metadata,
      ));
      return;
    }

    // Handle heartbeat messages (ignore silently)
    if (type == 'heartbeat') {
      // Heartbeat messages are keepalive pings, no action needed
      return;
    }

    // Handle server_stt (Speech-to-Text) messages
    if (type == 'server_stt' || type == ServerMessageType.serverStt.name.toLowerCase()) {
      final sttData = ServerSttData.fromJson(message.data);
      _eventsController.add(KuralitServerSttEvent(
        sessionId: message.sessionId,
        text: sttData.text,
        confidence: sttData.confidence,
      ));
      return;
    }

    // Backend sends snake_case: "server_text", "server_partial", "server_error", "server_tool_call", "server_tool_result"
    if (type == 'server_text' || type == ServerMessageType.serverText.name.toLowerCase()) {
      final textData = ServerTextData.fromJson(message.data);
      _eventsController.add(KuralitServerTextEvent(
        sessionId: message.sessionId,
        text: textData.text,
        metadata: textData.metadata,
      ));
    } else if (type == 'server_partial' || type == ServerMessageType.serverPartial.name.toLowerCase()) {
      final partialData = ServerPartialData.fromJson(message.data);
      _eventsController.add(KuralitServerPartialEvent(
        sessionId: message.sessionId,
        text: partialData.text,
        isFinal: partialData.isFinal,
        metadata: partialData.metadata,
      ));
    } else if (type == 'server_error' || type == ServerMessageType.serverError.name.toLowerCase()) {
      final errorData = ServerErrorData.fromJson(message.data);
      _eventsController.add(KuralitErrorEvent(
        code: errorData.code,
        message: errorData.message,
        retriable: errorData.retriable,
      ));
    } else if (type == 'server_tool_call' || type == ServerMessageType.serverToolCall.name.toLowerCase()) {
      final toolCallData = ServerToolCallData.fromJson(message.data);
      _eventsController.add(KuralitServerToolCallEvent(
        sessionId: message.sessionId,
        toolName: toolCallData.toolName,
        toolCallId: toolCallData.toolCallId,
        status: toolCallData.status,
        arguments: toolCallData.arguments,
      ));
    } else if (type == 'server_tool_result' || type == ServerMessageType.serverToolResult.name.toLowerCase()) {
      final toolResultData = ServerToolResultData.fromJson(message.data);
      _eventsController.add(KuralitServerToolResultEvent(
        sessionId: message.sessionId,
        toolName: toolResultData.toolName,
        toolCallId: toolResultData.toolCallId,
        status: toolResultData.status,
        result: toolResultData.result,
        error: toolResultData.error,
      ));
    } else {
      logger.warn('Unknown message type: ${message.type}');
    }
  }

  void _handleError(dynamic error) {
    logger.error('WebSocket error', error);
    _isConnected = false;
    _stopHeartbeat();

    _eventsController.add(KuralitErrorEvent(
      code: KuralitErrorCode.connectionError,
      message: 'WebSocket error: $error',
      retriable: true,
    ));

    if (config.reconnectEnabled) {
      _scheduleReconnect();
    }
  }

  void _handleDone() {
    logger.info('WebSocket connection closed');
    _isConnected = false;
    _stopHeartbeat();
    _eventsController.add(const KuralitDisconnectedEvent());

    if (config.reconnectEnabled) {
      _scheduleReconnect();
    }
  }

  bool _sendMessage(ClientMessage message) {
    try {
      final jsonString = message.toJsonString();
      logger.debug('Sending: ${KuralitLogger.truncateSensitive(jsonString)}');

      // Send immediately without any buffering or queuing
      // The WebSocket channel will handle the actual transmission
      _channel?.sink.add(jsonString);
      
      // For audio chunks, we want to ensure they're sent immediately
      // The sink.add() is synchronous and will queue if needed, but WebSocket
      // should send as fast as possible
      return true;
    } catch (e, stackTrace) {
      logger.error('Failed to send message', e, stackTrace);
      _eventsController.add(KuralitErrorEvent(
        code: KuralitErrorCode.sendError,
        message: 'Failed to send message: $e',
        retriable: true,
      ));
      return false;
    }
  }

  ClientMessage _createTextMessage(String sessionId, String text, Map<String, dynamic>? metadata) {
    // Format: {"type": "client_text", "session_id": "...", "data": {"text": "...", "metadata": {}}}
    // Use provided metadata or empty object, and merge with device metadata
    final dataMetadata = metadata ?? <String, dynamic>{};
    final mergedMetadata = _buildMetadata(dataMetadata);
    
    return ClientMessage(
      type: ClientMessageType.clientText.toSnakeCase(),
      sessionId: sessionId,
      data: {
        'text': text,
        'metadata': mergedMetadata.isEmpty ? <String, dynamic>{} : mergedMetadata,
      },
      metadata: null, // Don't put metadata at top level
    );
  }

  Map<String, dynamic> _buildMetadata([Map<String, dynamic>? additional]) {
    final deviceInfo = MetadataCollector.getDeviceInfo();
    final merged = <String, dynamic>{
      ...deviceInfo,
      'appId': config.appId,
    };

    if (_userId != null) {
      merged['userId'] = _userId;
    }

    if (_userProperties != null) {
      merged.addAll(_userProperties!);
    }

    if (additional != null) {
      merged.addAll(additional);
    }

    return merged;
  }

  void _startHeartbeat() {
    _stopHeartbeat();
    // Note: Heartbeat is disabled as the backend doesn't support ping messages
    // If heartbeat is needed, it should be implemented as a proper client message
    // For now, we'll just measure RTT without sending ping messages
    _heartbeatTimer = Timer.periodic(
      Duration(milliseconds: config.heartbeatIntervalMs),
      (_) {
        if (_isConnected) {
          _measureRtt();
          // Heartbeat ping disabled - backend doesn't support ping message type
          // _channel?.sink.add(jsonEncode({'type': 'ping'}));
        }
      },
    );
  }

  void _stopHeartbeat() {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = null;
  }

  void _measureRtt() {
    _lastRttMeasurement = DateTime.now();
  }

  void _scheduleReconnect() {
    if (_reconnectAttempts >= config.maxReconnectAttempts) {
      logger.error('Max reconnection attempts reached');
      _eventsController.add(KuralitErrorEvent(
        code: KuralitErrorCode.maxReconnectAttempts,
        message: 'Failed to reconnect after ${config.maxReconnectAttempts} attempts',
        retriable: false,
      ));
      return;
    }

    _cancelReconnect();
    _reconnectAttempts++;

    // Exponential backoff with jitter
    final baseDelay = config.reconnectDelayMs;
    final exponentialDelay = baseDelay * pow(2, (_reconnectAttempts - 1).clamp(0, 5));
    final jitter = Random().nextInt((exponentialDelay * 0.25).toInt());
    final totalDelay = (exponentialDelay + jitter).clamp(0, 30000); // Max 30 seconds

    logger.info('Scheduling reconnect attempt $_reconnectAttempts in ${totalDelay}ms');

    _reconnectTimer = Timer(Duration(milliseconds: totalDelay.toInt()), () {
      if (!_isConnected && !_isConnecting) {
        logger.info('Attempting reconnection...');
        connect();
      }
    });
  }

  void _cancelReconnect() {
    _reconnectTimer?.cancel();
    _reconnectTimer = null;
  }

  void _queueMessage(String messageJson) {
    _pendingMessages.add(messageJson);
    if (_pendingMessages.length > 100) {
      _pendingMessages.removeAt(0); // Keep queue size manageable
    }
  }

  void _flushPendingMessages() {
    if (_pendingMessages.isEmpty) return;

    logger.info('Flushing ${_pendingMessages.length} pending messages');
    final messages = List<String>.from(_pendingMessages);
    _pendingMessages.clear();

    for (final messageJson in messages) {
      try {
        _channel?.sink.add(messageJson);
      } catch (e) {
        logger.error('Failed to send pending message', e);
      }
    }
  }

  /// Disposes resources
  void dispose() {
    disconnect();
    _eventsController.close();
  }
}

