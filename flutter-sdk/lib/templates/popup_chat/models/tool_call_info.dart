/// Tool call information model for popup chat template
class ToolCallInfo {
  final String toolName;
  final String toolCallId;
  final String status;
  final Map<String, dynamic> arguments;
  final String? result;

  ToolCallInfo({
    required this.toolName,
    required this.toolCallId,
    required this.status,
    required this.arguments,
    this.result,
  });
}



