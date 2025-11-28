import 'dart:async';
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
      title: 'Kuralit Basic Chat',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const ChatScreen(),
    );
  }
}

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  // Text controller for input field
  final TextEditingController _textController = TextEditingController();
  
  // List to store messages
  final List<ChatMessage> _messages = [];
  
  // Connection status
  bool _isConnected = false;
  bool _isLoading = false;
  
  // Session ID for this conversation
  String? _sessionId;
  
  // Event subscription
  StreamSubscription<KuralitEvent>? _eventSubscription;

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
    
    // Listen to SDK events
    _setupEventListener();
    
    // Connect to server
    _connect();
  }

  /// Step 2: Set up event listener to receive messages
  void _setupEventListener() {
    _eventSubscription = Kuralit.events.listen((event) {
      if (!mounted) return;

      // Handle different event types
      if (event is KuralitConnectedEvent) {
        // WebSocket connected successfully
        setState(() {
          _isConnected = true;
        });
        _addSystemMessage('Connected to server');
      } else if (event is KuralitDisconnectedEvent) {
        // WebSocket disconnected
        setState(() {
          _isConnected = false;
        });
        _addSystemMessage('Disconnected from server');
      } else if (event is KuralitServerConnectedEvent) {
        // Server confirmed connection and provided session ID
        setState(() {
          _isConnected = true;
          // Use server session ID if provided
          if (event.sessionId.isNotEmpty) {
            _sessionId = event.sessionId;
          }
        });
        _addSystemMessage('Server connected. Session: ${event.sessionId}');
      } else if (event is KuralitServerTextEvent) {
        // Received final text response from server
        setState(() {
          _isLoading = false;
        });
        _addMessage(event.text, isUser: false);
      } else if (event is KuralitServerPartialEvent) {
        // Received partial/streaming text response
        setState(() {
          _isLoading = true;
        });
        // Update last message if it's a streaming one, or add new
        _updateOrAddStreamingMessage(event.text);
      } else if (event is KuralitErrorEvent) {
        // Error occurred
        setState(() {
          _isLoading = false;
        });
        _addSystemMessage('Error: ${event.message}', isError: true);
        _showError(event.message);
      }
    });
  }

  /// Step 3: Connect to the WebSocket server
  Future<void> _connect() async {
    try {
      await Kuralit.connect();
      setState(() {
        _isConnected = Kuralit.isConnected();
      });
    } catch (e) {
      _showError('Failed to connect: $e');
    }
  }

  /// Step 4: Send a text message
  void _sendMessage() {
    final text = _textController.text.trim();
    if (text.isEmpty || !_isConnected || _sessionId == null) {
      return;
    }

    // Add user message to UI
    _addMessage(text, isUser: true);
    
    // Clear input field
    _textController.clear();
    
    // Set loading state
    setState(() {
      _isLoading = true;
    });

    // Send message to server
    try {
      final sent = Kuralit.sendText(_sessionId!, text);
      if (!sent) {
        setState(() {
          _isLoading = false;
        });
        _showError('Failed to send message');
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      _showError('Error sending message: $e');
    }
  }

  /// Helper: Add a message to the list
  void _addMessage(String text, {required bool isUser}) {
    setState(() {
      _messages.add(ChatMessage(
        text: text,
        isUser: isUser,
        timestamp: DateTime.now(),
      ));
    });
    // Scroll to bottom
    WidgetsBinding.instance.addPostFrameCallback((_) {
      // Scroll logic would go here if using ScrollController
    });
  }

  /// Helper: Add or update streaming message
  void _updateOrAddStreamingMessage(String text) {
    setState(() {
      // Remove any existing streaming message
      _messages.removeWhere((msg) => msg.isStreaming);
      // Add new streaming message
      _messages.add(ChatMessage(
        text: text,
        isUser: false,
        timestamp: DateTime.now(),
        isStreaming: true,
      ));
    });
  }

  /// Helper: Add system message
  void _addSystemMessage(String text, {bool isError = false}) {
    setState(() {
      _messages.add(ChatMessage(
        text: text,
        isUser: false,
        timestamp: DateTime.now(),
        isSystem: true,
        isError: isError,
      ));
    });
  }

  /// Helper: Show error snackbar
  void _showError(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(message),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  void dispose() {
    _eventSubscription?.cancel();
    _textController.dispose();
    // Optionally disconnect when leaving
    // Kuralit.disconnect();
    // Kuralit.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Kuralit Basic Chat'),
        actions: [
          // Connection status indicator
          Container(
            margin: const EdgeInsets.only(right: 16),
            child: Row(
              children: [
                Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: _isConnected ? Colors.green : Colors.red,
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  _isConnected ? 'Connected' : 'Disconnected',
                  style: const TextStyle(fontSize: 12),
                ),
              ],
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // Messages list
          Expanded(
            child: _messages.isEmpty
                ? const Center(
                    child: Text(
                      'Start a conversation!\nSend a message below.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.grey),
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _messages.length,
                    itemBuilder: (context, index) {
                      final message = _messages[index];
                      return _buildMessageBubble(message);
                    },
                  ),
          ),
          
          // Loading indicator
          if (_isLoading)
            const Padding(
              padding: EdgeInsets.all(8.0),
              child: LinearProgressIndicator(),
            ),
          
          // Input area
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              border: Border(
                top: BorderSide(color: Colors.grey.shade300),
              ),
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _textController,
                    decoration: const InputDecoration(
                      hintText: 'Type a message...',
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: (_) => _sendMessage(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  icon: const Icon(Icons.send),
                  onPressed: _isConnected ? _sendMessage : null,
                  color: Colors.blue,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// Build message bubble widget
  Widget _buildMessageBubble(ChatMessage message) {
    if (message.isSystem) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Center(
          child: Text(
            message.text,
            style: TextStyle(
              fontSize: 12,
              color: message.isError ? Colors.red : Colors.grey,
              fontStyle: FontStyle.italic,
            ),
          ),
        ),
      );
    }

    return Align(
      alignment: message.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: message.isUser ? Colors.blue : Colors.grey.shade200,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              message.text,
              style: TextStyle(
                color: message.isUser ? Colors.white : Colors.black87,
                fontSize: 16,
              ),
            ),
            if (message.isStreaming)
              const Padding(
                padding: EdgeInsets.only(top: 4),
                child: Text(
                  '...',
                  style: TextStyle(fontSize: 12, color: Colors.grey),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

/// Simple message model
class ChatMessage {
  final String text;
  final bool isUser;
  final DateTime timestamp;
  final bool isStreaming;
  final bool isSystem;
  final bool isError;

  ChatMessage({
    required this.text,
    required this.isUser,
    required this.timestamp,
    this.isStreaming = false,
    this.isSystem = false,
    this.isError = false,
  });
}
