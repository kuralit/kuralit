"""AgentSession class for LiveKit-style agent configuration.

This module provides the AgentSession class which allows users to configure
agents using a LiveKit-style API with support for:
- String-based plugin specifications (e.g., "deepgram/nova-2:en")
- Direct plugin imports (e.g., from kuralit.plugins.stt import deepgram)
- Environment variable configuration (fallback)
"""

import logging
from typing import Any, List, Optional, Union

from kuralit.config.loader import ConfigManager
from kuralit.config.schema import (
    Config,
    STTConfig,
    LLMConfig,
    VADConfig,
    TurnDetectorConfig,
    AgentConfig,
    ToolsConfig,
)
from kuralit.core.resolver import PluginResolver
from kuralit.tools.api import RESTAPIToolkit

logger = logging.getLogger(__name__)


class AgentSession:
    """LiveKit-style agent configuration session.
    
    This class provides a unified way to configure agents with STT, LLM, VAD,
    Turn Detector, and tools. It supports three configuration approaches:
    
    1. **String-based**: `stt="deepgram/nova-2:en"`, `llm="gemini/gemini-2.0-flash-001"`
    2. **Direct imports**: `stt=deepgram.DeepgramSTT(config)`, `llm=gemini.Gemini(config)`
    3. **Environment variables**: Loads from .env if not provided
    
    Example:
        ```python
        # String-based (recommended)
        session = AgentSession(
            stt="deepgram/nova-2:en",
            llm="gemini/gemini-2.0-flash-001",
            instructions="You are a helpful assistant.",
        )
        
        # Direct imports
        from kuralit.plugins.stt import deepgram
        from kuralit.plugins.llm import gemini
        
        session2 = AgentSession(
            stt=deepgram.DeepgramSTTHandler(stt_config),
            llm=gemini.Gemini(llm_config),
        )
        ```
    """
    
    def __init__(
        self,
        stt: Optional[Union[str, Any]] = None,
        llm: Optional[Union[str, Any]] = None,
        vad: Optional[Union[str, Any]] = None,
        turn_detection: Optional[Union[str, Any]] = None,
        tools: Optional[List[Any]] = None,
        instructions: Optional[str] = None,
        name: Optional[str] = None,
        config: Optional[Config] = None,
    ):
        """Initialize AgentSession.
        
        Args:
            stt: STT specification (string like "deepgram/nova-2:en") or handler instance
            llm: LLM specification (string like "gemini/gemini-2.0-flash-001") or model instance
            vad: VAD specification (string like "silero/v3") or handler instance
            turn_detection: Turn Detector specification (string like "multilingual/v1") or handler instance
            tools: List of toolkits (e.g., RESTAPIToolkit instances)
            instructions: Agent system instructions (highest priority)
            name: Agent name
            config: Full Config object (used as fallback if components not provided)
        """
        # Load config if not provided
        if config is None:
            config_manager = ConfigManager()
            config = config_manager.load_from_env()
        
        self._config = config
        
        # Resolve components
        self.stt = self._resolve_stt(stt, config.stt)
        self.llm = self._resolve_llm(llm, config.llm)
        self.vad = self._resolve_vad(vad, config.vad)
        self.turn_detection = self._resolve_turn_detector(turn_detection, config.turn_detector)
        self.tools = tools or self._load_tools_from_config(config.tools)
        
        # Instructions priority: 1) Direct parameter, 2) Config, 3) Default
        self.instructions = instructions or config.agent.instructions or self._default_instructions()
        self.name = name or config.agent.name or "WebSocket Agent"
        
        logger.info(
            f"AgentSession initialized: name={self.name}, "
            f"stt={type(self.stt).__name__ if self.stt else None}, "
            f"llm={type(self.llm).__name__ if self.llm else None}, "
            f"vad={type(self.vad).__name__ if self.vad else None}, "
            f"turn_detection={type(self.turn_detection).__name__ if self.turn_detection else None}, "
            f"tools={len(self.tools) if self.tools else 0}"
        )
    
    def _resolve_stt(self, stt: Optional[Union[str, Any]], default_config: STTConfig) -> Optional[Any]:
        """Resolve STT handler from string or instance.
        
        Args:
            stt: String spec (e.g., "deepgram/nova-2:en") or handler instance
            default_config: Default STT config from environment
            
        Returns:
            STT handler instance or None
        """
        if stt is None:
            # Try to create from config
            if default_config.provider and default_config.api_key:
                try:
                    import kuralit.plugins.stt.deepgram  # Trigger registration
                    import kuralit.plugins.stt.google  # Trigger registration
                    return PluginResolver.resolve_stt(default_config.provider, default_config)
                except Exception as e:
                    logger.warning(f"Failed to create STT from config: {e}")
                    return None
            return None
        
        if isinstance(stt, str):
            # String-based resolution
            import kuralit.plugins.stt.deepgram  # Trigger registration
            import kuralit.plugins.stt.google  # Trigger registration
            return PluginResolver.resolve_stt(stt, default_config)
        else:
            # Direct instance
            return stt
    
    def _resolve_llm(self, llm: Optional[Union[str, Any]], default_config: LLMConfig) -> Optional[Any]:
        """Resolve LLM model from string or instance.
        
        Args:
            llm: String spec (e.g., "gemini/gemini-2.0-flash-001") or model instance
            default_config: Default LLM config from environment
            
        Returns:
            Model instance or None
        """
        if llm is None:
            # Try to create from config
            if default_config.provider and default_config.api_key:
                try:
                    import kuralit.plugins.llm.gemini  # Trigger registration
                    return PluginResolver.resolve_llm(default_config.provider, default_config)
                except Exception as e:
                    logger.warning(f"Failed to create LLM from config: {e}")
                    return None
            return None
        
        if isinstance(llm, str):
            # String-based resolution
            import kuralit.plugins.llm.gemini  # Trigger registration
            return PluginResolver.resolve_llm(llm, default_config)
        else:
            # Direct instance
            return llm
    
    def _resolve_vad(self, vad: Optional[Union[str, Any]], default_config: VADConfig) -> Optional[Any]:
        """Resolve VAD handler from string or instance.
        
        Args:
            vad: String spec (e.g., "silero/v3") or handler instance
            default_config: Default VAD config from environment
            
        Returns:
            VAD handler instance or None
        """
        if vad is None:
            # Try to create from config
            if default_config.enabled and default_config.provider:
                try:
                    import kuralit.plugins.vad.silero  # Trigger registration
                    return PluginResolver.resolve_vad(default_config.provider, default_config)
                except Exception as e:
                    logger.warning(f"Failed to create VAD from config: {e}")
                    return None
            return None
        
        if isinstance(vad, str):
            # String-based resolution
            import kuralit.plugins.vad.silero  # Trigger registration
            return PluginResolver.resolve_vad(vad, default_config)
        else:
            # Direct instance
            return vad
    
    def _resolve_turn_detector(
        self,
        turn_detection: Optional[Union[str, Any]],
        default_config: TurnDetectorConfig
    ) -> Optional[Any]:
        """Resolve Turn Detector handler from string or instance.
        
        Args:
            turn_detection: String spec (e.g., "multilingual/v1") or handler instance
            default_config: Default Turn Detector config from environment
            
        Returns:
            Turn Detector handler instance or None
        """
        if turn_detection is None:
            # Try to create from config
            if default_config.enabled and default_config.provider:
                try:
                    import kuralit.plugins.turn_detector.multilingual  # Trigger registration
                    return PluginResolver.resolve_turn_detector(default_config.provider, default_config)
                except Exception as e:
                    logger.warning(f"Failed to create Turn Detector from config: {e}")
                    return None
            return None
        
        if isinstance(turn_detection, str):
            # String-based resolution
            import kuralit.plugins.turn_detector.multilingual  # Trigger registration
            return PluginResolver.resolve_turn_detector(turn_detection, default_config)
        else:
            # Direct instance
            return turn_detection
    
    def _load_tools_from_config(self, tools_config: ToolsConfig) -> List[Any]:
        """Load tools from configuration.
        
        Args:
            tools_config: Tools configuration
            
        Returns:
            List of toolkits
        """
        tools = []
        
        if not tools_config.enabled:
            return tools
        
        # Load Postman collection if provided
        if tools_config.postman_collection_path:
            try:
                from pathlib import Path
                
                # Resolve collection path
                collection_path = Path(tools_config.postman_collection_path)
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
                        logger.warning(
                            f"Postman collection not found: {tools_config.postman_collection_path}"
                        )
                        return tools
                else:
                    if not collection_path.exists():
                        logger.warning(f"Postman collection not found: {collection_path}")
                        return tools
                    collection_path = collection_path.resolve()
                
                # Create REST API toolkit
                api_toolkit = RESTAPIToolkit.from_postman_collection(
                    collection_path=str(collection_path),
                    base_url=tools_config.api_base_url,
                    headers=tools_config.api_headers,
                )
                tools.append(api_toolkit)
                
                logger.info(f"Loaded REST API tools from: {collection_path}")
            except Exception as e:
                logger.warning(f"Failed to load REST API tools: {e}")
        
        return tools
    
    def _default_instructions(self) -> str:
        """Generate default instructions based on available tools.
        
        Returns:
            Default system instructions string
        """
        base = "You are a helpful assistant with access to realtime communication."
        
        if self.tools:
            # Get all function names from toolkits
            function_names = []
            for toolkit in self.tools:
                if hasattr(toolkit, 'get_functions'):
                    functions = toolkit.get_functions()
                    function_names.extend([f.name for f in functions])
            
            if function_names:
                base += f"\n\nYou have access to the following API tools: {', '.join(function_names)}."
                base += " When users ask about data, information, or operations that can be performed through these APIs, use the appropriate tool to fetch or manipulate the data."
                base += " Always use the tools when relevant to answer the user's question accurately."
            else:
                base += " You also have access to REST API endpoints. Use the available API tools to help users interact with APIs when needed."
        
        base += " Provide clear, concise, and helpful responses."
        return base

