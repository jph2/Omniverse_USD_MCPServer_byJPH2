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
import logging
import re
from typing import Dict, Any, Optional, List, Union, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("cursor_integration")

class CursorUsdTools:
    """
    Integration class for using the Omniverse USD MCP Server from Cursor AI.
    
    This class provides methods for creating and manipulating USD scenes through
    the MCP server, allowing for natural language interactions through Cursor.
    """
    
    def __init__(self, server_url: str = "http://127.0.0.1:5000"):
        """
        Initialize the Cursor USD Tools.
        
        Args:
            server_url: URL of the running MCP server (default: http://127.0.0.1:5000)
        """
        self.server_url = server_url
        logger.info(f"Initialized CursorUsdTools with server URL: {server_url}")
    
    def _call_server(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP server endpoint.
        
        Args:
            endpoint: The endpoint to call (e.g., 'open_stage')
            data: The data to send to the endpoint
            
        Returns:
            The server response as a dictionary
        """
        try:
            logger.debug(f"Calling endpoint {endpoint} with data: {data}")
            response = requests.post(f"{self.server_url}/{endpoint}", json=data)
            response.raise_for_status()
            result = response.json()
            
            # Handle both new and legacy response formats
            if isinstance(result, dict) and "ok" in result:
                if not result["ok"]:
                    logger.error(f"Server error: {result.get('message', 'Unknown error')}")
                return result
            else:
                # Legacy format - wrap in standard format
                return {"ok": True, "data": result, "message": "Success"}
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Error calling MCP server: {str(e)}"
            logger.error(error_msg)
            return {"ok": False, "message": error_msg}
    
    def execute(self, natural_language_request: str) -> Dict[str, Any]:
        """
        Execute a natural language request through the MCP server.
        
        This method is the primary interface for Cursor AI to interact with
        the MCP server using natural language.
        
        Args:
            natural_language_request: A natural language request describing USD operations
            
        Returns:
            The result of the operation
        """
        try:
            response = self._call_server("execute_command", {
                "command": natural_language_request
            })
            
            return response
        except Exception as e:
            error_msg = f"Error executing natural language request: {str(e)}"
            logger.error(error_msg)
            return {"ok": False, "message": error_msg}
    
    # Stage Operations
    
    def open_stage(self, file_path: str, create_if_missing: bool = False) -> Dict[str, Any]:
        """
        Open an existing USD stage or create a new one.
        
        Args:
            file_path: Path to the USD file
            create_if_missing: Whether to create a new stage if it doesn't exist
            
        Returns:
            Dictionary containing the stage_id if successful
        """
        return self._call_server("open_stage", {
            "file_path": file_path,
            "create_if_missing": create_if_missing
        })
    
    def close_stage(self, stage_id: str, save_if_modified: bool = True) -> Dict[str, Any]:
        """
        Close an open USD stage to free resources.
        
        Args:
            stage_id: ID of the stage to close
            save_if_modified: Whether to save the stage if it has been modified
            
        Returns:
            Result of the operation
        """
        return self._call_server("close_stage_by_id", {
            "stage_id": stage_id,
            "save_if_modified": save_if_modified
        })
    
    def save_stage(self, stage_id: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Save a USD stage to disk.
        
        Args:
            stage_id: ID of the stage to save
            file_path: Optional alternative path to save to
            
        Returns:
            Result of the operation
        """
        data = {"stage_id": stage_id}
        if file_path:
            data["file_path"] = file_path
            
        return self._call_server("save_stage_by_id", data)
    
    # Prim Operations
    
    def list_prims(self, stage_id: str, root_path: str = "/") -> Dict[str, Any]:
        """
        List all prims in a stage under a given root path.
        
        Args:
            stage_id: ID of the stage
            root_path: Root path to list prims under (default: "/")
            
        Returns:
            Dictionary containing the list of prim paths
        """
        return self._call_server("list_prims_by_id", {
            "stage_id": stage_id,
            "root_path": root_path
        })
    
    def define_prim(self, stage_id: str, prim_path: str, prim_type: str) -> Dict[str, Any]:
        """
        Define a new prim on the stage.
        
        Args:
            stage_id: ID of the stage
            prim_path: Path where the new prim should be created
            prim_type: Type of the prim (e.g., "Xform", "Mesh", "Material")
            
        Returns:
            Result of the operation
        """
        return self._call_server("define_prim_by_id", {
            "stage_id": stage_id,
            "path": prim_path,
            "type": prim_type
        })
    
    def create_primitive(self, stage_id: str, primitive_type: str, prim_path: str, 
                        size: float = 1.0, position: List[float] = None) -> Dict[str, Any]:
        """
        Create a geometric primitive (sphere, cube, etc.).
        
        Args:
            stage_id: ID of the stage
            primitive_type: Type of primitive ("sphere", "cube", "cylinder", "cone")
            prim_path: Path where the primitive should be created
            size: Size of the primitive (default: 1.0)
            position: Position [x, y, z] (default: [0, 0, 0])
            
        Returns:
            Result of the operation
        """
        if position is None:
            position = [0.0, 0.0, 0.0]
            
        return self._call_server("create_primitive_by_id", {
            "stage_id": stage_id,
            "prim_type": primitive_type,
            "prim_path": prim_path,
            "size": size,
            "position": position
        })
    
    # Material Operations
    
    def create_material(self, stage_id: str, material_path: str, diffuse_color: List[float] = None,
                       metallic: float = 0.0, roughness: float = 0.5) -> Dict[str, Any]:
        """
        Create a PBR material.
        
        Args:
            stage_id: ID of the stage
            material_path: Path where the material should be created
            diffuse_color: RGB color as [r, g, b] with values from 0-1
            metallic: Metallic value (0-1)
            roughness: Roughness value (0-1)
            
        Returns:
            Result of the operation
        """
        if diffuse_color is None:
            diffuse_color = [0.8, 0.8, 0.8]
            
        return self._call_server("create_material_by_id", {
            "stage_id": stage_id,
            "material_path": material_path,
            "diffuse_color": diffuse_color,
            "metallic": metallic,
            "roughness": roughness
        })
    
    def bind_material(self, stage_id: str, material_path: str, prim_path: str) -> Dict[str, Any]:
        """
        Bind a material to a prim.
        
        Args:
            stage_id: ID of the stage
            material_path: Path to the material
            prim_path: Path to the prim that should receive the material
            
        Returns:
            Result of the operation
        """
        return self._call_server("bind_material_by_id", {
            "stage_id": stage_id,
            "material_path": material_path,
            "prim_path": prim_path
        })
    
    # Physics Operations
    
    def setup_physics_scene(self, stage_id: str, gravity: List[float] = None) -> Dict[str, Any]:
        """
        Set up a physics scene on the stage.
        
        Args:
            stage_id: ID of the stage
            gravity: Gravity vector as [x, y, z] (default: [0, -9.81, 0])
            
        Returns:
            Result of the operation
        """
        if gravity is None:
            gravity = [0.0, -9.81, 0.0]
            
        return self._call_server("setup_physics_scene", {
            "stage_id": stage_id,
            "gravity": gravity
        })
    
    def add_rigid_body(self, stage_id: str, prim_path: str, mass: float = 1.0, 
                      is_dynamic: bool = True) -> Dict[str, Any]:
        """
        Add rigid body physics properties to a prim.
        
        Args:
            stage_id: ID of the stage
            prim_path: Path to the prim
            mass: Mass of the rigid body in kg
            is_dynamic: Whether the body should be dynamic (vs. static)
            
        Returns:
            Result of the operation
        """
        return self._call_server("add_rigid_body", {
            "stage_id": stage_id,
            "prim_path": prim_path,
            "mass": mass,
            "is_dynamic": is_dynamic
        })
    
    # Animation Operations
    
    def set_transform(self, stage_id: str, prim_path: str, position: List[float] = None,
                     rotation: List[float] = None, scale: List[float] = None) -> Dict[str, Any]:
        """
        Set the transform of a prim.
        
        Args:
            stage_id: ID of the stage
            prim_path: Path to the prim
            position: Position as [x, y, z]
            rotation: Rotation as euler angles [x, y, z] in degrees
            scale: Scale as [x, y, z]
            
        Returns:
            Result of the operation
        """
        data = {
            "stage_id": stage_id,
            "prim_path": prim_path
        }
        
        if position is not None:
            data["translate"] = position
        if rotation is not None:
            data["rotate"] = rotation
        if scale is not None:
            data["scale"] = scale
            
        return self._call_server("set_transform_by_id", data)
    
    def create_animation(self, stage_id: str, prim_path: str, property_path: str,
                        keyframes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create an animation by setting keyframes.
        
        Args:
            stage_id: ID of the stage
            prim_path: Path to the prim to animate
            property_path: Path to the property to animate (e.g., "xformOp:translate")
            keyframes: List of keyframes, each with "time" and "value" keys
            
        Returns:
            Result of the operation
        """
        return self._call_server("create_animation", {
            "stage_id": stage_id,
            "prim_path": prim_path,
            "property_path": property_path,
            "keyframes": keyframes
        })
    
    # Scene Graph Visualization
    
    def visualize_scene_graph(self, stage_id: str, format: str = "text", 
                            output_path: Optional[str] = None, max_depth: int = None,
                            filter_types: List[str] = None, 
                            theme: str = "light") -> Dict[str, Any]:
        """
        Generate a visualization of the USD scene graph.
        
        Args:
            stage_id: ID of the stage
            format: Output format ("text", "html", "json", "network")
            output_path: Path to save the output (required for non-text formats)
            max_depth: Maximum depth to display (None for unlimited)
            filter_types: List of prim types to include (None for all)
            theme: Visual theme ("light", "dark", "contrast")
            
        Returns:
            Result of the operation, including visualization content or path
        """
        data = {
            "stage_id": stage_id,
            "output_format": format,
            "theme": theme
        }
        
        if output_path:
            data["output_path"] = output_path
        if max_depth is not None:
            data["max_depth"] = max_depth
        if filter_types:
            data["filter_type"] = filter_types
            
        return self._call_server("visualize_scene_graph_by_id", data)

    # Helper methods for common operations
    
    def create_simple_scene(self, file_path: str, primitives: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a simple scene with multiple primitives and materials.
        
        Args:
            file_path: Path to save the USD file
            primitives: List of primitive specifications, each with:
                - type: Primitive type ("sphere", "cube", etc.)
                - path: Prim path
                - position: [x, y, z] position
                - size: Size of the primitive
                - color: [r, g, b] color (optional)
                
        Returns:
            Result of the operation with stage_id
        """
        try:
            # Create a new stage
            stage_result = self.open_stage(file_path, create_if_missing=True)
            if not stage_result["ok"]:
                return stage_result
                
            stage_id = stage_result["data"]["stage_id"]
            
            # Create default primitives if none provided
            if not primitives:
                primitives = [
                    {
                        "type": "sphere", 
                        "path": "/World/Sphere", 
                        "position": [0, 1, 0], 
                        "size": 1.0,
                        "color": [1, 0, 0]  # Red
                    },
                    {
                        "type": "cube", 
                        "path": "/World/Cube", 
                        "position": [2, 0, 0], 
                        "size": 1.0,
                        "color": [0, 0, 1]  # Blue
                    }
                ]
            
            # Create each primitive and its material
            for i, prim in enumerate(primitives):
                # Create the primitive
                self.create_primitive(
                    stage_id,
                    prim["type"],
                    prim["path"],
                    prim.get("size", 1.0),
                    prim.get("position", [0, 0, 0])
                )
                
                # Create a material if color specified
                if "color" in prim:
                    material_path = f"/World/Materials/Material_{i}"
                    self.create_material(
                        stage_id,
                        material_path,
                        diffuse_color=prim["color"]
                    )
                    self.bind_material(stage_id, material_path, prim["path"])
            
            # Save the stage
            self.save_stage(stage_id)
            
            return {
                "ok": True, 
                "message": "Created simple scene successfully", 
                "data": {"stage_id": stage_id}
            }
            
        except Exception as e:
            error_msg = f"Error creating simple scene: {str(e)}"
            logger.error(error_msg)
            return {"ok": False, "message": error_msg}


# Example usage if run directly
if __name__ == "__main__":
    tools = CursorUsdTools()
    
    # Example: Create a simple scene
    result = tools.create_simple_scene(
        file_path="cursor_demo.usda",
        primitives=[
            {"type": "sphere", "path": "/World/RedSphere", "position": [0, 1, 0], "color": [1, 0, 0]},
            {"type": "cube", "path": "/World/BlueCube", "position": [2, 0, 0], "color": [0, 0, 1]},
            {"type": "cylinder", "path": "/World/GreenCylinder", "position": [-2, 0, 0], "color": [0, 1, 0]}
        ]
    )
    
    print(f"Created scene: {result}")
    
    if result["ok"]:
        stage_id = result["data"]["stage_id"]
        
        # Visualize the scene graph
        viz_result = tools.visualize_scene_graph(
            stage_id=stage_id,
            format="html",
            output_path="cursor_demo_scene.html",
            theme="dark"
        )
        
        print(f"Visualization: {viz_result}") 