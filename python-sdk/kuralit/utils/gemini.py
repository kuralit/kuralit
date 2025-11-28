"""Standalone Gemini utility functions for KuralIt."""

import json
from typing import Any, Dict, List, Optional, Union


def format_function_definitions(tools: List[Union[Dict, Any]]) -> Dict[str, Any]:
    """Format function definitions for Gemini API.
    
    Args:
        tools: List of tool definitions (dicts or Function objects)
        
    Returns:
        Formatted tool definition for Gemini
    """
    function_declarations = []
    
    for tool in tools:
        if isinstance(tool, dict):
            # Already a dict, use it directly
            func_def = tool.copy()
        else:
            # Assume it's a Function-like object with to_dict method
            func_def = tool.to_dict() if hasattr(tool, 'to_dict') else {}
        
        # Ensure it has the right structure
        if "name" in func_def and "parameters" in func_def:
            function_declarations.append({
                "name": func_def["name"],
                "description": func_def.get("description", ""),
                "parameters": func_def.get("parameters", {})
            })
    
    return {"function_declarations": function_declarations}


def format_image_for_message(image: Any) -> Optional[Dict[str, Any]]:
    """Format an image for Gemini message.
    
    Args:
        image: Image object with content, url, or filepath
        
    Returns:
        Dictionary with mime_type and data, or None
    """
    if not image:
        return None
    
    # Try to get bytes
    image_bytes = None
    mime_type = "image/jpeg"  # Default
    
    if hasattr(image, 'get_content_bytes'):
        image_bytes = image.get_content_bytes()
    elif hasattr(image, 'content') and isinstance(image.content, bytes):
        image_bytes = image.content
    elif hasattr(image, 'filepath'):
        from pathlib import Path
        path = Path(image.filepath) if isinstance(image.filepath, str) else image.filepath
        if path.exists():
            image_bytes = path.read_bytes()
            # Try to determine mime type from extension
            ext = path.suffix.lower()
            mime_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
            }
            mime_type = mime_map.get(ext, 'image/jpeg')
    
    if image_bytes:
        return {
            "mime_type": mime_type,
            "data": image_bytes
        }
    
    return None


def prepare_response_schema(response_format: Optional[Union[Dict, Any]]) -> Optional[Dict[str, Any]]:
    """Prepare response schema for Gemini.
    
    Args:
        response_format: Response format (dict or Pydantic model)
        
    Returns:
        Schema dict for Gemini, or None
    """
    if response_format is None:
        return None
    
    if isinstance(response_format, dict):
        return response_format
    
    # If it's a Pydantic model, get its schema
    if hasattr(response_format, 'model_json_schema'):
        return response_format.model_json_schema()
    
    return None

