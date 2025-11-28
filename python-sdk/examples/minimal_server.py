"""Minimal Server Example - Simplest KuralIt WebSocket Server Setup

This example demonstrates the absolute minimum setup required to run a KuralIt
WebSocket server. This is the simplest possible configuration with no tools,
just basic STT, LLM, VAD, and turn detection.

Usage:
    python examples/minimal_server.py

Or with uvicorn directly:
    uvicorn examples.minimal_server:app --host 0.0.0.0 --port 8000

Required Environment Variables (set in .env file or environment):
    - DEEPGRAM_API_KEY: API key for Deepgram STT service
    - GEMINI_API_KEY: API key for Google Gemini LLM
    - KURALIT_API_KEY: API key for client authentication (defaults to "demo-api-key")

The server will:
    1. Load environment variables from .env file or environment
    2. Create a minimal AgentSession with default plugins
    3. Start a WebSocket server on port 8000
    4. Accept connections with API key authentication
"""

import os

# Step 1: Import required modules
from kuralit.server.agent_session import AgentSession
from kuralit.server.config import ServerConfig
from kuralit.server.websocket_server import create_app


# Step 2: Define API key validator function
# This function validates the API key sent by clients when connecting
def validate_api_key(api_key: str) -> bool:
    """Validate API key from client connection.
    
    In production, this should check against a database or secret store.
    For demo purposes, we use an environment variable or default value.
    
    Args:
        api_key: The API key provided by the client
        
    Returns:
        True if the API key is valid, False otherwise
    """
    # Get expected key from environment or use default for demo
    expected_key = os.getenv("KURALIT_API_KEY", "demo-api-key")
    return api_key == expected_key


if __name__ == "__main__":
    import uvicorn
    
    # Step 3: Create AgentSession with minimal configuration
    # This is the simplest possible setup - no tools, just basic plugins
    # String-based plugin specs are used (recommended approach)
    agent_session = AgentSession(
        # Speech-to-Text: Deepgram Nova-2 model for English (US)
        stt="deepgram/nova-2:en-US",
        
        # Large Language Model: Gemini 2.0 Flash
        llm="gemini/gemini-2.0-flash-001",
        
        # Voice Activity Detection: Silero VAD v3
        vad="silero/v3",
        
        # Turn Detection: Multilingual model v1
        turn_detection="multilingual/v1",
        
        # Basic instructions for the agent
        instructions="You are a helpful assistant. Provide clear, concise, and helpful responses.",
        
        # Agent name (optional, defaults to "WebSocket Agent")
        name="Minimal Server Agent",
        
        # No tools - this is the minimal setup
        tools=None,
    )
    
    # Step 4: Create FastAPI application with WebSocket support
    # The create_app function sets up the WebSocket endpoint and handlers
    app = create_app(
        api_key_validator=validate_api_key,
        agent_session=agent_session,
    )
    
    # Step 5: Get server configuration from AgentSession
    # This extracts the server config (host, port, etc.) from the AgentSession
    config = agent_session._config.server if agent_session._config else ServerConfig()
    
    # Step 6: Start the server
    print("🚀 Starting minimal WebSocket server...")
    print(f"   Host: {config.host}")
    print(f"   Port: {config.port}")
    print(f"   API Key: {os.getenv('KURALIT_API_KEY', 'demo-api-key')}")
    print(f"   Connect at: ws://{config.host}:{config.port}/ws")
    print("\n   Press Ctrl+C to stop the server\n")
    
    # Run the server using uvicorn
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level=config.log_level.lower(),
    )

