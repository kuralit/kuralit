"""Audio Client Example - Stream Audio to KuralIt WebSocket Server

This is a CLIENT example that connects to a KuralIt WebSocket server and streams
audio from your microphone. This is different from the server examples which
create WebSocket servers.

This client can be used to test any of the server examples:
- minimal_server.py
- simple_tools_demo.py
- postman_api_demo.py
- voice_assistant_demo.py
- customer_support_agent.py
- websocket_demo.py

Usage:
    # First, start a server in another terminal:
    python examples/minimal_server.py
    
    # Then, in this terminal, run the client:
    python examples/clients/send_audio_client.py

Or with custom server URL:
    python examples/clients/send_audio_client.py --server ws://localhost:8000/ws --api-key demo-api-key

Prerequisites:
    - A KuralIt WebSocket server must be running (use one of the server examples)
    - pip install websockets pyaudio

Configuration:
    - SERVER_URL: WebSocket server URL (default: ws://localhost:8000/ws)
    - API_KEY: API key matching the server configuration (default: demo-api-key)
    - APP_ID: Client application ID (default: python-client-demo)

What this client does:
    1. Connects to the WebSocket server
    2. Captures audio from your microphone
    3. Streams audio chunks to the server
    4. Receives and displays STT transcriptions and agent responses
"""

import asyncio
import base64
import json
import sys
import argparse
import queue
from typing import Optional

try:
    import pyaudio
    import websockets
except ImportError:
    print("❌ Missing dependencies. Please install:")
    print("   pip install websockets pyaudio")
    sys.exit(1)


# Default Configuration
DEFAULT_SERVER_URL = "ws://localhost:8000/ws"
DEFAULT_API_KEY = "demo-api-key"
APP_ID = "python-client-demo"

# Audio Configuration
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 1024  # Frames per buffer
FORMAT = pyaudio.paInt16


class AudioStreamClient:
    """Client for streaming audio to KuralIt WebSocket server.
    
    This client connects to a WebSocket server, captures audio from the microphone,
    and streams it to the server while receiving transcriptions and responses.
    """
    
    def __init__(self, server_url: str, api_key: str):
        """Initialize the audio streaming client.
        
        Args:
            server_url: WebSocket server URL to connect to
            api_key: API key for authentication
        """
        self.server_url = server_url
        self.api_key = api_key
        self.session_id: Optional[str] = None
        self.audio_queue = queue.Queue()
        self.is_running = False
        self.p = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None

    def audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for PyAudio to capture audio data."""
        if self.is_running:
            self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)

    def start_recording(self):
        """Start microphone recording."""
        try:
            self.stream = self.p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE,
                stream_callback=self.audio_callback
            )
            self.is_running = True
            print(f"🎤 Recording started ({SAMPLE_RATE}Hz, Mono)...")
            self.stream.start_stream()
        except Exception as e:
            print(f"❌ Failed to start recording: {e}")
            sys.exit(1)

    def stop_recording(self):
        """Stop microphone recording."""
        self.is_running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()
        print("\n🛑 Recording stopped.")

    async def send_audio(self, websocket):
        """Send audio chunks to the server."""
        # 1. Send Audio Start Message
        start_msg = {
            "type": "client_audio_start",
            "session_id": self.session_id,
            "data": {
                "sample_rate": SAMPLE_RATE,
                "encoding": "PCM16"
            }
        }
        await websocket.send(json.dumps(start_msg))
        print("📤 Sent audio start message")

        # 2. Stream Audio Chunks
        print("📤 Streaming audio... (Press Ctrl+C to stop)")
        try:
            while self.is_running:
                try:
                    # Non-blocking get from queue
                    audio_data = self.audio_queue.get_nowait()
                    
                    # Base64 encode
                    b64_audio = base64.b64encode(audio_data).decode('utf-8')
                    
                    chunk_msg = {
                        "type": "client_audio_chunk",
                        "session_id": self.session_id,
                        "data": {
                            "chunk": b64_audio
                        }
                    }
                    await websocket.send(json.dumps(chunk_msg))
                    # Small sleep to yield control
                    await asyncio.sleep(0.001)
                    
                except queue.Empty:
                    await asyncio.sleep(0.01)
                    
        except Exception as e:
            print(f"❌ Error sending audio: {e}")
        finally:
            # 3. Send Audio End Message
            end_msg = {
                "type": "client_audio_end",
                "session_id": self.session_id,
                "data": {}
            }
            await websocket.send(json.dumps(end_msg))
            print("📤 Sent audio end message")

    async def receive_messages(self, websocket):
        """Receive and print messages from the server."""
        try:
            async for message in websocket:
                data = json.loads(message)
                msg_type = data.get("type")
                
                if msg_type == "server_connected":
                    print(f"✅ Connected! Session ID: {data.get('session_id')}")
                    self.session_id = data.get('session_id')
                    
                elif msg_type == "server_stt":
                    text = data.get("data", {}).get("text", "")
                    print(f"🗣️  STT: {text}")
                    
                elif msg_type == "server_text":
                    text = data.get("data", {}).get("text", "")
                    print(f"🤖 Agent: {text}")
                    
                elif msg_type == "server_error":
                    error = data.get("data", {}).get("message", "Unknown error")
                    print(f"❌ Server Error: {error}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connection closed by server")

    async def run(self):
        """Main run loop - connects to server and streams audio."""
        headers = {
            "x-api-key": self.api_key,
            "x-app-id": APP_ID
        }
        
        print(f"🔌 Connecting to {self.server_url}...")
        print(f"   Make sure a KuralIt server is running at this URL!")
        print()
        
        async with websockets.connect(self.server_url, additional_headers=headers) as websocket:
            # Wait for connection message first
            first_msg = await websocket.recv()
            data = json.loads(first_msg)
            if data.get("type") == "server_connected":
                self.session_id = data.get("session_id")
                print(f"✅ Connected! Session ID: {self.session_id}")
            else:
                print(f"❌ Unexpected first message: {first_msg}")
                return

            # Start recording
            self.start_recording()
            
            # Run send and receive tasks concurrently
            send_task = asyncio.create_task(self.send_audio(websocket))
            recv_task = asyncio.create_task(self.receive_messages(websocket))
            
            try:
                await asyncio.gather(send_task, recv_task)
            except asyncio.CancelledError:
                pass
            finally:
                self.stop_recording()


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="KuralIt Audio Client - Stream audio to WebSocket server"
    )
    parser.add_argument(
        "--server",
        type=str,
        default=DEFAULT_SERVER_URL,
        help=f"WebSocket server URL (default: {DEFAULT_SERVER_URL})"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=DEFAULT_API_KEY,
        help=f"API key for authentication (default: {DEFAULT_API_KEY})"
    )
    args = parser.parse_args()
    
    # Create and run client
    client = AudioStreamClient(args.server, args.api_key)
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
        client.stop_recording()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   Make sure a KuralIt server is running at the specified URL.")
        client.stop_recording()

