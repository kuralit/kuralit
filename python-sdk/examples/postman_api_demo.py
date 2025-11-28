"""Postman API Demo - REST API Tools from Postman Collections

This example demonstrates how to load REST API tools from a Postman collection
and use them with a KuralIt agent. The agent can then make API calls based on
user requests.

Usage:
    python examples/postman_api_demo.py

Or with a custom Postman collection:
    python examples/postman_api_demo.py --collection path/to/collection.json

Required Environment Variables (set in .env file or environment):
    - DEEPGRAM_API_KEY: API key for Deepgram STT service
    - GEMINI_API_KEY: API key for Google Gemini LLM
    - KURALIT_API_KEY: API key for client authentication (defaults to "demo-api-key")
    - API_BASE_URL: Base URL for the API (defaults to "http://localhost:35814")

Optional:
    - Postman collection JSON file (default: postman.json in project root)

How it works:
    1. Loads a Postman collection JSON file
    2. Converts each API endpoint to a tool
    3. Agent can use these tools to make API calls
    4. User can ask natural language questions that trigger API calls

Example interactions:
    - "Get all notes" → Calls GET /notes
    - "Create a note titled 'Meeting Notes'" → Calls POST /notes
    - "Update note 123" → Calls PUT /notes/123
"""

import os
import argparse
from pathlib import Path

# Step 1: Import required modules
from kuralit.server.agent_session import AgentSession
from kuralit.server.config import ServerConfig
from kuralit.server.websocket_server import create_app


# Step 2: API key validator function
def validate_api_key(api_key: str) -> bool:
    """Validate API key from client connection."""
    expected_key = os.getenv("KURALIT_API_KEY", "demo-api-key")
    return api_key == expected_key


if __name__ == "__main__":
    import uvicorn
    
    # Step 5: Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="KuralIt WebSocket Server with Postman API Tools"
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="postman.json",
        help="Path to Postman collection JSON file (default: postman.json)"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=os.getenv("API_BASE_URL", "http://localhost:35814"),
        help="Base URL for the API (default: http://localhost:35814)"
    )
    args = parser.parse_args()
    
    # Step 4: Load Postman collection and create API toolkit
    tools = []
    collection_path = Path(args.collection)
    
    # Resolve path - try absolute, then relative to current directory, then project root
    if not collection_path.is_absolute():
        if not collection_path.exists():
            # Try project root
            project_root = Path(__file__).parent.parent
            collection_path = project_root / args.collection
    
    if collection_path.exists():
        try:
            from kuralit.tools.api import RESTAPIToolkit
            
            print(f"📦 Loading Postman collection: {collection_path}")
            
            # Create RESTAPIToolkit from Postman collection
            # This automatically converts each API endpoint to a tool
            api_toolkit = RESTAPIToolkit.from_postman_collection(
                collection_path=str(collection_path),
                base_url=args.base_url
            )
            
            tools.append(api_toolkit)
            print(f"✅ Loaded {len(api_toolkit.get_functions())} API tools from collection")
            
            # List available tools
            print("\n   Available API tools:")
            for func in api_toolkit.get_functions():
                print(f"   - {func.name}: {func.description or 'No description'}")
            print()
            
        except Exception as e:
            print(f"⚠️  Failed to load Postman collection: {e}")
            print("   Continuing without API tools...")
    else:
        print(f"⚠️  Postman collection not found: {args.collection}")
        print("   Continuing without API tools...")
        print("   To use API tools, provide a Postman collection JSON file.")
        print("   You can export one from Postman or create it manually.")
    
    # Step 5: Create AgentSession with API tools
    agent_session = AgentSession(
        stt="deepgram/nova-2:en-US",
        llm="gemini/gemini-2.0-flash-001",
        vad="silero/v3",
        turn_detection="multilingual/v1",
        
        # Pass API toolkit if loaded successfully
        tools=tools if tools else None,
        
        # Instructions for the agent about using API tools
        instructions="You are a helpful assistant with access to REST API tools. "
                    "When users make requests that can be fulfilled by API calls, "
                    "use the appropriate tool. Always explain what you're doing and "
                    "provide clear responses about the results.",
        
        name="API Tools Agent",
    )
    
    # Step 6: Create FastAPI application
    app = create_app(
        api_key_validator=validate_api_key,
        agent_session=agent_session,
    )
    
    # Step 7: Get server configuration
    config = agent_session._config.server if agent_session._config else ServerConfig()
    
    # Step 8: Start the server
    print("🚀 Starting WebSocket server with API tools...")
    print(f"   Host: {config.host}")
    print(f"   Port: {config.port}")
    print(f"   API Base URL: {args.base_url}")
    print(f"   Connect at: ws://{config.host}:{config.port}/ws")
    
    if tools:
        print("\n   The agent can now make API calls based on user requests.")
        print("   Try asking questions that would trigger API endpoints.")
    else:
        print("\n   ⚠️  No API tools loaded. Provide a Postman collection to enable API calls.")
    
    print("\n   Press Ctrl+C to stop the server\n")
    
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level=config.log_level.lower(),
    )

