#!/usr/bin/env python3
"""
Omniverse USD MCP Server - Cursor AI Integration

This module provides integration between the Omniverse USD MCP Server and Cursor AI.
It enables using natural language to create and manipulate USD scenes directly within Cursor.

Usage:
1. Run the USD MCP Server: python usd_mcp_server.py --host 0.0.0.0 --port 5000
2. Import this module in your Cursor projects
3. Use the CursorUsdTools class to interact with USD via natural language

Example:
    from cursor_integration import CursorUsdTools
    
    usd_tools = CursorUsdTools()
    usd_tools.create_scene("Create a scene with a red cube and a blue sphere")
"""

import requests
import json
import os
import re
from typing import Dict, Any, Optional, List, Union, Tuple

class CursorUsdTools:
    """Provides USD tools for Cursor AI via the MCP Server"""
    
    def __init__(self, host: str = "localhost", port: int = 5000):
        """Initialize the Cursor USD tools
        
        Args:
            host: MCP server host
            port: MCP server port
        """
        self.base_url = f"http://{host}:{port}"
        self.current_stage: Optional[str] = None
    
    def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool and return the result
        
        Args:
            tool_name: Name of the MCP tool to call
            params: Parameters for the tool
            
        Returns:
            Tool response as a dictionary
        """
        try:
            url = f"{self.base_url}/{tool_name}"
            response = requests.post(url, json=params)
            response.raise_for_status()
            result = response.json()
            return result
        except Exception as e:
            return {"ok": False, "message": f"Error calling tool {tool_name}: {str(e)}"}
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get current server status
        
        Returns:
            Server status information
        """
        return self.call_tool("get_server_status", {})
    
    def create_stage(self, file_path: str, template: str = "basic", up_axis: str = "Y") -> Dict[str, Any]:
        """Create a new USD stage
        
        Args:
            file_path: Path where the stage should be saved
            template: Stage template ('empty', 'basic', or 'full')
            up_axis: Up axis for the stage ('Y' or 'Z')
            
        Returns:
            Result of the operation
        """
        result = self.call_tool("create_stage", {
            "file_path": file_path,
            "template": template,
            "up_axis": up_axis
        })
        
        if result.get("ok", False):
            self.current_stage = file_path
        
        return result
    
    def create_primitive(self, file_path: str, prim_type: str, prim_path: str, 
                         size: float = 1.0, position: Tuple[float, float, float] = (0, 0, 0)) -> Dict[str, Any]:
        """Create a geometric primitive
        
        Args:
            file_path: USD stage file path
            prim_type: Type of primitive ('cube', 'sphere', 'cylinder', 'cone')
            prim_path: Path for the primitive in the stage
            size: Size of the primitive
            position: Position (x, y, z) of the primitive
            
        Returns:
            Result of the operation
        """
        return self.call_tool("create_primitive", {
            "file_path": file_path,
            "prim_type": prim_type,
            "prim_path": prim_path,
            "size": size,
            "position": position
        })
    
    def create_material(self, file_path: str, material_path: str, 
                        diffuse_color: Tuple[float, float, float] = (0.8, 0.8, 0.8), 
                        metallic: float = 0.0, roughness: float = 0.4) -> Dict[str, Any]:
        """Create a material
        
        Args:
            file_path: USD stage file path
            material_path: Path for the material in the stage
            diffuse_color: RGB diffuse color
            metallic: Metallic value (0-1)
            roughness: Roughness value (0-1)
            
        Returns:
            Result of the operation
        """
        return self.call_tool("create_material", {
            "file_path": file_path,
            "material_path": material_path,
            "diffuse_color": diffuse_color,
            "metallic": metallic,
            "roughness": roughness
        })
    
    def bind_material(self, file_path: str, prim_path: str, material_path: str) -> Dict[str, Any]:
        """Bind a material to a prim
        
        Args:
            file_path: USD stage file path
            prim_path: Path to the prim
            material_path: Path to the material
            
        Returns:
            Result of the operation
        """
        return self.call_tool("bind_material", {
            "file_path": file_path,
            "prim_path": prim_path,
            "material_path": material_path
        })
    
    def set_transform(self, file_path: str, prim_path: str, 
                      translate: Optional[Tuple[float, float, float]] = None,
                      rotate: Optional[Tuple[float, float, float]] = None,
                      scale: Optional[Tuple[float, float, float]] = None,
                      time_code: Optional[float] = None) -> Dict[str, Any]:
        """Set transform for a prim
        
        Args:
            file_path: USD stage file path
            prim_path: Path to the prim
            translate: Translation (x, y, z)
            rotate: Rotation in degrees (x, y, z)
            scale: Scale (x, y, z)
            time_code: Time code for animation
            
        Returns:
            Result of the operation
        """
        params = {
            "file_path": file_path,
            "prim_path": prim_path
        }
        
        if translate is not None:
            params["translate"] = translate
        if rotate is not None:
            params["rotate"] = rotate
        if scale is not None:
            params["scale"] = scale
        if time_code is not None:
            params["time_code"] = time_code
            
        return self.call_tool("set_transform", params)
    
    def setup_physics_scene(self, file_path: str, 
                           gravity: Tuple[float, float, float] = (0, -9.81, 0)) -> Dict[str, Any]:
        """Set up a physics scene
        
        Args:
            file_path: USD stage file path
            gravity: Gravity vector (x, y, z)
            
        Returns:
            Result of the operation
        """
        return self.call_tool("setup_physics_scene", {
            "file_path": file_path,
            "gravity": gravity
        })
    
    def add_rigid_body(self, file_path: str, prim_path: str, 
                      mass: float = 1.0, is_dynamic: bool = True) -> Dict[str, Any]:
        """Add a rigid body for physics simulation
        
        Args:
            file_path: USD stage file path
            prim_path: Path to the prim
            mass: Mass of the rigid body
            is_dynamic: Whether the body can move
            
        Returns:
            Result of the operation
        """
        return self.call_tool("add_rigid_body", {
            "file_path": file_path,
            "prim_path": prim_path,
            "mass": mass,
            "is_dynamic": is_dynamic
        })
    
    def create_animation(self, file_path: str, prim_path: str, attribute_name: str,
                        key_frames: List[Dict[str, Any]], 
                        interpolation: str = "linear") -> Dict[str, Any]:
        """Create an animation for an attribute
        
        Args:
            file_path: USD stage file path
            prim_path: Path to the prim
            attribute_name: Name of the attribute to animate
            key_frames: List of key frames (each with "time" and "value")
            interpolation: Interpolation type ("linear", "bezier", "held")
            
        Returns:
            Result of the operation
        """
        return self.call_tool("create_animation", {
            "file_path": file_path,
            "prim_path": prim_path,
            "attribute_name": attribute_name,
            "key_frames": key_frames,
            "interpolation": interpolation
        })
    
    def analyze_stage(self, file_path: str) -> Dict[str, Any]:
        """Analyze a USD stage
        
        Args:
            file_path: USD stage file path
            
        Returns:
            Result of the operation with stage analysis
        """
        return self.call_tool("analyze_stage", {
            "file_path": file_path
        })
    
    def export_to_format(self, file_path: str, output_path: str, format: str = "usda") -> Dict[str, Any]:
        """Export a USD stage to a different format
        
        Args:
            file_path: USD stage file path
            output_path: Output file path
            format: Output format ('usda', 'usdc', 'usdz')
            
        Returns:
            Result of the operation
        """
        return self.call_tool("export_to_format", {
            "file_path": file_path,
            "output_path": output_path,
            "format": format
        })
    
    def create_scene(self, description: str) -> Dict[str, Any]:
        """Create a scene from a natural language description
        
        This method parses the description and performs the necessary operations
        to create the described scene. This is designed to work with Cursor AI.
        
        Args:
            description: Natural language description of the scene
            
        Returns:
            Result of the operation
        """
        # Parse the description to determine what to create
        file_path = "cursor_scene.usda"
        
        # Create a new stage
        result = self.create_stage(file_path)
        if not result.get("ok", False):
            return result
        
        # Extract scene elements from the description
        scene_elements = self._parse_scene_description(description)
        
        # Process each scene element
        for element in scene_elements:
            element_type = element.get("type")
            
            if element_type == "primitive":
                # Create the primitive
                prim_result = self.create_primitive(
                    file_path,
                    element.get("prim_type", "cube"),
                    element.get("path", "/World/Geometry/Primitive"),
                    element.get("size", 1.0),
                    element.get("position", (0, 0, 0))
                )
                
                # If material properties are specified, create and bind a material
                if "color" in element or "metallic" in element or "roughness" in element:
                    material_path = f"{element.get('path', '/World/Geometry/Primitive')}_material"
                    
                    self.create_material(
                        file_path,
                        material_path,
                        element.get("color", (0.8, 0.8, 0.8)),
                        element.get("metallic", 0.0),
                        element.get("roughness", 0.4)
                    )
                    
                    self.bind_material(file_path, element.get("path", "/World/Geometry/Primitive"), material_path)
                
                # If physics properties are specified, add rigid body
                if "mass" in element:
                    # Ensure we have a physics scene
                    self.setup_physics_scene(file_path)
                    
                    self.add_rigid_body(
                        file_path,
                        element.get("path", "/World/Geometry/Primitive"),
                        element.get("mass", 1.0),
                        element.get("is_dynamic", True)
                    )
        
        # Analyze the created stage
        analysis = self.analyze_stage(file_path)
        
        return {
            "ok": True,
            "message": f"Created scene from description: {description}",
            "file_path": file_path,
            "analysis": analysis.get("data", {})
        }
    
    def _parse_scene_description(self, description: str) -> List[Dict[str, Any]]:
        """Parse a natural language scene description
        
        Args:
            description: Natural language description of the scene
            
        Returns:
            List of scene elements with their properties
        """
        elements = []
        
        # Match primitives with properties
        primitive_types = ["cube", "sphere", "cylinder", "cone"]
        for prim_type in primitive_types:
            if prim_type in description.lower():
                # Extract properties
                element = {
                    "type": "primitive",
                    "prim_type": prim_type,
                    "path": f"/World/Geometry/{prim_type.capitalize()}",
                    "size": 1.0,
                    "position": (0, 0, 0)
                }
                
                # Check for colors
                color_map = {
                    "red": (1, 0, 0),
                    "green": (0, 1, 0),
                    "blue": (0, 0, 1),
                    "yellow": (1, 1, 0),
                    "cyan": (0, 1, 1),
                    "magenta": (1, 0, 1),
                    "white": (1, 1, 1),
                    "black": (0, 0, 0),
                    "gray": (0.5, 0.5, 0.5)
                }
                
                for color_name, color_value in color_map.items():
                    pattern = f"{color_name}\\s+{prim_type}"
                    if re.search(pattern, description.lower()):
                        element["color"] = color_value
                
                # Check for metallic/roughness properties
                if "metallic" in description.lower() or "metal" in description.lower():
                    element["metallic"] = 0.8
                    element["roughness"] = 0.2
                
                # Check for physics properties
                if "physics" in description.lower() or "rigid body" in description.lower() or "dynamic" in description.lower():
                    element["mass"] = 1.0
                    element["is_dynamic"] = True
                
                elements.append(element)
        
        return elements
    
    def visualize_scene_graph(self, file_path: str, output_format: str = "text", 
                             output_path: Optional[str] = None, max_depth: int = -1, 
                             include_properties: bool = False) -> Dict[str, Any]:
        """Visualize the scene graph of a USD stage in various formats
        
        Args:
            file_path: Path to the USD stage file
            output_format: Format for visualization ('text', 'html', 'json', or 'network')
            output_path: Optional path for the output file
            max_depth: Maximum depth to visualize (-1 for unlimited)
            include_properties: Whether to include properties (for text format)
            
        Returns:
            Visualization result data
        """
        params = {
            "file_path": file_path,
            "output_format": output_format,
            "max_depth": max_depth,
            "include_properties": include_properties
        }
        
        if output_path:
            params["output_path"] = output_path
            
        return self.call_tool("visualize_scene_graph", params)


# Example usage when run directly
if __name__ == "__main__":
    usd_tools = CursorUsdTools()
    
    # Check if server is running
    status = usd_tools.get_server_status()
    if status.get("ok", False):
        print("Connected to USD MCP Server")
        print(f"Server status: {status.get('data', {})}")
        
        # Create a test scene
        scene_result = usd_tools.create_scene("Create a scene with a red cube and a blue sphere")
        print(json.dumps(scene_result, indent=2))
    else:
        print("Failed to connect to USD MCP Server. Make sure it's running with:")
        print("python usd_mcp_server.py --host 0.0.0.0 --port 5000") 