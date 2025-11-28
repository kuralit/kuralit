"""Standalone Toolkit class for managing tools in KuralIt."""

from collections import OrderedDict
from typing import Any, Callable, Dict, List, Optional, Union

from kuralit.tools.function import Function


class Toolkit:
    """A collection of tools that can be used by an agent."""

    def __init__(
        self,
        name: str = "toolkit",
        tools: List[Union[Callable, Function]] = [],
        instructions: Optional[str] = None,
        add_instructions: bool = False,
        include_tools: Optional[List[str]] = None,
        exclude_tools: Optional[List[str]] = None,
        requires_confirmation_tools: Optional[List[str]] = None,
        external_execution_required_tools: Optional[List[str]] = None,
        stop_after_tool_call_tools: Optional[List[str]] = None,
        show_result_tools: Optional[List[str]] = None,
        auto_register: bool = True,
    ):
        """Initialize a new Toolkit.

        Args:
            name: A descriptive name for the toolkit
            tools: List of tools (callables) to include in the toolkit
            instructions: Instructions for the toolkit
            add_instructions: Whether to add instructions to the toolkit
            include_tools: List of tool names to include in the toolkit
            exclude_tools: List of tool names to exclude from the toolkit
            requires_confirmation_tools: List of tool names that require user confirmation
            external_execution_required_tools: List of tool names that will be executed outside of the agent loop
            stop_after_tool_call_tools: List of function names that should stop the agent after execution
            show_result_tools: List of function names whose results should be shown
            auto_register: Whether to automatically register all methods in the class
        """
        self.name: str = name
        self.tools: List[Callable] = tools
        self.functions: Dict[str, Function] = OrderedDict()
        self.instructions: Optional[str] = instructions
        self.add_instructions: bool = add_instructions

        self.requires_confirmation_tools: List[str] = requires_confirmation_tools or []
        self.external_execution_required_tools: List[str] = external_execution_required_tools or []
        self.stop_after_tool_call_tools: List[str] = stop_after_tool_call_tools or []
        self.show_result_tools: List[str] = show_result_tools or []

        self.include_tools = include_tools
        self.exclude_tools = exclude_tools

        # Automatically register all methods if auto_register is True
        if auto_register and self.tools:
            self._register_tools()

    def _register_tools(self) -> None:
        """Register all tools."""
        for tool in self.tools:
            self.register(tool)

    def register(self, function: Any, name: Optional[str] = None) -> None:
        """Register a function with the toolkit.

        Args:
            function: The callable or Function object to register
            name: Optional custom name for the function
        """
        try:
            # Handle Function objects directly
            if isinstance(function, Function):
                f = function
                tool_name = name or f.name
                
                # Check include/exclude filters
                if self.include_tools is not None and tool_name not in self.include_tools:
                    return
                if self.exclude_tools is not None and tool_name in self.exclude_tools:
                    return
                
                # Update name if provided
                if name and name != f.name:
                    f.name = name
                    tool_name = name
                
                # Set special flags
                f.requires_confirmation = tool_name in self.requires_confirmation_tools
                f.external_execution = tool_name in self.external_execution_required_tools
                f.stop_after_tool_call = tool_name in self.stop_after_tool_call_tools
                f.show_result = (
                    tool_name in self.show_result_tools 
                    or tool_name in self.stop_after_tool_call_tools
                )
                
                self.functions[f.name] = f
                print(f"Function: {f.name} registered with {self.name}")
            else:
                # Handle callables - convert to Function
                tool_name = name or getattr(function, '__name__', 'unknown')
                
                # Check include/exclude filters
                if self.include_tools is not None and tool_name not in self.include_tools:
                    return
                if self.exclude_tools is not None and tool_name in self.exclude_tools:
                    return

                # Create Function from callable
                f = Function.from_callable(function, name=tool_name)
                
                # Set special flags
                f.requires_confirmation = tool_name in self.requires_confirmation_tools
                f.external_execution = tool_name in self.external_execution_required_tools
                f.stop_after_tool_call = tool_name in self.stop_after_tool_call_tools
                f.show_result = (
                    tool_name in self.show_result_tools 
                    or tool_name in self.stop_after_tool_call_tools
                )
                
                self.functions[f.name] = f
                print(f"Function: {f.name} registered with {self.name}")
        except Exception as e:
            func_name = getattr(function, 'name', None) or getattr(function, '__name__', 'unknown')
            print(f"Warning: Failed to create Function for: {func_name}: {e}")
            raise e

    def get_functions(self) -> List[Function]:
        """Get all registered functions."""
        return list(self.functions.values())

    def get_function(self, name: str) -> Optional[Function]:
        """Get a function by name."""
        return self.functions.get(name)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} functions={list(self.functions.keys())}>"

    def __str__(self) -> str:
        return self.__repr__()

