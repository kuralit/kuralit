"""Standalone base Model class for KuralIt."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, Union
from pydantic import BaseModel as PydanticBaseModel

from kuralit.models.message import Message
from kuralit.models.response import ModelResponse
from kuralit.tools.function import Function
from kuralit.utils.log import log_debug, log_error


@dataclass
class Model(ABC):
    """Base class for all models in KuralIt."""
    
    # ID of the model to use
    id: str
    
    # Name for this Model
    name: Optional[str] = None
    
    # Provider for this Model
    provider: Optional[str] = None
    
    # True if the Model supports structured outputs natively
    supports_native_structured_outputs: bool = False
    
    # True if the Model requires a json_schema for structured outputs
    supports_json_schema_outputs: bool = False
    
    # Controls which (if any) function is called by the model
    _tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    
    # System prompt from the model
    system_prompt: Optional[str] = None
    
    # Instructions from the model
    instructions: Optional[List[str]] = None
    
    # The role of the tool message
    tool_message_role: str = "tool"
    
    # The role of the assistant message
    assistant_message_role: str = "assistant"
    
    def __post_init__(self):
        if self.provider is None and self.name is not None:
            self.provider = f"{self.name} ({self.id})"
    
    def get_provider(self) -> str:
        """Get the provider name."""
        return self.provider or self.name or self.id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "name": self.name,
            "id": self.id,
            "provider": self.provider,
        }
    
    def _format_tools(self, tools: Optional[List[Union[Function, dict]]]) -> List[Dict[str, Any]]:
        """Format tools for the model."""
        if tools is None:
            return []
        
        tool_dicts = []
        for tool in tools:
            if isinstance(tool, Function):
                tool_dicts.append(tool.to_dict())
            elif isinstance(tool, dict):
                tool_dicts.append(tool)
        
        return tool_dicts
    
    @abstractmethod
    def invoke(
        self,
        messages: List[Message],
        assistant_message: Message,
        response_format: Optional[Union[Dict, Type[PydanticBaseModel]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        run_response: Optional[Any] = None,
    ) -> ModelResponse:
        """Invoke the model with messages and return response.
        
        This must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement invoke()")
    
    def _process_model_response(
        self,
        messages: List[Message],
        assistant_message: Message,
        model_response: ModelResponse,
        response_format: Optional[Union[Dict, Type[PydanticBaseModel]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        run_response: Optional[Any] = None,
    ) -> None:
        """Process a single model response."""
        # Generate response by calling invoke
        provider_response = self.invoke(
            assistant_message=assistant_message,
            messages=messages,
            response_format=response_format,
            tools=tools,
            tool_choice=tool_choice or self._tool_choice,
            run_response=run_response,
        )
        
        # Populate the assistant message
        self._populate_assistant_message(assistant_message=assistant_message, provider_response=provider_response)
        
        # Update model response with assistant message content
        if assistant_message.content is not None:
            if model_response.content is None:
                model_response.content = str(assistant_message.content)
            else:
                model_response.content += str(assistant_message.content)
        
        # Copy tool calls
        if assistant_message.tool_calls:
            model_response.tool_calls = assistant_message.tool_calls
    
    def _populate_assistant_message(
        self,
        assistant_message: Message,
        provider_response: ModelResponse,
    ) -> None:
        """Populate an assistant message with the provider response data."""
        if provider_response.role is not None:
            assistant_message.role = provider_response.role
        
        # Add content to assistant message
        if provider_response.content is not None:
            assistant_message.content = provider_response.content
        
        # Add tool calls to assistant message
        if provider_response.tool_calls is not None and len(provider_response.tool_calls) > 0:
            assistant_message.tool_calls = provider_response.tool_calls
    
    def format_function_call_results(
        self,
        messages: List[Message],
        function_call_results: List[Message],
        **kwargs: Any
    ) -> None:
        """Format function call results and add them to messages."""
        combined_content: List = []
        combined_function_result: List = []
        
        if len(function_call_results) > 0:
            for result in function_call_results:
                combined_content.append(result.content)
                # Handle tool_name attribute
                tool_name = getattr(result, 'tool_name', None) or getattr(result, 'name', 'unknown')
                combined_function_result.append({
                    "tool_name": tool_name,
                    "content": result.content
                })
        
        if combined_content:
            messages.append(
                Message(
                    role="tool",
                    content=combined_content,
                    tool_calls=combined_function_result,
                )
            )
    
    def response(
        self,
        messages: List[Message],
        response_format: Optional[Union[Dict, Type[PydanticBaseModel]]] = None,
        tools: Optional[List[Union[Function, dict]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        tool_call_limit: Optional[int] = None,
        run_response: Optional[Any] = None,
        send_media_to_model: bool = True,
    ) -> ModelResponse:
        """
        Generate a response from the model.
        
        This method handles the tool call loop automatically.
        
        Args:
            messages: List of messages to send to the model
            response_format: Response format to use
            tools: List of tools to use (Function objects or dicts)
            tool_choice: Tool choice to use
            tool_call_limit: Maximum number of tool calls
            run_response: Run response context
            send_media_to_model: Whether to send media to the model
            
        Returns:
            ModelResponse: The model response
        """
        log_debug(f"{self.get_provider()} Response Start", center=True, symbol="-")
        log_debug(f"Model: {self.id}", center=True, symbol="-")
        
        model_response = ModelResponse()
        function_call_count = 0
        
        # Format tools
        _tool_dicts = self._format_tools(tools) if tools is not None else []
        _functions = {tool.name: tool for tool in tools if isinstance(tool, Function)} if tools is not None else {}
        
        while True:
            # Get response from model
            assistant_message = Message(role=self.assistant_message_role)
            self._process_model_response(
                messages=messages,
                assistant_message=assistant_message,
                model_response=model_response,
                response_format=response_format,
                tools=_tool_dicts,
                tool_choice=tool_choice or self._tool_choice,
                run_response=run_response,
            )
            
            # Add assistant message to messages
            messages.append(assistant_message)
            
            # Handle tool calls if present
            if assistant_message.tool_calls:
                # Print reasoning/chain of thought if available
                if model_response.reasoning_content:
                    print("\n🤔 Chain of Thought / Reasoning:")
                    print("-" * 60)
                    print(model_response.reasoning_content)
                    print("-" * 60)
                    print()
                
                # Print available tools for context
                if _functions:
                    print(f"📋 Available tools: {', '.join(_functions.keys())}")
                    print()
                
                # Execute function calls
                function_call_results: List[Message] = []
                
                print(f"🔧 Executing {len(assistant_message.tool_calls)} tool call(s)...")
                print()
                
                for tool_call in assistant_message.tool_calls:
                    if isinstance(tool_call, dict):
                        func_name = tool_call.get("function", {}).get("name") or tool_call.get("name")
                        func_args_str = tool_call.get("function", {}).get("arguments", "{}")
                        
                        # Parse arguments
                        import json
                        try:
                            func_args = json.loads(func_args_str) if isinstance(func_args_str, str) else func_args_str
                        except:
                            func_args = {}
                        
                        # Print tool selection reasoning
                        print(f"  → Selected tool: {func_name}")
                        if func_args:
                            print(f"    Arguments: {func_args}")
                        print()
                        
                        # Get function and execute
                        if func_name in _functions:
                            func = _functions[func_name]
                            try:
                                print(f"    Executing {func_name}...")
                                # Execute the function - Function objects are callable
                                if hasattr(func, 'entrypoint') and func.entrypoint:
                                    result = func.entrypoint(**func_args)
                                elif callable(func):
                                    result = func(**func_args)
                                else:
                                    result = f"Function {func_name} is not callable"
                                
                                result_preview = str(result)[:100] + "..." if len(str(result)) > 100 else str(result)
                                print(f"    ✓ Result: {result_preview}")
                                print()
                                
                                function_call_results.append(
                                    Message(
                                        role="tool",
                                        content=str(result),
                                        tool_calls=[{
                                            "tool_name": func_name,
                                            "content": str(result)
                                        }]
                                    )
                                )
                            except Exception as e:
                                error_msg = f"Error executing {func_name}: {str(e)}"
                                print(f"    ✗ {error_msg}")
                                print()
                                function_call_results.append(
                                    Message(
                                        role="tool",
                                        content=error_msg,
                                        tool_calls=[{
                                            "tool_name": func_name,
                                            "content": error_msg
                                        }]
                                    )
                                )
                        else:
                            print(f"    ✗ Tool {func_name} not found in available functions")
                            print()
                
                # Add a function call for each successful execution
                function_call_count += len(function_call_results)
                
                # Format and add results to messages
                self.format_function_call_results(
                    messages=messages,
                    function_call_results=function_call_results,
                    **model_response.extra or {}
                )
                
                # Check tool call limit
                if tool_call_limit and function_call_count >= tool_call_limit:
                    break
                
                # Continue loop to get next response
                continue
            
            # No tool calls or finished processing them
            break
        
        log_debug(f"{self.get_provider()} Response End", center=True, symbol="-")
        
        return model_response

