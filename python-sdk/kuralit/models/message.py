"""Standalone Message class for KuralIt."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from kuralit.models.metrics import Metrics


@dataclass
class Citations:
    """Citations from the model."""
    pass


@dataclass
class UrlCitation:
    """URL citation."""
    url: str
    title: Optional[str] = None


@dataclass
class Message:
    """Message class for conversation."""
    
    role: str
    content: Optional[Any] = None
    
    # Tool calls
    tool_calls: Optional[List[Dict[str, Any]]] = None
    
    # Media
    images: Optional[List[Any]] = None
    videos: Optional[List[Any]] = None
    audios: Optional[List[Any]] = None
    files: Optional[List[Any]] = None
    
    # Citations
    citations: Optional[Citations] = None
    
    # Metrics
    metrics: Metrics = field(default_factory=Metrics)
    
    # Additional metadata
    stop_after_tool_call: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        result = {
            "role": self.role,
            "content": self.content,
        }
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        return result

