"""LLM plugins for Kuralit.

This module provides access to all LLM plugins.
"""

# Import gemini module to trigger auto-registration
from kuralit.plugins.llm import gemini

__all__ = ["gemini"]

