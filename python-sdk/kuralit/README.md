# Kuralit - Standalone Agent and Tools Framework

A standalone implementation of agents and tools, independent of the agno package. This framework allows you to create AI agents that can use tools to perform actions.

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

### 1. Function (`kuralit.tools.function`)

Represents a single tool that can be called by an agent.

```python
from kuralit.tools import Function

def greet(name: str) -> str:
    """Greet a person by name."""
    return f"Hello, {name}!"

# Create a Function from a callable
greet_tool = Function.from_callable(greet)

# Or create manually
greet_tool = Function(
    name="greet",
    description="Greet a person by name",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "The person's name"}
        },
        "required": ["name"]
    },
    entrypoint=greet
)
```

### 2. Toolkit (`kuralit.tools.toolkit`)

Groups multiple related tools together.

```python
from kuralit.tools import Toolkit

def get_weather(location: str) -> str:
    """Get weather for a location."""
    return f"Weather in {location}: sunny"

def get_time() -> str:
    """Get current time."""
    from datetime import datetime
    return datetime.now().strftime("%H:%M:%S")

# Create a toolkit
utility_tools = Toolkit(
    name="utility_tools",
    tools=[get_weather, get_time],
    instructions="Utility tools for weather and time"
)

# Access registered functions
functions = utility_tools.get_functions()
```

### 3. Agent (`kuralit.agent.agent`)

The main interface that uses models and tools.

```python
from kuralit.agent import Agent
from kuralit.tools import Toolkit

# Define tools
def calculate(expression: str) -> str:
    """Calculate a mathematical expression."""
    return str(eval(expression))

# Create toolkit
math_tools = Toolkit(name="math", tools=[calculate])

# Create agent (you need to provide a model)
agent = Agent(
    model=your_model,  # Model instance
    name="Math Agent",
    instructions="You are a helpful math assistant",
    tools=[math_tools]
)

# Use the agent
response = agent.run("What is 15 * 23?")
```

## How It Works

### 1. Tool Registration Flow

```
Function/Toolkit → Agent._register_tools() → Agent.functions (dict)
```

When you create an Agent with tools:
- Individual `Function` objects are added directly to `agent.functions`
- `Toolkit` objects are unpacked, and their functions are added to `agent.functions`
- Callables are automatically converted to `Function` objects

### 2. Tool Execution Flow

```
User Query → Agent.run() → Model (with tool definitions) 
    → Model Response (may include function calls)
    → Agent._handle_function_calls()
    → Function execution
    → Results back to model
    → Final response
```

### 3. Tool Definition Format

Tools are converted to a format that models can understand:

```python
{
    "name": "function_name",
    "description": "What the function does",
    "parameters": {
        "type": "object",
        "properties": {
            "param_name": {
                "type": "string",  # or "integer", "number", "boolean", etc.
                "description": "Parameter description"
            }
        },
        "required": ["param_name"]
    }
}
```

## Example: Complete Workflow

```python
from kuralit.agent import Agent
from kuralit.tools import Toolkit, Function

# Step 1: Define tools
def search_web(query: str) -> str:
    """Search the web for information."""
    # Implementation here
    return f"Search results for: {query}"

def get_stock_price(symbol: str) -> str:
    """Get current stock price."""
    # Implementation here
    return f"Price of {symbol}: $100"

# Step 2: Create toolkit
web_tools = Toolkit(
    name="web_tools",
    tools=[search_web, get_stock_price]
)

# Step 3: Create agent (with your model)
agent = Agent(
    model=your_model,
    tools=[web_tools],
    instructions="You are a helpful assistant with web search capabilities"
)

# Step 4: Use the agent
response = agent.run("What's the current price of AAPL?")
agent.print_response("Search for latest AI news")
```

## Integration with REST API Tools

The `kuralit.tools.api` module is designed to dynamically create tools from REST API endpoints. This will allow you to:

1. Load API specifications (OpenAPI/Swagger)
2. Automatically generate Function objects for each endpoint
3. Create a Toolkit with all API endpoints as tools
4. Use the toolkit with an Agent

```python
# Future usage (to be implemented)
from kuralit.tools.api import RESTAPIToolkit

# Load from OpenAPI spec
api_tools = RESTAPIToolkit.from_openapi_spec("api_spec.yaml")

# Or load from Postman collection
api_tools = RESTAPIToolkit.from_postman_collection("collection.json")

# Use with agent
agent = Agent(model=model, tools=[api_tools])
```

## Key Features

- **Standalone**: No dependencies on agno package
- **Simple**: Easy to understand and extend
- **Flexible**: Works with any model that supports function calling
- **Extensible**: Easy to add new tool types
- **Type-safe**: Uses type hints for parameter inference

## Requirements

- Python 3.8+
- pydantic
- docstring-parser (for parsing function docstrings)

## Next Steps

1. Integrate with your model implementation
2. Implement REST API tool generation
3. Add more advanced features (caching, validation, etc.)
4. Create examples with real models

## Differences from Agno

This implementation is simplified and focused on:
- Core agent-tool interaction
- Basic tool management
- Function calling workflow

It does NOT include:
- Database/storage integration
- Session management
- Advanced hooks and middleware
- Team/workflow orchestration
- Knowledge base integration

These can be added as needed without depending on agno.

