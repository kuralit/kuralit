"""Standalone exception classes for KuralIt."""
from typing import Optional

class ModelProviderError(Exception):
    """Exception raised when a model provider returns an error."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        model_name: Optional[str] = None,
        model_id: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.model_name = model_name
        self.model_id = model_id
        super().__init__(self.message)

