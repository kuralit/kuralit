import 'package:flutter/material.dart';
import 'package:kuralit_sdk/kuralit.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Kuralit Popup Chat',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  // Session ID for the conversation
  String? _sessionId;
  
  // Connection status
  bool _isInitialized = false;

  @override
  void initState() {
    super.initState();
    _initializeSDK();
  }

  /// Step 1: Initialize the Kuralit SDK
  void _initializeSDK() {
    // Replace these with your actual values
    const serverUrl = 'wss://api.kuralit.com/ws'; // Your WebSocket server URL
    const apiKey = 'your-api-key-here'; // Your API key
    const appId = 'your-app-id-here'; // Your App ID
    
    // Initialize SDK with configuration
    Kuralit.init(KuralitConfig(
      serverUrl: serverUrl,
      apiKey: apiKey,
      appId: appId,
      debug: true, // Enable debug logging
    ));
    
    // Generate a session ID for this conversation
    _sessionId = Kuralit.generateSessionId();
    
    // Connect to server (optional - can also connect when opening chat)
    _connect();
    
    setState(() {
      _isInitialized = true;
    });
  }

  /// Step 2: Connect to the WebSocket server
  Future<void> _connect() async {
    try {
      await Kuralit.connect();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to connect: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  /// Step 3: Open the popup chat dialog
  void _openChat() {
    if (_sessionId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Session ID not initialized'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    // Use the KuralitPopupChat.show() method to open the chat dialog
    // This is the simplest way - just one line!
    KuralitPopupChat.show(
      context,
      sessionId: _sessionId!,
      // Optional: Customize the chat appearance
      config: KuralitPopupChatConfig(
        // Theme colors
        backgroundColor: Colors.white,
        primaryColor: Colors.blue,
        
        // Enable/disable features
        enableAudioMode: true, // Allow voice input
        enableToolCalls: true, // Show tool calls
        
        // Callback when chat is closed
        onClose: () {
          print('Chat closed');
        },
      ),
    );
  }

  @override
  void dispose() {
    // Clean up when leaving
    // Kuralit.disconnect();
    // Kuralit.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Kuralit Popup Chat Example'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.chat_bubble_outline,
              size: 80,
              color: Colors.blue,
            ),
            const SizedBox(height: 24),
            const Text(
              'Popup Chat Example',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 32),
              child: Text(
                'This example shows how to use the KuralitPopupChat template.\n\n'
                'Just tap the button below to open a ready-made chat dialog!',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.grey,
                ),
              ),
            ),
            const SizedBox(height: 32),
            ElevatedButton.icon(
              onPressed: _isInitialized ? _openChat : null,
              icon: const Icon(Icons.chat),
              label: const Text('Open Chat Dialog'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(
                  horizontal: 32,
                  vertical: 16,
                ),
                textStyle: const TextStyle(fontSize: 18),
              ),
            ),
            if (!_isInitialized)
              const Padding(
                padding: EdgeInsets.only(top: 16),
                child: CircularProgressIndicator(),
              ),
            const SizedBox(height: 48),
            const Text(
              'Features:',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 16),
            _buildFeatureItem('✓ Text messaging'),
            _buildFeatureItem('✓ Voice input (audio mode)'),
            _buildFeatureItem('✓ Real-time responses'),
            _buildFeatureItem('✓ Tool calls display'),
            _buildFeatureItem('✓ Connection status'),
          ],
        ),
      ),
    );
  }

  Widget _buildFeatureItem(String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Text(
        text,
        style: const TextStyle(fontSize: 16, color: Colors.grey),
      ),
    );
  }
}
