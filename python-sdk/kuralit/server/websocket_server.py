"""FastAPI WebSocket server for Kuralit."""

import asyncio
import json
import logging
import time
from typing import Callable, Dict, Optional
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse

from kuralit.server.agent_handler import AgentHandler
from kuralit.server.agent_session import AgentSession
from kuralit.server.config import ServerConfig
from kuralit.server.exceptions import (
    AgentError,
    AudioProcessingError,
    AuthenticationError,
    ConnectionError,
    MessageValidationError,
    SessionNotFoundError,
    STTError,
    WebSocketError,
)
from kuralit.server.metrics import MetricsCollector
from kuralit.server.protocol import (
    ClientAudioChunkMessage,
    ClientAudioEndMessage,
    ClientAudioStartMessage,
    ClientTextMessage,
    parse_client_message,
    ServerConnectedMessage,
    ServerErrorMessage,
    ServerMessage,
    ServerSTTMessage,
)
from kuralit.server.session import Session
from kuralit.server.event_bus import EventBus, get_event_bus, Event
from kuralit.server.dashboard_utils import (
    get_all_sessions,
    get_agent_config,
    metrics_to_ui_format,
)
from kuralit.core.plugin_registry import PluginRegistry
from kuralit.plugins.stt.deepgram import DeepgramSTTHandler
from kuralit.plugins.stt.google import GoogleSTTHandler
from typing import Union

# Type alias for STT handlers
STTHandler = Union[DeepgramSTTHandler, GoogleSTTHandler]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global state
sessions: Dict[str, Session] = {}
connections: Dict[str, WebSocket] = {}
metrics_collector = MetricsCollector()
event_bus: EventBus = get_event_bus()  # Global event bus for dashboard updates


def create_app(
    api_key_validator: Callable[[str], bool],
    agent_session: Optional[AgentSession] = None,
    config: Optional[ServerConfig] = None,
) -> FastAPI:
    """Create FastAPI app with WebSocket endpoint.
    
    Args:
        api_key_validator: Function to validate API keys
        agent_session: Optional AgentSession configuration (takes precedence)
        config: Optional server configuration (fallback if agent_session not provided)
        
    Returns:
        FastAPI application
    """
    # Use AgentSession if provided, otherwise use config
    if agent_session:
        # Extract config from AgentSession or create default
        if agent_session._config:
            config = agent_session._config.server
        else:
            config = ServerConfig()
        config.api_key_validator = api_key_validator
        # Don't validate here - AgentSession handles its own validation
    else:
        # Fallback to old config-based approach
        if config is None:
            config = ServerConfig()
            config.api_key_validator = api_key_validator
        
        config.api_key_validator = api_key_validator
        config.validate()
    
    app = FastAPI(
        title="Kuralit WebSocket Server",
        description="Realtime text and audio communication server",
        version="1.0.0",
    )
    
    # Initialize handlers
    # Use AgentSession handlers if provided, otherwise use config-based initialization
    stt_handler = None
    if agent_session and agent_session.stt:
        # Use STT handler from AgentSession
        stt_handler = agent_session.stt
        logger.info(f"Using STT handler from AgentSession: {type(stt_handler).__name__}")
    elif hasattr(config, 'stt_enabled') and config.stt_enabled:
        # Fallback to old config-based approach (old ServerConfig has stt_enabled)
        try:
            if config.stt_provider == "deepgram":
                logger.info("Using Deepgram STT (recommended)")
                stt_handler = DeepgramSTTHandler(config)
                logger.info("Deepgram STT handler initialized successfully")
            elif config.stt_provider == "google":
                logger.info("Using Google STT")
                stt_handler = GoogleSTTHandler(config)
                logger.info("Google STT handler initialized successfully")
            else:
                raise ValueError(f"Unknown STT provider: {config.stt_provider}")
        except STTError as e:
            logger.warning(f"STT initialization failed: {e.message}. STT features will be disabled.")
            stt_handler = None
            # Optionally disable STT in config to prevent retry attempts
            if hasattr(config, 'stt_enabled'):
                config.stt_enabled = False
        except Exception as e:
            logger.warning(f"STT initialization failed: {e}. STT features will be disabled.")
            stt_handler = None
            if hasattr(config, 'stt_enabled'):
                config.stt_enabled = False
    
    # VAD handler - check if model is available at startup
    # When using AgentSession, VAD handler is already provided, so skip this check
    vad_handler_available = False
    if agent_session and agent_session.vad:
        # VAD handler provided by AgentSession - no need to check availability
        vad_handler_available = True
        logger.info("VAD handler provided by AgentSession")
    elif hasattr(config, 'vad_enabled') and config.vad_enabled:
        # Use plugin registry to check VAD availability
        try:
            vad_plugin = PluginRegistry.get_vad_plugin("silero")
            if vad_plugin:
                vad_handler_available = True
                logger.info("VAD plugin is available and will be enabled")
            else:
                logger.warning("VAD plugin not found. VAD will be disabled.")
                config.vad_enabled = False
        except Exception as e:
            logger.warning(f"VAD plugin not available: {e}. VAD will be disabled.")
            config.vad_enabled = False
    
    # Turn Detector handler - check if model is available at startup
    # When using AgentSession, Turn Detector handler is already provided, so skip this check
    turn_detector_handler_available = False
    if agent_session and agent_session.turn_detection:
        # Turn Detector handler provided by AgentSession - no need to check availability
        turn_detector_handler_available = True
        logger.info("Turn Detector handler provided by AgentSession")
    elif hasattr(config, 'turn_detector_enabled') and config.turn_detector_enabled:
        # Use plugin registry to check Turn Detector availability
        try:
            turn_detector_plugin = PluginRegistry.get_turn_detector_plugin("multilingual")
            if turn_detector_plugin:
                turn_detector_handler_available = True
                logger.info("Turn Detector plugin is available and will be enabled")
            else:
                logger.warning("Turn Detector plugin not found. Turn Detector will be disabled.")
                config.turn_detector_enabled = False
        except Exception as e:
            logger.warning(f"Turn Detector plugin not available: {e}. Turn Detector will be disabled.")
            config.turn_detector_enabled = False
    
    # Initialize AgentHandler - use AgentSession if provided
    if agent_session:
        agent_handler = AgentHandler(agent_session=agent_session, config=config, metrics=metrics_collector, event_bus=event_bus)
    else:
        agent_handler = AgentHandler(config=config, metrics=metrics_collector, event_bus=event_bus)
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "active_connections": metrics_collector.server_metrics.active_connections,
        }
    
    @app.get("/metrics")
    async def get_metrics():
        """Metrics endpoint."""
        if not config.enable_metrics:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "Metrics disabled"}
            )
        return metrics_collector.server_metrics.to_dict()
    
    # Dashboard API endpoints
    @app.get("/api/sessions")
    async def get_sessions():
        """Get list of active sessions."""
        try:
            # Authenticate (optional - can add API key check here)
            sessions_list = get_all_sessions(sessions)
            return {
                "sessions": sessions_list,
                "count": len(sessions_list),
            }
        except Exception as e:
            logger.error(f"[API] Error getting sessions: {e}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Failed to get sessions", "message": str(e)}
            )
    
    @app.get("/api/sessions/{session_id}")
    async def get_session(session_id: str):
        """Get details of a specific session."""
        try:
            if session_id not in sessions:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"error": "Session not found"}
                )
            
            session = sessions[session_id]
            from kuralit.server.dashboard_utils import session_to_conversation
            conversation = session_to_conversation(session)
            
            return conversation
        except Exception as e:
            logger.error(f"[API] Error getting session {session_id}: {e}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Failed to get session", "message": str(e)}
            )
    
    @app.get("/api/sessions/{session_id}/history")
    async def get_session_history(session_id: str):
        """Get conversation history for a session."""
        try:
            if session_id not in sessions:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"error": "Session not found"}
                )
            
            session = sessions[session_id]
            from kuralit.server.dashboard_utils import session_to_conversation
            conversation = session_to_conversation(session)
            
            return {
                "session_id": session_id,
                "history": conversation["items"],
                "count": len(conversation["items"]),
            }
        except Exception as e:
            logger.error(f"[API] Error getting session history {session_id}: {e}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Failed to get session history", "message": str(e)}
            )
    
    @app.get("/api/dashboard/metrics")
    async def get_dashboard_metrics():
        """Get metrics in dashboard format."""
        try:
            metrics = metrics_to_ui_format(metrics_collector)
            return {
                "metrics": metrics,
                "server_metrics": metrics_collector.server_metrics.to_dict(),
            }
        except Exception as e:
            logger.error(f"[API] Error getting dashboard metrics: {e}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Failed to get metrics", "message": str(e)}
            )
    
    @app.get("/api/config")
    async def get_config():
        """Get agent configuration."""
        try:
            config_dict = get_agent_config(agent_handler)
            return config_dict
        except Exception as e:
            logger.error(f"[API] Error getting config: {e}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Failed to get config", "message": str(e)}
            )
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for realtime communication."""
        connection_id = str(uuid4())
        session: Optional[Session] = None
        
        try:
            # Accept connection
            await websocket.accept()
            logger.info(f"[WS] Connection accepted: connection={connection_id}")
            
            # Authenticate
            api_key = websocket.headers.get("x-api-key") or websocket.headers.get("X-Api-Key")
            app_id = websocket.headers.get("x-app-id") or websocket.headers.get("X-App-Id")
            
            if not api_key or not config.api_key_validator(api_key):
                logger.warning(f"[WS] Invalid API key: connection={connection_id}")
                raise AuthenticationError("Invalid API key")
            
            if not app_id:
                logger.warning(f"[WS] Missing x-app-id header: connection={connection_id}")
                raise AuthenticationError("Missing x-app-id header")
            
            # Record connection
            metrics_collector.increment_connection()
            connections[connection_id] = websocket
            
            # Send connection confirmation
            initial_session_id = str(uuid4())
            # Pass handlers from AgentSession if available
            session = Session(
                session_id=initial_session_id,
                config=config,
                _vad_handler=agent_session.vad if agent_session else None,
                _turn_detector_handler=agent_session.turn_detection if agent_session else None,
            )
            sessions[initial_session_id] = session
            metrics_collector.create_session_metrics(initial_session_id)
            
            logger.info(f"[WS] Authenticated: connection={connection_id}, session={initial_session_id}, app_id={app_id}")
            
            await send_message(
                websocket,
                ServerConnectedMessage.create(
                    session_id=initial_session_id,
                    metadata={"app_id": app_id, "connection_id": connection_id}
                ),
                config=config
            )
            
            # Main message loop
            while True:
                try:
                    # Receive message
                    raw_message = await websocket.receive_text()
                    
                    # Log incoming request (only at DEBUG level to reduce noise)
                    logger.debug(f"[WS] Received message: connection={connection_id}, session={session.session_id if session else 'unknown'}")
                    
                    # Parse message
                    try:
                        message_data = json.loads(raw_message)
                        client_message = parse_client_message(message_data)
                        logger.debug(f"[WS] Parsed message: type={client_message.type}, session={client_message.session_id}")
                    except json.JSONDecodeError as e:
                        logger.error(f"[WS] JSON decode error: {e}")
                        error_msg = f"Invalid JSON: {str(e)}"
                        # Provide helpful hint for common quote escaping issues
                        if "Expecting ',' delimiter" in str(e) or "Unterminated string" in str(e):
                            error_msg += ". Hint: Make sure to escape double quotes inside strings (use \\\" instead of \")"
                        raise MessageValidationError(error_msg)
                    except Exception as e:
                        if isinstance(e, MessageValidationError):
                            logger.error(f"[WS] Validation error: {e}")
                            raise
                        logger.error(f"[WS] Parse error: {e}")
                        raise MessageValidationError(f"Failed to parse message: {str(e)}")
                    
                    # Get or create session
                    if client_message.session_id not in sessions:
                        # Pass handlers from AgentSession if available
                        session = Session(
                            session_id=client_message.session_id,
                            config=config,
                            _vad_handler=agent_session.vad if agent_session else None,
                            _turn_detector_handler=agent_session.turn_detection if agent_session else None,
                        )
                        sessions[client_message.session_id] = session
                        metrics_collector.create_session_metrics(client_message.session_id)
                        
                        # Emit session_created event
                        await event_bus.publish(
                            event_type="session_created",
                            session_id=session.session_id,
                            data={
                                "session_id": session.session_id,
                                "created_at": session.created_at,
                                "user_metadata": session.user_metadata,
                            }
                        )
                    else:
                        session = sessions[client_message.session_id]
                    
                    session.update_activity()
                    
                    # Handle message by type
                    # Note: metrics_updated will be emitted after agent response completes
                    if isinstance(client_message, ClientTextMessage):
                        # Record user text message in metrics (only actual messages, not audio signals)
                        metrics_collector.record_message(session.session_id)
                        
                        logger.info(f"[WS] Text message: session={session.session_id}, length={len(client_message.text)}")
                        
                        # Emit message_received event
                        logger.info(f"[WS] Publishing message_received event: session={session.session_id}, subscribers={event_bus.get_subscriber_count()}")
                        await event_bus.publish(
                            event_type="message_received",
                            session_id=session.session_id,
                            data={
                                "text": client_message.text,
                                "metadata": client_message.metadata or {},
                                "message_length": len(client_message.text),
                            }
                        )
                        logger.debug(f"[WS] message_received event published: session={session.session_id}")
                        
                        await handle_text_message(
                            websocket,
                            session,
                            client_message,
                            agent_handler,
                            config,
                        )
                    elif isinstance(client_message, ClientAudioStartMessage):
                        logger.info(f"[WS] Audio stream start: session={session.session_id}, sample_rate={client_message.sample_rate}Hz, encoding={client_message.encoding}")
                        await handle_audio_start(
                            websocket,
                            session,
                            client_message,
                            stt_handler,
                            agent_handler,
                            config,
                        )
                    elif isinstance(client_message, ClientAudioChunkMessage):
                        # Only log at DEBUG level for audio chunks to reduce noise
                        logger.debug(f"[WS] Audio chunk: session={session.session_id}, size={len(client_message.get_decoded_chunk())} bytes")
                        await handle_audio_chunk(
                            websocket,
                            session,
                            client_message,
                            stt_handler,
                            agent_handler,
                            config,
                        )
                    elif isinstance(client_message, ClientAudioEndMessage):
                        logger.info(f"[WS] Audio stream end: session={session.session_id}")
                        await handle_audio_end(
                            websocket,
                            session,
                            client_message,
                            stt_handler,
                            agent_handler,
                            config,
                        )
                    
                except WebSocketDisconnect:
                    logger.info(f"[WS] Disconnected: connection={connection_id}")
                    break
                except Exception as e:
                    logger.error(f"[WS] Error processing message: {e}, connection={connection_id}, session={session.session_id if session else 'unknown'}", exc_info=True)
                    await handle_error(websocket, session, e, config)
        
        except AuthenticationError as e:
            logger.warning(f"[WS] Authentication failed: {e}, connection={connection_id}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(e))
        except Exception as e:
            logger.error(f"[WS] Connection error: {e}, connection={connection_id}", exc_info=True)
            try:
                await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
            except:
                pass
        finally:
            # Cleanup
            connections.pop(connection_id, None)
            metrics_collector.decrement_connection()
            
            logger.info(f"[WS] Connection closed: connection={connection_id}")
    
    @app.websocket("/ws/dashboard")
    async def dashboard_endpoint(websocket: WebSocket):
        """WebSocket endpoint for dashboard/monitoring interface.
        
        This endpoint allows dashboard clients to:
        - Subscribe to real-time events
        - Receive initial state (sessions, metrics, config)
        - Monitor agent activity
        """
        dashboard_id = str(uuid4())
        
        try:
            # Accept connection
            await websocket.accept()
            logger.info(f"[Dashboard] Connection accepted: dashboard={dashboard_id}")
            
            # Authenticate (optional - can use same API key or separate dashboard key)
            api_key = websocket.headers.get("x-api-key") or websocket.headers.get("X-Api-Key")
            if api_key and config.api_key_validator:
                if not config.api_key_validator(api_key):
                    logger.warning(f"[Dashboard] Invalid API key: dashboard={dashboard_id}")
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid API key")
                    return
            elif not api_key:
                logger.warning(f"[Dashboard] No API key provided: dashboard={dashboard_id}")
                # Allow connection without auth for development (can be restricted later)
                logger.info(f"[Dashboard] Allowing connection without auth (development mode): dashboard={dashboard_id}")
            
            # Subscribe to event bus
            event_callback_ref = None  # Store reference for cleanup
            connection_active = True  # Track if connection is still active
            
            async def event_callback(event: Event) -> None:
                """Callback to send events to dashboard client."""
                nonlocal connection_active
                logger.debug(f"[Dashboard] Event callback invoked: {event.event_type}, connection_active={connection_active}")
                
                if not connection_active:
                    logger.debug(f"[Dashboard] Skipping event (connection inactive): {event.event_type}")
                    return  # Connection closed, don't try to send
                    
                try:
                    event_json = event.to_json()
                    logger.info(f"[Dashboard] Sending event to {dashboard_id}: {event.event_type} (session={event.session_id})")
                    await websocket.send_text(event_json)
                    logger.info(f"[Dashboard] ✓ Event sent successfully: {event.event_type} (session={event.session_id})")
                except WebSocketDisconnect as e:
                    logger.warning(f"[Dashboard] WebSocket disconnected while sending event: {event.event_type}, error={e}")
                    connection_active = False
                except Exception as e:
                    logger.error(f"[Dashboard] Error sending event to dashboard {dashboard_id}: {e}", exc_info=True)
                    connection_active = False
                    # Don't unsubscribe here - let finally block handle it
                    # This prevents trying to send more events to a closed connection
            
            event_callback_ref = event_callback
            event_bus.subscribe(event_callback)
            logger.info(f"[Dashboard] Subscribed to events: dashboard={dashboard_id}, subscribers={event_bus.get_subscriber_count()}")
            
            # Test the callback immediately with a test event
            try:
                test_event = Event(
                    event_type="dashboard_test",
                    session_id=None,
                    timestamp=time.time(),
                    data={"message": "Testing event callback", "dashboard_id": dashboard_id}
                )
                logger.info(f"[Dashboard] Testing event callback for {dashboard_id}")
                await event_callback(test_event)
                logger.info(f"[Dashboard] Test event sent successfully for {dashboard_id}")
            except Exception as e:
                logger.error(f"[Dashboard] Test event failed for {dashboard_id}: {e}", exc_info=True)
            
            # Send initial state
            try:
                initial_state = {
                    "type": "initial_state",
                    "sessions": get_all_sessions(sessions),
                    "metrics": metrics_to_ui_format(metrics_collector),
                    "config": get_agent_config(agent_handler),
                }
                await websocket.send_text(json.dumps(initial_state))
                logger.info(f"[Dashboard] Sent initial state: dashboard={dashboard_id}, sessions={len(sessions)}")
                
                # Send a test event to verify real-time updates work
                await asyncio.sleep(0.1)  # Small delay to ensure initial state is processed
                test_event = Event(
                    event_type="dashboard_connected",
                    session_id=None,
                    timestamp=time.time(),
                    data={"dashboard_id": dashboard_id, "message": "Dashboard connected successfully"}
                )
                await websocket.send_text(test_event.to_json())
                logger.info(f"[Dashboard] Sent test event to verify connection: dashboard={dashboard_id}")
            except Exception as e:
                logger.error(f"[Dashboard] Error sending initial state: {e}", exc_info=True)
                connection_active = False
            
            # Handle incoming messages in a separate task so it doesn't block event sending
            async def handle_incoming_messages():
                """Handle incoming messages from dashboard client."""
                nonlocal connection_active
                while connection_active:
                    try:
                        raw_message = await websocket.receive_text()
                        message_data = json.loads(raw_message)
                        message_type = message_data.get("type")
                        
                        if message_type == "subscribe":
                            # Handle subscription filters (future enhancement)
                            filters = message_data.get("filters", {})
                            logger.info(f"[Dashboard] Subscription filters updated: dashboard={dashboard_id}, filters={filters}")
                            # For now, we subscribe to all events
                            # In future, can filter by session_id, event_type, etc.
                        
                        elif message_type == "ping":
                            # Heartbeat/ping
                            await websocket.send_text(json.dumps({"type": "pong"}))
                        
                        elif message_type == "inject_message":
                            # Inject test message (for playground)
                            session_id = message_data.get("session_id")
                            text = message_data.get("text")
                            if session_id and text and session_id in sessions:
                                # Create a fake client message and process it
                                # This is a simplified version - in production, might want more validation
                                logger.info(f"[Dashboard] Injecting message: dashboard={dashboard_id}, session={session_id}, text={text[:50]}")
                                # Note: This would require access to agent_handler, which we have in scope
                                # For now, just emit an event - actual processing would need more setup
                                await event_bus.publish(
                                    event_type="message_received",
                                    session_id=session_id,
                                    data={
                                        "text": text,
                                        "metadata": {"source": "dashboard_playground"},
                                        "message_length": len(text),
                                    }
                                )
                                await websocket.send_text(json.dumps({
                                    "type": "inject_message_response",
                                    "success": True,
                                    "message": "Message injected (event emitted)"
                                }))
                            else:
                                await websocket.send_text(json.dumps({
                                    "type": "inject_message_response",
                                    "success": False,
                                    "error": "Invalid session_id or text"
                                }))
                        
                        else:
                            logger.warning(f"[Dashboard] Unknown message type: {message_type}, dashboard={dashboard_id}")
                    
                    except WebSocketDisconnect:
                        logger.info(f"[Dashboard] Disconnected: dashboard={dashboard_id}")
                        connection_active = False
                        break
                    except json.JSONDecodeError as e:
                        logger.error(f"[Dashboard] Invalid JSON: {e}, dashboard={dashboard_id}")
                        try:
                            await websocket.send_text(json.dumps({
                                "type": "error",
                                "error": "Invalid JSON",
                                "message": str(e)
                            }))
                        except:
                            connection_active = False
                            break
                    except Exception as e:
                        logger.error(f"[Dashboard] Error processing message: {e}, dashboard={dashboard_id}", exc_info=True)
                        try:
                            await websocket.send_text(json.dumps({
                                "type": "error",
                                "error": "Internal error",
                                "message": str(e)
                            }))
                        except:
                            connection_active = False
                            break
            
            # Start message handling task
            message_task = asyncio.create_task(handle_incoming_messages())
            
            # Wait for the task to complete (when connection closes)
            try:
                await message_task
            except asyncio.CancelledError:
                pass
        
        except Exception as e:
            logger.error(f"[Dashboard] Connection error: {e}, dashboard={dashboard_id}", exc_info=True)
            if 'connection_active' in locals():
                connection_active = False
            try:
                await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
            except:
                pass
        finally:
            # Unsubscribe from event bus
            try:
                if 'event_callback_ref' in locals() and event_callback_ref:
                    event_bus.unsubscribe(event_callback_ref)
                    logger.info(f"[Dashboard] Unsubscribed from events: dashboard={dashboard_id}, remaining subscribers={event_bus.get_subscriber_count()}")
            except Exception as e:
                logger.warning(f"[Dashboard] Error unsubscribing: {e}, dashboard={dashboard_id}")
            
            logger.info(f"[Dashboard] Connection closed: dashboard={dashboard_id}")
    
    return app


async def send_message(websocket: WebSocket, message: ServerMessage, config: Optional[ServerConfig] = None) -> None:
    """Send server message to client.
    
    Args:
        websocket: WebSocket connection
        message: Server message to send
        config: Optional server config for debug logging
    """
    try:
        message_json = message.model_dump_json()
        
        # Log outgoing response (only at DEBUG level to reduce noise)
        logger.debug(f"[WS] Response: type={message.type}, session={message.session_id}")
        if config and config.debug:
            print(f"📤 [WS Response] Type: {message.type}, Session: {message.session_id}")
            # Special formatting for tool messages
            if message.type == "server_tool_call":
                tool_name = message.data.get("tool_name", "unknown")
                tool_args = message.data.get("arguments", {})
                print(f"   Tool Call: {tool_name}")
                if tool_args:
                    args_preview = str(tool_args)[:100]
                    print(f"   Arguments: {args_preview}...")
            elif message.type == "server_tool_result":
                tool_name = message.data.get("tool_name", "unknown")
                status = message.data.get("status", "unknown")
                print(f"   Tool Result: {tool_name} ({status})")
                if status == "completed":
                    result = message.data.get("result", "")
                    result_preview = str(result)[:100] if result else ""
                    if result_preview:
                        print(f"   Result: {result_preview}...")
                else:
                    error = message.data.get("error", "")
                    print(f"   Error: {error}")
            else:
                # Truncate long messages for display
                display_msg = message_json[:150] + "..." if len(message_json) > 150 else message_json
                print(f"   Message: {display_msg}")
        
        await websocket.send_text(message_json)
    except Exception as e:
        logger.error(f"[WS Response] Failed to send message: {e}", exc_info=True)
        raise ConnectionError(f"Failed to send message: {str(e)}", retriable=True) from e


async def handle_text_message(
    websocket: WebSocket,
    session: Session,
    message: ClientTextMessage,
    agent_handler: AgentHandler,
    config: ServerConfig,
) -> None:
    """Handle text message.
    
    Args:
        websocket: WebSocket connection
        session: Session object
        message: Text message
        agent_handler: Agent handler
        config: Server configuration
    """
    try:
        logger.info(f"[Text] Processing: text='{message.text[:60]}{'...' if len(message.text) > 60 else ''}', session={session.session_id}")
        
        # Start keepalive ping task during agent processing to prevent connection timeout
        keepalive_task = None
        keepalive_active = True
        
        async def send_keepalive_pings():
                """Send periodic pings to keep WebSocket connection alive during long operations."""
                while keepalive_active:
                    try:
                        await asyncio.sleep(20)  # Send ping every 20 seconds
                        if keepalive_active:
                            # Try to send WebSocket ping frame using underlying connection
                            try:
                                # Access underlying websocket connection for ping
                                if hasattr(websocket, '_raw_websocket') and hasattr(websocket._raw_websocket, 'ping'):
                                    await websocket._raw_websocket.ping()
                                elif hasattr(websocket, 'client') and hasattr(websocket.client, 'ping'):
                                    await websocket.client.ping()
                                else:
                                    # Fallback: send minimal JSON heartbeat
                                    heartbeat = json.dumps({"type": "heartbeat", "session_id": session.session_id})
                                    await websocket.send_text(heartbeat)
                                logger.debug(f"[Text] Sent keepalive ping during agent processing, session={session.session_id}")
                            except AttributeError:
                                # Fallback: send minimal JSON heartbeat
                                heartbeat = json.dumps({"type": "heartbeat", "session_id": session.session_id})
                                await websocket.send_text(heartbeat)
                                logger.debug(f"[Text] Sent keepalive heartbeat during agent processing, session={session.session_id}")
                    except Exception as e:
                        logger.debug(f"[Text] Keepalive ping error (expected if connection closed): {e}, session={session.session_id}")
                        break
        
        # Start keepalive task
        keepalive_task = asyncio.create_task(send_keepalive_pings())
        
        try:
            # Emit agent_response_start event
            await event_bus.publish(
                event_type="agent_response_start",
                session_id=session.session_id,
                data={
                    "user_message": message.text,
                }
            )
            
            response_count = 0
            agent_start_time = time.time()
            accumulated_response_text = ""
            
            async for response in agent_handler.process_text_async(
                session,
                message.text,
                message.metadata,
            ):
                response_count += 1
                chunk_arrival_time = time.time()
                logger.debug(f"[Text] Agent response #{response_count}: type={response.type}, session={session.session_id}")
                
                # Track response content for events
                # Use the text property which accesses data["text"]
                try:
                    response_text = response.text if hasattr(response, 'text') else ""
                except:
                    response_text = response.data.get("text", "") if hasattr(response, 'data') else ""
                
                if response.type == "server_partial":
                    if response_text:
                        accumulated_response_text += response_text
                        logger.debug(f"[Text] Accumulated text length: {len(accumulated_response_text)}, chunk: {len(response_text)}")
                        # Emit streaming chunk event (throttled - only every few chunks to avoid spam)
                        if response_count % 5 == 0:  # Emit every 5th chunk
                            await event_bus.publish(
                                event_type="agent_response_chunk",
                                session_id=session.session_id,
                                data={
                                    "chunk_index": response_count,
                                    "text_so_far": accumulated_response_text,
                                }
                            )
                elif response.type == "server_text":
                    if response_text:
                        accumulated_response_text = response_text
                        logger.debug(f"[Text] Final text set from server_text, length: {len(accumulated_response_text)}")
                    # If we have accumulated text but server_text is empty, keep accumulated
                    # This handles cases where server_text is sent but text is in accumulated
                    elif accumulated_response_text:
                        logger.debug(f"[Text] server_text empty, keeping accumulated text, length: {len(accumulated_response_text)}")
                    else:
                        logger.warning(f"[Text] No text in server_text response and no accumulated text, response_count={response_count}")
                
                try:
                    send_start_time = time.time()
                    await send_message(websocket, response, config)
                    send_latency_ms = (time.time() - send_start_time) * 1000
                    arrival_to_send_ms = (send_start_time - chunk_arrival_time) * 1000
                    
                    # Log streaming performance for partial messages (actual content chunks)
                    if response.type == "server_partial":
                        logger.debug(f"[Text] Streaming: chunk_arrival_to_send={arrival_to_send_ms:.1f}ms, send_latency={send_latency_ms:.1f}ms, session={session.session_id}")
                except Exception as send_error:
                    logger.error(f"[Text] Failed to send response #{response_count}: {send_error}, type={response.type}, session={session.session_id}", exc_info=True)
                    
                    # Emit error event
                    await event_bus.publish(
                        event_type="error",
                        session_id=session.session_id,
                        data={
                            "error_type": "message_send_error",
                            "error_code": "MESSAGE_SEND_ERROR",
                            "message": str(send_error),
                            "retriable": True,
                        }
                    )
                    
                    # Try to send error message to client
                    try:
                        await send_message(
                            websocket,
                            ServerErrorMessage.create(
                                session_id=session.session_id,
                                error_code="MESSAGE_SEND_ERROR",
                                message=f"Failed to send {response.type} message: {str(send_error)}",
                                retriable=True,
                            ),
                            config=config
                        )
                    except Exception as error_send_failed:
                        logger.error(f"[Text] Failed to send error message: {error_send_failed}, session={session.session_id}")
                        # Don't raise - log the error but keep connection alive
                        logger.warning(f"[Text] Continuing despite error sending failure, session={session.session_id}")
            
            agent_total_time = (time.time() - agent_start_time) * 1000
            logger.info(f"[Text] Complete: {response_count} responses, total_time={agent_total_time:.0f}ms, session={session.session_id}")
            
            # Get final text from session conversation history (source of truth)
            # This ensures we get the same text that's shown in initial state
            final_text = accumulated_response_text if 'accumulated_response_text' in locals() else ""
            
            # Try to get the latest assistant message from conversation history
            conversation_history = session.get_conversation_history()
            if conversation_history:
                # Find the last assistant message
                for msg in reversed(conversation_history):
                    if msg.role == "assistant" and msg.content:
                        history_text = str(msg.content)
                        if history_text and len(history_text) > len(final_text):
                            final_text = history_text
                            logger.debug(f"[Text] Using text from conversation history, length: {len(final_text)}")
                        break
            
            logger.info(f"[Text] Sending agent_response_complete: response_count={response_count}, final_text_length={len(final_text)}")
            await event_bus.publish(
                event_type="agent_response_complete",
                session_id=session.session_id,
                data={
                    "response_count": response_count,
                    "total_time_ms": agent_total_time,
                    "final_text": final_text,
                }
            )
            
            # Emit metrics_updated event with server-level totals
            server_metrics = metrics_collector.server_metrics
            await event_bus.publish(
                event_type="metrics_updated",
                session_id=None,  # Global event, not session-specific
                data={
                    "total_messages": server_metrics.total_messages,
                    "total_tool_calls": server_metrics.total_tool_calls,
                    "total_errors": server_metrics.total_errors,
                    "average_latency_ms": server_metrics.average_latency_ms,
                }
            )
        finally:
            # Stop keepalive task
            keepalive_active = False
            if keepalive_task:
                keepalive_task.cancel()
                try:
                    await keepalive_task
                except asyncio.CancelledError:
                    pass
    except Exception as e:
        logger.error(f"[Text] Error: {e}, session={session.session_id}", exc_info=True)
        
        # Emit error event
        await event_bus.publish(
            event_type="error",
            session_id=session.session_id,
            data={
                "error_type": "text_processing_error",
                "error_code": "TEXT_PROCESSING_ERROR",
                "message": str(e),
                "retriable": True,
            }
        )
        
        # Try to send error message to client instead of raising
        try:
            await send_message(
                websocket,
                ServerErrorMessage.create(
                    session_id=session.session_id,
                    error_code="TEXT_PROCESSING_ERROR",
                    message=f"Error processing text: {str(e)}",
                    retriable=True,
                ),
                config=config
            )
        except Exception as error_send_failed:
            logger.error(f"[Text] Failed to send text processing error message: {error_send_failed}, session={session.session_id}")
            # Don't raise - log and continue to keep connection alive


async def handle_audio_start(
    websocket: WebSocket,
    session: Session,
    message: ClientAudioStartMessage,
    stt_handler: Optional[STTHandler],
    agent_handler: AgentHandler,
    config: Optional[ServerConfig] = None,
) -> None:
    """Handle audio stream start.
    
    Initializes the AudioRecognitionHandler for continuous streaming.
    
    Args:
        websocket: WebSocket connection
        session: Session object
        message: Audio start message
        stt_handler: STT handler for streaming transcription
        agent_handler: Agent handler for processing transcriptions
        config: Server configuration
    """
    try:
        session.start_audio_stream(
            sample_rate=message.sample_rate,
            encoding=message.encoding,
        )
        
        # Initialize AudioRecognitionHandler for continuous streaming
        if stt_handler and config:
            from kuralit.server.audio_recognition import AudioRecognitionHandler
            
            # Define callbacks for AudioRecognitionHandler
            async def on_transcript_callback(transcript: str, is_final: bool, confidence: Optional[float]):
                """Called when STT provides transcript (interim or final)."""
                # Send STT message to client
                stt_message = ServerSTTMessage.create(
                    session_id=session.session_id,
                    text=transcript,
                    confidence=confidence,
                    is_final=is_final
                )
                await send_message(websocket, stt_message, config)
                logger.debug(
                    f"[Audio] STT {'final' if is_final else 'interim'}: '{transcript[:60]}{'...' if len(transcript) > 60 else ''}', "
                    f"session={session.session_id}"
                )
            
            async def on_turn_end_callback(transcript: str):
                """Called when AudioRecognitionHandler commits user turn."""
                logger.info(f"[Audio] User turn committed: '{transcript[:60]}{'...' if len(transcript) > 60 else ''}', session={session.session_id}")
                
                # Process with agent
                await handle_user_turn_committed(
                    websocket,
                    session,
                    transcript,
                    agent_handler,
                    config,
                )
            
            def get_conversation_history_callback():
                """Get conversation history for turn detector."""
                return session.get_conversation_history_for_turn_detector()
            
            # Create AudioRecognitionHandler
            session.audio_recognition_handler = AudioRecognitionHandler(
                stt_handler=stt_handler,
                vad_handler=session.vad_handler,
                turn_detector_handler=session.turn_detector_handler,
                min_endpointing_delay=config.min_endpointing_delay,
                max_endpointing_delay=config.max_endpointing_delay,
                on_transcript_callback=on_transcript_callback,
                on_turn_end_callback=on_turn_end_callback,
                conversation_history_callback=get_conversation_history_callback,
            )
            
            # Start the audio recognition handler
            await session.audio_recognition_handler.start(
                sample_rate=message.sample_rate,
                encoding=message.encoding
            )
            
            logger.info(
                f"[Audio] Stream started with AudioRecognitionHandler: "
                f"session={session.session_id}, sample_rate={message.sample_rate}Hz, "
                f"encoding={message.encoding}, VAD={'enabled' if session.vad_handler else 'disabled'}, "
                f"TurnDetector={'enabled' if session.turn_detector_handler else 'disabled'}"
            )
        else:
            vad_status = "enabled" if session.vad_handler else "disabled"
            logger.info(f"[Audio] Stream started (STT disabled): session={session.session_id}, sample_rate={message.sample_rate}Hz, encoding={message.encoding}, VAD={vad_status}")
    
    except Exception as e:
        logger.error(f"[Audio] Error starting stream: {e}, session={session.session_id}", exc_info=True)
        raise AudioProcessingError(f"Failed to start audio stream: {str(e)}", retriable=False) from e


async def handle_audio_chunk(
    websocket: WebSocket,
    session: Session,
    message: ClientAudioChunkMessage,
    stt_handler: Optional[STTHandler],
    agent_handler: AgentHandler,
    config: ServerConfig,
) -> None:
    """Handle audio chunk - simplified for continuous streaming.
    
    In the new architecture, audio is streamed continuously to AudioRecognitionHandler,
    which coordinates STT, VAD, and Turn Detector.
    
    Args:
        websocket: WebSocket connection
        session: Session object
        message: Audio chunk message
        stt_handler: STT handler (optional, not used directly)
        agent_handler: Agent handler (not used here)
        config: Server configuration
    """
    try:
        # Decode chunk
        audio_chunk = message.get_decoded_chunk()
        
        # Log first chunk and every 100 chunks to verify we're receiving audio
        if not hasattr(session, '_audio_chunk_count'):
            session._audio_chunk_count = 0
        session._audio_chunk_count += 1
        
        if session._audio_chunk_count == 1 or session._audio_chunk_count % 100 == 0:
            logger.info(f"[Audio] Received chunk #{session._audio_chunk_count}: {len(audio_chunk)} bytes, session={session.session_id}")
        
        # Forward to AudioRecognitionHandler (continuous streaming)
        if session.audio_recognition_handler:
            await session.audio_recognition_handler.push_audio_frame(audio_chunk)
        else:
            logger.warning(f"[Audio] No AudioRecognitionHandler initialized, dropping chunk #{session._audio_chunk_count}, session={session.session_id}")
        
        # Process VAD in parallel (for events only)
        if session.vad_handler and session.is_audio_active:
            try:
                import numpy as np
                # Convert bytes to numpy array
                audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
                window_size = session.vad_handler.window_size_samples
                
                # Process frame-by-frame
                for i in range(0, len(audio_array), window_size):
                    frame = audio_array[i:i + window_size]
                    if len(frame) == window_size:
                        # Process complete frame
                        vad_result = session.vad_handler.process_audio_frame(frame)
                        event = vad_result.get("event", "CONTINUING")
                        prob = vad_result.get("probability", 0.0)
                        
                        # Debug: Log VAD probabilities every 100 chunks
                        if session._audio_chunk_count % 100 == 0:
                            vad_threshold = getattr(config, 'vad_activation_threshold', 0.5)
                            logger.info(f"[VAD] Chunk #{session._audio_chunk_count}: event={event}, prob={prob:.3f}, threshold={vad_threshold}, session={session.session_id}")
                        
                        # Forward VAD events to AudioRecognitionHandler
                        if event != "CONTINUING" and session.audio_recognition_handler:
                            await session.audio_recognition_handler.handle_vad_event(event, prob)
            except Exception as e:
                logger.warning(f"[VAD] Processing error: {e}, session={session.session_id}")
        
        metrics_collector.record_audio_chunk(session.session_id)
    
    except Exception as e:
        logger.error(f"[Audio] Error processing chunk: {e}, session={session.session_id}", exc_info=True)
        raise AudioProcessingError(f"Failed to process audio chunk: {str(e)}", retriable=True) from e


async def handle_user_turn_committed(
    websocket: WebSocket,
    session: Session,
    transcript: str,
    agent_handler: AgentHandler,
    config: ServerConfig,
) -> None:
    """
    Handle user turn committed by AudioRecognitionHandler.
    
    This is called when the audio recognition handler determines the user has
    finished their turn (based on VAD, STT, and Turn Detector signals).
    
    Args:
        websocket: WebSocket connection
        session: Session object
        transcript: Complete user transcript
        agent_handler: Agent handler for processing
        config: Server configuration
    """
    try:
        logger.info(f"[Audio] Processing user turn with agent: session={session.session_id}")
        
        # Record message in metrics
        session.update_activity()
        metrics_collector.record_message(session.session_id)
        
        # Note: metrics_updated will be emitted after agent response completes
        
        # Emit message_received event for audio transcript
        logger.info(f"[Audio] Publishing message_received event: session={session.session_id}, subscribers={event_bus.get_subscriber_count()}")
        await event_bus.publish(
            event_type="message_received",
            session_id=session.session_id,
            data={
                "text": transcript,
                "metadata": {"source": "audio", "transcription": True},
                "message_length": len(transcript),
            }
        )
        logger.debug(f"[Audio] message_received event published: session={session.session_id}")
        
        # Start keepalive ping task during agent processing to prevent connection timeout
        keepalive_task = None
        keepalive_active = True
        
        async def send_keepalive_pings():
            """Send periodic pings to keep WebSocket connection alive during long operations."""
            while keepalive_active:
                try:
                    await asyncio.sleep(20)  # Send ping every 20 seconds
                    if keepalive_active:
                        # Try to send WebSocket ping frame
                        try:
                            if hasattr(websocket, '_raw_websocket') and hasattr(websocket._raw_websocket, 'ping'):
                                await websocket._raw_websocket.ping()
                            elif hasattr(websocket, 'client') and hasattr(websocket.client, 'ping'):
                                await websocket.client.ping()
                            else:
                                # Fallback: send minimal JSON heartbeat
                                heartbeat = json.dumps({"type": "heartbeat", "session_id": session.session_id})
                                await websocket.send_text(heartbeat)
                        except AttributeError:
                            heartbeat = json.dumps({"type": "heartbeat", "session_id": session.session_id})
                            await websocket.send_text(heartbeat)
                except Exception as e:
                    logger.debug(f"[Audio] Keepalive ping error: {e}, session={session.session_id}")
                    break
        
        # Start keepalive task
        keepalive_task = asyncio.create_task(send_keepalive_pings())
        
        try:
            # Emit agent_response_start event
            await event_bus.publish(
                event_type="agent_response_start",
                session_id=session.session_id,
                data={
                    "user_message": transcript,
                }
            )
            
            response_count = 0
            agent_start_time = time.time()
            accumulated_response_text = ""
            
            async for response in agent_handler.process_transcription_async(
                session,
                transcript,
            ):
                response_count += 1
                logger.debug(f"[Audio] Agent response #{response_count}: type={response.type}, session={session.session_id}")
                
                # Track response content for events
                # Use the text property which accesses data["text"]
                try:
                    response_text = response.text if hasattr(response, 'text') else ""
                except:
                    response_text = response.data.get("text", "") if hasattr(response, 'data') else ""
                
                if response.type == "server_partial":
                    if response_text:
                        accumulated_response_text += response_text
                        logger.debug(f"[Audio] Accumulated text length: {len(accumulated_response_text)}, chunk: {len(response_text)}")
                        # Emit streaming chunk event (throttled - only every few chunks to avoid spam)
                        if response_count % 5 == 0:  # Emit every 5th chunk
                            await event_bus.publish(
                                event_type="agent_response_chunk",
                                session_id=session.session_id,
                                data={
                                    "chunk_index": response_count,
                                    "text_so_far": accumulated_response_text,
                                }
                            )
                elif response.type == "server_text":
                    if response_text:
                        accumulated_response_text = response_text
                        logger.debug(f"[Audio] Final text set from server_text, length: {len(accumulated_response_text)}")
                    # If we have accumulated text but server_text is empty, keep accumulated
                    # This handles cases where server_text is sent but text is in accumulated
                    elif accumulated_response_text:
                        logger.debug(f"[Audio] server_text empty, keeping accumulated text, length: {len(accumulated_response_text)}")
                    else:
                        logger.warning(f"[Audio] No text in server_text response and no accumulated text, response_count={response_count}")
                
                try:
                    await send_message(websocket, response, config)
                except Exception as send_error:
                    logger.error(f"[Audio] Failed to send response #{response_count}: {send_error}, session={session.session_id}", exc_info=True)
                    
                    # Emit error event
                    await event_bus.publish(
                        event_type="error",
                        session_id=session.session_id,
                        data={
                            "error_type": "message_send_error",
                            "error_code": "MESSAGE_SEND_ERROR",
                            "message": str(send_error),
                        }
                    )
                    
                    await send_message(
                        websocket,
                        ServerErrorMessage.create(
                            session_id=session.session_id,
                            error_code="MESSAGE_SEND_ERROR",
                            message=f"Failed to send {response.type} message: {str(send_error)}",
                            retriable=True,
                        ),
                        config=config
                    )
            
            agent_total_time = (time.time() - agent_start_time) * 1000
            logger.info(f"[Audio] Agent processing complete: {response_count} responses, total_time={agent_total_time:.0f}ms, session={session.session_id}")
            
            # Get final text from session conversation history (source of truth)
            # This ensures we get the same text that's shown in initial state
            final_text = accumulated_response_text if 'accumulated_response_text' in locals() else ""
            
            # Try to get the latest assistant message from conversation history
            conversation_history = session.get_conversation_history()
            if conversation_history:
                # Find the last assistant message
                for msg in reversed(conversation_history):
                    if msg.role == "assistant" and msg.content:
                        history_text = str(msg.content)
                        if history_text and len(history_text) > len(final_text):
                            final_text = history_text
                            logger.debug(f"[Audio] Using text from conversation history, length: {len(final_text)}")
                        break
            
            logger.info(f"[Audio] Sending agent_response_complete: response_count={response_count}, final_text_length={len(final_text)}")
            await event_bus.publish(
                event_type="agent_response_complete",
                session_id=session.session_id,
                data={
                    "response_count": response_count,
                    "total_time_ms": agent_total_time,
                    "final_text": final_text,
                }
            )
            
            # Emit metrics_updated event with server-level totals
            server_metrics = metrics_collector.server_metrics
            await event_bus.publish(
                event_type="metrics_updated",
                session_id=None,  # Global event, not session-specific
                data={
                    "total_messages": server_metrics.total_messages,
                    "total_tool_calls": server_metrics.total_tool_calls,
                    "total_errors": server_metrics.total_errors,
                    "average_latency_ms": server_metrics.average_latency_ms,
                }
            )
        
        finally:
            # Stop keepalive task
            keepalive_active = False
            if keepalive_task:
                keepalive_task.cancel()
                try:
                    await keepalive_task
                except asyncio.CancelledError:
                    pass
    
    except Exception as e:
        logger.error(f"[Audio] Error processing user turn: {e}, session={session.session_id}", exc_info=True)
        
        # Emit error event
        await event_bus.publish(
            event_type="error",
            session_id=session.session_id,
            data={
                "error_type": "audio_processing_error",
                "error_code": "AUDIO_PROCESSING_ERROR",
                "message": str(e),
            }
        )
        
        try:
            await send_message(
                websocket,
                ServerErrorMessage.create(
                    session_id=session.session_id,
                    error_code="AGENT_ERROR",
                    message=f"Agent processing failed: {str(e)}",
                    retriable=True,
                ),
                config=config
            )
        except Exception as error_send_failed:
            logger.error(f"[Audio] Failed to send error message: {error_send_failed}, session={session.session_id}")


async def handle_audio_end(
    websocket: WebSocket,
    session: Session,
    message: ClientAudioEndMessage,
    stt_handler: Optional[STTHandler],
    agent_handler: AgentHandler,
    config: ServerConfig,
) -> None:
    """Handle audio stream end.
    
    Stops the AudioRecognitionHandler and cleans up resources.
    
    Args:
        websocket: WebSocket connection
        session: Session object
        message: Audio end message
        stt_handler: STT handler (optional, not used directly)
        agent_handler: Agent handler (not used here)
        config: Server configuration
    """
    try:
        # Get final chunk if present
        final_chunk = message.get_decoded_final_chunk()
        if final_chunk:
            logger.debug(f"[Audio] Final chunk: {len(final_chunk)} bytes, session={session.session_id}")
            if session.audio_recognition_handler:
                await session.audio_recognition_handler.push_audio_frame(final_chunk)
        
        # Stop AudioRecognitionHandler
        if session.audio_recognition_handler:
            await session.audio_recognition_handler.stop()
            logger.info(f"[Audio] AudioRecognitionHandler stopped, session={session.session_id}")
        
        # End audio stream in session
        session.end_audio_stream()
        
        logger.info(f"[Audio] Stream ended, session={session.session_id}")
    
    except Exception as e:
        logger.error(f"[Audio] Error ending stream: {e}, session={session.session_id}", exc_info=True)
        raise AudioProcessingError(f"Failed to end audio stream: {str(e)}", retriable=False) from e


async def handle_error(
    websocket: WebSocket,
    session: Optional[Session],
    error: Exception,
    config: Optional[ServerConfig] = None,
) -> None:
    """Handle error and send error message to client.
    
    Args:
        websocket: WebSocket connection
        session: Session object (optional)
        error: Error exception
        config: Optional server configuration for logging
    """
    session_id = session.session_id if session else "unknown"
    
    if isinstance(error, WebSocketError):
        error_code = error.code
        error_message = error.message
        retriable = error.retriable
    else:
        error_code = "INTERNAL_ERROR"
        error_message = "An internal error occurred"
        retriable = False
    
    logger.error(f"[WS] Error: code={error_code}, message={error_message}, retriable={retriable}, session={session_id}")
    
    metrics_collector.record_error(session_id)
    
    # Emit metrics_updated event immediately after recording error
    server_metrics = metrics_collector.server_metrics
    await event_bus.publish(
        event_type="metrics_updated",
        session_id=None,  # Global event, not session-specific
        data={
            "total_messages": server_metrics.total_messages,
            "total_tool_calls": server_metrics.total_tool_calls,
            "total_errors": server_metrics.total_errors,
            "average_latency_ms": server_metrics.average_latency_ms,
        }
    )
    
    try:
        await send_message(
            websocket,
            ServerErrorMessage.create(
                session_id=session_id,
                error_code=error_code,
                message=error_message,
                retriable=retriable,
            ),
            config=config
        )
    except Exception as e:
        logger.error(f"[WS] Failed to send error message: {e}, session={session_id}", exc_info=True)


# Create default app instance
app: Optional[FastAPI] = None

