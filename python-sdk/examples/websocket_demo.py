"""Demo: Running Kuralit WebSocket Server

This example demonstrates how to start the WebSocket server with the new AgentSession API.

Usage:
    python websocket_server_demo.py

Or with uvicorn:
    uvicorn websocket_server_demo:app --host 0.0.0.0 --port 8000

The server supports three configuration approaches:
1. AgentSession with string-based plugin specs (recommended)
2. AgentSession with direct plugin imports
3. Old ServerConfig approach (backward compatible)

The server will automatically load environment variables from .env file in the root path.
"""

import os
import json
from pathlib import Path

# Load .env file from root path before importing server modules
try:
    from dotenv import load_dotenv
    # load the secrets_env.json file
    with open("secrets_env.json", "r") as f:
        secrets = json.load(f)
    for key, value in secrets.items():
        os.environ[key] = value
    
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    print("   Continuing without .env file support...")
except FileNotFoundError:
    print("⚠️  secrets_env.json not found. Using environment variables only.")

from kuralit.server.agent_session import AgentSession
from kuralit.server.config import ServerConfig
from kuralit.server.websocket_server import create_app

# API key validator function
def validate_api_key(api_key: str) -> bool:
    """Validate API key.
    
    In production, this should check against a database or secret store.
    For demo purposes, we'll use an environment variable.
    """
    expected_key = os.getenv("KURALIT_API_KEY", "demo-api-key")
    return api_key == expected_key

if __name__ == "__main__":
    import uvicorn
    
    # Load Postman collection if provided
    tools = []
    postman_collection_path = "postman.json"
    
    if postman_collection_path:
        try:
            from kuralit.tools.api import RESTAPIToolkit
            from pathlib import Path
            
            collection_path = Path(postman_collection_path)
            if not collection_path.is_absolute():
                resolved_path = Path.cwd() / collection_path
                if resolved_path.exists():
                    collection_path = resolved_path.resolve()
                else:
                    script_dir = Path(__file__).parent
                    resolved_path = script_dir / collection_path
                    if resolved_path.exists():
                        collection_path = resolved_path.resolve()
            
            if collection_path and collection_path.exists():
                api_toolkit = RESTAPIToolkit.from_postman_collection(
                    collection_path=str(collection_path),
                    base_url="http://localhost:35814"
                )
                tools.append(api_toolkit)
        except Exception as e:
            print(f"⚠️  Failed to load Postman collection: {e}")
    
    # Create AgentSession
    agent_session = AgentSession(
        stt="deepgram/nova-2:en-US",
        llm="gemini/gemini-2.0-flash-001",
        vad="silero/v3",
        turn_detection="multilingual/v1",
        instructions="You are a helpful assistant with access to realtime communication. "
                    "Provide clear, concise, and helpful responses.",
        name="Kuralit Demo Agent",
        tools=tools if tools else None,
    )
    
    app = create_app(
        api_key_validator=validate_api_key,
        agent_session=agent_session,
    )
    
    config = agent_session._config.server if agent_session._config else ServerConfig()
    
    print("🚀 Starting WebSocket server...")
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level=config.log_level.lower(),
    )

