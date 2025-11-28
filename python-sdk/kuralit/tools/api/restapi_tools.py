"""REST API Tools - Create tools from API endpoints."""

import json
import re
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

try:
    import requests
    from requests.auth import HTTPBasicAuth
except ImportError:
    raise ImportError("`requests` not installed. Please install using `pip install requests`")

from kuralit.tools.function import Function
from kuralit.utils.log import log_debug, log_error, log_info


def create_api_function(
    name: str,
    method: str,
    url_template: str,
    description: str,
    base_url: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    auth: Optional[Any] = None,
    verify_ssl: bool = True,
    timeout: int = 30,
    body_schema: Optional[Dict[str, Any]] = None,
) -> Function:
    """Create a Function object for an API endpoint.
    
    Args:
        name: Function name
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        url_template: URL template with variables (e.g., "/notes/{{note_id}}")
        description: Function description
        base_url: Base URL for the API
        headers: Default headers
        auth: Authentication object
        verify_ssl: Whether to verify SSL certificates
        timeout: Request timeout in seconds
        body_schema: JSON schema for request body
        
    Returns:
        Function object that can be called by the agent
    """
    # Extract path parameters from URL template
    path_params = re.findall(r'\{\{(\w+)\}\}', url_template)
    
    # Build parameters schema
    properties = {}
    required = []
    
    # Add path parameters
    for param in path_params:
        properties[param] = {
            "type": "string",
            "description": f"Path parameter: {param}"
        }
        required.append(param)
    
    # Add body parameters if method requires body
    if method in ["POST", "PUT", "PATCH"]:
        if body_schema:
            if "properties" in body_schema:
                properties.update(body_schema["properties"])
                if "required" in body_schema:
                    required.extend(body_schema["required"])
            else:
                # If body_schema is the properties directly
                properties.update(body_schema)
        else:
            # No schema provided, add generic body parameter
            properties["body"] = {
                "type": "object",
                "description": "Request body data"
            }
    
    # Add query parameters (optional)
    # For GET/DELETE, add optional query_params
    if method in ["GET", "DELETE"]:
        properties["query_params"] = {
            "type": "object",
            "description": "Optional query parameters",
            "properties": {}
        }
    
    parameters = {
        "type": "object",
        "properties": properties,
        "required": required
    }
    
    # Create the entrypoint function
    def api_entrypoint(**kwargs) -> str:
        """Execute the API request."""
        url = None  # Initialize for error handling
        try:
            # Build URL - replace path parameters
            url = url_template
            for param in path_params:
                if param not in kwargs:
                    raise ValueError(f"Missing required path parameter: {param}")
                # Replace both {{param}} and {param} formats
                url = url.replace(f"{{{{{param}}}}}", str(kwargs[param]))
                url = url.replace(f"{{{param}}}", str(kwargs[param]))
            
            # Clean up URL - ensure it starts with /
            url = url.strip('/')
            if url:
                url = f"/{url}"
            
            # Combine with base_url if provided
            if base_url:
                # If url already has a scheme, use it as-is
                if url.startswith(('http://', 'https://')):
                    pass  # Use URL as-is
                else:
                    url = f"{base_url.rstrip('/')}{url}"
            elif not url.startswith(('http://', 'https://')):
                # No base_url but URL doesn't have scheme - this is an error
                raise ValueError(f"Cannot make request: URL '{url}' is missing base URL. Provide base_url parameter.")
            
            # Remove path parameters and query_params from kwargs
            request_kwargs = {k: v for k, v in kwargs.items() if k not in path_params and k != "query_params"}
            
            # Prepare request
            request_headers = (headers or {}).copy()
            
            # Prepare body
            json_data = None
            data = None
            
            if method in ["POST", "PUT", "PATCH"]:
                # Use remaining kwargs as body, or use "body" parameter if provided
                if "body" in kwargs:
                    json_data = kwargs["body"]
                elif request_kwargs:
                    json_data = request_kwargs
                
                if json_data:
                    request_headers.setdefault("Content-Type", "application/json")
            
            # Prepare query params
            params = kwargs.get("query_params") or {}
            
            log_info(f"Making {method} request to {url}")
            if json_data:
                log_debug(f"Body: {json.dumps(json_data, indent=2)}")
            if params:
                log_debug(f"Query params: {params}")
            
            # Validate URL before making request
            if not url.startswith(('http://', 'https://')):
                error_msg = f"Invalid URL: '{url}'. URL must start with http:// or https://. Make sure base_url is configured correctly."
                log_error(error_msg)
                return json.dumps({"error": error_msg, "hint": "Set KURALIT_API_BASE_URL environment variable or provide base_url when creating RESTAPIToolkit"}, indent=2)
            
            # Make request
            log_info(f"Executing {method} {url} (timeout={timeout}s)")
            response = requests.request(
                method=method,
                url=url,
                json=json_data,
                data=data,
                params=params,
                headers=request_headers,
                auth=auth,
                verify=verify_ssl,
                timeout=timeout,
            )
            
            # Parse response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"text": response.text}
            
            result = {
                "status_code": response.status_code,
                "data": response_data,
            }
            
            if not response.ok:
                log_error(f"Request failed with status {response.status_code}: {response.text}")
                result["error"] = f"Request failed with status {response.status_code}"
            
            return json.dumps(result, indent=2)
            
        except requests.exceptions.Timeout as e:
            url_str = url if url else "unknown"
            error_message = f"Request to {url_str} timed out after {timeout} seconds. The API server may be slow or unreachable."
            log_error(error_message)
            return json.dumps({"error": error_message, "url": url_str, "timeout": timeout}, indent=2)
        except requests.exceptions.ConnectionError as e:
            url_str = url if url else "unknown"
            error_message = f"Failed to connect to {url_str}. Check if the API server is running and the base_url is correct."
            log_error(error_message)
            return json.dumps({"error": error_message, "url": url_str, "hint": "Verify KURALIT_API_BASE_URL is set to the correct API server URL (not the WebSocket server)"}, indent=2)
        except requests.exceptions.RequestException as e:
            url_str = url if url else "unknown"
            error_message = f"Request failed: {str(e)}"
            log_error(f"{error_message} (URL: {url_str})")
            return json.dumps({"error": error_message, "url": url_str}, indent=2)
        except Exception as e:
            url_str = url if url else "unknown"
            error_message = f"Unexpected error: {str(e)}"
            log_error(f"{error_message} (URL: {url_str})")
            return json.dumps({"error": error_message, "url": url_str}, indent=2)
    
    # Update docstring
    api_entrypoint.__doc__ = description
    
    # Create Function object
    return Function(
        name=name,
        description=description,
        parameters=parameters,
        entrypoint=api_entrypoint,
    )


def parse_postman_collection(
    collection_data: Dict[str, Any],
    base_url: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    api_key: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    verify_ssl: bool = True,
    timeout: int = 30,
) -> List[Function]:
    """Parse a Postman collection and create Function objects for each endpoint.
    
    Args:
        collection_data: Postman collection JSON data
        base_url: Override base URL (if not provided, uses collection variables)
        headers: Additional headers to include
        api_key: API key for authentication (adds Authorization header)
        verify_ssl: Whether to verify SSL certificates
        timeout: Request timeout in seconds
        
    Returns:
        List of Function objects, one for each API endpoint
    """
    functions = []
    
    # Get base URL from collection variables or use provided
    collection_vars = {var.get("key"): var.get("value") for var in collection_data.get("variable", [])}
    if not base_url:
        base_url = collection_vars.get("base_url", "")
    
    # Prepare headers
    request_headers = (headers or {}).copy()
    if api_key:
        request_headers["Authorization"] = f"Bearer {api_key}"
    
    # Prepare auth
    auth = None
    if username and password:
        try:
            from requests.auth import HTTPBasicAuth
            auth = HTTPBasicAuth(username, password)
        except ImportError:
            pass
    
    def process_item(item: Dict[str, Any], folder_name: str = "") -> None:
        """Recursively process Postman collection items."""
        if "request" in item:
            # This is an endpoint
            request = item["request"]
            method = request.get("method", "GET")
            api_name = item.get("name", f"{method} Request")
            
            # Create function name based on API name
            # Convert to valid Python identifier: lowercase, replace spaces/hyphens with underscores
            # Remove special characters, ensure it starts with a letter
            def sanitize_name(name: str) -> str:
                """Convert a name to a valid Python identifier."""
                # Convert to lowercase
                name = name.lower()
                # Replace spaces, hyphens, and other separators with underscores
                name = re.sub(r'[\s\-\.]+', '_', name)
                # Remove invalid characters (keep only alphanumeric and underscores)
                name = re.sub(r'[^a-z0-9_]', '', name)
                # Remove leading/trailing underscores
                name = name.strip('_')
                # Ensure it starts with a letter or underscore
                if name and name[0].isdigit():
                    name = f"_{name}"
                # If empty, use a default
                if not name:
                    name = "api_call"
                return name
            
            # Build function name from API name
            clean_api_name = sanitize_name(api_name)
            
            # Add folder prefix if available
            if folder_name:
                clean_folder = sanitize_name(folder_name)
                function_name = f"{clean_folder}_{clean_api_name}"
            else:
                function_name = clean_api_name
            
            # Ensure function name is not too long (max 64 chars as per OpenAI/function calling spec)
            if len(function_name) > 64:
                # Truncate but keep it meaningful
                function_name = function_name[:64].rstrip('_')
            
            # Get description
            description = item.get("description") or request.get("description") or f"{method} request to {api_name}"
            
            # Parse URL
            url_data = request.get("url", {})
            if isinstance(url_data, str):
                url_template = url_data
            else:
                # Build URL from parts
                raw_url = url_data.get("raw", "")
                if raw_url:
                    url_template = raw_url
                else:
                    # Build from host and path
                    host_parts = url_data.get("host", [])
                    path_parts = url_data.get("path", [])
                    
                    # Filter out empty path parts
                    path_parts = [p for p in path_parts if p and p.strip()]
                    
                    if host_parts:
                        # Host parts might contain variables like {{base_url}}
                        host = "/".join(host_parts)
                        # If host is a variable (like {{base_url}}), we'll use base_url instead
                        # Otherwise, if it's a real host, use it
                        if host.startswith("{{") and host.endswith("}}"):
                            # It's a variable, will be replaced by base_url at runtime
                            path = "/".join(path_parts) if path_parts else ""
                            url_template = f"/{path}" if path else "/"
                        else:
                            # Real host - use it (but base_url will override if provided)
                            path = "/".join(path_parts) if path_parts else ""
                            url_template = f"{host}/{path}" if path else host
                    else:
                        # No host, just path
                        path = "/".join(path_parts) if path_parts else ""
                        url_template = f"/{path}" if path else "/"
            
            # Clean up URL template - remove {{base_url}} variable (will use base_url parameter)
            # But keep other variables like {{note_id}} as path parameters
            url_template = re.sub(r'\{\{base_url\}\}/?', '', url_template)
            url_template = url_template.strip('/')
            if url_template and not url_template.startswith('/'):
                url_template = f"/{url_template}"
            
            # Extract body schema if present
            body_schema = None
            body = request.get("body", {})
            if body and body.get("mode") == "raw":
                try:
                    raw_body = body.get("raw", "{}")
                    if raw_body:
                        body_json = json.loads(raw_body)
                        # Create a simple schema from the example
                        if isinstance(body_json, dict):
                            # Map Python types to JSON schema types
                            type_map = {
                                "str": "string",
                                "int": "integer",
                                "float": "number",
                                "bool": "boolean",
                                "list": "array",
                                "dict": "object",
                            }
                            body_schema = {
                                "properties": {
                                    k: {"type": type_map.get(type(v).__name__, "string")} 
                                    for k, v in body_json.items()
                                },
                                "required": list(body_json.keys())
                            }
                except Exception as e:
                    log_debug(f"Could not parse body schema: {e}")
                    pass
            
            # Create function
            try:
                func = create_api_function(
                    name=function_name,
                    method=method,
                    url_template=url_template,
                    description=description,
                    base_url=base_url,
                    headers=request_headers,
                    auth=auth,
                    verify_ssl=verify_ssl,
                    timeout=timeout,
                    body_schema=body_schema,
                )
                functions.append(func)
                log_info(f"Created function: {function_name} ({method} {url_template})")
            except Exception as e:
                log_error(f"Failed to create function for {api_name}: {e}")
                import traceback
                traceback.print_exc()
        
        # Process nested items (folders)
        if "item" in item:
            current_folder = item.get("name", "")
            for sub_item in item["item"]:
                process_item(sub_item, current_folder if current_folder else folder_name)
    
    # Process all items in collection
    for item in collection_data.get("item", []):
        process_item(item)
    
    return functions

