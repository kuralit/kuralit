"""Standalone Agent class for Kuralit - independent of agno package."""

from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from kuralit.tools.function import Function
from kuralit.tools.toolkit import Toolkit


class Agent:
    """A standalone agent that can use tools to interact with models."""

    def __init__(
        self,
        model: Any,  # Model instance (e.g., Gemini)
        name: Optional[str] = None,
        instructions: Optional[str] = None,
        tools: Optional[List[Union[Toolkit, Function, callable]]] = None,
        debug_mode: bool = False,
    ):
        """Initialize an Agent.

        Args:
            model: The model to use (must have a run/arun method)
            name: Name of the agent
            instructions: System instructions for the agent
            tools: List of tools (Toolkit, Function, or callable)
            debug_mode: Enable debug output
        """
        self.model = model
        self.name = name or "Agent"
        self.instructions = instructions
        self.debug_mode = debug_mode
        
        # Collect all functions from tools
        self.functions: Dict[str, Function] = {}
        self.toolkits: List[Toolkit] = []
        
        if tools:
            self._register_tools(tools)

    def _register_tools(self, tools: List[Union[Toolkit, Function, callable]]) -> None:
        """Register tools with the agent."""
        for tool in tools:
            if isinstance(tool, Toolkit):
                self.toolkits.append(tool)
                # Register all functions from the toolkit
                for func in tool.get_functions():
                    self.functions[func.name] = func
            elif isinstance(tool, Function):
                self.functions[tool.name] = tool
            elif callable(tool):
                # Convert callable to Function
                func = Function.from_callable(tool)
                self.functions[func.name] = func
            else:
                raise ValueError(f"Invalid tool type: {type(tool)}")

    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions in format expected by models."""
        return [func.to_dict() for func in self.functions.values()]

    def _execute_function(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a function by name."""
        if function_name not in self.functions:
            raise ValueError(f"Function {function_name} not found")
        
        func = self.functions[function_name]
        
        if self.debug_mode:
            print(f"[DEBUG] Executing function: {function_name} with args: {arguments}")
        
        try:
            result = func(**arguments)
            return result
        except Exception as e:
            error_msg = f"Error executing {function_name}: {str(e)}"
            if self.debug_mode:
                print(f"[DEBUG] {error_msg}")
            raise Exception(error_msg) from e

    def run(
        self,
        input: Union[str, Dict, List],
        stream: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Run the agent with the given input.

        Args:
            input: User input (string, dict, or list)
            stream: Whether to stream the response (not yet implemented)
            **kwargs: Additional arguments to pass to model

        Returns:
            Model response
        """
        from kuralit.models.message import Message
        
        # Prepare tool definitions for the model (as Function objects)
        tool_definitions = []
        for func in self.functions.values():
            tool_definitions.append(func)
        
        # Prepare messages - convert to Message objects
        message_objects = []
        
        # Add system instructions if provided
        if self.instructions:
            message_objects.append(Message(role="system", content=self.instructions))
        
        # Convert input to messages
        if isinstance(input, str):
            message_objects.append(Message(role="user", content=input))
        elif isinstance(input, list):
            for msg in input:
                if isinstance(msg, dict):
                    message_objects.append(Message(
                        role=msg.get("role", "user"),
                        content=msg.get("content", ""),
                    ))
                elif isinstance(msg, Message):
                    message_objects.append(msg)
                else:
                    message_objects.append(Message(role="user", content=str(msg)))
        elif isinstance(input, dict):
            message_objects.append(Message(
                role=input.get("role", "user"),
                content=input.get("content", ""),
            ))
        else:
            message_objects.append(Message(role="user", content=str(input)))
        
        # Call model.response() - this handles tool calls automatically
        if hasattr(self.model, 'response'):
            response = self.model.response(
                messages=message_objects,
                tools=tool_definitions if tool_definitions else None,
                tool_choice="auto" if tool_definitions else None,
                **kwargs
            )
        elif hasattr(self.model, 'aresponse'):
            import asyncio
            response = asyncio.run(self.model.aresponse(
                messages=message_objects,
                tools=tool_definitions if tool_definitions else None,
                tool_choice="auto" if tool_definitions else None,
                **kwargs
            ))
        else:
            raise ValueError("Model must have either 'response' or 'aresponse' method")
        
        return response

    def print_response(self, input: Union[str, Dict, List], stream: bool = False, **kwargs: Any) -> None:
        """Run the agent and print the response."""
        response = self.run(input=input, stream=stream, **kwargs)
        
        if stream:
            for chunk in response:
                if hasattr(chunk, 'content'):
                    print(chunk.content, end='', flush=True)
                elif isinstance(chunk, str):
                    print(chunk, end='', flush=True)
                elif isinstance(chunk, dict) and 'content' in chunk:
                    print(chunk['content'], end='', flush=True)
            print()  # New line at the end
        else:
            if hasattr(response, 'content'):
                print(response.content)
            elif hasattr(response, 'text'):
                print(response.text)
            elif isinstance(response, str):
                print(response)
            elif isinstance(response, dict):
                print(response.get('content', response))
            else:
                print(response)
