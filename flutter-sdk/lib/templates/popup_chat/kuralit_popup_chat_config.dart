import 'package:flutter/material.dart';
import 'models/chat_message.dart';
import 'models/tool_call_info.dart';

/// Configuration class for Kuralit Popup Chat template
/// 
/// Provides customization options for theme, widget composition, and behavior
class KuralitPopupChatConfig {
  /// Theme customization
  final Color? primaryColor;
  final Color? backgroundColor;
  final Color? messageBubbleColor;
  final Color? userMessageColor;
  final Color? botMessageColor;
  
  /// Widget builders for full composition
  final Widget Function(ChatMessage)? messageBuilder;
  final Widget Function(String streamingText, bool isProcessing)? streamingMessageBuilder;
  final Widget Function(TextEditingController controller, bool isConnected, bool isLoading, VoidCallback onSend)? textInputBuilder;
  final Widget Function(bool isRecording, String sttText, bool isProcessing, VoidCallback onToggleRecording)? audioInputBuilder;
  final Widget Function(ToolCallInfo)? toolCallBuilder;
  final Widget Function(Map<String, dynamic> metadata)? toolMetadataBuilder;
  
  /// Behavior customization
  final bool enableAudioMode;
  final bool enableToolCalls;
  final VoidCallback? onClose;
  final bool showConnectionStatus;
  final bool showToolMetadata;
  
  /// Dialog customization
  final double? width;
  final double? height;
  final BorderRadius? borderRadius;
  
  const KuralitPopupChatConfig({
    this.primaryColor,
    this.backgroundColor,
    this.messageBubbleColor,
    this.userMessageColor,
    this.botMessageColor,
    this.messageBuilder,
    this.streamingMessageBuilder,
    this.textInputBuilder,
    this.audioInputBuilder,
    this.toolCallBuilder,
    this.toolMetadataBuilder,
    this.enableAudioMode = true,
    this.enableToolCalls = true,
    this.onClose,
    this.showConnectionStatus = true,
    this.showToolMetadata = true,
    this.width,
    this.height,
    this.borderRadius,
  });
}



