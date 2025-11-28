import 'package:flutter/material.dart';
import '../kuralit_popup_chat_config.dart';

/// Default streaming message widget
class StreamingMessageWidget extends StatelessWidget {
  final String streamingText;
  final bool isProcessing;
  final Map<String, dynamic>? toolMetadata;
  final KuralitPopupChatConfig? config;
  final Widget Function(Map<String, dynamic>)? metadataBuilder;

  const StreamingMessageWidget({
    Key? key,
    required this.streamingText,
    required this.isProcessing,
    this.toolMetadata,
    this.config,
    this.metadataBuilder,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Use custom builder if provided
    if (config?.streamingMessageBuilder != null) {
      return config!.streamingMessageBuilder!(streamingText, isProcessing);
    }

    // Default implementation
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
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
          Flexible(
            child: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            if (isProcessing && streamingText.isEmpty) ...[
                              Row(
                                children: [
                                  const SizedBox(
                                    width: 12,
                                    height: 12,
                                    child: CircularProgressIndicator(strokeWidth: 2),
                                  ),
                                  const SizedBox(width: 8),
                                  Text(
                                    'Processing...',
                                    style: TextStyle(
                                      fontSize: 14,
                                      fontStyle: FontStyle.italic,
                                      color: Colors.grey.shade600,
                                    ),
                                  ),
                                ],
                              ),
                            ] else if (streamingText.isNotEmpty) ...[
                              Text(
                                streamingText,
                                style: const TextStyle(fontSize: 14),
                              ),
                            ],
                          ],
                        ),
                      ),
                      if (isProcessing) ...[
                        const SizedBox(width: 8),
                        const SizedBox(
                          width: 12,
                          height: 12,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                      ],
                    ],
                  ),
                  if (toolMetadata != null && 
                      toolMetadata!.isNotEmpty && 
                      metadataBuilder != null) ...[
                    const SizedBox(height: 8),
                    metadataBuilder!(toolMetadata!),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}



