import 'package:flutter/material.dart';
import '../kuralit_popup_chat_config.dart';

/// Default text input widget
class TextInputWidget extends StatelessWidget {
  final TextEditingController controller;
  final bool isConnected;
  final bool isLoading;
  final VoidCallback onSend;
  final KuralitPopupChatConfig? config;

  const TextInputWidget({
    Key? key,
    required this.controller,
    required this.isConnected,
    required this.isLoading,
    required this.onSend,
    this.config,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Use custom builder if provided
    if (config?.textInputBuilder != null) {
      return config!.textInputBuilder!(
        controller,
        isConnected,
        isLoading,
        onSend,
      );
    }

    // Default implementation
    return Row(
      children: [
        Expanded(
          child: TextField(
            controller: controller,
            decoration: InputDecoration(
              hintText: isConnected ? 'Type your message...' : 'Connecting...',
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(24),
              ),
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 12,
              ),
            ),
            enabled: isConnected && !isLoading,
            onSubmitted: (_) => onSend(),
          ),
        ),
        const SizedBox(width: 8),
        IconButton(
          onPressed: isConnected && !isLoading ? onSend : null,
          icon: isLoading
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.send),
          color: config?.primaryColor ?? Colors.blue,
        ),
      ],
    );
  }
}



