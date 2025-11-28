import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../../src/kuralit.dart';
import '../../src/kuralit_events.dart';
import '../../src/audio/audio_recorder_service.dart';
import 'kuralit_popup_chat_config.dart';
import 'models/chat_message.dart';
import 'models/tool_call_info.dart';
import 'widgets/message_widget.dart';
import 'widgets/streaming_message_widget.dart';
import 'widgets/tool_call_widget.dart';
import 'widgets/text_input_widget.dart';
import 'widgets/audio_input_widget.dart';
import '../base_template.dart';

/// Kuralit Popup Chat Template
/// 
/// A ready-to-use chat dialog template that can be invoked on specific pages.
/// Supports full widget composition for customization.
class KuralitPopupChat extends KuralitBaseTemplate {
  final KuralitPopupChatConfig? config;

  const KuralitPopupChat({
    Key? key,
    required String sessionId,
    this.config,
  }) : super(key: key, sessionId: sessionId);

  /// Show the popup chat dialog
  /// 
  /// Convenience method to show the chat dialog on any page.
  static void show(
    BuildContext context, {
    required String sessionId,
    KuralitPopupChatConfig? config,
  }) {
    showDialog(
      context: context,
      barrierDismissible: true,
      builder: (context) => KuralitPopupChat(
        sessionId: sessionId,
        config: config,
      ),
    );
  }

  @override
  State<KuralitPopupChat> createState() => _KuralitPopupChatState();
}

class _KuralitPopupChatState extends State<KuralitPopupChat>
    with TickerProviderStateMixin {
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<ChatMessage> _messages = [];
  bool _isConnected = false;
  bool _isLoading = false;
  bool _isProcessing = false;
  StreamSubscription<KuralitEvent>? _eventSubscription;
  String _streamingText = '';
  Map<String, dynamic>? _toolMetadata;
  final Map<String, ToolCallInfo> _activeToolCalls = {};

  // Audio mode state
  bool _isAudioMode = false;
  bool _isRecording = false;
  String _sttText = '';
  final AudioRecorderService _audioRecorder = AudioRecorderService();
  StreamSubscription<Uint8List>? _audioChunkSubscription;
  late AnimationController _pulseAnimationController;
  late Animation<double> _pulseAnimation;
  String? _serverSessionId;

  @override
  void initState() {
    super.initState();
    _setupEventListener();
    _checkConnection();
    _setupAudioAnimations();
    _requestAudioPermission();
  }

  void _setupAudioAnimations() {
    _pulseAnimationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1000),
    );
    _pulseAnimation = Tween<double>(begin: 0.8, end: 1.0).animate(
      CurvedAnimation(
        parent: _pulseAnimationController,
        curve: Curves.easeInOut,
      ),
    );
  }

  Future<void> _requestAudioPermission() async {
    await _audioRecorder.requestPermission();
  }

  String get _currentSessionId => _serverSessionId ?? widget.sessionId;

  void _checkConnection() {
    setState(() {
      _isConnected = Kuralit.isConnected();
    });
  }

  void _setupEventListener() {
    _eventSubscription = Kuralit.events.listen((event) {
      if (!mounted) return;

      if (event is KuralitServerConnectedEvent) {
        setState(() {
          _isConnected = true;
          _serverSessionId = event.sessionId;
        });
        print('✅ Chat: Server connected with session_id: ${event.sessionId}');
      } else if (event is KuralitConnectedEvent) {
        setState(() {
          _isConnected = true;
        });
      } else if (event is KuralitDisconnectedEvent) {
        setState(() {
          _isConnected = false;
        });
        _stopRecording('Disconnected event');
      } else if (event is KuralitServerPartialEvent) {
        setState(() {
          final newText = event.text;
          
          if (_streamingText.isEmpty) {
            _streamingText = newText;
          } else if (newText.contains(_streamingText.trim())) {
            _streamingText = newText;
          } else {
            _streamingText += newText;
          }
          
          _isLoading = true;
          _isProcessing = false;
          
          if (event.metadata != null && event.metadata!.isNotEmpty) {
            _toolMetadata = event.metadata;
          }
        });
        _scrollToBottom();
      } else if (event is KuralitServerTextEvent) {
        setState(() {
          _isProcessing = false;
          _isLoading = false;
          _sttText = '';
          
          _messages.removeWhere((msg) => msg.isStreaming);
          
          _messages.add(ChatMessage(
            text: event.text,
            isUser: false,
            metadata: event.metadata,
            timestamp: DateTime.now(),
          ));
          
          _streamingText = '';
          _toolMetadata = event.metadata;
        });
        _scrollToBottom();
      } else if (event is KuralitServerToolCallEvent && (widget.config?.enableToolCalls ?? true)) {
        setState(() {
          _activeToolCalls[event.toolCallId] = ToolCallInfo(
            toolName: event.toolName,
            toolCallId: event.toolCallId,
            status: event.status,
            arguments: event.arguments,
            result: null,
          );
        });
        _scrollToBottom();
      } else if (event is KuralitServerToolResultEvent && (widget.config?.enableToolCalls ?? true)) {
        setState(() {
          if (_activeToolCalls.containsKey(event.toolCallId)) {
            _activeToolCalls[event.toolCallId] = ToolCallInfo(
              toolName: event.toolName,
              toolCallId: event.toolCallId,
              status: event.status,
              arguments: _activeToolCalls[event.toolCallId]!.arguments,
              result: event.result,
            );
          } else {
            _activeToolCalls[event.toolCallId] = ToolCallInfo(
              toolName: event.toolName,
              toolCallId: event.toolCallId,
              status: event.status,
              arguments: {},
              result: event.result,
            );
          }
        });
        _scrollToBottom();
      } else if (event is KuralitServerSttEvent) {
        setState(() {
          _sttText = event.text;
        });
        _scrollToBottom();
      } else if (event is KuralitErrorEvent) {
        setState(() {
          _isLoading = false;
          _isProcessing = false;
          _streamingText = '';
          if (_isRecording) {
            _stopRecording('Error event: ${event.message}');
          }
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: ${event.message}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    });
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _sendMessage() async {
    final text = _textController.text.trim();
    if (text.isEmpty || !_isConnected) return;

    setState(() {
      _messages.add(ChatMessage(
        text: text,
        isUser: true,
        timestamp: DateTime.now(),
      ));
      _isLoading = true;
      _isProcessing = false;
      _streamingText = '';
      _toolMetadata = null;
    });

    _textController.clear();
    _scrollToBottom();

    try {
      Kuralit.sendText(_currentSessionId, text, metadata: <String, dynamic>{});
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to send: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  void _connectIfNeeded() async {
    if (!_isConnected) {
      try {
        await Kuralit.connect();
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Failed to connect: $e'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    }
  }

  Future<void> _startRecording() async {
    if (!_isConnected || _isRecording) return;

    setState(() {
      _isRecording = true;
      _sttText = '';
      _isProcessing = false;
    });

    _pulseAnimationController.repeat(reverse: true);

    if (!await _audioRecorder.checkPermission()) {
      if (!await _audioRecorder.requestPermission()) {
        _stopRecording('Permission denied');
        return;
      }
    }

    print('📤 Chat: Sending client_audio_start message...');
    final streamStarted = Kuralit.startAudioStream(
      _currentSessionId,
      sampleRate: 16000,
      encoding: 'PCM16',
    );
    
    if (!streamStarted) {
      _stopRecording('Failed to send start message');
      return;
    }

    print('🎤 Chat: Starting audio recorder...');
    
    _audioChunkSubscription = _audioRecorder.audioChunks.listen(
      (chunk) {
        if (_isRecording && _isConnected) {
          Kuralit.sendAudioChunk(_currentSessionId, chunk);
        }
      },
      onError: (e) => print('❌ Chat: Audio stream error: $e'),
    );

    final started = await _audioRecorder.startRecording();
    if (!started) {
      _stopRecording('Failed to start recorder');
      return;
    }
    
    print('✅ Chat: Recording started & streaming');
  }

  Future<void> _stopRecording(String reason) async {
    if (!_isRecording) return;

    print('🛑 Chat: Stopping recording... Reason: $reason');

    _isRecording = false;
    
    await _audioChunkSubscription?.cancel();
    _audioChunkSubscription = null;

    await _audioRecorder.stopRecording();
    print('✅ Chat: Recording stopped');

    print('📤 Chat: Sending client_audio_end message...');
    Kuralit.endAudioStream(_currentSessionId);
    print('✅ Chat: Audio end message sent');

    setState(() {
      if (_streamingText.isEmpty && _sttText.isEmpty) {
        _isProcessing = true;
      }
    });

    _pulseAnimationController.stop();
    _pulseAnimationController.reset();
    
    print('🎤 Chat: Waiting for server response...');
  }

  void _toggleAudioMode() {
    setState(() {
      _isAudioMode = !_isAudioMode;
      if (_isAudioMode) {
        _isProcessing = false;
        _isLoading = false;
        _sttText = '';
        _streamingText = '';
      }
      if (!_isAudioMode && _isRecording) {
        _stopRecording('Audio mode switched off');
      }
    });
  }

  @override
  void dispose() {
    _eventSubscription?.cancel();
    _audioChunkSubscription?.cancel();
    _stopRecording('Widget dispose');
    _audioRecorder.dispose();
    _pulseAnimationController.dispose();
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Widget _buildMetadataInfo(Map<String, dynamic> metadata) {
    final toolInfo = <String>[];
    
    if (metadata.containsKey('tools_used')) {
      final tools = metadata['tools_used'];
      if (tools is List) {
        for (var tool in tools) {
          if (tool is Map) {
            final name = tool['name'] ?? 'Unknown';
            final params = tool['parameters'] ?? {};
            toolInfo.add('$name(${params.keys.join(", ")})');
          }
        }
      }
    }

    if (toolInfo.isEmpty && metadata.isNotEmpty) {
      metadata.forEach((key, value) {
        if (key != 'tools_used' && value != null) {
          toolInfo.add('$key: $value');
        }
      });
    }

    if (toolInfo.isEmpty) return const SizedBox.shrink();

    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Colors.blue.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.blue.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.info_outline, size: 14, color: Colors.blue.shade700),
              const SizedBox(width: 4),
              Text(
                'Tool Details',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  color: Colors.blue.shade700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          ...toolInfo.map((info) => Padding(
                padding: const EdgeInsets.only(top: 2),
                child: Text(
                  '• $info',
                  style: TextStyle(
                    fontSize: 11,
                    color: Colors.blue.shade700,
                  ),
                ),
              )),
        ],
      ),
    );
  }

  Widget _buildToolMetadataBanner() {
    if (_toolMetadata == null || _toolMetadata!.isEmpty || !(widget.config?.showToolMetadata ?? true)) {
      return const SizedBox.shrink();
    }

    if (widget.config?.toolMetadataBuilder != null) {
      return widget.config!.toolMetadataBuilder!(_toolMetadata!);
    }

    final toolsUsed = <String>[];

    if (_toolMetadata!.containsKey('tools_used')) {
      final tools = _toolMetadata!['tools_used'];
      if (tools is List) {
        for (var tool in tools) {
          if (tool is Map) {
            final name = tool['name'] ?? 'Unknown';
            toolsUsed.add(name);
          }
        }
      }
    }

    _toolMetadata!.forEach((key, value) {
      if (key.contains('tool') && value != null && !toolsUsed.contains(key)) {
        toolsUsed.add(key);
      }
    });

    if (toolsUsed.isEmpty) {
      return const SizedBox.shrink();
    }

    final toolCount = toolsUsed.length;
    final toolNames = toolsUsed.join(', ');

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.blue.shade50,
        border: Border(
          top: BorderSide(color: Colors.blue.shade200),
          bottom: BorderSide(color: Colors.blue.shade200),
        ),
      ),
      child: Row(
        children: [
          Icon(Icons.build, size: 16, color: Colors.blue.shade700),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              toolCount > 0
                  ? 'Used ${toolCount} tool${toolCount > 1 ? 's' : ''}: $toolNames'
                  : 'Tool details available',
              style: TextStyle(
                fontSize: 12,
                color: Colors.blue.shade700,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    _connectIfNeeded();

    final config = widget.config;
    final backgroundColor = config?.backgroundColor ?? Colors.white;
    final borderRadius = config?.borderRadius ?? BorderRadius.circular(16);
    final width = config?.width ?? MediaQuery.of(context).size.width * 0.9;
    final height = config?.height ?? MediaQuery.of(context).size.height * 0.8;

    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: borderRadius),
      child: Container(
        width: width,
        height: height,
        decoration: BoxDecoration(
          borderRadius: borderRadius,
          color: backgroundColor,
        ),
        child: Column(
          children: [
            // Header
            if (config?.showConnectionStatus ?? true)
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: _isConnected ? Colors.green.shade50 : Colors.grey.shade100,
                  borderRadius: BorderRadius.only(
                    topLeft: borderRadius.topLeft,
                    topRight: borderRadius.topRight,
                  ),
                ),
                child: Row(
                  children: [
                    Container(
                      width: 12,
                      height: 12,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: _isConnected ? Colors.green : Colors.grey,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Row(
                        children: [
                          Text(
                            'Kuralit AI',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: _isConnected ? Colors.green.shade700 : Colors.grey.shade700,
                            ),
                          ),
                          if (_isAudioMode && (config?.enableAudioMode ?? true)) ...[
                            const SizedBox(width: 8),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: Colors.blue.shade100,
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(Icons.mic, size: 14, color: Colors.blue.shade700),
                                  const SizedBox(width: 4),
                                  Text(
                                    'Audio Mode',
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: Colors.blue.shade700,
                                      fontWeight: FontWeight.w500,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                    if (config?.enableAudioMode ?? true)
                      IconButton(
                        icon: Icon(
                          _isAudioMode ? Icons.keyboard : Icons.mic,
                          color: _isAudioMode ? Colors.blue : Colors.grey,
                        ),
                        onPressed: _toggleAudioMode,
                        tooltip: _isAudioMode ? 'Switch to text mode' : 'Switch to audio mode',
                      ),
                    IconButton(
                      icon: const Icon(Icons.close),
                      onPressed: () {
                        config?.onClose?.call();
                        Navigator.of(context).pop();
                      },
                    ),
                  ],
                ),
              ),

            // Messages area
            Expanded(
              child: _messages.isEmpty && _streamingText.isEmpty && _activeToolCalls.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.chat_bubble_outline,
                            size: 64,
                            color: Colors.grey.shade300,
                          ),
                          const SizedBox(height: 16),
                          Text(
                            'Start a conversation',
                            style: TextStyle(
                              color: Colors.grey.shade600,
                              fontSize: 16,
                            ),
                          ),
                        ],
                      ),
                    )
                  : ListView.builder(
                      controller: _scrollController,
                      padding: const EdgeInsets.all(16),
                      itemCount: _messages.length + 
                          (_streamingText.isNotEmpty ? 1 : 0) + 
                          _activeToolCalls.length,
                      itemBuilder: (context, index) {
                        int messageIndex = index;
                        
                        if (index < _activeToolCalls.length) {
                          final toolCall = _activeToolCalls.values.elementAt(index);
                          return ToolCallWidget(
                            toolCall: toolCall,
                            config: config,
                          );
                        }
                        
                        messageIndex -= _activeToolCalls.length;
                        
                        if (messageIndex == _messages.length && _streamingText.isNotEmpty) {
                          return StreamingMessageWidget(
                            streamingText: _streamingText,
                            isProcessing: _isProcessing,
                            toolMetadata: _toolMetadata,
                            config: config,
                            metadataBuilder: _buildMetadataInfo,
                          );
                        }
                        
                        return MessageWidget(
                          message: _messages[messageIndex],
                          config: config,
                          metadataBuilder: _buildMetadataInfo,
                        );
                      },
                    ),
            ),

            // Tool metadata banner
            _buildToolMetadataBanner(),

            // STT transcription display
            if (_sttText.isNotEmpty)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.blue.shade50,
                  border: Border(
                    top: BorderSide(color: Colors.blue.shade200),
                  ),
                ),
                child: Row(
                  children: [
                    Icon(Icons.mic, size: 16, color: Colors.blue.shade700),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        _sttText,
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.blue.shade900,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ),
                  ],
                ),
              ),

            // Input area
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                border: Border(
                  top: BorderSide(color: Colors.grey.shade200),
                ),
              ),
              child: _isAudioMode && (config?.enableAudioMode ?? true)
                  ? AudioInputWidget(
                      isRecording: _isRecording,
                      sttText: _sttText,
                      isProcessing: _isProcessing,
                      onToggleRecording: () {
                        if (_isRecording) {
                          _stopRecording('User tapped mic button');
                        } else {
                          _startRecording();
                        }
                      },
                      pulseAnimation: _pulseAnimation,
                      config: config,
                    )
                  : TextInputWidget(
                      controller: _textController,
                      isConnected: _isConnected,
                      isLoading: _isLoading,
                      onSend: _sendMessage,
                      config: config,
                    ),
            ),
          ],
        ),
      ),
    );
  }
}



