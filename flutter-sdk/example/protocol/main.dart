import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:kuralit_sdk/kuralit.dart';
import 'package:kuralit_sdk/src/audio/audio_recorder_service.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Kuralit Protocol Example',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const ProtocolScreen(),
    );
  }
}

class ProtocolScreen extends StatefulWidget {
  const ProtocolScreen({super.key});

  @override
  State<ProtocolScreen> createState() => _ProtocolScreenState();
}

class _ProtocolScreenState extends State<ProtocolScreen> {
  // Text controller for input
  final TextEditingController _textController = TextEditingController();
  
  // List to store all WebSocket messages (sent and received)
  final List<ProtocolMessage> _messages = [];
  
  // Connection status
  bool _isConnected = false;
  
  // Session ID
  String? _sessionId;
  
  // Event subscription
  StreamSubscription<KuralitEvent>? _eventSubscription;
  
  // Audio recording
  final AudioRecorderService _audioRecorder = AudioRecorderService();
  bool _isRecording = false;
  StreamSubscription<Uint8List>? _audioChunkSubscription;
  int _audioChunkCount = 0;

  @override
  void initState() {
    super.initState();
    _initializeSDK();
  }

  /// Step 1: Initialize the Kuralit SDK
  void _initializeSDK() {
    // Replace these with your actual values
    const serverUrl = 'wss://api.kuralit.com/ws';
    const apiKey = 'your-api-key-here';
    const appId = 'your-app-id-here';
    
    Kuralit.init(KuralitConfig(
      serverUrl: serverUrl,
      apiKey: apiKey,
      appId: appId,
      debug: true,
    ));
    
    _sessionId = Kuralit.generateSessionId();
    _addMessage('SDK Initialized', isSent: false, isSystem: true);
    _addMessage('Session ID: $_sessionId', isSent: false, isSystem: true);
    
    _setupEventListener();
    _connect();
  }

  /// Step 2: Set up event listener to see all responses
  void _setupEventListener() {
    _eventSubscription = Kuralit.events.listen((event) {
      if (!mounted) return;

      // Log each event type with its data
      if (event is KuralitConnectedEvent) {
        setState(() {
          _isConnected = true;
        });
        _addMessage(
          'WebSocket Connected',
          isSent: false,
          isSystem: true,
        );
        _addMessage(
          _formatJson({
            'type': 'connection',
            'status': 'connected',
          }),
          isSent: false,
        );
      } else if (event is KuralitDisconnectedEvent) {
        setState(() {
          _isConnected = false;
        });
        _addMessage(
          'WebSocket Disconnected',
          isSent: false,
          isSystem: true,
        );
        _addMessage(
          _formatJson({
            'type': 'connection',
            'status': 'disconnected',
          }),
          isSent: false,
        );
      } else if (event is KuralitServerConnectedEvent) {
        setState(() {
          _isConnected = true;
          if (event.sessionId.isNotEmpty) {
            _sessionId = event.sessionId;
          }
        });
        _addMessage(
          'Server Connected Response',
          isSent: false,
          isSystem: true,
        );
        _addMessage(
          _formatJson({
            'type': 'server_connected',
            'session_id': event.sessionId,
            'metadata': event.metadata,
          }),
          isSent: false,
        );
      } else if (event is KuralitServerTextEvent) {
        _addMessage(
          'Server Text Response (Final)',
          isSent: false,
          isSystem: true,
        );
        _addMessage(
          _formatJson({
            'type': 'server_text',
            'session_id': event.sessionId,
            'text': event.text,
            'metadata': event.metadata,
          }),
          isSent: false,
        );
      } else if (event is KuralitServerPartialEvent) {
        _addMessage(
          'Server Partial Response (Streaming)',
          isSent: false,
          isSystem: true,
        );
        _addMessage(
          _formatJson({
            'type': 'server_partial',
            'session_id': event.sessionId,
            'text': event.text,
            'is_final': event.isFinal,
            'metadata': event.metadata,
          }),
          isSent: false,
        );
      } else if (event is KuralitServerSttEvent) {
        _addMessage(
          'Server STT (Speech-to-Text) Response',
          isSent: false,
          isSystem: true,
        );
        _addMessage(
          _formatJson({
            'type': 'server_stt',
            'session_id': event.sessionId,
            'text': event.text,
            'confidence': event.confidence,
          }),
          isSent: false,
        );
      } else if (event is KuralitServerToolCallEvent) {
        _addMessage(
          'Server Tool Call Event',
          isSent: false,
          isSystem: true,
        );
        _addMessage(
          _formatJson({
            'type': 'server_tool_call',
            'session_id': event.sessionId,
            'tool_name': event.toolName,
            'tool_call_id': event.toolCallId,
            'status': event.status,
            'arguments': event.arguments,
          }),
          isSent: false,
        );
      } else if (event is KuralitServerToolResultEvent) {
        _addMessage(
          'Server Tool Result Event',
          isSent: false,
          isSystem: true,
        );
        _addMessage(
          _formatJson({
            'type': 'server_tool_result',
            'session_id': event.sessionId,
            'tool_name': event.toolName,
            'tool_call_id': event.toolCallId,
            'status': event.status,
            'result': event.result,
            'error': event.error,
          }),
          isSent: false,
        );
      } else if (event is KuralitErrorEvent) {
        _addMessage(
          'Error Event',
          isSent: false,
          isSystem: true,
          isError: true,
        );
        _addMessage(
          _formatJson({
            'type': 'error',
            'code': event.code,
            'message': event.message,
            'retriable': event.retriable,
          }),
          isSent: false,
          isError: true,
        );
      }
    });
  }

  /// Step 3: Connect to server
  Future<void> _connect() async {
    try {
      await Kuralit.connect();
    } catch (e) {
      _addMessage('Connection Error: $e', isSent: false, isError: true);
    }
  }

  /// Step 4: Send text message (shows the message format)
  void _sendText() {
    final text = _textController.text.trim();
    if (text.isEmpty || !_isConnected || _sessionId == null) {
      return;
    }

    // Show what we're sending
    _addMessage(
      'Sending Text Message',
      isSent: true,
      isSystem: true,
    );
    _addMessage(
      _formatJson({
        'type': 'client_text',
        'session_id': _sessionId,
        'text': text,
      }),
      isSent: true,
    );

    _textController.clear();

    try {
      final sent = Kuralit.sendText(_sessionId!, text);
      if (!sent) {
        _addMessage('Failed to send text', isSent: true, isError: true);
      }
    } catch (e) {
      _addMessage('Error: $e', isSent: true, isError: true);
    }
  }

  /// Step 5: Send audio (shows start, chunks, end format)
  Future<void> _startAudio() async {
    if (!_isConnected || _sessionId == null || _isRecording) return;

    // Request permission
    if (!await _audioRecorder.checkPermission()) {
      if (!await _audioRecorder.requestPermission()) {
        _addMessage('Microphone permission denied', isSent: false, isError: true);
        return;
      }
    }

    setState(() {
      _isRecording = true;
      _audioChunkCount = 0;
    });

    // Show audio start message
    _addMessage(
      'Sending Audio Start',
      isSent: true,
      isSystem: true,
    );
    _addMessage(
      _formatJson({
        'type': 'client_audio_start',
        'session_id': _sessionId,
        'sample_rate': 16000,
        'encoding': 'PCM16',
      }),
      isSent: true,
    );

    // Send start message
    final started = Kuralit.startAudioStream(
      _sessionId!,
      sampleRate: 16000,
      encoding: 'PCM16',
    );

    if (!started) {
      setState(() {
        _isRecording = false;
      });
      _addMessage('Failed to start audio stream', isSent: true, isError: true);
      return;
    }

    // Listen to audio chunks
    _audioChunkSubscription = _audioRecorder.audioChunks.listen(
      (chunk) {
        if (_isRecording && _isConnected) {
          _audioChunkCount++;
          
          // Show chunk format (only first few to avoid spam)
          if (_audioChunkCount <= 3) {
            _addMessage(
              'Sending Audio Chunk #$_audioChunkCount',
              isSent: true,
              isSystem: true,
            );
            _addMessage(
              _formatJson({
                'type': 'client_audio_chunk',
                'session_id': _sessionId,
                'data_size': chunk.length,
                'timestamp': DateTime.now().millisecondsSinceEpoch / 1000.0,
                'note': 'Actual audio data is binary (Uint8List)',
              }),
              isSent: true,
            );
          } else if (_audioChunkCount == 4) {
            _addMessage(
              '... (more chunks being sent) ...',
              isSent: true,
              isSystem: true,
            );
          }

          Kuralit.sendAudioChunk(_sessionId!, chunk);
        }
      },
      onError: (e) {
        _addMessage('Audio stream error: $e', isSent: false, isError: true);
      },
    );

    final recordingStarted = await _audioRecorder.startRecording();
    if (!recordingStarted) {
      setState(() {
        _isRecording = false;
      });
      Kuralit.endAudioStream(_sessionId!);
      _addMessage('Failed to start recording', isSent: true, isError: true);
    }
  }

  /// Stop audio recording
  Future<void> _stopAudio() async {
    if (!_isRecording) return;

    setState(() {
      _isRecording = false;
    });

    await _audioChunkSubscription?.cancel();
    _audioChunkSubscription = null;
    await _audioRecorder.stopRecording();

    // Show audio end message
    _addMessage(
      'Sending Audio End',
      isSent: true,
      isSystem: true,
    );
    _addMessage(
      _formatJson({
        'type': 'client_audio_end',
        'session_id': _sessionId,
        'total_chunks': _audioChunkCount,
      }),
      isSent: true,
    );

    Kuralit.endAudioStream(_sessionId!);
    _addMessage(
      'Audio recording stopped. Total chunks sent: $_audioChunkCount',
      isSent: false,
      isSystem: true,
    );
  }

  /// Helper: Add message to log
  void _addMessage(String content, {required bool isSent, bool isSystem = false, bool isError = false}) {
    setState(() {
      _messages.add(ProtocolMessage(
        content: content,
        isSent: isSent,
        isSystem: isSystem,
        isError: isError,
        timestamp: DateTime.now(),
      ));
    });
    // Auto-scroll would go here
  }

  /// Helper: Format JSON nicely
  String _formatJson(Map<String, dynamic> json) {
    const encoder = JsonEncoder.withIndent('  ');
    return encoder.convert(json);
  }

  @override
  void dispose() {
    _eventSubscription?.cancel();
    _audioChunkSubscription?.cancel();
    _audioRecorder.dispose();
    _textController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('WebSocket Protocol Example'),
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 16),
            child: Row(
              children: [
                Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: _isConnected ? Colors.green : Colors.red,
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  _isConnected ? 'Connected' : 'Disconnected',
                  style: const TextStyle(fontSize: 12),
                ),
              ],
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // Controls section
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.grey.shade100,
              border: Border(
                bottom: BorderSide(color: Colors.grey.shade300),
              ),
            ),
            child: Column(
              children: [
                // Text input
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _textController,
                        decoration: const InputDecoration(
                          hintText: 'Type a message...',
                          border: OutlineInputBorder(),
                          isDense: true,
                        ),
                        onSubmitted: (_) => _sendText(),
                      ),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton(
                      onPressed: _isConnected ? _sendText : null,
                      child: const Text('Send Text'),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                // Audio controls
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    ElevatedButton.icon(
                      onPressed: _isConnected && !_isRecording
                          ? _startAudio
                          : null,
                      icon: const Icon(Icons.mic),
                      label: const Text('Start Audio'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green,
                        foregroundColor: Colors.white,
                      ),
                    ),
                    const SizedBox(width: 16),
                    ElevatedButton.icon(
                      onPressed: _isRecording ? _stopAudio : null,
                      icon: const Icon(Icons.stop),
                      label: const Text('Stop Audio'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.red,
                        foregroundColor: Colors.white,
                      ),
                    ),
                    if (_isRecording) ...[
                      const SizedBox(width: 16),
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.red.shade100,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Row(
                          children: [
                            Container(
                              width: 12,
                              height: 12,
                              decoration: const BoxDecoration(
                                shape: BoxShape.circle,
                                color: Colors.red,
                              ),
                            ),
                            const SizedBox(width: 8),
                            const Text('Recording...'),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ],
            ),
          ),

          // Messages log
          Expanded(
            child: _messages.isEmpty
                ? const Center(
                    child: Text(
                      'WebSocket messages will appear here.\n\n'
                      'Send a text message or start audio recording to see the message formats.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.grey),
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _messages.length,
                    itemBuilder: (context, index) {
                      final message = _messages[index];
                      return _buildMessageItem(message);
                    },
                  ),
          ),
        ],
      ),
    );
  }

  /// Build message item widget
  Widget _buildMessageItem(ProtocolMessage message) {
    Color bgColor;
    Color textColor;
    IconData icon;

    if (message.isError) {
      bgColor = Colors.red.shade50;
      textColor = Colors.red.shade900;
      icon = Icons.error;
    } else if (message.isSystem) {
      bgColor = Colors.blue.shade50;
      textColor = Colors.blue.shade900;
      icon = message.isSent ? Icons.arrow_upward : Icons.arrow_downward;
    } else if (message.isSent) {
      bgColor = Colors.green.shade50;
      textColor = Colors.green.shade900;
      icon = Icons.send;
    } else {
      bgColor = Colors.orange.shade50;
      textColor = Colors.orange.shade900;
      icon = Icons.reply;
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: textColor.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 16, color: textColor),
              const SizedBox(width: 8),
              Text(
                message.isSystem
                    ? (message.isSent ? 'SENT' : 'RECEIVED')
                    : (message.isSent ? 'SENT' : 'RECEIVED'),
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  color: textColor,
                ),
              ),
              const Spacer(),
              Text(
                '${message.timestamp.hour}:${message.timestamp.minute.toString().padLeft(2, '0')}',
                style: TextStyle(
                  fontSize: 10,
                  color: textColor.withOpacity(0.7),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          SelectableText(
            message.content,
            style: TextStyle(
              fontSize: 12,
              fontFamily: 'monospace',
              color: textColor,
            ),
          ),
        ],
      ),
    );
  }
}

/// Protocol message model
class ProtocolMessage {
  final String content;
  final bool isSent;
  final bool isSystem;
  final bool isError;
  final DateTime timestamp;

  ProtocolMessage({
    required this.content,
    required this.isSent,
    this.isSystem = false,
    this.isError = false,
    required this.timestamp,
  });
}
