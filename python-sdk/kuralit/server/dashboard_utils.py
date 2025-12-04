"""Utilities for transforming backend data to dashboard UI format."""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from kuralit.models.message import Message
from kuralit.server.agent_handler import AgentHandler
from kuralit.server.metrics import MetricsCollector, SessionMetrics
from kuralit.server.session import Session

logger = logging.getLogger(__name__)


def format_timestamp(timestamp: float) -> str:
    """Format timestamp to UI format.
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        Formatted timestamp string (e.g., "2025-11-25 . 18:00")
    """
    dt = datetime.fromtimestamp(timestamp)
    date_str = dt.strftime("%Y-%m-%d")
    time_str = dt.strftime("%H:%M")
    return f"{date_str} . {time_str}"


def format_time_only(timestamp: float) -> str:
    """Format timestamp to time-only format.
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        Formatted time string (e.g., "18:00:00")
    """
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%H:%M:%S")


def message_to_timeline_item(
    message: Message,
    index: int = 0,
    previous_timestamp: Optional[float] = None,
    tool_calls: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """Convert Message to TimelineItem format for UI.
    
    Args:
        message: Message object
        index: Index in conversation history
        previous_timestamp: Timestamp of previous message (for latency calculation)
        tool_calls: Optional tool calls associated with this message
        
    Returns:
        TimelineItem dictionary
    """
    # Determine message type
    if message.role == "user":
        msg_type = "USER"
        status = "info"
    elif message.role == "assistant":
        msg_type = "AGENT"
        status = "success"
    elif message.role == "tool":
        msg_type = "EVENT"
        status = "success"
    else:
        msg_type = "USER"
        status = "info"
    
    # Calculate latency (if previous timestamp available)
    latency = None
    if previous_timestamp and hasattr(message, 'timestamp'):
        latency_ms = (message.timestamp - previous_timestamp) * 1000
        latency = f"+{latency_ms/1000:.2f}s"
    elif index == 0:
        latency = "+0.00s"
    
    # Format timestamp
    if hasattr(message, 'timestamp') and message.timestamp:
        timestamp = format_time_only(message.timestamp)
    else:
        timestamp = format_time_only(time.time())
    
    # Extract content
    content = str(message.content) if message.content else ""
    
    # Build raw payload
    raw = {
        "role": message.role,
        "content": content,
    }
    
    # Add tool calls if present
    if tool_calls:
        raw["tool_calls"] = tool_calls
    elif hasattr(message, 'tool_calls') and message.tool_calls:
        raw["tool_calls"] = message.tool_calls
    
    # Add usage info if available
    if hasattr(message, 'usage') and message.usage:
        raw["usage"] = message.usage
    
    # For tool messages, extract details
    details = None
    if message.role == "tool":
        # Try to extract tool name and result
        if hasattr(message, 'tool_calls') and message.tool_calls:
            tool_call = message.tool_calls[0] if message.tool_calls else {}
            tool_name = tool_call.get("tool_name", "unknown")
            details = f"tool:{tool_name}"
        else:
            details = "tool:result"
        
        # Check if it's an error
        if content and content.startswith("Error:"):
            status = "error"
            details = content
    
    return {
        "id": f"msg_{index}",
        "type": msg_type,
        "content": content,
        "details": details,
        "timestamp": timestamp,
        "latency": latency,
        "status": status,
        "raw": raw,
    }


def session_to_conversation(session: Session) -> Dict[str, Any]:
    """Convert Session to Conversation format for UI.
    
    Args:
        session: Session object
        
    Returns:
        Conversation dictionary
    """
    # Generate title from first user message or use session ID
    title = session.session_id
    preview = ""
    
    # Find first user message for title/preview
    for msg in session.conversation_history:
        if msg.role == "user" and msg.content:
            preview = str(msg.content)
            # Use first 50 chars as title
            if len(preview) > 50:
                title = preview[:47] + "..."
            else:
                title = preview
            break
    
    # Convert messages to timeline items
    timeline_items = []
    previous_timestamp = session.created_at
    
    for i, message in enumerate(session.conversation_history):
        item = message_to_timeline_item(
            message,
            index=i,
            previous_timestamp=previous_timestamp,
        )
        timeline_items.append(item)
        
        # Update previous timestamp (use message timestamp if available)
        if hasattr(message, 'timestamp') and message.timestamp:
            previous_timestamp = message.timestamp
        else:
            # Estimate timestamp based on creation time + index
            previous_timestamp = session.created_at + (i * 0.1)
    
    return {
        "id": session.session_id,
        "timestamp": format_timestamp(session.created_at),
        "title": title or session.session_id,
        "preview": preview or "No messages yet",
        "items": timeline_items,
    }


def metrics_to_ui_format(
    metrics_collector: MetricsCollector,
    session_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Convert metrics to UI Metric format.
    
    Args:
        metrics_collector: MetricsCollector instance
        session_id: Optional session ID for per-session metrics
        
    Returns:
        List of Metric dictionaries
    """
    if session_id:
        # Per-session metrics
        session_metrics = metrics_collector.get_session_metrics(session_id)
        if not session_metrics:
            return []
        
        return [
            {
                "label": "Messages",
                "value": session_metrics.messages_received,
            },
            {
                "label": "Tool Calls",
                "value": session_metrics.agent_responses,  # Approximate
            },
            {
                "label": "Errors",
                "value": session_metrics.errors,
            },
            {
                "label": "Latency (p95)",
                "value": int(session_metrics.get_average_latency_ms()),
            },
        ]
    else:
        # Server-level metrics
        server_metrics = metrics_collector.server_metrics
        
        return [
            {
                "label": "Messages",
                "value": server_metrics.total_messages,
            },
            {
                "label": "Tool Calls",
                "value": server_metrics.total_tool_calls,
            },
            {
                "label": "Errors",
                "value": server_metrics.total_errors,
            },
            {
                "label": "Latency (p95)",
                "value": int(server_metrics.average_latency_ms),
            },
        ]


def get_agent_config(agent_handler: AgentHandler) -> Dict[str, Any]:
    """Extract agent configuration for UI.
    
    Args:
        agent_handler: AgentHandler instance
        
    Returns:
        SDKConfig dictionary
    """
    # Get model name
    model_name = "unknown"
    if hasattr(agent_handler, 'model') and agent_handler.model:
        if hasattr(agent_handler.model, 'id'):
            model_name = agent_handler.model.id
        elif hasattr(agent_handler.model, 'model_id'):
            model_name = agent_handler.model.model_id
    
    # Get model parameters
    temperature = 0.7
    top_p = 0.9
    if hasattr(agent_handler, 'model') and agent_handler.model:
        if hasattr(agent_handler.model, 'temperature'):
            temperature = agent_handler.model.temperature
        if hasattr(agent_handler.model, 'top_p'):
            top_p = agent_handler.model.top_p
    
    # Get capabilities (tools)
    capabilities = []
    if hasattr(agent_handler, 'agent') and agent_handler.agent:
        if hasattr(agent_handler.agent, 'functions') and agent_handler.agent.functions:
            capabilities = list(agent_handler.agent.functions.keys())
    
    return {
        "identity": {
            "agentId": agent_handler.name if hasattr(agent_handler, 'name') else "agent_unknown",
            "sdkVersion": "0.1.1",  # TODO: Get from version file
            "environment": "development",  # TODO: Get from config
        },
        "model": {
            "name": model_name,
            "temperature": temperature,
            "topP": top_p,
        },
        "client": {
            "platform": "Unknown",
            "appState": "foreground",
            "permissions": "granted",
            "socketStatus": "connected",
            "lastHeartbeat": "0ms ago",
        },
        "capabilities": capabilities,
    }


def get_all_sessions(sessions: Dict[str, Session]) -> List[Dict[str, Any]]:
    """Get all sessions as conversations.
    
    Args:
        sessions: Dictionary of sessions
        
    Returns:
        List of Conversation dictionaries
    """
    return [session_to_conversation(session) for session in sessions.values()]

