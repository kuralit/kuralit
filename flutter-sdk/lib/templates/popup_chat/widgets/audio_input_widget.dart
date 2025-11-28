import 'package:flutter/material.dart';
import '../kuralit_popup_chat_config.dart';

/// Default audio input widget
class AudioInputWidget extends StatelessWidget {
  final bool isRecording;
  final String sttText;
  final bool isProcessing;
  final VoidCallback onToggleRecording;
  final Animation<double>? pulseAnimation;
  final KuralitPopupChatConfig? config;

  const AudioInputWidget({
    Key? key,
    required this.isRecording,
    required this.sttText,
    required this.isProcessing,
    required this.onToggleRecording,
    this.pulseAnimation,
    this.config,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Use custom builder if provided
    if (config?.audioInputBuilder != null) {
      return config!.audioInputBuilder!(
        isRecording,
        sttText,
        isProcessing,
        onToggleRecording,
      );
    }

    // Default implementation
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Status text with priority order:
          // 1. Recording → "Listening..."
          // 2. STT text → Show real-time transcription
          // 3. Processing → "Processing..."
          // 4. Default → "Tap to speak"
          if (isRecording)
            Text(
              'Listening...',
              style: TextStyle(
                fontSize: 14,
                color: Colors.red.shade700,
                fontWeight: FontWeight.w500,
              ),
            )
          else if (sttText.isNotEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Text(
                sttText,
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.blue.shade700,
                  fontStyle: FontStyle.italic,
                ),
                textAlign: TextAlign.center,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            )
          else if (isProcessing)
            Text(
              'Processing...',
              style: TextStyle(
                fontSize: 14,
                color: Colors.blue.shade700,
                fontWeight: FontWeight.w500,
              ),
            )
          else
            Text(
              'Tap to speak',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey.shade600,
              ),
            ),
          const SizedBox(height: 16),
          // Microphone button - tap to toggle recording on/off
          GestureDetector(
            onTap: onToggleRecording,
            child: pulseAnimation != null
                ? AnimatedBuilder(
                    animation: pulseAnimation!,
                    builder: (context, child) {
                      return Transform.scale(
                        scale: isRecording ? pulseAnimation!.value : 1.0,
                        child: _buildMicrophoneButton(),
                      );
                    },
                  )
                : _buildMicrophoneButton(),
          ),
        ],
      ),
    );
  }

  Widget _buildMicrophoneButton() {
    return Container(
      width: 72,
      height: 72,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: isRecording
            ? Colors.red.shade400
            : (config?.primaryColor ?? Colors.blue.shade400),
        boxShadow: [
          BoxShadow(
            color: (isRecording ? Colors.red : (config?.primaryColor ?? Colors.blue))
                .withOpacity(0.3),
            blurRadius: isRecording ? 20 : 10,
            spreadRadius: isRecording ? 5 : 2,
          ),
        ],
      ),
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Microphone icon
          Icon(
            isRecording ? Icons.mic : Icons.mic_none,
            size: 36,
            color: Colors.white,
          ),
          // AI sparkle icon overlay
          if (!isRecording)
            Positioned(
              top: 8,
              right: 8,
              child: Container(
                width: 20,
                height: 20,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: Colors.amber.shade400,
                ),
                child: const Icon(
                  Icons.auto_awesome,
                  size: 12,
                  color: Colors.white,
                ),
              ),
            ),
        ],
      ),
    );
  }
}



