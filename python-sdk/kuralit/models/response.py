"""Standalone ModelResponse class for Kuralit."""

from dataclasses import dataclass, field
from time import time
from typing import Any, Dict, List, Optional

from kuralit.models.metrics import Metrics


@dataclass
class ToolExecution:
    """Represents a tool execution."""
    
    id: str
    name: str
    content: Any
    result: Optional[Any] = None
    error: Optional[str] = None
    metrics: Optional[Metrics] = None


@dataclass
class ModelResponse:
    """Response from the model provider."""
    
    role: Optional[str] = None
    content: Optional[Any] = None
    parsed: Optional[Any] = None
    
    # Media fields
    images: Optional[List[Any]] = None
    videos: Optional[List[Any]] = None
    audios: Optional[List[Any]] = None
    files: Optional[List[Any]] = None
    
    # Model tool calls
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    
    # Actual tool executions
    tool_executions: Optional[List[ToolExecution]] = field(default_factory=list)
    
    event: str = "assistant_response"
    
    provider_data: Optional[Dict[str, Any]] = None
    
    reasoning_content: Optional[str] = None
    
    citations: Optional[Any] = None
    
    response_usage: Optional[Metrics] = None
    
    created_at: int = field(default_factory=lambda: int(time()))
    
    extra: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize ModelResponse to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "tool_calls": self.tool_calls,
            "created_at": self.created_at,
        }

