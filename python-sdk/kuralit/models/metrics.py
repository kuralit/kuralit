"""Standalone Metrics class for KuralIt."""

from dataclasses import dataclass, field
from time import time
from typing import Optional


@dataclass
class Metrics:
    """Metrics for model usage and performance."""
    
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    
    # Timing metrics
    time_to_first_token: Optional[float] = None
    time_to_last_token: Optional[float] = None
    total_time: Optional[float] = None
    
    # Cost metrics
    cost: Optional[float] = None
    
    _start_time: Optional[float] = field(default=None, repr=False)
    _first_token_time: Optional[float] = field(default=None, repr=False)
    
    def start_timer(self) -> None:
        """Start the timer."""
        self._start_time = time()
    
    def stop_timer(self) -> None:
        """Stop the timer and calculate total time."""
        if self._start_time is not None:
            self.total_time = time() - self._start_time
    
    def set_time_to_first_token(self) -> None:
        """Set the time to first token."""
        if self._start_time is not None:
            self._first_token_time = time()
            self.time_to_first_token = self._first_token_time - self._start_time

