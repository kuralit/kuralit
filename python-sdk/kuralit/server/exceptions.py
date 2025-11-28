"""Custom exceptions for WebSocket server."""


class WebSocketError(Exception):
    """Base exception for all WebSocket server errors."""
    
    def __init__(self, message: str, code: str = "WEBSOCKET_ERROR", retriable: bool = False):
        self.message = message
        self.code = code
        self.retriable = retriable
        super().__init__(self.message)


class AuthenticationError(WebSocketError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, code="AUTHENTICATION_ERROR", retriable=False)


class MessageValidationError(WebSocketError):
    """Raised when message validation fails."""
    
    def __init__(self, message: str, field: str = None):
        if field:
            message = f"Validation error in field '{field}': {message}"
        super().__init__(message, code="VALIDATION_ERROR", retriable=False)
        self.field = field


class SessionNotFoundError(WebSocketError):
    """Raised when session is not found."""
    
    def __init__(self, session_id: str):
        super().__init__(
            f"Session not found: {session_id}",
            code="SESSION_NOT_FOUND",
            retriable=False
        )
        self.session_id = session_id


class AudioProcessingError(WebSocketError):
    """Raised when audio processing fails."""
    
    def __init__(self, message: str, retriable: bool = True):
        super().__init__(message, code="AUDIO_PROCESSING_ERROR", retriable=retriable)


class STTError(WebSocketError):
    """Raised when STT processing fails."""
    
    def __init__(self, message: str, retriable: bool = True):
        super().__init__(message, code="STT_ERROR", retriable=retriable)


class AgentError(WebSocketError):
    """Raised when agent processing fails."""
    
    def __init__(self, message: str, retriable: bool = False):
        super().__init__(message, code="AGENT_ERROR", retriable=retriable)


class ConnectionError(WebSocketError):
    """Raised when connection issues occur."""
    
    def __init__(self, message: str, retriable: bool = True):
        super().__init__(message, code="CONNECTION_ERROR", retriable=retriable)

