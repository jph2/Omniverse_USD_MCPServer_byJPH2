"""
Main entry point for the USD MCP server.

This module initializes the MCP server and registers all available tools.
"""

import os
import sys
import argparse
import json
import logging
import threading
import time
from datetime import datetime

import mcp

from .core.registry import start_maintenance_threads
from .core.stage_operations import (
    create_stage,
    open_stage,
    save_stage,
    list_prims,
    analyze_stage,
    define_prim,
    create_reference,
    create_mesh,
    success_response,
    error_response
)

from .physics.setup import setup_physics_scene_by_id
from .physics.collisions import add_collision_by_id, remove_collision_by_id
from .physics.rigid_bodies import add_rigid_body_by_id, update_rigid_body_by_id, remove_rigid_body_by_id
from .physics.joints import create_joint_by_id, configure_joint_by_id, remove_joint_by_id

from .materials.shaders import (
    create_material_by_id,
    assign_material_by_id,
    update_material_by_id,
    create_texture_material_by_id
)

from .animation.keyframes import (
    set_keyframe_by_id,
    create_animation_by_id,
    create_transform_animation_by_id
)

from .visualization.scene_graph import visualize_scene_graph_by_id

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Global server start time for uptime tracking
server_start_time = time.time()

# Register core tools
@mcp.tool()
def get_health() -> str:
    """Get comprehensive health information about the server
    
    Returns:
        JSON string with detailed health metrics
    """
    try:
        import psutil
        import platform
        
        # Calculate server uptime
        uptime_seconds = int(time.time() - server_start_time)
        uptime_days, remainder = divmod(uptime_seconds, 86400)
        uptime_hours, remainder = divmod(remainder, 3600)
        uptime_minutes, uptime_seconds = divmod(remainder, 60)
        uptime_formatted = f"{uptime_days}d {uptime_hours}h {uptime_minutes}m {uptime_seconds}s"
        
        # Get process information
        process = psutil.Process()
        memory_info = process.memory_info()
        
        # Get stage registry information
        from .core.registry import stage_registry
        registry_stats = stage_registry.get_stats()
        
        # Collect health metrics
        health_data = {
            "status": "healthy",
            "server": {
                "name": "USD MCP Server",
                "version": "0.1.0",
                "uptime_seconds": int(time.time() - server_start_time),
                "uptime_formatted": uptime_formatted,
                "start_time": datetime.fromtimestamp(server_start_time).isoformat()
            },
            "system": {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": os.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent
            },
            "process": {
                "pid": process.pid,
                "memory_usage_mb": memory_info.rss / 1024 / 1024,
                "threads": process.num_threads()
            },
            "stages": registry_stats
        }
        
        return success_response("Server health information", health_data)
    except Exception as e:
        logger.exception(f"Error getting server health: {str(e)}")
        return error_response(f"Error getting server health: {str(e)}")

@mcp.tool()
def get_available_tools() -> str:
    """Get comprehensive information about all available tools
    
    Returns:
        JSON string with detailed information about all available tools
    """
    try:
        import inspect
        
        tools_info = []
        
        # Get all functions with @mcp.tool() decorator
        for name, func in inspect.getmembers(sys.modules[__name__]):
            if hasattr(func, "__wrapped__") and hasattr(func, "__name__"):
                # Get function signature
                sig = inspect.signature(func.__wrapped__)
                
                # Extract parameter info
                parameters = []
                for param_name, param in sig.parameters.items():
                    param_info = {
                        "name": param_name,
                        "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "any"
                    }
                    if param.default != inspect.Parameter.empty:
                        param_info["default"] = str(param.default)
                    parameters.append(param_info)
                
                # Add tool info
                tool_info = {
                    "name": func.__name__,
                    "description": func.__doc__.strip() if func.__doc__ else "No description available",
                    "parameters": parameters,
                    "return_type": str(sig.return_annotation) if sig.return_annotation != inspect.Signature.empty else "any"
                }
                tools_info.append(tool_info)
        
        return success_response("Available tools", {
            "tools_count": len(tools_info),
            "tools": tools_info
        })
    except Exception as e:
        logger.exception(f"Error getting available tools: {str(e)}")
        return error_response(f"Error getting available tools: {str(e)}")

# Register core USD operations
@mcp.tool()
def create_new_stage(file_path: str, template: str = "empty", up_axis: str = "Y") -> str:
    """Create a new USD stage with optional template
    
    Args:
        file_path: Path to save the new USD file
        template: Template to use ('empty', 'basic', 'physics', etc.)
        up_axis: Up axis for the stage ('Y' or 'Z')
        
    Returns:
        JSON string with stage ID or error description
    """
    return create_stage(file_path, template, up_axis)

@mcp.tool()
def open_usd_stage(file_path: str, create_if_missing: bool = False) -> str:
    """Open an existing USD stage or create it if requested
    
    Args:
        file_path: Path to the USD file to open
        create_if_missing: Whether to create the file if it doesn't exist
        
    Returns:
        JSON string with stage ID or error description
    """
    return open_stage(file_path, create_if_missing)

@mcp.tool()
def save_usd_stage(stage_id: str) -> str:
    """Save a stage if it has been modified
    
    Args:
        stage_id: The ID of the stage to save
        
    Returns:
        JSON string with success or error description
    """
    return save_stage(stage_id)

@mcp.tool()
def list_stage_prims(stage_id: str, prim_path: str = "/") -> str:
    """List all prims under a given path in the stage
    
    Args:
        stage_id: The ID of the stage to query
        prim_path: The path to start listing prims from
        
    Returns:
        JSON string with list of prims or error description
    """
    return list_prims(stage_id, prim_path)

@mcp.tool()
def analyze_usd_stage(file_path: str) -> str:
    """Analyze a USD stage and return information about its contents
    
    Args:
        file_path: Path to the USD file to analyze
        
    Returns:
        JSON string containing stage information or error description
    """
    return analyze_stage(file_path)

@mcp.tool()
def define_stage_prim(stage_id: str, prim_path: str, prim_type: str = "Xform") -> str:
    """Define a new prim on the stage
    
    Args:
        stage_id: The ID of the stage to modify
        prim_path: The path where the new prim should be created
        prim_type: The type of prim to create (Xform, Mesh, Sphere, etc.)
        
    Returns:
        JSON string with success or error description
    """
    return define_prim(stage_id, prim_path, prim_type)

@mcp.tool()
def create_stage_reference(stage_id: str, prim_path: str, reference_file_path: str, reference_prim_path: str = "") -> str:
    """Create a reference from a prim to an external USD file
    
    Args:
        stage_id: The ID of the stage to modify
        prim_path: The path to the prim that should reference the external file
        reference_file_path: Path to the referenced USD file
        reference_prim_path: Optional path to a specific prim in the referenced file
        
    Returns:
        JSON string with success or error description
    """
    return create_reference(stage_id, prim_path, reference_file_path, reference_prim_path)

@mcp.tool()
def create_stage_mesh(stage_id: str, prim_path: str, points: list, face_vertex_counts: list, face_vertex_indices: list) -> str:
    """Create a new mesh prim with the given geometry data
    
    Args:
        stage_id: The ID of the stage to modify
        prim_path: The path where the new mesh should be created
        points: List of points as [x,y,z] coordinates
        face_vertex_counts: Number of vertices per face
        face_vertex_indices: Indices into the points array for each vertex of each face
        
    Returns:
        JSON string with success or error description
    """
    return create_mesh(stage_id, prim_path, points, face_vertex_counts, face_vertex_indices)

# Register physics tools
@mcp.tool()
def setup_physics_scene(stage_id: str, scene_path: str) -> str:
    """Create a physics scene on a stage identified by ID
    
    Args:
        stage_id: The ID of the stage
        scene_path: Path where the physics scene will be created
        
    Returns:
        JSON string with result information
    """
    return setup_physics_scene_by_id(stage_id, scene_path)

@mcp.tool()
def add_collision(stage_id: str, prim_path: str, collision_type: str = "mesh",
                approximation: str = "convexHull", dimensions: list = None) -> str:
    """Add a collision shape to an existing prim by stage ID
    
    Args:
        stage_id: The ID of the stage
        prim_path: Path to the prim to add collision to
        collision_type: Type of collision shape ("mesh", "box", "sphere", "capsule", "plane")
        approximation: Collision approximation method ("convexHull", "meshSimplification", "none")
        dimensions: Optional dimensions for primitive shapes
        
    Returns:
        JSON string with result information
    """
    return add_collision_by_id(stage_id, prim_path, collision_type, approximation, dimensions)

@mcp.tool()
def remove_collision(stage_id: str, prim_path: str) -> str:
    """Remove collision from a prim by stage ID
    
    Args:
        stage_id: The ID of the stage
        prim_path: Path to the prim to remove collision from
        
    Returns:
        JSON string with result information
    """
    return remove_collision_by_id(stage_id, prim_path)

@mcp.tool()
def add_rigid_body(stage_id: str, prim_path: str, mass: float = 1.0, dynamic: bool = True,
                  initial_velocity: list = None) -> str:
    """Add rigid body behavior to an existing prim by stage ID
    
    Args:
        stage_id: The ID of the stage
        prim_path: Path to the prim to make a rigid body
        mass: Mass of the rigid body in kg
        dynamic: Whether the body is dynamic (affected by physics) or static
        initial_velocity: Optional initial linear velocity for the rigid body as [x, y, z]
        
    Returns:
        JSON string with result information
    """
    return add_rigid_body_by_id(stage_id, prim_path, mass, dynamic, initial_velocity)

@mcp.tool()
def update_rigid_body(stage_id: str, prim_path: str, mass: float = None,
                     dynamic: bool = None, velocity: list = None) -> str:
    """Update rigid body properties for an existing rigid body by stage ID
    
    Args:
        stage_id: The ID of the stage
        prim_path: Path to the prim with the rigid body
        mass: Optional new mass value
        dynamic: Optional new dynamic state
        velocity: Optional new velocity as [x, y, z]
        
    Returns:
        JSON string with result information
    """
    return update_rigid_body_by_id(stage_id, prim_path, mass, dynamic, velocity)

@mcp.tool()
def remove_rigid_body(stage_id: str, prim_path: str) -> str:
    """Remove rigid body behavior from a prim by stage ID
    
    Args:
        stage_id: The ID of the stage
        prim_path: Path to the prim to remove rigid body from
        
    Returns:
        JSON string with result information
    """
    return remove_rigid_body_by_id(stage_id, prim_path)

@mcp.tool()
def create_joint(stage_id: str, joint_path: str, joint_type: str, body0_path: str, body1_path: str,
               local_pos0: list = None, local_pos1: list = None,
               local_rot0: list = None, local_rot1: list = None,
               break_force: float = None, break_torque: float = None) -> str:
    """Create a joint between two rigid bodies by stage ID
    
    Args:
        stage_id: The ID of the stage
        joint_path: Path where the joint prim will be created
        joint_type: Type of joint ("fixed", "revolute", "prismatic", "spherical", "distance")
        body0_path: Path to the first body
        body1_path: Path to the second body
        local_pos0: Optional local position for the joint on the first body as [x, y, z]
        local_pos1: Optional local position for the joint on the second body as [x, y, z]
        local_rot0: Optional local rotation for the joint on the first body as [x, y, z, w]
        local_rot1: Optional local rotation for the joint on the second body as [x, y, z, w]
        break_force: Optional break force for the joint
        break_torque: Optional break torque for the joint
        
    Returns:
        JSON string with result information
    """
    return create_joint_by_id(
        stage_id, joint_path, joint_type, body0_path, body1_path,
        local_pos0, local_pos1, local_rot0, local_rot1,
        break_force, break_torque
    )

@mcp.tool()
def configure_joint(stage_id: str, joint_path: str, axis: list = None, limits: dict = None) -> str:
    """Configure parameters for an existing joint by stage ID
    
    Args:
        stage_id: The ID of the stage
        joint_path: Path to the joint prim
        axis: Optional axis direction as [x, y, z] (for revolute and prismatic joints)
        limits: Optional limits configuration dictionary with keys like "low", "high", "softness", etc.
        
    Returns:
        JSON string with result information
    """
    return configure_joint_by_id(stage_id, joint_path, axis, limits)

@mcp.tool()
def remove_joint(stage_id: str, joint_path: str) -> str:
    """Remove a joint by stage ID
    
    Args:
        stage_id: The ID of the stage
        joint_path: Path to the joint to remove
        
    Returns:
        JSON string with result information
    """
    return remove_joint_by_id(stage_id, joint_path)

# Register material tools
@mcp.tool()
def create_material(stage_id: str, material_path: str, material_type: str = "preview_surface",
                  diffuse_color: list = None, emissive_color: list = None,
                  metallic: float = None, roughness: float = None,
                  opacity: float = None) -> str:
    """Create a material by stage ID
    
    Args:
        stage_id: The ID of the stage
        material_path: Path where the material will be created
        material_type: Type of material ("preview_surface", "pbr", etc.)
        diffuse_color: Optional diffuse color as [r, g, b]
        emissive_color: Optional emissive color as [r, g, b]
        metallic: Optional metallic value (0-1)
        roughness: Optional roughness value (0-1)
        opacity: Optional opacity value (0-1)
        
    Returns:
        JSON string with result information
    """
    return create_material_by_id(
        stage_id, material_path, material_type,
        diffuse_color, emissive_color, metallic, roughness, opacity
    )

@mcp.tool()
def assign_material(stage_id: str, prim_path: str, material_path: str) -> str:
    """Assign a material to a prim by stage ID
    
    Args:
        stage_id: The ID of the stage
        prim_path: Path to the prim to assign the material to
        material_path: Path to the material to assign
        
    Returns:
        JSON string with result information
    """
    return assign_material_by_id(stage_id, prim_path, material_path)

@mcp.tool()
def update_material(stage_id: str, material_path: str,
                  diffuse_color: list = None, emissive_color: list = None,
                  metallic: float = None, roughness: float = None,
                  opacity: float = None) -> str:
    """Update a material's properties by stage ID
    
    Args:
        stage_id: The ID of the stage
        material_path: Path to the material to update
        diffuse_color: Optional diffuse color as [r, g, b]
        emissive_color: Optional emissive color as [r, g, b]
        metallic: Optional metallic value (0-1)
        roughness: Optional roughness value (0-1)
        opacity: Optional opacity value (0-1)
        
    Returns:
        JSON string with result information
    """
    return update_material_by_id(
        stage_id, material_path,
        diffuse_color, emissive_color, metallic, roughness, opacity
    )

@mcp.tool()
def create_texture_material(stage_id: str, material_path: str, 
                          texture_file_path: str, 
                          texture_type: str = "diffuse") -> str:
    """Create a material with a texture by stage ID
    
    Args:
        stage_id: The ID of the stage
        material_path: Path where the material will be created
        texture_file_path: Path to the texture file (PNG, JPG, etc.)
        texture_type: Type of texture ("diffuse", "normal", "roughness", etc.)
        
    Returns:
        JSON string with result information
    """
    return create_texture_material_by_id(
        stage_id, material_path, texture_file_path, texture_type
    )

# Register animation tools
@mcp.tool()
def set_keyframe(stage_id: str, prim_path: str, attribute_name: str,
               time: float, value: list = None,
               interpolation: str = "linear") -> str:
    """Set a keyframe for an attribute at a specific time by stage ID
    
    Args:
        stage_id: The ID of the stage
        prim_path: Path to the prim
        attribute_name: Name of the attribute to animate
        time: Time code for the keyframe
        value: Value at the keyframe
        interpolation: Interpolation type ("linear", "held", "bezier")
        
    Returns:
        JSON string with result information
    """
    return set_keyframe_by_id(
        stage_id, prim_path, attribute_name,
        time, value, interpolation
    )

@mcp.tool()
def create_animation(stage_id: str, prim_path: str, attribute_name: str,
                   keyframes: list = None,
                   time_range: list = None) -> str:
    """Create a complete animation with multiple keyframes by stage ID
    
    Args:
        stage_id: The ID of the stage
        prim_path: Path to the prim
        attribute_name: Name of the attribute to animate
        keyframes: List of keyframe dictionaries with 'time', 'value', and optional 'interpolation'
        time_range: Optional explicit time range for the animation as [start, end]
        
    Returns:
        JSON string with result information
    """
    # Convert time_range from list to tuple if provided
    time_range_tuple = tuple(time_range) if time_range else None
    
    return create_animation_by_id(
        stage_id, prim_path, attribute_name,
        keyframes, time_range_tuple
    )

@mcp.tool()
def create_transform_animation(stage_id: str, prim_path: str,
                             translate_keyframes: list = None,
                             rotate_keyframes: list = None,
                             scale_keyframes: list = None,
                             time_range: list = None) -> str:
    """Create a complete transform animation (translation, rotation, scale) by stage ID
    
    Args:
        stage_id: The ID of the stage
        prim_path: Path to the prim
        translate_keyframes: Optional list of translation keyframe dictionaries
        rotate_keyframes: Optional list of rotation keyframe dictionaries
        scale_keyframes: Optional list of scale keyframe dictionaries
        time_range: Optional explicit time range for the animation as [start, end]
        
    Returns:
        JSON string with result information
    """
    # Convert time_range from list to tuple if provided
    time_range_tuple = tuple(time_range) if time_range else None
    
    return create_transform_animation_by_id(
        stage_id, prim_path,
        translate_keyframes, rotate_keyframes, scale_keyframes,
        time_range_tuple
    )

# Register visualization tools
@mcp.tool()
def visualize_scene_graph(stage_id: str, root_path: str = "/", format: str = "html") -> str:
    """Generate a visualization of a stage's scene graph by stage ID
    
    Args:
        stage_id: The ID of the stage
        root_path: The root path to start visualization from
        format: Output format ("html", "json", "text")
        
    Returns:
        Visualization in the requested format or error response
    """
    return visualize_scene_graph_by_id(stage_id, root_path, format)

# Register resources
@mcp.resource("usd://schema")
def get_usd_schema() -> str:
    """Return information about common USD schema types
    
    Returns:
        JSON string containing schema information
    """
    try:
        schema_info = {
            "UsdGeom.Xform": "Transform node that can be used for grouping and hierarchical transformations",
            "UsdGeom.Mesh": "Polygonal mesh representation",
            "UsdGeom.Points": "Point cloud representation",
            "UsdGeom.Cube": "Parametric cube primitive",
            "UsdGeom.Sphere": "Parametric sphere primitive",
            "UsdGeom.Cylinder": "Parametric cylinder primitive",
            "UsdGeom.Cone": "Parametric cone primitive",
            "UsdLux.DistantLight": "Distant/directional light source",
            "UsdLux.DomeLight": "Dome/environment light source",
            "UsdLux.DiskLight": "Disk-shaped area light source",
            "UsdLux.SphereLight": "Spherical area light source",
            "UsdLux.RectLight": "Rectangular area light source",
            "UsdShade.Material": "Material definition for surfaces",
            "UsdPhysics.Scene": "Physics scene configuration",
            "UsdPhysics.RigidBodyAPI": "Rigid body dynamics API",
            "UsdPhysics.CollisionAPI": "Collision behavior API",
            "UsdPhysics.MeshCollisionAPI": "Mesh-specific collision API",
            "UsdPhysics.JointAPI": "Base API for all joint types",
            "UsdPhysics.RevoluteJoint": "Revolute (hinge) joint",
            "UsdPhysics.PrismaticJoint": "Prismatic (slider) joint",
            "UsdPhysics.SphericalJoint": "Spherical (ball-and-socket) joint",
            "UsdPhysics.FixedJoint": "Fixed (immovable) joint",
            "UsdPhysics.DistanceJoint": "Distance constraint joint",
            "UsdSkel.Skeleton": "Skeleton for skinned animation",
            "UsdSkel.Animation": "Animation data for a skeleton",
            "UsdSkel.BindingAPI": "API for binding meshes to skeletons"
        }
        
        return success_response("USD schema information", schema_info)
    except Exception as e:
        logger.exception(f"Error getting USD schema: {str(e)}")
        return error_response(f"Error getting USD schema: {str(e)}")

@mcp.resource("usd://help")
def get_omniverse_help() -> str:
    """Return help information about the Omniverse USD MCP server
    
    Returns:
        JSON string containing help information
    """
    try:
        help_info = {
            "name": "Omniverse USD MCP Server",
            "version": "0.1.0",
            "description": "A Model Context Protocol (MCP) server for USD and Omniverse operations",
            "documentation": "https://github.com/yourusername/omniverse-usd-mcp-server/blob/main/README.md",
            "command_categories": {
                "Core USD": ["create_new_stage", "open_usd_stage", "save_usd_stage", "list_stage_prims", "analyze_usd_stage", "define_stage_prim", "create_stage_reference", "create_stage_mesh"],
                "Physics": ["setup_physics_scene", "add_collision", "remove_collision", "add_rigid_body", "update_rigid_body", "remove_rigid_body", "create_joint", "configure_joint", "remove_joint"],
                "Materials": ["create_material", "assign_material", "update_material", "create_texture_material"],
                "Animation": ["set_keyframe", "create_animation", "create_transform_animation"],
                "Visualization": ["visualize_scene_graph"],
                "Server": ["get_health", "get_available_tools"]
            },
            "example_usages": {
                "create_basic_scene": "1. create_new_stage('my_scene.usda', 'basic', 'Y') - Create a new stage with a basic scene template\n2. save_usd_stage(stage_id) - Save the stage",
                "add_physics": "1. open_usd_stage('my_scene.usda') - Open an existing stage\n2. setup_physics_scene(stage_id, '/World/PhysicsScene') - Set up physics scene\n3. add_rigid_body(stage_id, '/World/Cube', 1.0, True) - Make a cube dynamic\n4. add_collision(stage_id, '/World/Cube', 'box') - Add collision to the cube",
                "create_animation": "1. open_usd_stage('my_scene.usda') - Open an existing stage\n2. create_transform_animation(stage_id, '/World/Cube', [{\"time\": 0, \"value\": [0,0,0]}, {\"time\": 30, \"value\": [10,0,0]}]) - Animate cube position"
            }
        }
        
        return success_response("Omniverse USD MCP server help", help_info)
    except Exception as e:
        logger.exception(f"Error getting Omniverse help: {str(e)}")
        return error_response(f"Error getting Omniverse help: {str(e)}")

def parse_args():
    """Parse command line arguments for the server"""
    parser = argparse.ArgumentParser(description='Omniverse USD MCP Server')
    parser.add_argument('--protocol', type=str, default='stdio', choices=['stdio', 'http', 'websocket', 'sse', 'tcp', 'zmq'],
                        help='Communication protocol for the server')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host for HTTP/TCP/WebSocket/SSE servers')
    parser.add_argument('--port', type=int, default=5000, help='Port for HTTP/TCP/WebSocket/SSE servers')
    parser.add_argument('--log-level', type=str, default='info', choices=['debug', 'info', 'warning', 'error', 'critical'],
                        help='Logging level')
    return parser.parse_args()

def main():
    """Main entry point for the USD MCP server"""
    args = parse_args()
    
    # Set up logging
    log_level_map = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }
    logging.basicConfig(level=log_level_map[args.log_level])
    
    # Start maintenance threads
    cache_thread, registry_thread = start_maintenance_threads()
    
    # Set up server based on protocol
    if args.protocol == 'stdio':
        logger.info("Starting USD MCP server with stdio protocol")
        server = mcp.StdioServer()
    elif args.protocol == 'http':
        logger.info(f"Starting USD MCP server with HTTP protocol on {args.host}:{args.port}")
        server = mcp.HttpServer(host=args.host, port=args.port)
    elif args.protocol == 'websocket':
        logger.info(f"Starting USD MCP server with WebSocket protocol on {args.host}:{args.port}")
        server = mcp.WebSocketServer(host=args.host, port=args.port)
    elif args.protocol == 'sse':
        logger.info(f"Starting USD MCP server with SSE protocol on {args.host}:{args.port}")
        server = mcp.SseServer(host=args.host, port=args.port)
    elif args.protocol == 'tcp':
        logger.info(f"Starting USD MCP server with TCP protocol on {args.host}:{args.port}")
        server = mcp.TcpServer(host=args.host, port=args.port)
    elif args.protocol == 'zmq':
        logger.info(f"Starting USD MCP server with ZeroMQ protocol on {args.host}:{args.port}")
        server = mcp.ZmqServer(host=args.host, port=args.port)
    else:
        logger.error(f"Unsupported protocol: {args.protocol}")
        return
    
    # Start the server
    server.serve()

if __name__ == "__main__":
    main() 