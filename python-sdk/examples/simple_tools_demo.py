"""Simple Tools Demo - Custom Python Functions as Tools

This example demonstrates how to create custom Python functions as tools and
use them with a Kuralit agent. It shows:
- Creating simple utility functions (calculator, time, weather, currency)
- Converting functions to tools using Function.from_callable()
- Creating a Toolkit to group related tools
- Passing tools to AgentSession
- Agent using tools in conversation

Usage:
    python examples/simple_tools_demo.py

Required Environment Variables (set in .env file or environment):
    - DEEPGRAM_API_KEY: API key for Deepgram STT service
    - GEMINI_API_KEY: API key for Google Gemini LLM
    - KURALIT_API_KEY: API key for client authentication (defaults to "demo-api-key")

Example interactions:
    - "What's 25 times 17?" → Uses calculate tool
    - "What time is it?" → Uses get_current_time tool
    - "What's the weather in London?" → Uses get_weather tool
    - "Convert 100 USD to EUR" → Uses convert_currency tool
"""

import os
from datetime import datetime
from typing import Optional

# Step 1: Import required modules
from kuralit.server.agent_session import AgentSession
from kuralit.server.config import ServerConfig
from kuralit.server.websocket_server import create_app
from kuralit.tools.toolkit import Toolkit


# Step 2: Define custom tool functions
# These are regular Python functions that will be converted to tools
# The function docstrings and type hints are automatically used to create
# the tool schema that the LLM understands

def calculate(expression: str) -> str:
    """Calculate a mathematical expression.
    
    This function evaluates a mathematical expression and returns the result.
    Supports basic arithmetic operations: +, -, *, /, and parentheses.
    
    Args:
        expression: A string containing a mathematical expression
                   (e.g., "15 * 23 + 10", "(100 + 50) / 2")
    
    Returns:
        The result of the calculation as a string
        
    Example:
        calculate("15 * 23") returns "345"
    """
    try:
        # WARNING: Using eval() is for demo purposes only
        # In production, use a proper expression parser for security
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error calculating expression: {str(e)}"


def get_current_time() -> str:
    """Get the current time.
    
    Returns the current time in a human-readable format.
    
    Returns:
        Current time as a formatted string (e.g., "14:30:45")
    """
    now = datetime.now()
    return now.strftime("%H:%M:%S")


def get_weather(location: str) -> str:
    """Get weather information for a location.
    
    This is a mock implementation that returns simulated weather data.
    In production, you would call a real weather API (e.g., OpenWeatherMap).
    
    Args:
        location: The name of the city or location
        
    Returns:
        Weather information as a formatted string
    """
    # Mock weather data - in production, call a real API
    mock_weather = {
        "london": "Cloudy, 15°C",
        "new york": "Sunny, 22°C",
        "tokyo": "Rainy, 18°C",
        "paris": "Partly cloudy, 16°C",
    }
    
    location_lower = location.lower()
    weather = mock_weather.get(location_lower, f"Partly cloudy, 20°C")
    return f"Weather in {location}: {weather}"


def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert currency from one type to another.
    
    This is a mock implementation with fixed exchange rates.
    In production, you would call a real currency API (e.g., ExchangeRate-API).
    
    Args:
        amount: The amount to convert
        from_currency: Source currency code (e.g., "USD", "EUR")
        to_currency: Target currency code (e.g., "USD", "EUR")
        
    Returns:
        Conversion result as a formatted string
    """
    # Mock exchange rates - in production, fetch from a real API
    exchange_rates = {
        "USD": {"EUR": 0.85, "GBP": 0.73, "JPY": 110.0},
        "EUR": {"USD": 1.18, "GBP": 0.86, "JPY": 129.0},
        "GBP": {"USD": 1.37, "EUR": 1.16, "JPY": 150.0},
    }
    
    # If same currency, no conversion needed
    if from_currency.upper() == to_currency.upper():
        return f"{amount} {from_currency.upper()} = {amount} {to_currency.upper()}"
    
    # Get exchange rate
    from_curr = from_currency.upper()
    to_curr = to_currency.upper()
    
    if from_curr in exchange_rates and to_curr in exchange_rates[from_curr]:
        rate = exchange_rates[from_curr][to_curr]
        converted = amount * rate
        return f"{amount} {from_curr} = {converted:.2f} {to_curr}"
    else:
        return f"Exchange rate not available for {from_curr} to {to_curr}"


# Step 3: API key validator function
def validate_api_key(api_key: str) -> bool:
    """Validate API key from client connection."""
    expected_key = os.getenv("KURALIT_API_KEY", "demo-api-key")
    return api_key == expected_key


if __name__ == "__main__":
    import uvicorn
    
    # Step 4: Create a Toolkit with our custom functions
    # A Toolkit groups related tools together and provides instructions
    # about when and how to use them
    utility_tools = Toolkit(
        name="utility_tools",
        tools=[calculate, get_current_time, get_weather, convert_currency],
        instructions="Utility tools for calculations, time, weather, and currency conversion. "
                    "Use these tools when the user asks about math, time, weather, or currency.",
    )
    
    # Step 5: Create AgentSession with tools
    # The tools parameter accepts a list of Toolkits or Functions
    agent_session = AgentSession(
        stt="deepgram/nova-2:en-US",
        llm="gemini/gemini-2.0-flash-001",
        vad="silero/v3",
        turn_detection="multilingual/v1",
        
        # Pass our toolkit to the agent
        tools=[utility_tools],
        
        # Instructions that tell the agent about available tools
        instructions="You are a helpful assistant with access to utility tools. "
                    "You can perform calculations, tell the time, get weather information, "
                    "and convert currencies. Use the appropriate tool when users ask for "
                    "these services. Always provide clear and helpful responses.",
        
        name="Utility Tools Agent",
    )
    
    # Step 6: Create FastAPI application
    app = create_app(
        api_key_validator=validate_api_key,
        agent_session=agent_session,
    )
    
    # Step 7: Get server configuration
    config = agent_session._config.server if agent_session._config else ServerConfig()
    
    # Step 8: Start the server
    print("🚀 Starting WebSocket server with utility tools...")
    print(f"   Host: {config.host}")
    print(f"   Port: {config.port}")
    print(f"   Available tools: calculate, get_current_time, get_weather, convert_currency")
    print(f"   Connect at: ws://{config.host}:{config.port}/ws")
    print("\n   Try asking:")
    print("   - 'What's 25 times 17?'")
    print("   - 'What time is it?'")
    print("   - 'What's the weather in London?'")
    print("   - 'Convert 100 USD to EUR'")
    print("\n   Press Ctrl+C to stop the server\n")
    
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level=config.log_level.lower(),
    )

