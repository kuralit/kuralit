/// Chat message model for popup chat template
class ChatMessage {
  final String text;
  final bool isUser;
  final Map<String, dynamic>? metadata;
  final DateTime timestamp;
  final bool isStreaming;

  ChatMessage({
    required this.text,
    required this.isUser,
    this.metadata,
    required this.timestamp,
    this.isStreaming = false,
  });
}



