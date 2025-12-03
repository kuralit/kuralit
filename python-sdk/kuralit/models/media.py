"""Standalone media classes for Kuralit."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union


@dataclass
class Image:
    """Image media object."""
    
    content: Optional[Any] = None
    url: Optional[str] = None
    filepath: Optional[Union[str, Path]] = None
    format: Optional[str] = None
    
    def get_content_bytes(self) -> Optional[bytes]:
        """Get image content as bytes."""
        if self.content and isinstance(self.content, bytes):
            return self.content
        elif self.filepath:
            path = Path(self.filepath) if isinstance(self.filepath, str) else self.filepath
            if path.exists():
                return path.read_bytes()
        return None


@dataclass
class Video:
    """Video media object."""
    
    content: Optional[Any] = None
    url: Optional[str] = None
    filepath: Optional[Union[str, Path]] = None
    format: Optional[str] = None
    
    def get_content_bytes(self) -> Optional[bytes]:
        """Get video content as bytes."""
        if self.content and isinstance(self.content, bytes):
            return self.content
        elif self.filepath:
            path = Path(self.filepath) if isinstance(self.filepath, str) else self.filepath
            if path.exists():
                return path.read_bytes()
        return None


@dataclass
class Audio:
    """Audio media object."""
    
    content: Optional[Any] = None
    url: Optional[str] = None
    filepath: Optional[Union[str, Path]] = None
    format: Optional[str] = None
    
    def get_content_bytes(self) -> Optional[bytes]:
        """Get audio content as bytes."""
        if self.content and isinstance(self.content, bytes):
            return self.content
        elif self.filepath:
            path = Path(self.filepath) if isinstance(self.filepath, str) else self.filepath
            if path.exists():
                return path.read_bytes()
        return None


@dataclass
class File:
    """File media object."""
    
    content: Optional[Any] = None
    url: Optional[str] = None
    filepath: Optional[Union[str, Path]] = None
    format: Optional[str] = None
    mime_type: Optional[str] = None
    external: Optional[Any] = None  # For Gemini File objects
    
    def get_content_bytes(self) -> Optional[bytes]:
        """Get file content as bytes."""
        if self.content and isinstance(self.content, bytes):
            return self.content
        elif self.filepath:
            path = Path(self.filepath) if isinstance(self.filepath, str) else self.filepath
            if path.exists():
                return path.read_bytes()
        return None
    
    @property
    def file_url_content(self) -> Optional[tuple]:
        """Get file content from URL as (content, mime_type) tuple."""
        if self.url:
            try:
                import urllib.request
                import mimetypes
                
                with urllib.request.urlopen(self.url) as response:
                    content = response.read()
                    mime_type = response.headers.get('Content-Type') or mimetypes.guess_type(self.url)[0]
                    return (content, mime_type)
            except Exception:
                return None
        return None

