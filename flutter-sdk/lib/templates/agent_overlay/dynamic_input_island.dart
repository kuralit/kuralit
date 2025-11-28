import 'package:flutter/material.dart';
import 'dart:math' as math;

class DynamicInputIsland extends StatefulWidget {
  final bool isRecording;
  final VoidCallback onMicTap;
  final Function(String) onTextSubmit;
  final double audioLevel; // 0.0 to 1.0
  final String? transcription;

  const DynamicInputIsland({
    Key? key,
    required this.isRecording,
    required this.onMicTap,
    required this.onTextSubmit,
    this.audioLevel = 0.0,
    this.transcription,
  }) : super(key: key);

  @override
  State<DynamicInputIsland> createState() => _DynamicInputIslandState();
}

class _DynamicInputIslandState extends State<DynamicInputIsland> with TickerProviderStateMixin {
  bool _isTextMode = false;
  final TextEditingController _textController = TextEditingController();
  final FocusNode _focusNode = FocusNode();
  
  // Animation for the "breathing" glow effect when recording
  late AnimationController _breathingController;
  late Animation<double> _breathingAnimation;

  @override
  void initState() {
    super.initState();
    _breathingController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    )..repeat(reverse: true);
    
    _breathingAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _breathingController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _textController.dispose();
    _focusNode.dispose();
    _breathingController.dispose();
    super.dispose();
  }

  void _toggleMode() {
    setState(() {
      _isTextMode = !_isTextMode;
      if (_isTextMode) {
        _focusNode.requestFocus();
      } else {
        _focusNode.unfocus();
      }
    });
  }

  void _handleTextSubmit() {
    if (_textController.text.trim().isNotEmpty) {
      widget.onTextSubmit(_textController.text.trim());
      _textController.clear();
      _focusNode.requestFocus();
    }
  }

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final targetWidth = _isTextMode ? screenWidth * 0.92 : 140.0;
    final targetHeight = 60.0;

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Real-time Transcription Display
        if (widget.isRecording && widget.transcription != null && widget.transcription!.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: AnimatedOpacity(
              duration: const Duration(milliseconds: 300),
              opacity: 1.0,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.6),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Text(
                  widget.transcription!,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                  ),
                  textAlign: TextAlign.center,
                ),
              ),
            ),
          ),

        GestureDetector(
          onTap: () {},
          child: AnimatedBuilder(
            animation: _breathingAnimation,
            builder: (context, child) {
              return AnimatedContainer(
                duration: const Duration(milliseconds: 400),
                curve: Curves.easeOutQuart, // easeOutBack causes negative blur radius on overshoot
                width: targetWidth,
                height: targetHeight,
                decoration: BoxDecoration(
                  color: Colors.black,
                  borderRadius: BorderRadius.circular(30),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.3),
                      blurRadius: 20,
                      offset: const Offset(0, 8),
                      spreadRadius: 2,
                    ),
                    // Breathing Glow when recording
                    if (widget.isRecording)
                      BoxShadow(
                        color: const Color(0xFFFFD700).withOpacity(0.3 * _breathingAnimation.value),
                        blurRadius: 15 + (10 * _breathingAnimation.value),
                        spreadRadius: 2 * _breathingAnimation.value,
                      ),
                    // Inner glow
                    BoxShadow(
                      color: Colors.white.withOpacity(0.1),
                      blurRadius: 1,
                      offset: const Offset(0, 1),
                      spreadRadius: 0,
                      blurStyle: BlurStyle.inner,
                    ),
                  ],
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(30),
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      // --- Mic Mode Content ---
                      AnimatedOpacity(
                        duration: const Duration(milliseconds: 200),
                        opacity: _isTextMode ? 0.0 : 1.0,
                        child: IgnorePointer(
                          ignoring: _isTextMode,
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                            children: [
                              // Keyboard Switcher
                              IconButton(
                                icon: const Icon(Icons.keyboard_alt_outlined, color: Colors.white70),
                                tooltip: 'Type a message',
                                onPressed: _toggleMode,
                              ),
                              
                              // Mic / Waveform Button
                              GestureDetector(
                                onTap: widget.onMicTap,
                                child: Container(
                                  width: 44,
                                  height: 44,
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    color: widget.isRecording ? const Color(0xFFFFD700).withOpacity(0.2) : Colors.transparent,
                                  ),
                                  child: widget.isRecording
                                      ? CustomPaint(
                                          painter: WaveformPainter(
                                            audioLevel: widget.audioLevel,
                                            color: const Color(0xFFFFD700),
                                          ),
                                          child: const Center(
                                            child: Icon(Icons.stop_rounded, color: Color(0xFFFFD700), size: 20),
                                          ),
                                        )
                                      : const Icon(Icons.mic, color: Colors.white, size: 24),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),

                      // --- Text Mode Content ---
                      AnimatedOpacity(
                        duration: const Duration(milliseconds: 300),
                        opacity: _isTextMode ? 1.0 : 0.0,
                        child: IgnorePointer(
                          ignoring: !_isTextMode,
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 8.0),
                            child: Row(
                              children: [
                                IconButton(
                                  icon: const Icon(Icons.mic_none_outlined, color: Colors.white70),
                                  onPressed: _toggleMode,
                                ),
                                Expanded(
                                  child: TextField(
                                    controller: _textController,
                                    focusNode: _focusNode,
                                    style: const TextStyle(color: Colors.white, fontSize: 16),
                                    cursorColor: const Color(0xFFFFD700),
                                    decoration: const InputDecoration(
                                      hintText: 'Type...',
                                      hintStyle: TextStyle(color: Colors.white38),
                                      border: InputBorder.none,
                                      contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                                      isDense: true,
                                    ),
                                    onSubmitted: (_) => _handleTextSubmit(),
                                  ),
                                ),
                                Container(
                                  margin: const EdgeInsets.only(left: 4),
                                  decoration: const BoxDecoration(
                                    color: Color(0xFFB38728), // Gold accent
                                    shape: BoxShape.circle,
                                  ),
                                  child: IconButton(
                                    icon: const Icon(Icons.arrow_upward, color: Colors.white, size: 20),
                                    constraints: const BoxConstraints(minWidth: 36, minHeight: 36),
                                    padding: EdgeInsets.zero,
                                    onPressed: _handleTextSubmit,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

class WaveformPainter extends CustomPainter {
  final double audioLevel; // 0.0 to 1.0
  final Color color;

  WaveformPainter({required this.audioLevel, required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0
      ..strokeCap = StrokeCap.round;

    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2;
    
    // Draw a base circle
    // canvas.drawCircle(center, radius, paint..style = PaintingStyle.stroke..strokeWidth = 1);

    // Draw dynamic waveform bars around the circle
    final count = 12;
    final angleStep = (2 * math.pi) / count;
    
    for (int i = 0; i < count; i++) {
      final angle = i * angleStep;
      // Randomize slightly based on audio level
      final barHeight = 4.0 + (audioLevel * 12.0 * (0.5 + 0.5 * math.sin(i * 3)));
      
      final startX = center.dx + (radius - 2) * math.cos(angle);
      final startY = center.dy + (radius - 2) * math.sin(angle);
      
      final endX = center.dx + (radius + barHeight) * math.cos(angle);
      final endY = center.dy + (radius + barHeight) * math.sin(angle);
      
      canvas.drawLine(Offset(startX, startY), Offset(endX, endY), paint);
    }
  }

  @override
  bool shouldRepaint(WaveformPainter oldDelegate) {
    return oldDelegate.audioLevel != audioLevel || oldDelegate.color != color;
  }
}
