<div align="center">
  <a href="https://kuralit.com">
    <img src="docs/logo/kuralit-w.jpeg" alt="Kuralit Logo" width="200"/>
  </a>
</div>

<div align="center">

[Documentation](https://docs.kuralit.com) • [Examples](docs/python-sdk/examples/) • [Website](https://kuralit.com)

</div>

# Kuralit - World's 1<sup>st</sup> AI Agent for Mobile Apps

Kuralit is the world's 1<sup>st</sup> AI agent for mobile apps, enabling you to build intelligent agents with real-time communication capabilities. The framework provides both Python and Flutter SDKs for building AI-powered applications with WebSocket support, tool calling, and voice interaction.

## Overview

Kuralit consists of two main SDKs:

- **Python SDK** - Server-side framework for building AI agents with WebSocket servers, tool integration, and plugin architecture
- **Flutter SDK** - Client-side SDK for Flutter applications with real-time communication, audio streaming, and pre-built UI components

## Features

### Core Capabilities

- **World's 1<sup>st</sup> AI Agent for Mobile Apps** - Create intelligent agents with customizable instructions and tool support
- **Tool System** - Build and organize tools using Functions and Toolkits
- **Plugin Architecture** - Modular plugins for LLM, STT, VAD, and turn detection
- **WebSocket Server** - Real-time bidirectional communication for text and audio
- **REST API Tools** - Automatically generate tools from Postman collections or OpenAPI specs
- **Speech-to-Text** - Support for multiple STT providers (Deepgram, Google Cloud Speech)
- **Voice Activity Detection** - Built-in VAD support with Silero
- **Turn Detection** - Multilingual turn detection for natural conversations
- **Type-Safe** - Full type hints and Pydantic validation
- **Minimal Dependencies** - Core packages have only essential dependencies

### Python SDK Features

- Standalone agent framework with no external dependencies
- WebSocket server with FastAPI
- Plugin system for LLM, STT, VAD, and turn detection
- REST API toolkit generation from Postman collections
- Real-time audio streaming and processing
- Comprehensive examples and documentation

### Flutter SDK Features

- WebSocket client with automatic reconnection
- Text and audio streaming support
- Pre-built UI templates (Popup Chat, Agent Overlay)
- Event-driven architecture
- Tool call handling
- Debug mode with comprehensive logging

## Quick Start

### Python SDK

```bash
# Install the Python SDK (includes all features)
pip install kuralit
```

```python
from kuralit.server import create_app
from kuralit.server.agent_session import AgentSession

# Create agent session
agent = AgentSession(
    stt="deepgram/nova-2:en-US",
    llm="gemini/gemini-2.0-flash-001",
    vad="silero/v3",
    turn_detection="multilingual/v1",
    instructions="You are a helpful assistant."
)

# Create FastAPI app
app = create_app(
    api_key_validator=lambda key: key == "your-secret-key",
    agent_session=agent
)

# Run with: uvicorn app:app --host 0.0.0.0 --port 8000
```

See the [Python SDK README](python-sdk/README.md) for more details.

### Flutter SDK

```yaml
# Add to pubspec.yaml
dependencies:
  kuralit_sdk: ^1.0.0
```

Or install from [pub.dev](https://pub.dev/packages/kuralit_sdk):

```dart
import 'package:kuralit_sdk/kuralit.dart';

// Initialize SDK
await Kuralit.init(KuralitConfig(
  serverUrl: 'wss://api.kuralit.com/ws',
  apiKey: 'your-api-key',
  appId: 'your-app-id',
));

// Connect and send messages
await Kuralit.connect();
final sessionId = Kuralit.generateSessionId();
await Kuralit.sendText(sessionId, 'Hello, Kuralit!');
```

See the [Flutter SDK README](flutter-sdk/README.md) for more details.

## Architecture

```mermaid
graph TD
    subgraph PythonSDK
        subgraph Core
            PluginRegistry
            PluginResolver
        end
        subgraph Models
            Message
            Model
            ModelResponse
            Metrics
        end
        subgraph Agent_
            Agent
        end
        subgraph Tools
            Function
            Toolkit
        end
        subgraph Config
            ConfigManager
            LLMConfig
            STTConfig
            VADConfig
            TurnDetectorConfig
            AgentConfig
            ToolsConfig
            ServerConfig
        end
    end

    subgraph FlutterSDK
        subgraph Templates
            KuralitPopupChat
            KuralitAgentOverlay
        end
        subgraph Audio
            AudioRecorderService
            AudioStreamer
        end
        subgraph Core
            KuralitClient
            KuralitConfig
            KuralitEvents
        end
    end

    PythonSDK --> FlutterSDK
    Core --> Models
    Core --> Agent
    Core --> Tools
    Core --> Config
    FlutterSDK --> Templates
    FlutterSDK --> Audio
    FlutterSDK --> Core
```

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- [Getting Started](docs/getting-started/)
- [Python SDK Documentation](docs/python-sdk/)
- [Flutter SDK Documentation](docs/flutter-sdk/)
- [API Reference](docs/python-sdk/api-reference/)
- [Examples](docs/python-sdk/examples/)

## SDKs

### Python SDK

The Python SDK provides server-side capabilities for building AI agents:

- **Location**: [`python-sdk/`](python-sdk/)
- **Installation**: `pip install kuralit`
- **Documentation**: [Python SDK README](python-sdk/README.md)
- **Examples**: [`python-sdk/examples/`](python-sdk/examples/)

### Flutter SDK

The Flutter SDK provides client-side capabilities for mobile and web applications:

- **Package**: [kuralit_sdk on pub.dev](https://pub.dev/packages/kuralit_sdk)
- **Location**: [`flutter-sdk/`](flutter-sdk/)
- **Installation**: Add to `pubspec.yaml`
- **Documentation**: [Flutter SDK README](flutter-sdk/README.md)
- **Examples**: [`flutter-sdk/example/`](flutter-sdk/example/)

## Examples

### Python SDK Examples

- `minimal_server.py` - Simplest WebSocket server setup
- `simple_tools_demo.py` - Basic agent with tools
- `websocket_demo.py` - WebSocket server example
- `voice_assistant_demo.py` - Voice assistant with STT
- `postman_api_demo.py` - Using Postman collections as tools
- `customer_support_agent.py` - Customer support agent example

### Flutter SDK Examples

- `basic` - Basic text chat implementation
- `popup_chat` - Popup chat dialog example
- `agent_overlay` - Agent overlay interface example
- `protocol` - Low-level protocol usage example

## What's Next

We're continuously working on expanding Kuralit's capabilities. Here's what's coming soon:

1. **React Native SDK** - Native mobile app support for React Native applications
2. **Firebase Integration** - Seamless integration with Firebase services for enhanced functionality

## Requirements

### Python SDK
- Python 3.10+
- Core dependencies: `pydantic`, `docstring-parser`
- Optional dependencies based on features used

### Flutter SDK
- Dart SDK: `>=2.17.0 <4.0.0`
- Flutter: `>=3.0.0`

## License

This software is licensed under a **Non-Commercial License**.

**You may:**
- Use the software for personal, non-commercial purposes
- Modify and distribute the software for non-commercial use
- Use the software for educational purposes

**You may NOT:**
- Use the software for commercial purposes
- Sell the software or derivative works
- Use the software in a commercial product or service

For commercial licensing, please contact the copyright holder.

See [LICENSE](LICENSE) for full terms.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to the project.

Key areas where contributions are welcome:
- Bug fixes and improvements
- New features and plugins
- Documentation improvements
- Example applications
- Test coverage

## Security

For security vulnerabilities, please see [SECURITY.md](SECURITY.md) for information on how to report them responsibly.

## Support

- **Documentation**: Check the `docs/` directory for comprehensive guides
- **Issues**: [GitHub Issues](https://github.com/kuralit/kuralit/issues)
- **Questions**: Open a discussion on GitHub
- **Commercial Licensing**: Contact hello@kuralit.com

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.

---

**Note**: This framework is for non-commercial use only. For commercial licensing, please contact the maintainers at hello@kuralit.com.

