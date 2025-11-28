import 'dart:convert';
import 'package:flutter/material.dart';
import '../models/tool_call_info.dart';
import '../kuralit_popup_chat_config.dart';

/// Default tool call widget
class ToolCallWidget extends StatelessWidget {
  final ToolCallInfo toolCall;
  final KuralitPopupChatConfig? config;

  const ToolCallWidget({
    Key? key,
    required this.toolCall,
    this.config,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Use custom builder if provided
    if (config?.toolCallBuilder != null) {
      return config!.toolCallBuilder!(toolCall);
    }

    // Default implementation
    final isCompleted = toolCall.status == 'completed' && toolCall.result != null;
    final isCalling = toolCall.status == 'calling';

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isCompleted ? Colors.green.shade50 : Colors.orange.shade50,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isCompleted ? Colors.green.shade200 : Colors.orange.shade200,
            width: 1,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  isCompleted ? Icons.check_circle : Icons.build_circle,
                  size: 20,
                  color: isCompleted ? Colors.green.shade700 : Colors.orange.shade700,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Tool: ${toolCall.toolName}',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: isCompleted ? Colors.green.shade700 : Colors.orange.shade700,
                    ),
                  ),
                ),
                if (isCalling)
                  const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
              ],
            ),
            const SizedBox(height: 8),
            if (toolCall.arguments.isNotEmpty) ...[
              Text(
                'Arguments:',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: Colors.grey.shade700,
                ),
              ),
              const SizedBox(height: 4),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  _formatJson(toolCall.arguments),
                  style: TextStyle(
                    fontSize: 11,
                    fontFamily: 'monospace',
                    color: Colors.grey.shade800,
                  ),
                ),
              ),
              const SizedBox(height: 8),
            ],
            if (isCompleted && toolCall.result != null) ...[
              Text(
                'Result:',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: Colors.grey.shade700,
                ),
              ),
              const SizedBox(height: 4),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Text(
                    _formatJsonString(toolCall.result!),
                    style: TextStyle(
                      fontSize: 11,
                      fontFamily: 'monospace',
                      color: Colors.grey.shade800,
                    ),
                  ),
                ),
              ),
            ] else if (isCalling) ...[
              Text(
                'Status: Calling...',
                style: TextStyle(
                  fontSize: 12,
                  fontStyle: FontStyle.italic,
                  color: Colors.orange.shade700,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  String _formatJson(Map<String, dynamic> json) {
    try {
      return const JsonEncoder.withIndent('  ').convert(json);
    } catch (e) {
      return json.toString();
    }
  }

  String _formatJsonString(String jsonString) {
    try {
      final decoded = jsonDecode(jsonString);
      return const JsonEncoder.withIndent('  ').convert(decoded);
    } catch (e) {
      return jsonString;
    }
  }
}



