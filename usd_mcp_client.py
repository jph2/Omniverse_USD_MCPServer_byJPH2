#!/usr/bin/env python3
"""
Omniverse_USD_MCPServer_byJPH2 Client

This module provides a client for the Model Context Protocol (MCP) server that offers
tools and resources for working with Universal Scene Description (USD) and NVIDIA Omniverse.

This client demonstrates how to:
- Connect to the MCP server via multiple protocols (stdio, HTTP, SSE)
- List available tools and resources
- Create and manipulate USD stages and prims
- Access documentation and development guides
"""

import asyncio
import os
import argparse
import sys
import json
import logging
import requests
from urllib.parse import urljoin
from typing import List, Dict, Any, Optional, Union, Callable
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

# Try to import SSE/HTTP client support if available
try:
    from mcp.client.http import HttpServerParameters, http_client
    from mcp.client.sse import SseServerParameters, sse_client
    HTTP_SUPPORT = True
except ImportError:
    HTTP_SUPPORT = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("usd_mcp_client.log")
    ]
)
logger = logging.getLogger(__name__)

class UsdMcpClient:
    """A client for the Omniverse_USD_MCPServer_byJPH2"""
    
    def __init__(self, 
                command: Optional[str] = None, 
                args: Optional[List[str]] = None, 
                env: Optional[Dict[str, str]] = None,
                protocol: str = "stdio",
                host: str = "localhost",
                port: int = 5000):
        """Initialize the client with server connection parameters
        
        Args:
            command: Command to start the server (for stdio)
            args: Arguments for the server command (for stdio)
            env: Environment variables for the server process (for stdio)
            protocol: Connection protocol ('stdio', 'http', or 'sse')
            host: Server host (for HTTP/SSE)
            port: Server port (for HTTP/SSE)
        """
        self.protocol = protocol
        self.host = host
        self.port = port
        
        if protocol == "stdio":
            if not command:
                raise ValueError("Command is required for stdio protocol")
        self.server_params = StdioServerParameters(
            command=command,
                args=args or [],
            env=env
        )
        elif protocol == "http":
            if not HTTP_SUPPORT:
                raise ImportError("HTTP protocol support not available. Install required dependencies.")
            self.server_params = HttpServerParameters(
                url=f"http://{host}:{port}"
            )
        elif protocol == "sse":
            if not HTTP_SUPPORT:
                raise ImportError("SSE protocol support not available. Install required dependencies.")
            self.server_params = SseServerParameters(
                url=f"http://{host}:{port}"
            )
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")
            
        self.session = None
        self.read = None
        self.write = None
    
    async def connect(self):
        """Connect to the MCP server"""
        if self.protocol == "stdio":
            self.read, self.write = await stdio_client(self.server_params)
        elif self.protocol == "http":
            self.read, self.write = await http_client(self.server_params)
        elif self.protocol == "sse":
            self.read, self.write = await sse_client(self.server_params)
        else:
            raise ValueError(f"Unsupported protocol: {self.protocol}")
            
        self.session = await ClientSession(self.read, self.write)
        await self.session.initialize()
        logger.info(f"Connected to USD MCP server via {self.protocol}")
        return self.session
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self.session:
            # The session will be closed by the context manager
            self.session = None
            self.read = None
            self.write = None
            logger.info("Disconnected from USD MCP server")
    
    async def list_capabilities(self):
        """List the server's capabilities"""
        if not self.session:
            raise ValueError("Not connected to server")
        
        server_info = self.session.server_info
        server_capabilities = self.session.server_capabilities
        
        print("\nServer Information:")
        print(f"  Name: {server_info.name}")
        print(f"  Version: {server_info.version}")
        
        print("\nServer Capabilities:")
        for capability, value in server_capabilities.__dict__.items():
            if value is not None:
                print(f"  {capability}: {value}")
        
        return {
            "name": server_info.name,
            "version": server_info.version,
            "capabilities": {k: v for k, v in server_capabilities.__dict__.items() if v is not None}
        }
    
    async def list_tools(self):
        """List available tools from the server"""
        if not self.session:
            raise ValueError("Not connected to server")
        
        tools = await self.session.list_tools()
        print("\nAvailable Tools:")
        for tool in tools.tools:
            print(f"- {tool.name}: {tool.description}")
        
        return [{"name": t.name, "description": t.description} for t in tools.tools]
    
    async def list_resources(self):
        """List available resources from the server"""
        if not self.session:
            raise ValueError("Not connected to server")
        
        resources = await self.session.list_resources()
        print("\nAvailable Resources:")
        for resource in resources.resources:
            print(f"- {resource.uri}")
    
        return [{"uri": r.uri} for r in resources.resources]
    
    async def get_server_status(self):
        """Get current server status information
        
        Returns:
            Server status information or None on error
        """
        if not self.session:
            raise ValueError("Not connected to server")
        
        print("\n--- Getting server status ---")
        status_result = await self.session.call_tool("get_server_status", {})
        
        try:
            response = json.loads(status_result.content)
            if response.get("ok", False):
                status_data = response.get("data", {})
                print(json.dumps(status_data, indent=2))
                return status_data
            else:
                logger.error(f"Error: {response.get('message', 'Unknown error')}")
                return None
        except json.JSONDecodeError:
            print(status_result.content)
            return None
    
    async def create_test_stage(self, file_path: str, template: str = "basic", up_axis: str = "Y"):
        """Create a test USD stage
        
        Args:
            file_path: Path where the stage should be saved
            template: Stage template ('empty', 'basic', or 'full')
            up_axis: Up axis for the stage ('Y' or 'Z')
            
        Returns:
            Stage information or None on error
        """
        if not self.session:
            raise ValueError("Not connected to server")
        
        print(f"\n--- Creating a USD stage at {file_path} ---")
        create_result = await self.session.call_tool("create_stage", {
            "file_path": file_path,
            "template": template,
            "up_axis": up_axis
        })
        
        # Parse JSON response
        try:
            response = json.loads(create_result.content)
            if response.get("ok", False):
                print(f"Success: {response.get('message', '')}")
                return response.get("data", {})
            else:
                logger.error(f"Error: {response.get('message', 'Unknown error')}")
                return None
        except json.JSONDecodeError:
            # Fallback for non-JSON responses
        print(create_result.content)
        return create_result.content
    
    async def close_stage(self, file_path: str):
        """Close a USD stage and release resources
        
        Args:
            file_path: Path to the USD file
        """
        if not self.session:
            raise ValueError("Not connected to server")
        
        print(f"\n--- Closing stage {file_path} ---")
        close_result = await self.session.call_tool("close_stage", {"file_path": file_path})
        
        # Parse JSON response
        try:
            response = json.loads(close_result.content)
            if response.get("ok", False):
                print(f"Success: {response.get('message', '')}")
                return True
            else:
                logger.error(f"Error: {response.get('message', 'Unknown error')}")
                return False
        except json.JSONDecodeError:
            # Fallback for non-JSON responses
            print(close_result.content)
            return False
    
    async def create_cube_mesh(self, file_path: str, prim_path: str = "/root/cube"):
        """Create a simple cube mesh in a USD stage
        
        Args:
            file_path: Path to the USD file
            prim_path: Path within the stage to create the mesh
        """
        if not self.session:
            raise ValueError("Not connected to server")
        
        print(f"\n--- Creating a cube mesh at {prim_path} ---")
        
        # Define a simple cube
        points = [
            (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
            (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)
        ]
        face_vertex_counts = [4, 4, 4, 4, 4, 4]  # 6 faces, 4 vertices each
        face_vertex_indices = [
            0, 1, 2, 3,  # bottom
            4, 5, 6, 7,  # top
            0, 1, 5, 4,  # front
            1, 2, 6, 5,  # right
            2, 3, 7, 6,  # back
            3, 0, 4, 7   # left
        ]
        
        mesh_result = await self.session.call_tool("create_mesh", {
            "file_path": file_path,
            "prim_path": prim_path,
            "points": points,
            "face_vertex_counts": face_vertex_counts,
            "face_vertex_indices": face_vertex_indices
        })
        
        # Parse JSON response
        try:
            response = json.loads(mesh_result.content)
            if response.get("ok", False):
                print(f"Success: {response.get('message', '')}")
                return response.get("data", {})
            else:
                logger.error(f"Error: {response.get('message', 'Unknown error')}")
                return None
        except json.JSONDecodeError:
            # Fallback for non-JSON responses
        print(mesh_result.content)
        return mesh_result.content
    
    async def analyze_stage(self, file_path: str):
        """Analyze a USD stage and print information about its contents
        
        Args:
            file_path: Path to the USD file to analyze
        """
        if not self.session:
            raise ValueError("Not connected to server")
        
        print(f"\n--- Analyzing stage {file_path} ---")
        analyze_result = await self.session.call_tool("analyze_stage", {"file_path": file_path})
        
        # Parse JSON response
        try:
            response = json.loads(analyze_result.content)
            if response.get("ok", False):
                stage_info = response.get("data", {})
                print(json.dumps(stage_info, indent=2))
                return stage_info
            else:
                logger.error(f"Error: {response.get('message', 'Unknown error')}")
                return None
        except json.JSONDecodeError:
            # Fallback handling for non-JSON responses
            try:
                # Try parsing as direct JSON (legacy format)
            stage_info = json.loads(analyze_result.content)
            print(json.dumps(stage_info, indent=2))
                return stage_info
        except:
            print(analyze_result.content)
                return analyze_result.content
    
    async def create_reference(self, file_path: str, prim_path: str, reference_file_path: str, reference_prim_path: str = ""):
        """Add a reference to an external USD file
        
        Args:
            file_path: Path to the target USD file
            prim_path: Path where to create/add reference
            reference_file_path: Path to the referenced USD file
            reference_prim_path: Optional prim path within the referenced file
            
        Returns:
            Reference information or None on error
        """
        if not self.session:
            raise ValueError("Not connected to server")
        
        print(f"\n--- Adding reference to {reference_file_path} at {prim_path} ---")
        result = await self.session.call_tool("create_reference", {
            "file_path": file_path,
            "prim_path": prim_path,
            "reference_file_path": reference_file_path,
            "reference_prim_path": reference_prim_path
        })
        
        # Parse JSON response
        try:
            response = json.loads(result.content)
            if response.get("ok", False):
                ref_data = response.get("data", {})
                print(f"Success: {response.get('message', '')}")
                return ref_data
            else:
                logger.error(f"Error: {response.get('message', 'Unknown error')}")
                return None
        except json.JSONDecodeError:
            # Fallback for non-JSON responses
            print(result.content)
            return result.content
    
    async def create_material(self, file_path: str, material_path: str, diffuse_color=(0.8, 0.8, 0.8), metallic=0.0, roughness=0.4):
        """Create an OmniPBR material in a USD stage
        
        Args:
            file_path: Path to the USD file
            material_path: Path where to create the material
            diffuse_color: RGB tuple for diffuse color (default: light gray)
            metallic: Metallic value between 0.0 and 1.0 (default: 0.0)
            roughness: Roughness value between 0.0 and 1.0 (default: 0.4)
            
        Returns:
            Material information or None on error
        """
        if not self.session:
            raise ValueError("Not connected to server")
        
        print(f"\n--- Creating material at {material_path} ---")
        result = await self.session.call_tool("create_material", {
            "file_path": file_path,
            "material_path": material_path,
            "diffuse_color": diffuse_color,
            "metallic": metallic,
            "roughness": roughness
        })
        
        # Parse JSON response
        try:
            response = json.loads(result.content)
            if response.get("ok", False):
                material_data = response.get("data", {})
                print(f"Success: {response.get('message', '')}")
                return material_data
            else:
                logger.error(f"Error: {response.get('message', 'Unknown error')}")
                return None
        except json.JSONDecodeError:
            # Fallback for non-JSON responses
            print(result.content)
            return result.content
    
    async def bind_material(self, file_path: str, prim_path: str, material_path: str):
        """Bind a material to a prim in the USD stage
        
        Args:
            file_path: Path to the USD file
            prim_path: Path to the prim to bind the material to
            material_path: Path to the material to bind
            
        Returns:
            Binding information or None on error
        """
        if not self.session:
            raise ValueError("Not connected to server")
        
        print(f"\n--- Binding material {material_path} to {prim_path} ---")
        result = await self.session.call_tool("bind_material", {
            "file_path": file_path,
            "prim_path": prim_path,
            "material_path": material_path
        })
        
        # Parse JSON response
        try:
            response = json.loads(result.content)
            if response.get("ok", False):
                binding_data = response.get("data", {})
                print(f"Success: {response.get('message', '')}")
                return binding_data
            else:
                logger.error(f"Error: {response.get('message', 'Unknown error')}")
                return None
        except json.JSONDecodeError:
            # Fallback for non-JSON responses
            print(result.content)
            return result.content
    
    async def create_primitive(self, file_path: str, prim_type: str, prim_path: str, size: float = 1.0, position: tuple = (0, 0, 0)):
        """Create a geometric primitive in a USD stage
        
        Args:
            file_path: Path to the USD file
            prim_type: Type of primitive ('cube', 'sphere', 'cylinder', 'cone')
            prim_path: Path where to create the primitive
            size: Size of the primitive (default: 1.0)
            position: XYZ position tuple (default: origin)
            
        Returns:
            Primitive information or None on error
        """
        if not self.session:
            raise ValueError("Not connected to server")
        
        print(f"\n--- Creating {prim_type} at {prim_path} ---")
        result = await self.session.call_tool("create_primitive", {
            "file_path": file_path,
            "prim_type": prim_type,
            "prim_path": prim_path,
            "size": size,
            "position": position
        })
        
        # Parse JSON response
        try:
            response = json.loads(result.content)
            if response.get("ok", False):
                prim_data = response.get("data", {})
                print(f"Success: {response.get('message', '')}")
                return prim_data
            else:
                logger.error(f"Error: {response.get('message', 'Unknown error')}")
                return None
        except json.JSONDecodeError:
            # Fallback for non-JSON responses
            print(result.content)
            return result.content
    
    async def export_to_format(self, file_path: str, output_path: str, format: str = "usda"):
        """Export a USD stage to a different format
        
        Args:
            file_path: Path to the source USD file
            output_path: Path where to save the exported file
            format: Target format ('usda', 'usdc', 'usdz')
            
        Returns:
            Export information or None on error
        """
        if not self.session:
            raise ValueError("Not connected to server")
        
        print(f"\n--- Exporting stage to {format} format at {output_path} ---")
        result = await self.session.call_tool("export_to_format", {
            "file_path": file_path,
            "output_path": output_path,
            "format": format
        })
        
        # Parse JSON response
        try:
            response = json.loads(result.content)
            if response.get("ok", False):
                export_data = response.get("data", {})
                print(f"Success: {response.get('message', '')}")
                return export_data
            else:
                logger.error(f"Error: {response.get('message', 'Unknown error')}")
                return None
        except json.JSONDecodeError:
            # Fallback for non-JSON responses
            print(result.content)
            return result.content
    
    async def setup_physics_scene(self, file_path: str, gravity: tuple = (0, -9.81, 0)):
        """Setup physics scene in a USD stage
        
        Args:
            file_path: Path to the USD file
            gravity: XYZ gravity vector (default: Earth gravity)
            
        Returns:
            Physics scene information or None on error
        """
        if not self.session:
            raise ValueError("Not connected to server")
        
        print(f"\n--- Setting up physics scene in {file_path} ---")
        result = await self.session.call_tool("setup_physics_scene", {
            "file_path": file_path,
            "gravity": gravity
        })
        
        # Parse JSON response
        try:
            response = json.loads(result.content)
            if response.get("ok", False):
                scene_data = response.get("data", {})
                print(f"Success: {response.get('message', '')}")
                return scene_data
            else:
                logger.error(f"Error: {response.get('message', 'Unknown error')}")
                return None
        except json.JSONDecodeError:
            # Fallback for non-JSON responses
            print(result.content)
            return result.content
    
    async def add_rigid_body(self, file_path: str, prim_path: str, mass: float = 1.0, is_dynamic: bool = True):
        """Add rigid body properties to a prim
        
        Args:
            file_path: Path to the USD file
            prim_path: Path to the prim to make a rigid body
            mass: Mass in kg (default: 1.0)
            is_dynamic: Whether the body is dynamic (true) or kinematic (false)
            
        Returns:
            Rigid body information or None on error
        """
        if not self.session:
            raise ValueError("Not connected to server")
        
        print(f"\n--- Adding {'dynamic' if is_dynamic else 'kinematic'} rigid body to {prim_path} ---")
        result = await self.session.call_tool("add_rigid_body", {
            "file_path": file_path,
            "prim_path": prim_path,
            "mass": mass,
            "is_dynamic": is_dynamic
        })
        
        # Parse JSON response
        try:
            response = json.loads(result.content)
            if response.get("ok", False):
                body_data = response.get("data", {})
                print(f"Success: {response.get('message', '')}")
                return body_data
            else:
                logger.error(f"Error: {response.get('message', 'Unknown error')}")
                return None
        except json.JSONDecodeError:
            # Fallback for non-JSON responses
            print(result.content)
            return result.content
    
    async def set_transform(self, file_path: str, prim_path: str, translate=None, rotate=None, scale=None, time_code=None):
        """Set or animate transform on a prim
        
        Args:
            file_path: Path to the USD file
            prim_path: Path to the prim to transform
            translate: Optional XYZ translation values
            rotate: Optional XYZ rotation values in degrees
            scale: Optional XYZ scale values
            time_code: Optional time code for animation (if None, not animated)
            
        Returns:
            Transform information or None on error
        """
        if not self.session:
            raise ValueError("Not connected to server")
        
        if translate is None and rotate is None and scale is None:
            raise ValueError("At least one of translate, rotate, or scale must be provided")
        
        print(f"\n--- Setting transform on {prim_path} ---")
        params = {
            "file_path": file_path,
            "prim_path": prim_path,
        }
        
        if translate is not None:
            params["translate"] = translate
        if rotate is not None:
            params["rotate"] = rotate
        if scale is not None:
            params["scale"] = scale
        if time_code is not None:
            params["time_code"] = time_code
        
        result = await self.session.call_tool("set_transform", params)
        
        # Parse JSON response
        try:
            response = json.loads(result.content)
            if response.get("ok", False):
                transform_data = response.get("data", {})
                print(f"Success: {response.get('message', '')}")
                return transform_data
            else:
                logger.error(f"Error: {response.get('message', 'Unknown error')}")
                return None
        except json.JSONDecodeError:
            # Fallback for non-JSON responses
            print(result.content)
            return result.content
    
    async def create_animation(self, file_path: str, prim_path: str, attribute_name: str, key_frames: List[Dict], interpolation: str = "linear"):
        """Create an animation for a prim attribute with keyframes
        
        Args:
            file_path: Path to the USD file
            prim_path: Path to the prim with the attribute to animate
            attribute_name: Name of the attribute to animate
            key_frames: List of dictionaries with 'time' and 'value' keys
            interpolation: Interpolation method ('linear', 'held', 'bezier')
            
        Returns:
            Animation information or None on error
        """
        if not self.session:
            raise ValueError("Not connected to server")
        
        print(f"\n--- Creating animation for {attribute_name} on {prim_path} ---")
        result = await self.session.call_tool("create_animation", {
            "file_path": file_path,
            "prim_path": prim_path,
            "attribute_name": attribute_name,
            "key_frames": key_frames,
            "interpolation": interpolation
        })
        
        # Parse JSON response
        try:
            response = json.loads(result.content)
            if response.get("ok", False):
                animation_data = response.get("data", {})
                print(f"Success: {response.get('message', '')}")
                return animation_data
            else:
                logger.error(f"Error: {response.get('message', 'Unknown error')}")
                return None
        except json.JSONDecodeError:
            # Fallback for non-JSON responses
            print(result.content)
            return result.content
    
    async def create_animation_sequence(self, file_path: str, prim_path: str, attribute_name: str, start_time: float,
                                     end_time: float, num_frames: int, start_value: Any, end_value: Any,
                                     interpolation: str = "linear"):
        """Helper method to create a simple animation sequence with linear interpolation between values
        
        Args:
            file_path: Path to the USD file
            prim_path: Path to the prim with the attribute to animate
            attribute_name: Name of the attribute to animate
            start_time: Start time code
            end_time: End time code
            num_frames: Number of frames (keyframes) in the sequence
            start_value: Value at start time
            end_value: Value at end time
            interpolation: Interpolation method
            
        Returns:
            Animation information or None on error
        """
        if not self.session:
            raise ValueError("Not connected to server")
        
        # Generate keyframes
        key_frames = []
        
        # Calculate time step
        if num_frames <= 1:
            # If only one frame, just use the start time
            key_frames.append({"time": start_time, "value": start_value})
        else:
            time_step = (end_time - start_time) / (num_frames - 1)
            
            for i in range(num_frames):
                time = start_time + (i * time_step)
                
                # Linearly interpolate the value
                if isinstance(start_value, (int, float)) and isinstance(end_value, (int, float)):
                    # Numeric values
                    alpha = i / (num_frames - 1)
                    value = start_value + (end_value - start_value) * alpha
                elif isinstance(start_value, (list, tuple)) and isinstance(end_value, (list, tuple)):
                    # Tuple/list values (like coordinates)
                    if len(start_value) != len(end_value):
                        raise ValueError("Start and end values must have the same length")
                    
                    alpha = i / (num_frames - 1)
                    value = [start_value[j] + (end_value[j] - start_value[j]) * alpha for j in range(len(start_value))]
                    
                    # Convert to tuple if original was a tuple
                    if isinstance(start_value, tuple):
                        value = tuple(value)
                else:
                    # For frame 0, use start_value; for the last frame, use end_value
                    # For other frames, use start_value
                    if i == 0:
                        value = start_value
                    elif i == num_frames - 1:
                        value = end_value
                    else:
                        # Non-interpolatable values
                        if (num_frames - 1) // 2 == i:
                            # Middle frame - use end_value
                            value = end_value
                        else:
                            # Use start_value
                            value = start_value
                
                key_frames.append({"time": time, "value": value})
        
        # Create the animation using the generated keyframes
        return await self.create_animation(file_path, prim_path, attribute_name, key_frames, interpolation)
    
    async def get_usd_schema(self):
        """Get information about common USD schema types"""
        if not self.session:
            raise ValueError("Not connected to server")
        
        print("\n--- Fetching USD schema information ---")
        schema_info, _ = await self.session.read_resource("usd://schema")
        
        # Pretty-print the JSON result
        try:
            schema_dict = json.loads(schema_info)
            print(json.dumps(schema_dict, indent=2))
            return schema_dict
        except json.JSONDecodeError:
            print(schema_info)
        return schema_info
    
    async def get_omniverse_help(self):
        """Get help information about Omniverse Kit and USD integration"""
        if not self.session:
            raise ValueError("Not connected to server")
        
        print("\n--- Getting Omniverse help ---")
        omni_help, _ = await self.session.read_resource("omniverse://help")
        print(omni_help)
        return omni_help
    
    async def get_development_guide(self, preview_chars: int = 500):
        """Get the Comprehensive Omniverse Development Guide
        
        Args:
            preview_chars: Number of characters to preview (0 for all)
        """
        if not self.session:
            raise ValueError("Not connected to server")
        
        print("\n--- Accessing Omniverse Development Guide ---")
        guide, _ = await self.session.read_resource("omniverse://development-guide")
        
        if preview_chars > 0 and len(guide) > preview_chars:
            print(f"Preview ({preview_chars} chars):")
            print(guide[:preview_chars] + "...")
            print(f"\nTotal length: {len(guide)} characters")
        else:
            print(guide)
        
        return guide
    
    async def search_guide(self, topics: List[str]):
        """Search the Omniverse development guide for specific topics
        
        Args:
            topics: List of topics to search for
            
        Returns:
            Search results or None on error
        """
        print(f"\n--- Searching Omniverse Guide for topics: {', '.join(topics)} ---")
        search_result = await self.session.call_tool("search_omniverse_guide", {"topic": " ".join(topics)})
        
        try:
            response = json.loads(search_result.content)
            if response.get("ok", False):
                search_data = response.get("data", {})
                print(f"Found {len(search_data.get('results', []))} results")
                return search_data
            else:
                logger.error(f"Error: {response.get('message', 'Unknown error')}")
                return None
        except json.JSONDecodeError:
            print(search_result.content)
            return None
    
    async def visualize_scene_graph(self, file_path: str, output_format: str = "text", 
                                   output_path: Optional[str] = None, max_depth: int = -1, 
                                   include_properties: bool = False):
        """Visualize the scene graph of a USD stage in various formats
        
        Args:
            file_path: Path to the USD stage file
            output_format: Format for visualization ('text', 'html', 'json', or 'network')
            output_path: Optional path for the output file
            max_depth: Maximum depth to visualize (-1 for unlimited)
            include_properties: Whether to include properties (for text format)
            
        Returns:
            Visualization result or None on error
        """
        print(f"\n--- Visualizing scene graph for {file_path} ---")
        
        params = {
            "file_path": file_path,
            "output_format": output_format,
            "max_depth": max_depth,
            "include_properties": include_properties
        }
        
        if output_path:
            params["output_path"] = output_path
            
        result = await self.session.call_tool("visualize_scene_graph", params)
        
        try:
            response = json.loads(result.content)
            if response.get("ok", False):
                data = response.get("data", {})
                
                # Handle different output formats
                if output_format == "text" and "visualization" in data:
                    # Print the text visualization if available
                    print("\nScene Graph Visualization:")
                    print(data["visualization"])
                
                if "output_file" in data:
                    print(f"\nVisualization saved to: {data['output_file']}")
                    
                return data
            else:
                logger.error(f"Error: {response.get('message', 'Unknown error')}")
                return None
        except json.JSONDecodeError:
            print(result.content)
            return None


async def run_demo():
    """Run a demonstration of the USD MCP client functionality"""
    parser = argparse.ArgumentParser(description='USD MCP Client Demo')
    parser.add_argument('--server', default='python', help='Server command')
    parser.add_argument('--args', nargs='*', default=['usd_mcp_server.py'], help='Server arguments')
    parser.add_argument('--output', default='demo_output', help='Output directory for demo files')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Initialize client
    client = UsdMcpClient(args.server, args.args)
    
    try:
        # Connect to server
        await client.connect()
        
        # List capabilities, tools, and resources
                await client.list_capabilities()
                await client.list_tools()
                await client.list_resources()
                
                # Create a test stage
        test_file = os.path.join(args.output, "test_stage.usda")
        await client.create_test_stage(test_file)
                
        # Create a mesh
        await client.create_cube_mesh(test_file)
                
                # Analyze the stage
        await client.analyze_stage(test_file)
        
        # Close the stage to release resources
        await client.close_stage(test_file)
                
                # Get USD schema information
                await client.get_usd_schema()
                
        # Get help information
                await client.get_omniverse_help()
                
        # Preview development guide
                await client.get_development_guide()
                
        # Search guide for specific topics
        await client.search_guide(["material", "shader"])
                
    except Exception as e:
        logger.exception("Error in demo")
        print(f"Error during demo: {e}")
    finally:
        # Disconnect from server
        await client.disconnect()
        print("\nDemo completed")


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description='USD MCP Client')
    parser.add_argument('--server', default='python', help='Server command')
    parser.add_argument('--args', nargs='*', default=['usd_mcp_server.py'], help='Server arguments')
    parser.add_argument('--demo', action='store_true', help='Run demonstration')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    
    if args.demo:
        # Run the demonstration
        asyncio.run(run_demo())
    else:
        # Run interactive mode or other functionality
        print("USD MCP Client initialized. Use --demo to run the demonstration.") 