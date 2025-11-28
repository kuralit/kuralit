"""WebSocket message protocol models."""

import base64
from typing import Any, Dict, Literal, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

from kuralit.server.exceptions import MessageValidationError


class ClientMessageBase(BaseModel):
    """Base class for all client messages."""
    
    type: str
    session_id: str
    data: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("session_id cannot be empty")
        return v.strip()


class ClientTextMessage(ClientMessageBase):
    """Client text message."""
    
    type: Literal["client_text"] = "client_text"
    data: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def text(self) -> str:
        """Get text from data."""
        return self.data.get("text", "")
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get metadata from data."""
        return self.data.get("metadata", {})
    
    @model_validator(mode="after")
    def validate_text(self) -> "ClientTextMessage":
        text = self.data.get("text", "")
        if not text or not isinstance(text, str):
            raise ValueError("text field is required and must be a string")
        if len(text.encode("utf-8")) > 4096:  # 4KB limit
            raise ValueError("text exceeds maximum size of 4KB")
        return self


class ClientAudioStartMessage(ClientMessageBase):
    """Client audio stream start message."""
    
    type: Literal["client_audio_start"] = "client_audio_start"
    data: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def sample_rate(self) -> int:
        """Get sample rate from data."""
        return self.data.get("sample_rate", 16000)
    
    @property
    def encoding(self) -> str:
        """Get encoding from data."""
        return self.data.get("encoding", "PCM16")
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get metadata from data."""
        return self.data.get("metadata", {})
    
    @model_validator(mode="after")
    def validate_audio_start(self) -> "ClientAudioStartMessage":
        sample_rate = self.data.get("sample_rate")
        if not sample_rate or not isinstance(sample_rate, int):
            raise ValueError("sample_rate is required and must be an integer")
        if sample_rate not in [8000, 16000, 44100, 48000]:
            raise ValueError("sample_rate must be one of: 8000, 16000, 44100, 48000")
        
        encoding = self.data.get("encoding", "PCM16")
        if encoding not in ["PCM16", "PCM8"]:
            raise ValueError("encoding must be PCM16 or PCM8")
        
        return self


class ClientAudioChunkMessage(ClientMessageBase):
    """Client audio chunk message."""
    
    type: Literal["client_audio_chunk"] = "client_audio_chunk"
    data: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def chunk(self) -> str:
        """Get base64-encoded chunk from data."""
        return self.data.get("chunk", "")
    
    @property
    def timestamp(self) -> Optional[float]:
        """Get timestamp from data."""
        return self.data.get("timestamp")
    
    @model_validator(mode="after")
    def validate_chunk(self) -> "ClientAudioChunkMessage":
        chunk = self.data.get("chunk", "")
        if not chunk or not isinstance(chunk, str):
            raise ValueError("chunk field is required and must be a string")
        
        # Validate base64 and size
        try:
            decoded = base64.b64decode(chunk)
            if len(decoded) > 16384:  # 16KB limit
                raise ValueError("audio chunk exceeds maximum size of 16KB")
        except Exception as e:
            raise ValueError(f"Invalid base64 chunk: {str(e)}")
        
        return self
    
    def get_decoded_chunk(self) -> bytes:
        """Get decoded audio chunk."""
        return base64.b64decode(self.chunk)


class ClientAudioEndMessage(ClientMessageBase):
    """Client audio stream end message."""
    
    type: Literal["client_audio_end"] = "client_audio_end"
    data: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def final_chunk(self) -> Optional[str]:
        """Get optional final chunk from data."""
        return self.data.get("final_chunk")
    
    def get_decoded_final_chunk(self) -> Optional[bytes]:
        """Get decoded final chunk if present."""
        final_chunk = self.final_chunk
        if final_chunk:
            return base64.b64decode(final_chunk)
        return None


# Union type for all client messages
ClientMessage = Union[
    ClientTextMessage,
    ClientAudioStartMessage,
    ClientAudioChunkMessage,
    ClientAudioEndMessage,
]


class ServerMessageBase(BaseModel):
    """Base class for all server messages."""
    
    type: str
    session_id: str
    data: Dict[str, Any] = Field(default_factory=dict)


class ServerTextMessage(ServerMessageBase):
    """Server final text response message."""
    
    type: Literal["server_text"] = "server_text"
    data: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def create(cls, session_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> "ServerTextMessage":
        """Create a server text message."""
        return cls(
            session_id=session_id,
            data={
                "text": text,
                "metadata": metadata or {},
            }
        )


class ServerPartialMessage(ServerMessageBase):
    """Server streaming partial response message."""
    
    type: Literal["server_partial"] = "server_partial"
    data: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def create(cls, session_id: str, text: str, is_final: bool = False) -> "ServerPartialMessage":
        """Create a server partial message."""
        return cls(
            session_id=session_id,
            data={
                "text": text,
                "is_final": is_final,
            }
        )


class ServerSTTMessage(ServerMessageBase):
    """Server STT transcription message (intermediate)."""
    
    type: Literal["server_stt"] = "server_stt"
    data: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def create(
        cls, 
        session_id: str, 
        text: str, 
        confidence: Optional[float] = None,
        is_final: bool = False
    ) -> "ServerSTTMessage":
        """Create a server STT message.
        
        Args:
            session_id: Session identifier
            text: Transcribed text
            confidence: Optional confidence score (typically only for final transcripts)
            is_final: Whether this is a final transcript (False for interim)
        """
        data = {"text": text, "is_final": is_final}
        if confidence is not None:
            data["confidence"] = confidence
        return cls(
            session_id=session_id,
            data=data
        )


class ServerErrorMessage(ServerMessageBase):
    """Server error message."""
    
    type: Literal["server_error"] = "server_error"
    data: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        session_id: str,
        error_code: str,
        message: str,
        retriable: bool = False,
    ) -> "ServerErrorMessage":
        """Create a server error message."""
        return cls(
            session_id=session_id,
            data={
                "error_code": error_code,
                "message": message,
                "retriable": retriable,
            }
        )


class ServerConnectedMessage(ServerMessageBase):
    """Server connection confirmation message."""
    
    type: Literal["server_connected"] = "server_connected"
    data: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def create(cls, session_id: str, metadata: Optional[Dict[str, Any]] = None) -> "ServerConnectedMessage":
        """Create a server connected message."""
        return cls(
            session_id=session_id,
            data={
                "message": "Connected successfully",
                "metadata": metadata or {},
            }
        )


class ServerToolCallMessage(ServerMessageBase):
    """Server tool call notification message."""
    
    type: Literal["server_tool_call"] = "server_tool_call"
    data: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        session_id: str,
        tool_name: str,
        tool_arguments: Dict[str, Any],
        tool_call_id: Optional[str] = None,
    ) -> "ServerToolCallMessage":
        """Create a server tool call message."""
        return cls(
            session_id=session_id,
            data={
                "tool_name": tool_name,
                "arguments": tool_arguments,
                "tool_call_id": tool_call_id,
                "status": "calling",
            }
        )


class ServerToolResultMessage(ServerMessageBase):
    """Server tool result notification message."""
    
    type: Literal["server_tool_result"] = "server_tool_result"
    data: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        session_id: str,
        tool_name: str,
        result: Any,
        tool_call_id: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None,
    ) -> "ServerToolResultMessage":
        """Create a server tool result message."""
        data = {
            "tool_name": tool_name,
            "tool_call_id": tool_call_id,
            "status": "completed" if success else "failed",
        }
        
        if success:
            data["result"] = result if isinstance(result, (str, dict, list, int, float, bool)) else str(result)
        else:
            data["error"] = error or "Tool execution failed"
        
        return cls(
            session_id=session_id,
            data=data
        )


# Union type for all server messages
ServerMessage = Union[
    ServerTextMessage,
    ServerPartialMessage,
    ServerSTTMessage,
    ServerErrorMessage,
    ServerConnectedMessage,
    ServerToolCallMessage,
    ServerToolResultMessage,
]


def parse_client_message(raw_message: Dict[str, Any]) -> ClientMessage:
    """Parse a raw client message into a typed message object."""
    try:
        msg_type = raw_message.get("type")
        
        if msg_type == "client_text":
            return ClientTextMessage(**raw_message)
        elif msg_type == "client_audio_start":
            return ClientAudioStartMessage(**raw_message)
        elif msg_type == "client_audio_chunk":
            return ClientAudioChunkMessage(**raw_message)
        elif msg_type == "client_audio_end":
            return ClientAudioEndMessage(**raw_message)
        else:
            raise MessageValidationError(f"Unknown message type: {msg_type}")
    except Exception as e:
        if isinstance(e, MessageValidationError):
            raise
        raise MessageValidationError(f"Failed to parse message: {str(e)}")

