/// Logging utility for the Kuralit SDK
class KuralitLogger {
  final bool enabled;

  /// Creates a new logger instance
  const KuralitLogger({required this.enabled});

  /// Logs a debug message
  void debug(String message, [Object? error, StackTrace? stackTrace]) {
    if (enabled) {
      _log('DEBUG', message, error, stackTrace);
    }
  }

  /// Logs an info message
  void info(String message, [Object? error, StackTrace? stackTrace]) {
    if (enabled) {
      _log('INFO', message, error, stackTrace);
    }
  }

  /// Logs a warning message
  void warn(String message, [Object? error, StackTrace? stackTrace]) {
    if (enabled) {
      _log('WARN', message, error, stackTrace);
    }
  }

  /// Logs an error message
  void error(String message, [Object? error, StackTrace? stackTrace]) {
    if (enabled) {
      _log('ERROR', message, error, stackTrace);
    }
  }

  void _log(String level, String message, Object? error, StackTrace? stackTrace) {
    final timestamp = DateTime.now().toIso8601String();
    print('[$timestamp] [$level] [KuralitSDK] $message');
    if (error != null) {
      print('Error: $error');
    }
    if (stackTrace != null) {
      print('StackTrace: $stackTrace');
    }
  }

  /// Truncates sensitive data in logs
  static String truncateSensitive(String data, {int maxLength = 100}) {
    if (data.length <= maxLength) {
      return data;
    }
    return '${data.substring(0, maxLength)}... (truncated)';
  }
}

