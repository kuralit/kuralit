"""Standalone Function class for representing tools in Kuralit."""

from dataclasses import dataclass
from functools import partial
from inspect import getdoc, signature
from typing import Any, Callable, Dict, List, Optional, Type, get_type_hints

from docstring_parser import parse
from pydantic import BaseModel, Field


def get_entrypoint_docstring(entrypoint: Callable) -> str:
    """Extract docstring from a callable."""
    if isinstance(entrypoint, partial):
        return str(entrypoint)

    docstring = getdoc(entrypoint)
    if not docstring:
        return ""

    parsed_doc = parse(docstring)

    # Combine short and long descriptions
    lines = []
    if parsed_doc.short_description:
        lines.append(parsed_doc.short_description)
    if parsed_doc.long_description:
        lines.extend(parsed_doc.long_description.split("\n"))

    return "\n".join(lines)


def get_json_schema_from_type_hints(func: Callable) -> Dict[str, Any]:
    """Generate JSON schema from function type hints."""
    try:
        sig = signature(func)
        type_hints = get_type_hints(func)
        
        # Remove special parameters
        if "agent" in sig.parameters:
            sig = sig.replace(parameters=[p for p in sig.parameters.values() if p.name != "agent"])
        if "team" in sig.parameters:
            sig = sig.replace(parameters=[p for p in sig.parameters.values() if p.name != "team"])
        
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name in ["agent", "team"]:
                continue
                
            param_type = type_hints.get(param_name, Any)
            param_default = param.default
            
            # Convert Python types to JSON schema types
            if param_type == str or param_type == Any:
                param_schema = {"type": "string"}
            elif param_type == int:
                param_schema = {"type": "integer"}
            elif param_type == float:
                param_schema = {"type": "number"}
            elif param_type == bool:
                param_schema = {"type": "boolean"}
            elif param_type == list or param_type == List:
                param_schema = {"type": "array"}
            elif param_type == dict or param_type == Dict:
                param_schema = {"type": "object"}
            else:
                param_schema = {"type": "string"}  # Default to string
            
            # Add description from docstring if available
            docstring = getdoc(func)
            if docstring:
                parsed_doc = parse(docstring)
                for param_doc in parsed_doc.params:
                    if param_doc.arg_name == param_name:
                        param_schema["description"] = param_doc.description
                        break
            
            properties[param_name] = param_schema
            
            # Add to required if no default value
            if param_default == param.empty:
                required.append(param_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    except Exception:
        return {"type": "object", "properties": {}, "required": []}


class Function(BaseModel):
    """Model for storing functions that can be called by an agent."""

    # The name of the function to be called
    name: str
    
    # A description of what the function does
    description: Optional[str] = None
    
    # The parameters the function accepts, described as a JSON Schema object
    parameters: Dict[str, Any] = Field(
        default_factory=lambda: {"type": "object", "properties": {}, "required": []},
        description="JSON Schema object describing function parameters",
    )
    
    # The function to be called
    entrypoint: Optional[Callable] = None
    
    # If True, the function call will show the result
    show_result: bool = False
    
    # If True, the agent will stop after the function call
    stop_after_tool_call: bool = False
    
    # If True, the function will require confirmation before execution
    requires_confirmation: bool = False
    
    # If True, the function will be executed outside the agent's control
    external_execution: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert function to dictionary for API calls."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }

    @classmethod
    def from_callable(cls, c: Callable, name: Optional[str] = None) -> "Function":
        """Create a Function from a callable."""
        function_name = name or c.__name__
        
        # Get description from docstring
        description = get_entrypoint_docstring(c)
        if not description:
            description = f"Call the {function_name} function"
        
        # Get parameters schema
        parameters = get_json_schema_from_type_hints(c)
        
        return cls(
            name=function_name,
            description=description,
            parameters=parameters,
            entrypoint=c,
        )

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call the function entrypoint."""
        if self.entrypoint is None:
            raise ValueError(f"Function {self.name} has no entrypoint")
        return self.entrypoint(*args, **kwargs)

