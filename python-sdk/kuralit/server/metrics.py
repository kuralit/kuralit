"""Metrics collection for WebSocket server."""

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class SessionMetrics:
    """Metrics for a single session."""
    
    messages_sent: int = 0
    messages_received: int = 0
    audio_chunks_received: int = 0
    stt_transcriptions: int = 0
    agent_responses: int = 0
    total_latency_ms: float = 0.0
    stt_latency_ms: float = 0.0
    agent_latency_ms: float = 0.0
    errors: int = 0
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()
    
    def get_average_latency_ms(self) -> float:
        """Get average latency in milliseconds."""
        if self.agent_responses == 0:
            return 0.0
        return self.total_latency_ms / self.agent_responses
    
    def get_average_stt_latency_ms(self) -> float:
        """Get average STT latency in milliseconds."""
        if self.stt_transcriptions == 0:
            return 0.0
        return self.stt_latency_ms / self.stt_transcriptions


@dataclass
class ServerMetrics:
    """Global server metrics."""
    
    active_connections: int = 0
    total_connections: int = 0
    total_messages: int = 0
    total_errors: int = 0
    total_audio_chunks: int = 0
    total_stt_transcriptions: int = 0
    total_agent_responses: int = 0
    average_latency_ms: float = 0.0
    average_stt_latency_ms: float = 0.0
    start_time: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        """Convert metrics to dictionary."""
        uptime_seconds = time.time() - self.start_time
        return {
            "active_connections": self.active_connections,
            "total_connections": self.total_connections,
            "total_messages": self.total_messages,
            "total_errors": self.total_errors,
            "total_audio_chunks": self.total_audio_chunks,
            "total_stt_transcriptions": self.total_stt_transcriptions,
            "total_agent_responses": self.total_agent_responses,
            "average_latency_ms": self.average_latency_ms,
            "average_stt_latency_ms": self.average_stt_latency_ms,
            "uptime_seconds": uptime_seconds,
        }


class MetricsCollector:
    """Collects and aggregates metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.server_metrics = ServerMetrics()
        self.session_metrics: Dict[str, SessionMetrics] = {}
    
    def create_session_metrics(self, session_id: str) -> SessionMetrics:
        """Create metrics for a session."""
        metrics = SessionMetrics()
        self.session_metrics[session_id] = metrics
        return metrics
    
    def get_session_metrics(self, session_id: str) -> Optional[SessionMetrics]:
        """Get metrics for a session."""
        return self.session_metrics.get(session_id)
    
    def remove_session_metrics(self, session_id: str) -> None:
        """Remove metrics for a session."""
        self.session_metrics.pop(session_id, None)
    
    def increment_connection(self) -> None:
        """Increment connection count."""
        self.server_metrics.active_connections += 1
        self.server_metrics.total_connections += 1
    
    def decrement_connection(self) -> None:
        """Decrement connection count."""
        self.server_metrics.active_connections = max(0, self.server_metrics.active_connections - 1)
    
    def record_message(self, session_id: Optional[str] = None) -> None:
        """Record a message."""
        self.server_metrics.total_messages += 1
        if session_id:
            metrics = self.get_session_metrics(session_id)
            if metrics:
                metrics.messages_received += 1
                metrics.update_activity()
    
    def record_error(self, session_id: Optional[str] = None) -> None:
        """Record an error."""
        self.server_metrics.total_errors += 1
        if session_id:
            metrics = self.get_session_metrics(session_id)
            if metrics:
                metrics.errors += 1
    
    def record_audio_chunk(self, session_id: Optional[str] = None) -> None:
        """Record an audio chunk."""
        self.server_metrics.total_audio_chunks += 1
        if session_id:
            metrics = self.get_session_metrics(session_id)
            if metrics:
                metrics.audio_chunks_received += 1
    
    def record_stt_transcription(self, latency_ms: float, session_id: Optional[str] = None) -> None:
        """Record an STT transcription."""
        self.server_metrics.total_stt_transcriptions += 1
        if session_id:
            metrics = self.get_session_metrics(session_id)
            if metrics:
                metrics.stt_transcriptions += 1
                metrics.stt_latency_ms += latency_ms
    
    def record_agent_response(self, latency_ms: float, session_id: Optional[str] = None) -> None:
        """Record an agent response."""
        self.server_metrics.total_agent_responses += 1
        if session_id:
            metrics = self.get_session_metrics(session_id)
            if metrics:
                metrics.agent_responses += 1
                metrics.total_latency_ms += latency_ms
                metrics.agent_latency_ms += latency_ms
    
    def get_server_metrics(self) -> ServerMetrics:
        """Get server metrics."""
        return self.server_metrics

