/// Example: Integrating Kuralit SDK with App Lifecycle
/// 
/// This example shows how to track app state (foreground/background)
/// and include it in message metadata automatically.

import 'package:flutter/material.dart';
import 'package:kuralit_sdk/kuralit.dart';

class AppLifecycleExample extends StatefulWidget {
  const AppLifecycleExample({super.key});

  @override
  State<AppLifecycleExample> createState() => _AppLifecycleExampleState();
}

class _AppLifecycleExampleState extends State<AppLifecycleExample>
    with WidgetsBindingObserver {
  String? _sessionId;
  bool _isConnected = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    
    // Initialize SDK
    _initializeSDK();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    Kuralit.dispose();
    super.dispose();
  }

  /// App lifecycle observer - automatically tracks app state
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    super.didChangeAppLifecycleState(state);
    
    switch (state) {
      case AppLifecycleState.resumed:
        // App is in foreground
        Kuralit.setAppState('foreground');
        break;
      case AppLifecycleState.paused:
      case AppLifecycleState.inactive:
      case AppLifecycleState.detached:
      case AppLifecycleState.hidden:
        // App is in background
        Kuralit.setAppState('background');
        break;
    }
  }

  Future<void> _initializeSDK() async {
    // Initialize SDK
    Kuralit.init(KuralitConfig(
      serverUrl: 'ws://localhost:8000/ws',
      apiKey: 'your-api-key',
      appId: 'your-app-id',
      debug: true,
    ));

    // Listen to events
    Kuralit.events.listen((event) {
      if (event is KuralitConnectedEvent) {
        setState(() {
          _isConnected = true;
        });
        _sessionId = Kuralit.generateSessionId(prefix: 'user_123');
      } else if (event is KuralitDisconnectedEvent) {
        setState(() {
          _isConnected = false;
        });
      }
    });

    // Connect
    await Kuralit.connect();
  }

  void _sendMessage(String text) {
    if (_sessionId == null) {
      _sessionId = Kuralit.generateSessionId(prefix: 'user_123');
    }

    // Send message with custom metadata
    // Note: Device metadata (platform, app_state, etc.) is automatically included
    Kuralit.sendText(
      _sessionId!,
      text,
      metadata: {
        'source': 'example_app',
        'screen': 'chat_screen',
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Kuralit SDK - App Lifecycle Example'),
      ),
      body: Column(
        children: [
          // Connection status
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
              children: [
                Icon(
                  _isConnected ? Icons.check_circle : Icons.error,
                  color: _isConnected ? Colors.green : Colors.red,
                ),
                const SizedBox(width: 8),
                Text(
                  _isConnected ? 'Connected' : 'Disconnected',
                  style: TextStyle(
                    color: _isConnected ? Colors.green : Colors.red,
                  ),
                ),
              ],
            ),
          ),
          
          // Session ID
          if (_sessionId != null)
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Text('Session: $_sessionId'),
            ),
          
          // Send message button
          ElevatedButton(
            onPressed: _isConnected
                ? () => _sendMessage('Hello from Flutter!')
                : null,
            child: const Text('Send Message'),
          ),
        ],
      ),
    );
  }
}

/// Alternative: Using AppLifecycleListener (Flutter 3.13+)
/// 
/// If you're using Flutter 3.13 or later, you can use AppLifecycleListener:
/// 
/// ```dart
/// AppLifecycleListener(
///   onStateChange: (state) {
///     if (state == AppLifecycleState.resumed) {
///       Kuralit.setAppState('foreground');
///     } else {
///       Kuralit.setAppState('background');
///     }
///   },
/// )
/// ```

