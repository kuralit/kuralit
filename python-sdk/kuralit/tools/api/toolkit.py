"""
REST API Toolkit for KuralIt.

Dynamically creates tools from REST API endpoints.
Supports Postman collections and can be extended for OpenAPI/Swagger.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from kuralit.tools.toolkit import Toolkit as BaseToolkit
from kuralit.tools.api.restapi_tools import parse_postman_collection, create_api_function
from kuralit.utils.log import log_info, log_error

try:
    from requests.auth import HTTPBasicAuth
except ImportError:
    HTTPBasicAuth = None


class RESTAPIToolkit(BaseToolkit):
    """
    Toolkit for REST API endpoints.
    
    Dynamically creates Function objects for each API endpoint,
    allowing the agent to call APIs as tools.
    """
    
    def __init__(
        self,
        name: str = "rest_api_toolkit",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        verify_ssl: bool = True,
        timeout: int = 30,
        tools: Optional[List[Any]] = None,
        **kwargs
    ):
        """Initialize REST API Toolkit.
        
        Args:
            name: Name of the toolkit
            base_url: Base URL for the API
            api_key: API key for authentication (adds Authorization: Bearer header)
            headers: Additional headers to include in all requests
            username: Username for basic auth
            password: Password for basic auth
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
            tools: Optional list of pre-created tools
            **kwargs: Additional arguments passed to base Toolkit
        """
        self.base_url = base_url
        self.api_key = api_key
        self.headers = headers or {}
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        
        # Prepare auth if credentials provided
        self.auth = None
        if username and password and HTTPBasicAuth:
            self.auth = HTTPBasicAuth(username, password)
        
        # If tools are provided, use them; otherwise start empty
        # Tools will be added via from_postman_collection or manually
        super().__init__(name=name, tools=tools or [], **kwargs)
    
    @classmethod
    def from_postman_collection(
        cls,
        collection_path: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        verify_ssl: bool = True,
        timeout: int = 30,
        **kwargs
    ) -> "RESTAPIToolkit":
        """Create toolkit from Postman collection.
        
        Args:
            collection_path: Path to Postman collection file (JSON)
            base_url: Override base URL (if not provided, uses collection variables)
            api_key: API key for authentication
            headers: Additional headers
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
            **kwargs: Additional arguments
            
        Returns:
            RESTAPIToolkit instance with functions for each endpoint
        """
        # Load collection
        collection_file = Path(collection_path)
        if not collection_file.exists():
            raise FileNotFoundError(f"Postman collection not found: {collection_path}")
        
        with open(collection_file, 'r') as f:
            collection_data = json.load(f)
        
        # Get auth credentials from kwargs if provided
        username = kwargs.get("username")
        password = kwargs.get("password")
        
        # Parse collection and create functions
        functions = parse_postman_collection(
            collection_data=collection_data,
            base_url=base_url,
            headers=headers,
            api_key=api_key,
            username=username,
            password=password,
            verify_ssl=verify_ssl,
            timeout=timeout,
        )
        
        if not functions:
            log_error("No functions created from Postman collection")
        
        # Create toolkit with functions
        toolkit = cls(
            name=collection_data.get("info", {}).get("name", "rest_api_toolkit"),
            base_url=base_url,
            api_key=api_key,
            headers=headers,
            verify_ssl=verify_ssl,
            timeout=timeout,
            tools=functions,
            **kwargs
        )
        
        log_info(f"Created RESTAPIToolkit with {len(functions)} functions from {collection_path}")
        return toolkit
    
    @classmethod
    def from_openapi_spec(cls, spec_path: str, **kwargs) -> "RESTAPIToolkit":
        """Create toolkit from OpenAPI specification.
        
        Args:
            spec_path: Path to OpenAPI spec file (YAML or JSON)
            **kwargs: Additional arguments
            
        Returns:
            RESTAPIToolkit instance
        """
        # TODO: Implement OpenAPI spec parsing
        raise NotImplementedError("OpenAPI spec parsing not yet implemented. Use from_postman_collection for now.")
    
    def add_endpoint(
        self,
        name: str,
        method: str,
        endpoint: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Manually add an API endpoint as a tool.
        
        Args:
            name: Function name
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint path (can include {{variable}} placeholders)
            description: Function description
            parameters: Optional JSON schema for parameters
        """
        func = create_api_function(
            name=name,
            method=method,
            url_template=endpoint,
            description=description,
            base_url=self.base_url,
            headers=self.headers,
            auth=self.auth,
            verify_ssl=self.verify_ssl,
            timeout=self.timeout,
            body_schema=parameters,
        )
        
        self.register(func, name=name)
        log_info(f"Added endpoint: {name} ({method} {endpoint})")
