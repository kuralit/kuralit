/// Configuration for the Kuralit SDK
class KuralitConfig {
  /// WebSocket server URL (e.g., "wss://api.kuralit.com/ws")
  final String serverUrl;

  /// API key for authentication
  final String apiKey;

  /// Application ID
  final String appId;

  /// Enable debug logging
  final bool debug;

  /// Enable automatic reconnection
  final bool reconnectEnabled;

  /// Maximum number of reconnection attempts
  final int maxReconnectAttempts;

  /// Initial reconnect delay in milliseconds
  final int reconnectDelayMs;

  /// Heartbeat interval in milliseconds (0 to disable)
  final int heartbeatIntervalMs;

  /// Creates a new KuralitConfig instance
  KuralitConfig({
    required this.serverUrl,
    required this.apiKey,
    required this.appId,
    this.debug = false,
    this.reconnectEnabled = true,
    this.maxReconnectAttempts = 10,
    this.reconnectDelayMs = 1000,
    this.heartbeatIntervalMs = 30000,
  })  : assert(serverUrl.isNotEmpty, 'serverUrl cannot be empty'),
        assert(apiKey.isNotEmpty, 'apiKey cannot be empty'),
        assert(appId.isNotEmpty, 'appId cannot be empty'),
        assert(maxReconnectAttempts > 0, 'maxReconnectAttempts must be > 0'),
        assert(reconnectDelayMs > 0, 'reconnectDelayMs must be > 0'),
        assert(heartbeatIntervalMs >= 0, 'heartbeatIntervalMs must be >= 0');

  /// Creates a config with default settings
  factory KuralitConfig.defaults({
    required String serverUrl,
    required String apiKey,
    required String appId,
    bool debug = false,
  }) {
    return KuralitConfig(
      serverUrl: serverUrl,
      apiKey: apiKey,
      appId: appId,
      debug: debug,
    );
  }

  /// Creates a config optimized for production
  factory KuralitConfig.production({
    required String serverUrl,
    required String apiKey,
    required String appId,
  }) {
    return KuralitConfig(
      serverUrl: serverUrl,
      apiKey: apiKey,
      appId: appId,
      debug: false,
      reconnectEnabled: true,
      maxReconnectAttempts: 10,
      reconnectDelayMs: 1000,
      heartbeatIntervalMs: 30000,
    );
  }

  /// Creates a config optimized for development
  factory KuralitConfig.development({
    required String serverUrl,
    required String apiKey,
    required String appId,
  }) {
    return KuralitConfig(
      serverUrl: serverUrl,
      apiKey: apiKey,
      appId: appId,
      debug: true,
      reconnectEnabled: true,
      maxReconnectAttempts: 5,
      reconnectDelayMs: 500,
      heartbeatIntervalMs: 15000,
    );
  }
}

