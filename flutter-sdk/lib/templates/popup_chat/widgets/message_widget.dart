import 'package:flutter/material.dart';
import '../models/chat_message.dart';
import '../kuralit_popup_chat_config.dart';

/// Default message widget for chat messages
class MessageWidget extends StatelessWidget {
  final ChatMessage message;
  final KuralitPopupChatConfig? config;
  final Widget Function(Map<String, dynamic>)? metadataBuilder;

  const MessageWidget({
    Key? key,
    required this.message,
    this.config,
    this.metadataBuilder,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Use custom builder if provided
    if (config?.messageBuilder != null) {
      return config!.messageBuilder!(message);
    }

    // Default implementation
    final userColor = config?.userMessageColor ?? Colors.blue.shade50;
    final botColor = config?.botMessageColor ?? Colors.grey.shade100;
    final bubbleColor = message.isUser ? userColor : botColor;

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: message.isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        children: [
          if (!message.isUser) ...[
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: Colors.blue.shade100,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.smart_toy, size: 20, color: Colors.blue),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: bubbleColor,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    message.text,
                    style: const TextStyle(fontSize: 14),
                  ),
                  if (message.metadata != null && 
                      message.metadata!.isNotEmpty && 
                      metadataBuilder != null) ...[
                    const SizedBox(height: 8),
                    metadataBuilder!(message.metadata!),
                  ],
                ],
              ),
            ),
          ),
          if (message.isUser) ...[
            const SizedBox(width: 8),
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: Colors.grey.shade200,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.person, size: 20),
            ),
          ],
        ],
      ),
    );
  }
}



