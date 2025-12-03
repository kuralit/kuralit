"""Agent integration handler for WebSocket server."""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import AsyncIterator, Dict, List, Optional

logger = logging.getLogger(__name__)

from kuralit.agent import Agent
from kuralit.plugins.llm.gemini import Gemini
from kuralit.models.message import Message
from kuralit.models.response import ModelResponse
from kuralit.tools.api import RESTAPIToolkit

from kuralit.server.agent_session import AgentSession
from kuralit.server.config import ServerConfig
from kuralit.server.event_bus import EventBus
from kuralit.server.exceptions import AgentError
from kuralit.server.metrics import MetricsCollector
from kuralit.server.protocol import (
    ServerPartialMessage,
    ServerSTTMessage,
    ServerTextMessage,
    ServerToolCallMessage,
    ServerToolResultMessage,
)
from kuralit.server.session import Session


class AgentHandler:
    """Handles agent processing for WebSocket server."""
    
    def __init__(
        self,
        agent_session: Optional[AgentSession] = None,
        config: Optional[ServerConfig] = None,
        metrics: Optional[MetricsCollector] = None,
        event_bus: Optional[EventBus] = None,
    ):
        """Initialize agent handler.
        
        Args:
            agent_session: Optional AgentSession configuration (takes precedence)
            config: Optional server configuration (fallback if agent_session not provided)
            metrics: Optional metrics collector
            event_bus: Optional event bus for broadcasting events
        """
        # Store event bus
        self.event_bus = event_bus
        
        # Use AgentSession if provided, otherwise use config
        if agent_session:
            self.config = agent_session._config.server if agent_session._config else (config or ServerConfig())
            self.metrics = metrics
            
            # Extract from AgentSession
            self.model = agent_session.llm
            self.tools = agent_session.tools or []
            self.instructions = agent_session.instructions
            self.name = agent_session.name
            
            # Log instructions status
            if self.instructions:
                logger.info(f"AgentHandler: Instructions loaded from AgentSession (length: {len(self.instructions)} chars)")
                logger.debug(f"AgentHandler: Instructions preview: {self.instructions[:150]}...")
            else:
                logger.warning("AgentHandler: No instructions provided in AgentSession")
        elif config:
            # Fallback to old config-based approach
            self.config = config
            self.metrics = metrics
            
            # Create Gemini model (old way)
            self.model = Gemini(
                id=config.agent_model_id,
                api_key=config.agent_api_key,
                include_thoughts=True,
            )
            
            # Load REST API tools if Postman collection is provided
            tools = []
            if config.postman_collection_path:
                try:
                    # Resolve collection path
                    collection_path = Path(config.postman_collection_path)
                    if not collection_path.is_absolute():
                        # Try relative to project root
                        project_root = Path(__file__).parent.parent.parent.parent
                        resolved_path = project_root / collection_path
                        if not resolved_path.exists():
                            # Try relative to current working directory
                            resolved_path = Path.cwd() / collection_path
                        if resolved_path.exists():
                            collection_path = resolved_path.resolve()
                        else:
                            raise FileNotFoundError(
                                f"Postman collection not found: {config.postman_collection_path}. "
                                f"Tried: {project_root / config.postman_collection_path}, "
                                f"{Path.cwd() / config.postman_collection_path}"
                            )
                    else:
                        if not collection_path.exists():
                            raise FileNotFoundError(f"Postman collection not found: {collection_path}")
                        collection_path = collection_path.resolve()
                    
                    # Create REST API toolkit from Postman collection
                    api_toolkit = RESTAPIToolkit.from_postman_collection(
                        collection_path=str(collection_path),
                        base_url=config.api_base_url,
                        # api_key can be added if needed
                        # headers=config.api_headers,
                    )
                    tools.append(api_toolkit)
                    
                    # Log available tools
                    if config.debug:
                        print(f"✅ Loaded REST API tools from: {collection_path}")
                        if hasattr(api_toolkit, 'get_functions'):
                            functions = api_toolkit.get_functions()
                            print(f"   Available API tools: {len(functions)}")
                            if len(functions) <= 10:
                                print(f"   Tools: {', '.join(f.name for f in functions)}")
                            else:
                                print(f"   Tools: {', '.join(f.name for f in functions[:10])}... and {len(functions) - 10} more")
                except Exception as e:
                    import warnings
                    warnings.warn(
                        f"Failed to load REST API tools from Postman collection: {e}. "
                        f"Continuing without API tools."
                    )
        
            # Create agent with tools (old way)
            instructions = "You are a helpful assistant with access to realtime communication. "
            if tools:
                instructions += "You also have access to REST API endpoints. Use the available API tools to help users interact with APIs when needed. "
            instructions += "Provide clear, concise, and helpful responses."
            
            self.tools = tools
            self.instructions = instructions
            self.name = "WebSocket Agent"
        else:
            # No config or agent_session - create minimal defaults
            self.config = ServerConfig()
            self.metrics = metrics
            raise ValueError("Either agent_session or config must be provided")
        
        # Create agent with instructions
        # Log tool registration for debugging
        if self.tools:
            logger.info(f"AgentHandler: Registering {len(self.tools)} toolkit(s) with agent")
            for i, tool in enumerate(self.tools):
                if hasattr(tool, 'get_functions'):
                    functions = tool.get_functions()
                    logger.info(f"  Toolkit {i+1}: {len(functions)} functions - {', '.join(f.name for f in functions[:5])}{'...' if len(functions) > 5 else ''}")
        else:
            logger.info("AgentHandler: No tools provided to agent")
        
        self.agent = Agent(
            model=self.model,
            name=self.name,
            instructions=self.instructions,
            tools=self.tools if self.tools else None,
            debug_mode=self.config.debug,
        )
        
        # Log registered functions
        if self.agent.functions:
            logger.info(f"AgentHandler: Agent has {len(self.agent.functions)} registered functions: {', '.join(list(self.agent.functions.keys())[:5])}{'...' if len(self.agent.functions) > 5 else ''}")
        else:
            logger.warning("AgentHandler: Agent has NO registered functions despite tools being provided")
    
    def _prepare_messages_with_instructions(self, messages: List[Message]) -> List[Message]:
        """Prepare messages with system instructions if provided.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            List of messages with system instructions prepended if available
        """
        # Check if messages already have a system message
        has_system_message = any(msg.role == "system" for msg in messages)
        
        # Check if there are tool results in the messages
        has_tool_results = any(msg.role == "tool" for msg in messages)
        
        # Add system instructions if provided and not already present
        if self.instructions and not has_system_message:
            instructions = self.instructions
            
            # If tool results are present, add an extra reminder to convert them to natural language
            if has_tool_results:
                reminder = "\n\nREMINDER: You have just received tool/API results. You MUST convert these results into natural, conversational English. NEVER output the raw JSON, code blocks, or technical data structures. Extract the meaningful information and present it as if you're telling a friend about it."
                instructions = instructions + reminder
                logger.debug("AgentHandler: Added tool result conversion reminder to instructions")
            
            system_message = Message(role="system", content=instructions)
            logger.info(f"AgentHandler: Adding system instructions to messages (length: {len(instructions)} chars)")
            logger.debug(f"AgentHandler: System instructions preview: {instructions[:100]}...")
            return [system_message] + messages
        elif has_system_message:
            logger.debug("AgentHandler: System message already present in conversation history")
        elif not self.instructions:
            logger.debug("AgentHandler: No instructions provided, using default behavior")
        return messages
    
    async def process_text_async(
        self,
        session: Session,
        text: str,
        metadata: Optional[Dict] = None,
    ) -> AsyncIterator[ServerPartialMessage | ServerTextMessage | ServerToolCallMessage | ServerToolResultMessage]:
        """Process text input and stream response.
        
        Args:
            session: Session object
            text: Input text
            metadata: Optional metadata
            
        Yields:
            ServerPartialMessage, ServerTextMessage, ServerToolCallMessage, 
            or ServerToolResultMessage
        """
        start_time = time.time()
        
        try:
            # Add user message to conversation
            user_message = Message(role="user", content=text)
            session.add_message(user_message)
            
            # Get conversation history
            messages = session.get_conversation_history()
            
            # Use agent.run() which handles tool calls automatically
            # But we need to stream the response, so we'll use the model directly
            # and handle tool calls if needed
            
            # Check if agent has tools (REST API tools)
            has_tools = self.agent.functions and len(self.agent.functions) > 0
            
            # Prepare tool definitions if tools are available
            # Convert Function objects to dicts for Gemini API
            tool_definitions = []
            if has_tools:
                for func in self.agent.functions.values():
                    # Convert Function to dict format expected by Gemini
                    if hasattr(func, 'to_dict'):
                        tool_definitions.append(func.to_dict())
                    elif isinstance(func, dict):
                        tool_definitions.append(func)
                    else:
                        logger.warning(f"AgentHandler: Function {func.name} cannot be converted to dict")
                logger.info(f"AgentHandler: Prepared {len(tool_definitions)} tool definitions for model: {[f.get('name', 'unknown') for f in tool_definitions[:5]]}")
            else:
                logger.debug("AgentHandler: No tools available for this request")
            
            # Use model's response method which handles tool calls automatically
            # We'll use aresponse for async support
            assistant_message = Message(role="assistant")
            messages.append(assistant_message)
            
            # Prepare messages with system instructions
            messages_with_instructions = self._prepare_messages_with_instructions(messages[:-1])
            
            # Log message structure for debugging
            message_roles = [msg.role for msg in messages_with_instructions]
            logger.debug(f"AgentHandler: Sending {len(messages_with_instructions)} messages to LLM with roles: {message_roles}")
            if messages_with_instructions and messages_with_instructions[0].role == "system":
                logger.info(f"AgentHandler: System instructions included in LLM request (first message is system)")
            
            accumulated_text = ""
            collected_tool_calls = []
            
            # Stream response with tool support
            async for response_chunk in self.model.ainvoke_stream(
                messages=messages_with_instructions,
                assistant_message=assistant_message,
                tools=tool_definitions if tool_definitions else None,
                tool_choice="auto" if tool_definitions else None,
            ):
                if response_chunk.content:
                    chunk_text = response_chunk.content
                    accumulated_text += chunk_text
                    
                    # Yield partial message
                    yield ServerPartialMessage.create(
                        session_id=session.session_id,
                        text=chunk_text,
                        is_final=False,
                    )
                
                # Collect tool calls from chunks
                if response_chunk.tool_calls:
                    collected_tool_calls.extend(response_chunk.tool_calls)
            
            # After streaming, check if we need to handle tool calls
            # Use collected_tool_calls or assistant_message.tool_calls
            tool_calls_to_execute = collected_tool_calls if collected_tool_calls else (assistant_message.tool_calls or [])
            
            if tool_calls_to_execute:
                # Execute tool calls using agent's method
                try:
                    # Execute collected tool calls
                    function_call_results = []
                    for tool_call in tool_calls_to_execute:
                        func_name = tool_call.get("function", {}).get("name", "unknown")
                        func_args_str = tool_call.get("function", {}).get("arguments", "{}")
                        tool_call_id = tool_call.get("id") or tool_call.get("function", {}).get("id")
                        
                        try:
                            import json
                            func_args = json.loads(func_args_str) if isinstance(func_args_str, str) else func_args_str
                            
                            # Notify client that tool is being called
                            yield ServerToolCallMessage.create(
                                session_id=session.session_id,
                                tool_name=func_name,
                                tool_arguments=func_args,
                                tool_call_id=tool_call_id,
                            )
                            
                            # Emit tool_call_start event
                            if self.event_bus:
                                await self.event_bus.publish(
                                    event_type="tool_call_start",
                                    session_id=session.session_id,
                                    data={
                                        "tool_name": func_name,
                                        "tool_arguments": func_args,
                                        "tool_call_id": tool_call_id,
                                    }
                                )
                            
                            # Record tool call in metrics
                            if self.metrics:
                                self.metrics.record_tool_call(session.session_id)
                                # Note: metrics_updated will be emitted after agent response completes
                            
                            # Execute the function in a thread pool to avoid blocking the event loop
                            # Tool execution (HTTP requests) is synchronous and can take time
                            logger.info(f"AgentHandler: Executing tool '{func_name}' with args: {func_args}")
                            loop = asyncio.get_event_loop()
                            try:
                                # Run in executor with timeout
                                result = await asyncio.wait_for(
                                    loop.run_in_executor(
                                        None,
                                        self.agent._execute_function,
                                        func_name,
                                        func_args
                                    ),
                                    timeout=30.0  # 30 second timeout for tool execution
                                )
                                logger.info(f"AgentHandler: Tool '{func_name}' completed successfully")
                                
                                # Emit tool_call_complete event
                                if self.event_bus:
                                    # Format result preview for event (truncate if too long)
                                    result_preview = str(result)
                                    if len(result_preview) > 500:
                                        result_preview = result_preview[:500] + "..."
                                    
                                    await self.event_bus.publish(
                                        event_type="tool_call_complete",
                                        session_id=session.session_id,
                                        data={
                                            "tool_name": func_name,
                                            "tool_call_id": tool_call_id,
                                            "result_preview": result_preview,
                                            "success": True,
                                        }
                                    )
                            except asyncio.TimeoutError:
                                error_msg = f"Tool '{func_name}' execution timed out after 30 seconds"
                                logger.error(error_msg)
                                
                                # Emit tool_call_error event
                                if self.event_bus:
                                    await self.event_bus.publish(
                                        event_type="tool_call_error",
                                        session_id=session.session_id,
                                        data={
                                            "tool_name": func_name,
                                            "tool_call_id": tool_call_id,
                                            "error": error_msg,
                                            "error_type": "timeout",
                                        }
                                    )
                                
                                raise TimeoutError(error_msg)
                            
                            # Notify client of tool result
                            yield ServerToolResultMessage.create(
                                session_id=session.session_id,
                                tool_name=func_name,
                                result=result,
                                tool_call_id=tool_call_id,
                                success=True,
                            )
                            
                            # Format tool result properly for Gemini function response
                            # REST API tools return json.dumps() which is already a JSON string
                            # We need to ensure it's clean and properly formatted
                            import json
                            
                            # Log raw result for debugging
                            result_preview = str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
                            logger.debug(f"AgentHandler: Raw tool result from '{func_name}': {result_preview}")
                            logger.debug(f"AgentHandler: Tool result type: {type(result)}")
                            
                            # Format tool result content
                            if isinstance(result, str):
                                # Result is already a string - could be JSON string or plain text
                                tool_result_content = result
                                # Try to parse and re-serialize to ensure it's valid JSON
                                # This helps catch nested JSON strings (double-encoded)
                                try:
                                    parsed = json.loads(result)
                                    # If it parses successfully, re-serialize to ensure clean format
                                    # This handles cases where JSON might be nested as a string
                                    tool_result_content = json.dumps(parsed, ensure_ascii=False)
                                    logger.debug(f"AgentHandler: Tool result parsed and re-serialized as JSON")
                                except (json.JSONDecodeError, TypeError):
                                    # Not JSON, use as-is (plain text result)
                                    tool_result_content = result
                                    logger.debug(f"AgentHandler: Tool result is plain text, using as-is")
                            elif isinstance(result, (dict, list)):
                                # Result is a dict/list - serialize to JSON
                                tool_result_content = json.dumps(result, ensure_ascii=False)
                                logger.debug(f"AgentHandler: Tool result is dict/list, serialized to JSON")
                            else:
                                # Other types - convert to string
                                tool_result_content = str(result)
                                logger.debug(f"AgentHandler: Tool result is {type(result)}, converted to string")
                            
                            # Log formatted content preview
                            content_preview = tool_result_content[:200] + "..." if len(tool_result_content) > 200 else tool_result_content
                            logger.debug(f"AgentHandler: Formatted tool result content: {content_preview}")
                            
                            # Create Message with proper structure for Gemini function response
                            # Gemini expects: role="tool" with tool_calls containing tool_name and content
                            tool_result_message = Message(
                                role="tool",
                                content=tool_result_content,
                                tool_calls=[{
                                    "tool_name": func_name,
                                    "content": tool_result_content
                                }]
                            )
                            
                            # Log the Message structure for debugging
                            logger.debug(f"AgentHandler: Created tool result Message - role={tool_result_message.role}, "
                                       f"tool_calls count={len(tool_result_message.tool_calls) if tool_result_message.tool_calls else 0}")
                            
                            function_call_results.append(tool_result_message)
                        except Exception as e:
                            error_msg = str(e)
                            if self.config.debug:
                                print(f"Error executing tool {func_name}: {error_msg}")
                            
                            # Emit tool_call_error event
                            if self.event_bus:
                                await self.event_bus.publish(
                                    event_type="tool_call_error",
                                    session_id=session.session_id,
                                    data={
                                        "tool_name": func_name,
                                        "tool_call_id": tool_call_id,
                                        "error": error_msg,
                                        "error_type": "execution_error",
                                    }
                                )
                            
                            # Notify client of tool error
                            yield ServerToolResultMessage.create(
                                session_id=session.session_id,
                                tool_name=func_name,
                                result=None,
                                tool_call_id=tool_call_id,
                                success=False,
                                error=error_msg,
                            )
                            
                            function_call_results.append(Message(
                                role="tool",
                                content=f"Error: {error_msg}",
                                tool_calls=[{
                                    "tool_name": func_name,
                                    "content": f"Error: {error_msg}"
                                }]
                            ))
                    
                    # Add tool results to conversation
                    for result in function_call_results:
                        session.add_message(result)
                        # Log each tool result message structure
                        logger.debug(f"AgentHandler: Added tool result message to session - "
                                   f"role={result.role}, "
                                   f"has_tool_calls={result.tool_calls is not None and len(result.tool_calls) > 0}, "
                                   f"content_length={len(str(result.content)) if result.content else 0}")
                    
                    # Continue with another round - get final response with tool results
                    messages = session.get_conversation_history()
                    assistant_message = Message(role="assistant")
                    messages.append(assistant_message)
                    
                    # Prepare messages with system instructions
                    messages_with_instructions = self._prepare_messages_with_instructions(messages[:-1])
                    
                    # Log detailed message structure for debugging (second round after tool execution)
                    message_roles = [msg.role for msg in messages_with_instructions]
                    logger.info(f"AgentHandler: Sending {len(messages_with_instructions)} messages to LLM (after tool execution) with roles: {message_roles}")
                    
                    # Log tool messages specifically
                    tool_messages = [msg for msg in messages_with_instructions if msg.role == "tool"]
                    if tool_messages:
                        logger.info(f"AgentHandler: Found {len(tool_messages)} tool result message(s) in conversation")
                        for i, tool_msg in enumerate(tool_messages):
                            tool_calls_info = "has tool_calls" if tool_msg.tool_calls else "no tool_calls"
                            content_preview = str(tool_msg.content)[:100] + "..." if tool_msg.content and len(str(tool_msg.content)) > 100 else str(tool_msg.content)
                            logger.debug(f"AgentHandler: Tool message {i+1}: role={tool_msg.role}, {tool_calls_info}, "
                                       f"content_preview={content_preview}")
                            if tool_msg.tool_calls:
                                for j, tc in enumerate(tool_msg.tool_calls):
                                    logger.debug(f"AgentHandler:   Tool call {j+1}: tool_name={tc.get('tool_name')}, "
                                               f"content_length={len(str(tc.get('content', '')))}")
                    
                    # The system instructions should already handle conversion to natural language
                    if tool_messages:
                        logger.debug("AgentHandler: Tool results present in conversation - LLM should convert to natural language per instructions")
                    
                    # Stream the final response after tool execution
                    final_text = ""
                    async for response_chunk in self.model.ainvoke_stream(
                        messages=messages_with_instructions,
                        assistant_message=assistant_message,
                        tools=tool_definitions if tool_definitions else None,
                        tool_choice="auto" if tool_definitions else None,
                    ):
                        if response_chunk.content:
                            chunk_text = response_chunk.content
                            final_text += chunk_text
                            
                            # Yield partial message
                            yield ServerPartialMessage.create(
                                session_id=session.session_id,
                                text=chunk_text,
                                is_final=False,
                            )
                    
                    accumulated_text = final_text
                except Exception as e:
                    error_msg = f"Error handling tool calls: {str(e)}"
                    logger.error(f"[Agent] Tool handling error: {error_msg}, session={session.session_id}", exc_info=True)
                    # If we had accumulated text from first response, use it; otherwise set empty
                    if not accumulated_text:
                        accumulated_text = ""
                    # Log but don't raise - we'll still send what we have
                    # The accumulated_text from the initial response will be sent as final message
            
            # Final message
            if accumulated_text:
                assistant_message.content = accumulated_text
                session.add_message(assistant_message)
                
                # Record metrics
                latency_ms = (time.time() - start_time) * 1000
                if self.metrics:
                    self.metrics.record_agent_response(latency_ms, session.session_id)
                
                yield ServerTextMessage.create(
                    session_id=session.session_id,
                    text=accumulated_text,
                    metadata=metadata,
                )
            else:
                # Empty response
                yield ServerTextMessage.create(
                    session_id=session.session_id,
                    text="",
                    metadata=metadata,
                )
                
        except Exception as e:
            error_msg = f"Agent processing failed: {str(e)}"
            if self.metrics:
                self.metrics.record_error(session.session_id)
            raise AgentError(error_msg, retriable=False) from e
    
    async def process_transcription_async(
        self,
        session: Session,
        transcription: str,
        metadata: Optional[Dict] = None,
    ) -> AsyncIterator[ServerPartialMessage | ServerTextMessage | ServerToolCallMessage | ServerToolResultMessage]:
        """Process STT transcription and stream response.
        
        Args:
            session: Session object
            transcription: Transcribed text
            metadata: Optional metadata
            
        Yields:
            ServerPartialMessage, ServerTextMessage, 
            ServerToolCallMessage, or ServerToolResultMessage
            
        Note: ServerSTTMessage is sent separately by the websocket server
        before calling this method, so we don't send it here to avoid duplicates.
        """
        # Process as text (STT message is already sent by websocket_server)
        async for message in self.process_text_async(session, transcription, metadata):
            yield message
    
    async def process_audio_async(
        self,
        session: Session,
        audio_bytes: bytes,
        sample_rate: int,
        encoding: str,
        metadata: Optional[Dict] = None,
    ) -> AsyncIterator[ServerPartialMessage | ServerTextMessage]:
        """Process audio input (directly to agent, bypassing STT).
        
        Note: This is for future use when Gemini supports direct audio input.
        Currently, audio should be transcribed first using STT.
        
        Args:
            session: Session object
            audio_bytes: Audio bytes
            sample_rate: Sample rate
            encoding: Encoding format
            metadata: Optional metadata
            
        Yields:
            ServerPartialMessage or ServerTextMessage
        """
        raise NotImplementedError("Direct audio processing not yet implemented. Use STT first.")

