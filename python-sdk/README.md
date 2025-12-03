# Kuralit - World's 1<sup>st</sup> AI Agent for Mobile Apps

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Non--Commercial-red.svg)](LICENSE)

The world's 1<sup>st</sup> AI agent for mobile apps, enabling you to create intelligent agents with tool-calling capabilities. Kuralit provides a clean architecture for building AI assistants that can interact with models, use tools, and handle real-time communication.

## Features

- 🤖 **Agent Framework**: Create AI agents with customizable instructions and tool support
- 🛠️ **Tool System**: Build and organize tools using Functions and Toolkits
- 🔌 **Plugin Architecture**: Modular plugins for LLM, STT, VAD, and more
- 🌐 **WebSocket Server**: Real-time communication support for text and audio
- 📡 **REST API Tools**: Automatically generate tools from Postman collections or OpenAPI specs
- 🎤 **Speech-to-Text**: Support for multiple STT providers (Deepgram, Google Cloud Speech)
- 🔊 **Voice Activity Detection**: Built-in VAD support with Silero
- 🔧 **Type-Safe**: Full type hints and Pydantic validation
- ⚡ **Minimal Dependencies**: Core package has only essential dependencies

## Installation

### Standard Installation

```bash
pip install kuralit
```

This installs all dependencies including:
- Google Gemini LLM support
- WebSocket server support
- Speech-to-Text support
- Voice Activity Detection
- REST API tools support
- And all other features

### Optional: Install Specific Feature Groups

If you only need specific features, you can install them individually:

```bash
pip install kuralit[gemini]      # Only Google Gemini LLM support
pip install kuralit[websocket]    # Only WebSocket server support
pip install kuralit[stt]         # Only Speech-to-Text support
pip install kuralit[vad]         # Only Voice Activity Detection
pip install kuralit[rest]         # Only REST API tools support
```

Note: The standard `pip install kuralit` includes all features by default.

## Quick Start

### Basic Agent with Tools

```python
from kuralit.agent import Agent
from kuralit.tools import Toolkit

# Define a simple tool
def get_weather(location: str) -> str:
    """Get weather for a location."""
    return f"Weather in {location}: sunny, 72°F"

# Create a toolkit
weather_tools = Toolkit(
    name="weather",
    tools=[get_weather],
    instructions="Weather information tools"
)

# Create an agent (you need to provide a model)
agent = Agent(
    model=your_model,  # Your model instance
    name="Weather Assistant",
    instructions="You are a helpful weather assistant",
    tools=[weather_tools]
)

# Use the agent
response = agent.run("What's the weather in San Francisco?")
print(response)
```

### WebSocket Server

```python
from kuralit.server import create_app
from kuralit.server.agent_session import AgentSession
from kuralit.plugins.llm import gemini
from kuralit.plugins.stt import deepgram

# Configure agent session
session = AgentSession(
    llm=gemini.Gemini(api_key="your-key", model_id="gemini-2.0-flash-001"),
    stt=deepgram.DeepgramSTTHandler(api_key="your-key"),
    agent_name="WebSocket Agent",
    agent_instructions="You are a helpful assistant"
)

# Create FastAPI app
app = create_app(
    api_key_validator=lambda key: key == "your-secret-key",
    agent_session=session
)

# Run with: uvicorn app:app --host 0.0.0.0 --port 8000
```

## Architecture

```
┌─────────────┐
│   Agent     │  ← Main interface for interacting with models
└──────┬──────┘
       │ uses
       ▼
┌─────────────┐
│  Toolkit    │  ← Groups related tools together
└──────┬──────┘
       │ contains
       ▼
┌─────────────┐
│  Function   │  ← Represents individual tools (callables)
└─────────────┘
```

## Core Components

### Agent

The main interface that orchestrates model interactions and tool execution.

```python
from kuralit.agent import Agent

agent = Agent(
    model=your_model,
    name="My Agent",
    instructions="You are a helpful assistant",
    tools=[toolkit1, toolkit2]
)
```

### Toolkit

Groups multiple related tools together for better organization.

```python
from kuralit.tools import Toolkit

toolkit = Toolkit(
    name="my_tools",
    tools=[function1, function2, function3],
    instructions="Description of what these tools do"
)
```

### Function

Represents a single tool that can be called by an agent.

```python
from kuralit.tools import Function

# Create from a callable
def my_function(param: str) -> str:
    """Function description."""
    return f"Result: {param}"

tool = Function.from_callable(my_function)
```

## Optional Features

### LLM Plugins

```python
# Google Gemini
from kuralit.plugins.llm import gemini
model = gemini.Gemini(api_key="...", model_id="gemini-2.0-flash-001")
```

### Speech-to-Text

```python
# Deepgram (recommended)
from kuralit.plugins.stt import deepgram
stt = deepgram.DeepgramSTTHandler(api_key="...")

# Google Cloud Speech
from kuralit.plugins.stt import google
stt = google.GoogleSTTHandler(credentials_path="...")
```

### Voice Activity Detection

```python
from kuralit.plugins.vad import silero
vad = silero.SileroVADHandler()
```

### REST API Tools

```python
from kuralit.tools.api import RESTAPIToolkit

# Load from Postman collection
api_tools = RESTAPIToolkit.from_postman_collection("collection.json")

# Use with agent
agent = Agent(model=model, tools=[api_tools])
```

## Requirements

- Python 3.10+
- Core dependencies: `pydantic`, `docstring-parser`
- Optional dependencies based on features used (see installation section)

## Documentation

For detailed documentation, examples, and API reference, please visit the [repository](https://github.com/kuralit/kuralit).

## Examples

Check out the `examples/` directory for complete working examples:

- `simple_tools_demo.py` - Basic agent with tools
- `websocket_demo.py` - WebSocket server example
- `voice_assistant_demo.py` - Voice assistant with STT
- `postman_api_demo.py` - Using Postman collections as tools
- `customer_support_agent.py` - Customer support agent example

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

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/kuralit/kuralit/issues).

## Key Features

- **Standalone**: No dependencies on other agent frameworks
- **Simple**: Easy to understand and extend
- **Flexible**: Works with any model that supports function calling
- **Extensible**: Easy to add new tool types and plugins
- **Type-Safe**: Full type hints and Pydantic validation
- **Production-Ready**: WebSocket server with real-time audio support

---

**Note**: This package is for non-commercial use only. For commercial licensing, please contact the maintainers.

