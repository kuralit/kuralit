import 'dart:async';
import 'dart:math' as math;
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../src/kuralit.dart';
import '../../src/kuralit_events.dart';
import '../../src/audio/audio_recorder_service.dart';
import '../base_template.dart';
import 'dynamic_input_island.dart';

/// Kuralit Agent Overlay Template
/// 
/// A full-screen overlay with animated golden borders and floating dust particles.
class KuralitAgentOverlay extends KuralitBaseTemplate {
  const KuralitAgentOverlay({
    Key? key,
    required String sessionId,
  }) : super(key: key, sessionId: sessionId);

  /// Show the agent overlay
  static void show(
    BuildContext context, {
    required String sessionId,
  }) {
    showDialog(
      context: context,
      barrierColor: Colors.transparent, // Transparent barrier
      barrierDismissible: true,
      builder: (context) => KuralitAgentOverlay(sessionId: sessionId),
    );
  }

  @override
  State<KuralitAgentOverlay> createState() => _KuralitAgentOverlayState();
}

class _KuralitAgentOverlayState extends State<KuralitAgentOverlay>
    with TickerProviderStateMixin {
  bool _isConnected = false;
  bool _isAgentActive = false;
  StreamSubscription<KuralitEvent>? _eventSubscription;
  
  // Animation controllers
  late AnimationController _borderAnimationController;
  late AnimationController _shimmerController;
  late Animation<double> _shimmerAnimation;
  late AnimationController _particleController;
  late AnimationController _slideController;
  late Animation<Offset> _slideAnimation;
  
  // Particles
  final List<Particle> _particles = [];
  final math.Random _random = math.Random();

  // Audio recording
  final AudioRecorderService _audioRecorder = AudioRecorderService();
  StreamSubscription<Uint8List>? _audioChunkSubscription;
  bool _isRecording = false;
  String? _serverSessionId;

  // Conversation State
  final List<ConversationItem> _conversationItems = [];
  final ScrollController _scrollController = ScrollController();

  // Voice UI State
  Timer? _amplitudeTimer;
  double _audioLevel = 0.0;
  String? _currentTranscription;
  DateTime? _recordingStartTime;

  @override
  void initState() {
    super.initState();
    _setupAnimations();
    _initParticles();
    _setupEventListener();
    _connectAndStartAgent();

    // Listen for audio stalls
    _audioRecorder.onAudioStalled.listen((_) {
      if (mounted && _isRecording && _isConnected) {
        print('⚠️ Agent: Audio stalled, restarting recorder...');
        _restartAudioRecorder();
      }
    });
  }

  Future<void> _restartAudioRecorder() async {
    // Stop recording but keep connection
    await _audioRecorder.stopRecording();
    
    // Wait a bit
    await Future.delayed(const Duration(milliseconds: 200));
    
    // Restart recording
    final started = await _audioRecorder.startRecording();
    if (started) {
       print('✅ Agent: Audio recorder restarted successfully');
    } else {
       print('❌ Agent: Failed to restart audio recorder');
       if (mounted) {
         ScaffoldMessenger.of(context).showSnackBar(
           const SnackBar(
             content: Text('Microphone issue. Please restart the agent.'),
             backgroundColor: Colors.red,
           ),
         );
       }
       }
    }

  void _setupAnimations() {
    // Border animation - continuous rotation/flow
    _borderAnimationController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 4),
    )..repeat();

    // Shimmer animation for glittering effect
    _shimmerController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    )..repeat();

    _shimmerAnimation = Tween<double>(begin: -1.0, end: 2.0).animate(
      CurvedAnimation(
        parent: _shimmerController,
        curve: Curves.easeInOut,
      ),
    );

    // Particle animation loop
    _particleController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 10), // Long duration for continuous loop
    )..repeat();
    
    _particleController.addListener(_updateParticles);

    // Slide animation for chat content
    _slideController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    
    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, 1),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _slideController,
      curve: Curves.easeOutQuart,
    ));

    // Start slide animation after a small delay
    Future.delayed(const Duration(milliseconds: 100), () {
      if (mounted) _slideController.forward();
    });
  }

  void _initParticles() {
    for (int i = 0; i < 80; i++) {
      _particles.add(_createParticle());
    }
  }

  Particle _createParticle() {
    return Particle(
      pathPosition: _random.nextDouble(), // 0.0 to 1.0 along the perimeter
      offset: _random.nextDouble() * 20.0 - 10.0, // -10 to +10 offset from border center
      size: _random.nextDouble() * 3 + 1, // 1.0 to 4.0
      speed: _random.nextDouble() * 0.001 + 0.0002, // Speed along path
      opacity: _random.nextDouble() * 0.6 + 0.2,
    );
  }

  void _updateParticles() {
    for (var particle in _particles) {
      // Move along the path
      particle.pathPosition += particle.speed;
      if (particle.pathPosition > 1.0) {
        particle.pathPosition -= 1.0;
      }
    }
    // No setState needed here if using AnimatedBuilder on the controller
  }

  void _setupEventListener() {
    _eventSubscription = Kuralit.events.listen((event) {
      if (!mounted) return;

      if (event is KuralitServerConnectedEvent) {
        setState(() {
          _isConnected = true;
          _serverSessionId = event.sessionId;
        });
        _startAgent();
      } else if (event is KuralitConnectedEvent) {
        setState(() {
          _isConnected = true;
        });
        _startAgent();
      } else if (event is KuralitDisconnectedEvent) {
        setState(() {
          _isConnected = false;
        });
        _stopAgent(); // Ensure recorder is stopped and cleaned up
      } else if (event is KuralitServerTextEvent) {
        setState(() {
          _isAgentActive = true;
          _addOrUpdateAgentMessage(event.text, isFinal: true);
        });
      } else if (event is KuralitServerPartialEvent) {
        setState(() {
          _isAgentActive = true;
          _addOrUpdateAgentMessage(event.text, isFinal: event.isFinal);
        });
      } else if (event is KuralitServerToolCallEvent) {
        setState(() {
          _isAgentActive = true;
          _addToolCall(event);
        });
      } else if (event is KuralitServerToolResultEvent) {
        setState(() {
          _isAgentActive = true;
          _updateToolResult(event);
        });
      } else if (event is KuralitServerSttEvent) {
        setState(() {
          _isAgentActive = true;
          
          // Find the last user message
          UserMessageItem? lastUserMsg;
          int lastUserMsgIndex = -1;
          for (int i = _conversationItems.length - 1; i >= 0; i--) {
            if (_conversationItems[i] is UserMessageItem) {
              lastUserMsg = _conversationItems[i] as UserMessageItem;
              lastUserMsgIndex = i;
              break;
            }
          }

          if (lastUserMsg != null) {
             bool isLastItem = lastUserMsgIndex == _conversationItems.length - 1;
             
             // If the text is identical to the last user message, ignore it to prevent duplicates
             // (This handles late final packets arriving after agent starts typing)
             if (lastUserMsg.text == event.text) {
               return;
             }

             if (isLastItem) {
                 // Update in place if it's the very last item (streaming)
                 _conversationItems[lastUserMsgIndex] = UserMessageItem(text: event.text);
             } else {
                 // If agent has already spoken (not last item), but we got new text:
                 // It's likely a new utterance. Add it.
                 _conversationItems.add(UserMessageItem(text: event.text));
             }
          } else {
            // First user message
            _conversationItems.add(UserMessageItem(text: event.text));
          }

          _scrollToBottom();
          
          // Update real-time transcription for the UI
          _currentTranscription = event.text;
        });
      } else if (event is KuralitErrorEvent) {
        setState(() {
          _isRecording = false;
          _isAgentActive = false;
        });
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Error: ${event.message}'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    });
  }

  void _addOrUpdateAgentMessage(String text, {required bool isFinal}) {
    if (_conversationItems.isNotEmpty && _conversationItems.last is AgentMessageItem) {
      final lastMsg = _conversationItems.last as AgentMessageItem;
      if (!lastMsg.isFinal) {
        // Update existing partial message
        // If it's a partial event, the text is a chunk, so we append it.
        // Wait, KuralitServerPartialEvent usually sends chunks.
        // Let's assume text is the chunk.
        // NOTE: If the server sends the FULL text each time, we should replace.
        // Based on typical streaming, it's chunks.
        // However, let's check if we need to append or replace.
        // Assuming append for now based on standard streaming.
        // Actually, let's look at the event definition or usage.
        // Re-reading KuralitServerPartialEvent: "Partial text content (incremental chunk)"
        // So we append.
        
        // But wait, if we receive KuralitServerTextEvent (final), that might be the whole text?
        // KuralitServerTextEvent: "Text content".
        
        if (isFinal) {
             // Final message replaces the partial content
             _conversationItems.last = AgentMessageItem(
               text: text, 
               isFinal: true,
               timestamp: lastMsg.timestamp,
             );
        } else {
             // Partial message appends
             _conversationItems.last = AgentMessageItem(
                text: lastMsg.text + text,
                isFinal: isFinal,
                timestamp: lastMsg.timestamp,
             );
        }
      } else {
        // Last message was final, start new one
        _conversationItems.add(AgentMessageItem(text: text, isFinal: isFinal));
      }
    } else {
      _conversationItems.add(AgentMessageItem(text: text, isFinal: isFinal));
    }
    _scrollToBottom();
  }

  void _addToolCall(KuralitServerToolCallEvent event) {
    _conversationItems.add(ToolCallItem(
      id: event.toolCallId,
      name: event.toolName,
      status: 'Running...',
      args: event.arguments,
    ));
    _scrollToBottom();
  }

  void _updateToolResult(KuralitServerToolResultEvent event) {
    final index = _conversationItems.indexWhere((item) => 
      item is ToolCallItem && item.id == event.toolCallId);
    
    if (index != -1) {
      final toolItem = _conversationItems[index] as ToolCallItem;
      _conversationItems[index] = ToolCallItem(
        id: toolItem.id,
        name: toolItem.name,
        status: event.status == 'success' ? 'Completed' : 'Failed',
        args: toolItem.args,
        result: event.result?.toString(),
        error: event.error,
        isCompleted: true,
        timestamp: toolItem.timestamp,
      );
    }
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

  String get _currentSessionId => _serverSessionId ?? widget.sessionId;

  Future<void> _connectAndStartAgent() async {
    if (!Kuralit.isConnected()) {
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
    } else {
      setState(() {
        _isConnected = true;
      });
      _startAgent();
    }
  }

  Future<void> _startAgent() async {
    if (!_isConnected) {
      // Wait for connection
      return;
    }

    if (_isRecording) return;

    // Request audio permission
    if (!await _audioRecorder.checkPermission()) {
      if (!await _audioRecorder.requestPermission()) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Microphone permission required'),
              backgroundColor: Colors.red,
            ),
          );
        }
        return;
      }
    }

    // Start audio stream
    final streamStarted = Kuralit.startAudioStream(
      _currentSessionId,
      sampleRate: 16000,
      encoding: 'PCM16',
    );

    if (!streamStarted) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Failed to start audio stream'),
            backgroundColor: Colors.red,
          ),
        );
      }
      return;
    }

    // Start recording
    setState(() {
      _isRecording = true;
      _isAgentActive = true;
      _currentTranscription = 'Listening...';
      _recordingStartTime = DateTime.now();
    });
    
    HapticFeedback.lightImpact();
    _startAmplitudePolling();

    _audioChunkSubscription = _audioRecorder.audioChunks.listen(
      (chunk) {
        if (_isRecording && _isConnected && _recordingStartTime != null) {
          final duration = DateTime.now().difference(_recordingStartTime!);
          // Convert to seconds with millisecond precision
          final timestamp = duration.inMilliseconds / 1000.0;
          try {
            Kuralit.sendAudioChunk(_currentSessionId, chunk, timestamp: timestamp);
          } catch (e) {
            print('❌ Agent: Failed to send audio chunk: $e');
            if (mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Connection unstable. Stopping agent.'),
                  backgroundColor: Colors.red,
                ),
              );
            }
            _stopAgent();
          }
        }
      },
      onError: (e) => print('❌ Agent: Audio stream error: $e'),
    );
    final started = await _audioRecorder.startRecording();
    if (!started) {
      setState(() {
        _isRecording = false;
        _isAgentActive = false;
        _currentTranscription = null;
        _recordingStartTime = null;
      });
      _stopAmplitudePolling();
      Kuralit.endAudioStream(_currentSessionId);
    }
  }
  
  void _startAmplitudePolling() {
    _amplitudeTimer?.cancel();
    _amplitudeTimer = Timer.periodic(const Duration(milliseconds: 100), (timer) async {
      if (!_isRecording) {
        timer.cancel();
        return;
      }
      final amp = await _audioRecorder.getAmplitude();
      // Normalize amplitude (usually -160 to 0 dB) to 0.0 - 1.0
      // Let's assume useful range is -60dB to 0dB
      double level = (amp.current + 60) / 60;
      level = level.clamp(0.0, 1.0);
      
      if (mounted) {
        setState(() {
          _audioLevel = level;
        });
      }
    });
  }

  void _stopAmplitudePolling() {
    _amplitudeTimer?.cancel();
    _amplitudeTimer = null;
    setState(() {
      _audioLevel = 0.0;
    });
  }

  Future<void> _stopAgent() async {
    if (!_isRecording) return;

    HapticFeedback.mediumImpact();
    _stopAmplitudePolling();

    setState(() {
      _isRecording = false;
      _currentTranscription = null;
    });

    await _audioChunkSubscription?.cancel();
    _audioChunkSubscription = null;
    await _audioRecorder.stopRecording();
    Kuralit.endAudioStream(_currentSessionId);
  }

  void _handleTextSubmit(String text) {
    if (!_isConnected) return;

    setState(() {
      _conversationItems.add(UserMessageItem(text: text));
      _scrollToBottom();
    });

    Kuralit.sendText(_currentSessionId, text);
  }

  @override
  void dispose() {
    _stopAgent();
    _eventSubscription?.cancel();
    _audioRecorder.dispose();
    _borderAnimationController.dispose();
    _shimmerController.dispose();
    _particleController.dispose();
    _slideController.dispose();
    _particleController.dispose();
    _slideController.dispose();
    _scrollController.dispose();
    _amplitudeTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      type: MaterialType.transparency,
      child: Stack(
        children: [
          // 1. Strong Frost Blur + Dimmed Overlay (Background)
          Positioned.fill(
            child: BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 15, sigmaY: 15),
              child: Container(
                color: Colors.black.withOpacity(0.4), // Dimmed overlay
              ),
            ),
          ),

          // 2. Subtle Golden Glow (Bottom Area Only)
          Positioned.fill(
            child: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Colors.transparent,
                    Colors.transparent,
                    const Color(0xFFFFD700).withOpacity(0.1), // Subtle gold at bottom
                  ],
                  stops: const [0.0, 0.7, 1.0],
                ),
              ),
            ),
          ),
          
          // 3. Main Content with Slide Animation
          SlideTransition(
            position: _slideAnimation,
            child: SafeArea(
              child: Column(
                children: [
                  // Sleek Top Header / Handle
                  Container(
                    padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 20),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        // Context Title
                        Row(
                          children: [
                            Container(
                              width: 4,
                              height: 16,
                              decoration: BoxDecoration(
                                color: const Color(0xFFFFD700),
                                borderRadius: BorderRadius.circular(2),
                              ),
                            ),
                            const SizedBox(width: 8),
                            const Text(
                              'Kuralit Agent',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                                letterSpacing: 0.5,
                              ),
                            ),
                          ],
                        ),
                        
                        // Close Control
                        IconButton(
                          icon: const Icon(Icons.close_rounded, color: Colors.white70),
                          onPressed: () {
                            _slideController.reverse().then((_) {
                              _stopAgent();
                              Navigator.of(context).pop();
                            });
                          },
                        ),
                      ],
                    ),
                  ),
                  
                  // Chat Area
                  Expanded(
                    child: ShaderMask(
                      shaderCallback: (Rect bounds) {
                        return LinearGradient(
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                          colors: [Colors.transparent, Colors.white, Colors.white, Colors.transparent],
                          stops: const [0.0, 0.05, 0.95, 1.0],
                        ).createShader(bounds);
                      },
                      blendMode: BlendMode.dstIn,
                      child: ListView.builder(
                        controller: _scrollController,
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
                        itemCount: _conversationItems.length + 
                            (_conversationItems.isNotEmpty && _conversationItems.last is UserMessageItem ? 1 : 0),
                        itemBuilder: (context, index) {
                          if (index == _conversationItems.length) {
                            return const ThinkingBubble();
                          }
                          final item = _conversationItems[index];
                          return _buildConversationItem(item);
                        },
                      ),
                    ),
                  ),
                  
                  // Bottom Controls: Dynamic Input Island
                  Padding(
                    padding: const EdgeInsets.only(bottom: 20, top: 10),
                    child: Center(
                      child: DynamicInputIsland(
                        isRecording: _isRecording,
                        audioLevel: _audioLevel,
                        transcription: _currentTranscription,
                        onMicTap: () {
                          if (_isRecording) {
                            _stopAgent();
                          } else {
                            _startAgent();
                          }
                        },
                        onTextSubmit: _handleTextSubmit,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildConversationItem(ConversationItem item) {
    if (item is AgentMessageItem) {
      return Padding(
        padding: const EdgeInsets.only(bottom: 24),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: const Color(0xFFB38728),
                shape: BoxShape.circle,
                border: Border.all(color: const Color(0xFFFFD700), width: 1),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.2),
                    blurRadius: 4,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: const Icon(Icons.smart_toy, color: Colors.white, size: 14),
            ),
            const SizedBox(width: 12),
            Flexible(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.95),
                      borderRadius: const BorderRadius.only(
                        topLeft: Radius.circular(18),
                        topRight: Radius.circular(18),
                        bottomRight: Radius.circular(18),
                        bottomLeft: Radius.circular(4),
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.1),
                          blurRadius: 6,
                          offset: const Offset(0, 3),
                        ),
                      ],
                    ),
                    child: Text(
                      item.text,
                      style: const TextStyle(
                        color: Colors.black87,
                        fontSize: 16,
                        height: 1.4,
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Padding(
                    padding: const EdgeInsets.only(left: 4),
                    child: Text(
                      _formatTime(item.timestamp),
                      style: TextStyle(
                        color: Colors.black.withOpacity(0.4),
                        fontSize: 10,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 40), // Breathing space
          ],
        ),
      );
    } else if (item is UserMessageItem) {
      return Padding(
        padding: const EdgeInsets.only(bottom: 24),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.end,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            const SizedBox(width: 40), // Breathing space
            Flexible(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [const Color(0xFF4A90E2), const Color(0xFF357ABD)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: const BorderRadius.only(
                        topLeft: Radius.circular(18),
                        topRight: Radius.circular(18),
                        bottomLeft: Radius.circular(18),
                        bottomRight: Radius.circular(4),
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFF357ABD).withOpacity(0.3),
                          blurRadius: 8,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: Text(
                      item.text,
                      textAlign: TextAlign.right,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        height: 1.4,
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Padding(
                    padding: const EdgeInsets.only(right: 4),
                    child: Text(
                      _formatTime(item.timestamp),
                      style: TextStyle(
                        color: Colors.black.withOpacity(0.4),
                        fontSize: 10,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 12),
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.9),
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.1),
                    blurRadius: 4,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: const Icon(Icons.person, color: Colors.black54, size: 14),
            ),
          ],
        ),
      );
    } else if (item is ToolCallItem) {
      return Padding(
        padding: const EdgeInsets.only(bottom: 20),
        child: Center(
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: Colors.black.withOpacity(0.6),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  item.isCompleted 
                      ? (item.status == 'Completed' ? Icons.check_circle : Icons.error)
                      : Icons.build_circle_outlined,
                  color: item.isCompleted 
                      ? (item.status == 'Completed' ? Colors.greenAccent : Colors.redAccent)
                      : Colors.white70,
                  size: 16,
                ),
                const SizedBox(width: 8),
                Text(
                  'Used ${item.name}',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    }
    return const SizedBox.shrink();
  }

  String _formatTime(DateTime time) {
    final hour = time.hour > 12 ? time.hour - 12 : (time.hour == 0 ? 12 : time.hour);
    final minute = time.minute.toString().padLeft(2, '0');
    final period = time.hour >= 12 ? 'PM' : 'AM';
    return '$hour:$minute $period';
  }
}

// Conversation Data Classes
abstract class ConversationItem {
  final DateTime timestamp;
  ConversationItem({required this.timestamp});
}

class AgentMessageItem extends ConversationItem {
  final String text;
  final bool isFinal;

  AgentMessageItem({required String text, required bool isFinal, DateTime? timestamp}) 
      : this.text = text,
        this.isFinal = isFinal,
        super(timestamp: timestamp ?? DateTime.now());
}

class ToolCallItem extends ConversationItem {
  final String id;
  final String name;
  final String status;
  final Map<String, dynamic> args;
  final String? result;
  final String? error;
  final bool isCompleted;

  ToolCallItem({
    required this.id,
    required this.name,
    required this.status,
    required this.args,
    this.result,
    this.error,
    this.isCompleted = false,
    DateTime? timestamp,
  }) : super(timestamp: timestamp ?? DateTime.now());
}

class UserMessageItem extends ConversationItem {
  final String text;

  UserMessageItem({required this.text, DateTime? timestamp}) : super(timestamp: timestamp ?? DateTime.now());
}



class Particle {
  double pathPosition; // 0.0 to 1.0 along the perimeter
  double offset; // Offset from the border line (perpendicular)
  double size;
  double speed;
  double opacity;

  Particle({
    required this.pathPosition,
    required this.offset,
    required this.size,
    required this.speed,
    required this.opacity,
  });
}

class ThinkingBubble extends StatefulWidget {
  const ThinkingBubble({Key? key}) : super(key: key);

  @override
  State<ThinkingBubble> createState() => _ThinkingBubbleState();
}

class _ThinkingBubbleState extends State<ThinkingBubble> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: const Color(0xFFB38728).withOpacity(0.9),
              shape: BoxShape.circle,
              border: Border.all(color: const Color(0xFFFFD700), width: 1),
            ),
            child: const Icon(Icons.smart_toy, color: Colors.white, size: 16),
          ),
          const SizedBox(width: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.95),
              borderRadius: const BorderRadius.only(
                topRight: Radius.circular(20),
                bottomLeft: Radius.circular(20),
                bottomRight: Radius.circular(20),
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.2),
                  blurRadius: 8,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: List.generate(3, (index) {
                return AnimatedBuilder(
                  animation: _controller,
                  builder: (context, child) {
                    // Staggered sine wave animation
                    final double t = (_controller.value + index * 0.2) % 1.0;
                    final double opacity = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(t * 2 * math.pi));
                    
                    return Container(
                      margin: const EdgeInsets.symmetric(horizontal: 2),
                      width: 8,
                      height: 8,
                      decoration: BoxDecoration(
                        color: Colors.black87.withOpacity(opacity),
                        shape: BoxShape.circle,
                      ),
                    );
                  },
                );
              }),
            ),
          ),
        ],
      ),
    );
  }
}

/// Custom painter for Golden borders with Dust Particles
class GoldenGlitterPainter extends CustomPainter {
  final double animation;
  final double shimmer;
  final bool isActive;
  final List<Particle> particles;

  GoldenGlitterPainter({
    required this.animation,
    required this.shimmer,
    required this.isActive,
    required this.particles,
  });

  @override
  void paint(Canvas canvas, Size size) {
    // 1. Define Golden Colors
    final colors = isActive
        ? [
            const Color(0xFFFFD700), // Gold
            const Color(0xFFFDB931), // Light Gold
            const Color(0xFFBF953F), // Dark Gold
            const Color(0xFFB38728), // Antique Gold
            const Color(0xFFFFD700), // Loop back to Gold
          ]
        : [
            Colors.grey.shade400,
            Colors.grey.shade300,
            Colors.grey.shade400,
          ];

    // 2. Define Geometry (Rounded Rectangle)
    final rect = Rect.fromLTWH(0, 0, size.width, size.height);
    final rrect = RRect.fromRectAndRadius(rect, const Radius.circular(24));

    // 3. Paint Particles (Golden Dust) - Flowing along edges
    if (isActive) {
      _drawParticles(canvas, size, rrect);
    }

    // 4. Paint the Glow (Behind the border)
    if (isActive) {
      final glowPaint = Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 12.0
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 10.0);

      // Create a sweeping gradient for the glow
      final glowGradient = SweepGradient(
        colors: colors,
        stops: _calculateStops(colors.length),
        transform: GradientRotation(animation * 2 * math.pi),
      );

      glowPaint.shader = glowGradient.createShader(rect);
      canvas.drawRRect(rrect, glowPaint);
    }

    // 5. Paint the Main Border
    final borderPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 4.0
      ..strokeCap = StrokeCap.round;

    // Create a sweeping gradient for the border
    final borderGradient = SweepGradient(
      colors: colors,
      stops: _calculateStops(colors.length),
      transform: GradientRotation(animation * 2 * math.pi),
    );

    borderPaint.shader = borderGradient.createShader(rect);
    canvas.drawRRect(rrect, borderPaint);

    // 6. Paint the Shimmer (Bright white traveling spot)
    if (isActive) {
      _drawShimmer(canvas, rrect, shimmer);
    }
  }

  void _drawParticles(Canvas canvas, Size size, RRect rrect) {
    final path = Path()..addRRect(rrect);
    final metrics = path.computeMetrics().first;
    final length = metrics.length;

    for (var particle in particles) {
      // Calculate position on the path
      final distance = particle.pathPosition * length;
      final tangent = metrics.getTangentForOffset(distance);

      if (tangent != null) {
        // Calculate perpendicular offset
        // Tangent vector is (tx, ty). Normal is (-ty, tx)
        final normal = Offset(-tangent.vector.dy, tangent.vector.dx);
        final pos = tangent.position + normal * particle.offset;

        final paint = Paint()
          ..color = const Color(0xFFFFD700).withOpacity(particle.opacity)
          ..style = PaintingStyle.fill
          ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 1.0);

        canvas.drawCircle(pos, particle.size, paint);
      }
    }
  }

  List<double> _calculateStops(int count) {
    return List.generate(count, (index) => index / (count - 1));
  }

  void _drawShimmer(Canvas canvas, RRect rrect, double shimmerValue) {
    final path = Path()..addRRect(rrect);
    final metrics = path.computeMetrics().first;
    final length = metrics.length;

    if (shimmerValue < -0.2 || shimmerValue > 1.2) return;

    final shimmerCenter = shimmerValue * length;
    final shimmerLen = 150.0;
    final start = shimmerCenter - shimmerLen / 2;
    final end = shimmerCenter + shimmerLen / 2;

    final extractPath = metrics.extractPath(start, end);

    final shimmerPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 4.0
      ..color = Colors.white
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 4.0);
      
    shimmerPaint.shader = LinearGradient(
      colors: [
        Colors.white.withOpacity(0.0),
        Colors.white,
        Colors.white.withOpacity(0.0),
      ],
      stops: const [0.0, 0.5, 1.0],
    ).createShader(extractPath.getBounds());

    canvas.drawPath(extractPath, shimmerPaint);
  }

  @override
  bool shouldRepaint(GoldenGlitterPainter oldDelegate) {
    return oldDelegate.animation != animation ||
        oldDelegate.shimmer != shimmer ||
        oldDelegate.isActive != isActive ||
        oldDelegate.particles != particles;
  }
}
