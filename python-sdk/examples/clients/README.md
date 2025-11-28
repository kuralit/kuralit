# Client Examples

This directory contains client examples that connect to KuralIt WebSocket servers.

## Available Clients

### `send_audio_client.py`
A client that streams audio from your microphone to a KuralIt WebSocket server.

**Usage:**
```bash
# First, start a server in another terminal:
python examples/minimal_server.py

# Then, run the client:
python examples/clients/send_audio_client.py
```

**Features:**
- Connects to WebSocket server
- Captures audio from microphone
- Streams audio in real-time
- Receives and displays STT transcriptions
- Receives and displays agent responses

**Configuration:**
- `--server`: WebSocket server URL (default: `ws://localhost:8000/ws`)
- `--api-key`: API key for authentication (default: `demo-api-key`)

## Difference from Server Examples

- **Server examples** (in parent `examples/` directory): Create WebSocket servers that process audio and respond
- **Client examples** (in this directory): Connect to servers and send audio/data

You need to run a server example first, then connect to it using a client example.

