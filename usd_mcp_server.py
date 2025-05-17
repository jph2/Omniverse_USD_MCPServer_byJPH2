"""
Omniverse_USD_MCPServer_byJPH2

This module provides a Model Context Protocol (MCP) server that offers tools and resources
for working with Universal Scene Description (USD) and NVIDIA Omniverse development.

The server provides the following capabilities:
- Tools for creating and manipulating USD stages and prims
- Resources containing documentation and guides for USD and Omniverse development
- Search functionality for the Omniverse Development Guide
"""

from mcp.server.fastmcp import FastMCP, Context
from pxr import Usd, UsdGeom, Sdf
import os
import json
import re
import argparse
import sys
import logging
import platform
import threading
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Set

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("usd_mcp_server.log")
    ]
)
logger = logging.getLogger(__name__)

# Version information
VERSION = "0.2.0"
SERVER_NAME = "Omniverse_USD_MCPServer_byJPH2"

# Track server start time
server_start_time = time.time()

# Create a named server with version
mcp = FastMCP(SERVER_NAME, version=VERSION)

# Add server metadata
mcp.add_server_metadata({
    "description": "MCP server for Universal Scene Description (USD) and NVIDIA Omniverse",
    "author": "Jan Haluszka",
    "website": "https://github.com/jph2/Omniverse_USD_MCPServer_byJPH2",
    "license": "MIT",
    "environment": {
        "os": platform.system(),
        "python": platform.python_version(),
        "usd_version": getattr(Usd, "GetVersion", lambda: "unknown")()
    }
})

# Stage cache dictionary
stage_cache = {}
# Track stage access times for cache management
stage_access_times = {}
# Track stage modifications
stage_modified = {}
# Maximum number of stages to keep in cache
MAX_CACHE_SIZE = 10
# Cache maintenance interval in seconds
CACHE_MAINTENANCE_INTERVAL = 300  # 5 minutes

# Custom exceptions
class StageError(Exception):
    """Error raised when operations on a USD stage fail"""
    pass

class MeshError(Exception):
    """Error raised when mesh operations fail"""
    pass

class CacheError(Exception):
    """Error raised when cache operations fail"""
    pass

# Helper functions for response formatting
def success_response(message: str, data: Optional[Dict[str, Any]] = None) -> str:
    """Format a successful response as JSON"""
    response = {
        "ok": True,
        "message": message,
        "data": data or {},
        "timestamp": datetime.now().isoformat()
    }
    return json.dumps(response)

def error_response(message: str, error_code: Optional[str] = None) -> str:
    """Format an error response as JSON"""
    response = {
        "ok": False,
        "message": message,
        "error_code": error_code or "UNKNOWN_ERROR",
        "data": {},
        "timestamp": datetime.now().isoformat()
    }
    return json.dumps(response)

# Cache management functions
def maintain_stage_cache():
    """Background thread function to maintain the stage cache"""
    while True:
        try:
            time.sleep(CACHE_MAINTENANCE_INTERVAL)
            cleanup_stage_cache()
        except Exception as e:
            logger.exception(f"Error during cache maintenance: {e}")

def cleanup_stage_cache():
    """Remove least recently used stages from cache if cache exceeds maximum size"""
    global stage_cache, stage_access_times
    
    if len(stage_cache) <= MAX_CACHE_SIZE:
        return
    
    # Get list of stages sorted by access time (oldest first)
    sorted_stages = sorted(stage_access_times.items(), key=lambda x: x[1])
    
    # Number of stages to remove
    num_to_remove = len(stage_cache) - MAX_CACHE_SIZE
    
    # Remove oldest stages
    for i in range(num_to_remove):
        stage_path = sorted_stages[i][0]
        if stage_path in stage_cache:
            try:
                logger.info(f"Unloading stage from cache: {stage_path}")
                # Check if stage is modified
                if stage_path in stage_modified and stage_modified[stage_path]:
                    logger.warning(f"Unloading modified stage: {stage_path}")
                    # Save stage before unloading
                    stage_cache[stage_path].GetRootLayer().Save()
                # Unload the stage
                stage_cache[stage_path].Unload()
                # Remove from cache and tracking
                del stage_cache[stage_path]
                del stage_access_times[stage_path]
                if stage_path in stage_modified:
                    del stage_modified[stage_path]
            except Exception as e:
                logger.exception(f"Error unloading stage {stage_path}: {e}")

# Start the cache maintenance thread
cache_thread = threading.Thread(target=maintain_stage_cache, daemon=True)
cache_thread.start()

# Start the stage registry maintenance thread
registry_thread = threading.Thread(target=maintain_stage_registry, daemon=True)
registry_thread.start()

def maintain_stage_registry():
    """Background thread function to periodically maintain the stage registry.
    
    This function:
    1. Performs cache cleanup based on LRU policy
    2. Saves modified stages periodically
    """
    logger.info("Stage registry maintenance thread started")
    
    while True:
        try:
            # Sleep for the maintenance interval
            time.sleep(300)  # Every 5 minutes
            
            # Perform cache cleanup if needed
            stages_removed = stage_registry.perform_cache_cleanup()
            if stages_removed > 0:
                logger.info(f"Stage registry maintenance: removed {stages_removed} stages from cache")
            
            # Get statistics
            stats = stage_registry.get_stats()
            logger.debug(f"Stage registry stats: {stats}")
            
        except Exception as e:
            logger.exception(f"Error in stage registry maintenance thread: {str(e)}")
            # Continue running even if there was an error

# =============================================================================
# USD Stage Tools
# =============================================================================

@mcp.tool()
def create_stage(file_path: str, template: Optional[str] = None, up_axis: str = "Y") -> str:
    """Create a new USD stage and save it to the specified file path
    
    Args:
        file_path: Path where the USD stage should be saved
        template: Optional template to use ('empty', 'basic', 'full')
        up_axis: Up axis for the stage ('Y' or 'Z')
        
    Returns:
        JSON string with success status, message, and stage path data
    """
    try:
        # Validate parameters
        if up_axis not in ['Y', 'Z']:
            raise ValueError(f"Invalid up_axis: {up_axis}. Must be 'Y' or 'Z'")
            
        if template and template not in ['empty', 'basic', 'full']:
            raise ValueError(f"Invalid template: {template}. Must be 'empty', 'basic', or 'full'")
        
        # Ensure directory exists
        folder = os.path.dirname(file_path)
        if folder and not os.path.isdir(folder):
            os.makedirs(folder, exist_ok=True)
            
        # Create new stage
        stage = Usd.Stage.CreateNew(file_path)
        if not stage:
            raise StageError(f"Unable to create stage at '{file_path}'")
        
        # Create stage content based on template
        if not template or template == 'empty':
            # Just create an empty root prim
            root_prim = UsdGeom.Xform.Define(stage, '/root')
            stage.SetDefaultPrim(root_prim.GetPrim())
        elif template == 'basic':
            # Create basic scene structure
            root_prim = UsdGeom.Xform.Define(stage, '/World')
            stage.SetDefaultPrim(root_prim.GetPrim())
            
            # Add a camera
            camera = UsdGeom.Camera.Define(stage, '/World/Camera')
            camera.CreateFocalLengthAttr(24.0)
            camera.CreateClippingRangeAttr((0.01, 10000.0))
            camera.CreateFocusDistanceAttr(5.0)
            
            # Add a light
            light = UsdGeom.Xform.Define(stage, '/World/Light')
        elif template == 'full':
            # Create comprehensive scene structure
            world = UsdGeom.Xform.Define(stage, '/World')
            stage.SetDefaultPrim(world.GetPrim())
            
            # Create useful subgroups
            UsdGeom.Xform.Define(stage, '/World/Geometry')
            UsdGeom.Xform.Define(stage, '/World/Cameras')
            UsdGeom.Xform.Define(stage, '/World/Lights')
            UsdGeom.Xform.Define(stage, '/World/Materials')
            
            # Add a default camera
            camera = UsdGeom.Camera.Define(stage, '/World/Cameras/MainCamera')
            camera.CreateFocalLengthAttr(24.0)
            camera.CreateClippingRangeAttr((0.01, 10000.0))
            camera.CreateFocusDistanceAttr(5.0)
            
            # Create a ground plane
            ground = UsdGeom.Mesh.Define(stage, '/World/Geometry/GroundPlane')
            ground.CreatePointsAttr([(-10, 0, -10), (10, 0, -10), (10, 0, 10), (-10, 0, 10)])
            ground.CreateFaceVertexCountsAttr([4])
            ground.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
            ground.CreateNormalsAttr([(0, 1, 0), (0, 1, 0), (0, 1, 0), (0, 1, 0)])
            
            # Add a key light
            key_light = UsdGeom.Xform.Define(stage, '/World/Lights/KeyLight')
        
        # Set stage metadata
        with Sdf.ChangeBlock():
            # Set up axis
            UsdGeom.SetStageUpAxis(stage, up_axis)
            
            # Set time codes
            stage.SetStartTimeCode(1)
            stage.SetEndTimeCode(240)  # Assume 240 frames (10 seconds at 24 fps)
            
            # Set meters per unit
            UsdGeom.SetStageMetersPerUnit(stage, 0.01)  # 1 unit = 1 cm
            
            # Add creation info
            stage.GetRootLayer().SetDocumentation(f"Created by {SERVER_NAME} v{VERSION} on {datetime.now().isoformat()}")
            
            # Add custom layer metadata
            stage.GetRootLayer().customLayerData = {
                "creator": SERVER_NAME,
                "version": VERSION,
                "created": datetime.now().isoformat(),
                "template": template or "empty"
            }
        
        # Save stage
        stage.GetRootLayer().Save()
        
        # Generate a unique ID for this stage
        stage_id = str(uuid.uuid4())
        
        # Cache stage with absolute path as key
        abs_path = os.path.abspath(file_path)
        stage_cache[abs_path] = stage
        stage_access_times[abs_path] = time.time()
        stage_modified[abs_path] = False
        
        return success_response(
            f"Successfully created USD stage at {file_path}", 
            {
                "stage_path": file_path,
                "stage_id": stage_id,
                "template": template or "empty",
                "up_axis": up_axis,
                "default_prim": str(stage.GetDefaultPrim().GetPath())
            }
        )
    except Exception as e:
        logger.exception(f"Error creating stage: {str(e)}")
        return error_response(f"Error creating stage: {str(e)}", "STAGE_CREATE_ERROR")

@mcp.tool()
def close_stage(file_path: str) -> str:
    """Unload and release a USD stage from memory
    
    Args:
        file_path: Path to the USD stage to close
        
    Returns:
        JSON string with success status and message
    """
    try:
        abs_path = os.path.abspath(file_path)
        if abs_path in stage_cache:
            # Explicitly unload the stage
            stage_cache[abs_path].Unload()
            # Remove from cache
            del stage_cache[abs_path]
            return success_response(f"Stage {file_path} successfully closed")
        else:
            return error_response(f"Stage {file_path} not found in cache")
    except Exception as e:
        logger.exception(f"Error closing stage: {str(e)}")
        return error_response(f"Error closing stage: {str(e)}")

@mcp.tool()
def analyze_stage(file_path: str) -> str:
    """Analyze a USD stage and return information about its contents
    
    Args:
        file_path: Path to the USD file to analyze
        
    Returns:
        JSON string containing stage information or error description
    """
    try:
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(file_path):
            return error_response(f"File not found: {file_path}")
        
        # Try to use cached stage or open a new one
        if abs_path in stage_cache:
            stage = stage_cache[abs_path]
        else:
            stage = Usd.Stage.Open(file_path)
            if not stage:
                return error_response(f"Failed to open stage: {file_path}")
            stage_cache[abs_path] = stage
        
        # Get basic stage information
        result = {
            "root_layer_path": stage.GetRootLayer().realPath,
            "up_axis": UsdGeom.GetStageUpAxis(stage),
            "time_code_range": [stage.GetStartTimeCode(), stage.GetEndTimeCode()],
            "default_prim": str(stage.GetDefaultPrim().GetPath()) if stage.GetDefaultPrim() else None,
            "prims": []
        }
        
        # Traverse prim hierarchy with SdfChangeBlock for better performance
        with Sdf.ChangeBlock():
            for prim in Usd.PrimRange.Stage(stage):
                prim_data = {
                    "path": str(prim.GetPath()),
                    "type": prim.GetTypeName(),
                    "active": prim.IsActive(),
                    "attributes": []
                }
                
                # Gather attribute information for this prim
                if prim.GetTypeName():  # Only if prim has a type
                    for attribute in prim.GetAttributes():
                        attr_data = {
                            "name": attribute.GetName(),
                            "type": str(attribute.GetTypeName())
                        }
                        
                        # Try to get the attribute value
                        try:
                            value = attribute.Get()
                            if value is not None:
                                attr_data["value"] = str(value)
                        except:
                            pass  # Skip if we can't get the value
                        
                        prim_data["attributes"].append(attr_data)
                
                result["prims"].append(prim_data)
        
        return success_response("Stage analysis complete", result)
    except Exception as e:
        logger.exception(f"Error analyzing stage: {str(e)}")
        return error_response(f"Error analyzing stage: {str(e)}")

@mcp.tool()
def create_mesh(
    file_path: str, 
    prim_path: str, 
    points: List[tuple], 
    face_vertex_counts: List[int], 
    face_vertex_indices: List[int]
) -> str:
    """Create a mesh in a USD stage with specified geometry data
    
    Args:
        file_path: Path to the USD file
        prim_path: Path within the stage to create the mesh
        points: List of 3D points (vertices) as tuples
        face_vertex_counts: Number of vertices per face
        face_vertex_indices: Indices into the points array for each vertex of each face
        
    Returns:
        JSON string with success status and message
    """
    try:
        # Validate inputs
        if not points:
            raise MeshError("Points list cannot be empty")
        
        if not face_vertex_counts:
            raise MeshError("Face vertex counts list cannot be empty")
            
        if not face_vertex_indices:
            raise MeshError("Face vertex indices list cannot be empty")
            
        if len(face_vertex_indices) != sum(face_vertex_counts):
            raise MeshError(f"Face vertex indices count ({len(face_vertex_indices)}) does not match sum of face vertex counts ({sum(face_vertex_counts)})")
        
        abs_path = os.path.abspath(file_path)
        # Use cached stage or open/create a new one
        if abs_path in stage_cache:
            stage = stage_cache[abs_path]
        else:
            if os.path.exists(file_path):
                stage = Usd.Stage.Open(file_path)
            else:
                stage = Usd.Stage.CreateNew(file_path)
            
            if not stage:
                raise StageError(f"Failed to open or create stage: {file_path}")
            
            stage_cache[abs_path] = stage
        
        # Use a ChangeBlock for performance
        with Sdf.ChangeBlock():
            # Create mesh
            mesh = UsdGeom.Mesh.Define(stage, prim_path)
            
            # Set mesh data
            mesh.GetPointsAttr().Set(points)
            mesh.GetFaceVertexCountsAttr().Set(face_vertex_counts)
            mesh.GetFaceVertexIndicesAttr().Set(face_vertex_indices)
            
            # Add display color attribute if it doesn't exist
            if not mesh.GetDisplayColorAttr():
                mesh.CreateDisplayColorAttr()
                mesh.GetDisplayColorAttr().Set([(0.8, 0.8, 0.8)])  # Default gray color
        
        # Save stage
        stage.GetRootLayer().Save()
        
        return success_response(
            f"Successfully created mesh at {prim_path}",
            {
                "stage_path": file_path,
                "prim_path": prim_path
            }
        )
    except Exception as e:
        logger.exception(f"Error creating mesh: {str(e)}")
        return error_response(f"Error creating mesh: {str(e)}")

# =============================================================================
# Advanced USD Tools
# =============================================================================

@mcp.tool()
def create_reference(file_path: str, prim_path: str, reference_file_path: str, reference_prim_path: str = "") -> str:
    """Add a reference to an external USD file
    
    Args:
        file_path: Path to the target USD file
        prim_path: Path where to create/add reference
        reference_file_path: Path to the referenced USD file
        reference_prim_path: Optional prim path within the referenced file (defaults to root)
        
    Returns:
        JSON string with success status and message
    """
    try:
        # Validate input
        if not os.path.exists(reference_file_path):
            raise ValueError(f"Referenced file does not exist: {reference_file_path}")
            
        abs_path = os.path.abspath(file_path)
        # Use cached stage or open/create a new one
        if abs_path in stage_cache:
            stage = stage_cache[abs_path]
        else:
            if os.path.exists(file_path):
                stage = Usd.Stage.Open(file_path)
            else:
                stage = Usd.Stage.CreateNew(file_path)
            
            if not stage:
                raise StageError(f"Failed to open or create stage: {file_path}")
            
            stage_cache[abs_path] = stage
            stage_access_times[abs_path] = time.time()
        
        # Get or create the prim
        prim = stage.GetPrimAtPath(prim_path)
        if not prim:
            # Create the required prim if it doesn't exist
            prim = UsdGeom.Xform.Define(stage, prim_path).GetPrim()
        
        # Add the reference
        prim.GetReferences().AddReference(reference_file_path, reference_prim_path)
        
        # Mark stage as modified
        stage_modified[abs_path] = True
        
        # Save stage
        stage.GetRootLayer().Save()
        
        return success_response(
            f"Successfully added reference to {reference_file_path} at {prim_path}",
            {
                "stage_path": file_path,
                "prim_path": prim_path,
                "reference_path": reference_file_path,
                "reference_prim_path": reference_prim_path or "/"
            }
        )
    except Exception as e:
        logger.exception(f"Error adding reference: {str(e)}")
        return error_response(f"Error adding reference: {str(e)}")

@mcp.tool()
def create_material(file_path: str, material_path: str, diffuse_color: tuple = (0.8, 0.8, 0.8), metallic: float = 0.0, roughness: float = 0.4) -> str:
    """Create an OmniPBR material in a USD stage
    
    Args:
        file_path: Path to the USD file
        material_path: Path where to create the material
        diffuse_color: RGB tuple for diffuse color (default: light gray)
        metallic: Metallic value between 0.0 and 1.0 (default: 0.0)
        roughness: Roughness value between 0.0 and 1.0 (default: 0.4)
        
    Returns:
        JSON string with success status and message
    """
    try:
        # Validate parameters
        if not (0 <= metallic <= 1):
            raise ValueError(f"Metallic value must be between 0 and 1, got {metallic}")
        if not (0 <= roughness <= 1): 
            raise ValueError(f"Roughness value must be between 0 and 1, got {roughness}")
            
        abs_path = os.path.abspath(file_path)
        # Use cached stage or open/create a new one
        if abs_path in stage_cache:
            stage = stage_cache[abs_path]
        else:
            if os.path.exists(file_path):
                stage = Usd.Stage.Open(file_path)
            else:
                stage = Usd.Stage.CreateNew(file_path)
            
            if not stage:
                raise StageError(f"Failed to open or create stage: {file_path}")
            
            stage_cache[abs_path] = stage
            stage_access_times[abs_path] = time.time()
        
        # Create material with Sdf.ChangeBlock for better performance
        with Sdf.ChangeBlock():
            # Create material
            from pxr import UsdShade
            material = UsdShade.Material.Define(stage, material_path)
            
            # Create shader
            shader_path = f"{material_path}/Shader"
            shader = UsdShade.Shader.Define(stage, shader_path)
            shader.CreateIdAttr("OmniPBR")
            
            # Set shader inputs
            shader.CreateInput("diffuse_color", Sdf.ValueTypeNames.Color3f).Set(diffuse_color)
            shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(metallic)
            shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(roughness)
            
            # Connect shader to material
            material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
        
        # Mark stage as modified
        stage_modified[abs_path] = True
        
        # Save stage
        stage.GetRootLayer().Save()
        
        return success_response(
            f"Successfully created material at {material_path}",
            {
                "stage_path": file_path,
                "material_path": material_path,
                "properties": {
                    "diffuse_color": diffuse_color,
                    "metallic": metallic,
                    "roughness": roughness
                }
            }
        )
    except Exception as e:
        logger.exception(f"Error creating material: {str(e)}")
        return error_response(f"Error creating material: {str(e)}")

@mcp.tool()
def bind_material(file_path: str, prim_path: str, material_path: str) -> str:
    """Bind a material to a prim in the USD stage
    
    Args:
        file_path: Path to the USD file
        prim_path: Path to the prim to bind the material to
        material_path: Path to the material to bind
        
    Returns:
        JSON string with success status and message
    """
    try:
        abs_path = os.path.abspath(file_path)
        # Use cached stage or open a new one
        if abs_path in stage_cache:
            stage = stage_cache[abs_path]
        else:
            if not os.path.exists(file_path):
                return error_response(f"File not found: {file_path}")
                
            stage = Usd.Stage.Open(file_path)
            if not stage:
                return error_response(f"Failed to open stage: {file_path}")
                
            stage_cache[abs_path] = stage
            stage_access_times[abs_path] = time.time()
        
        # Get the prim and material
        prim = stage.GetPrimAtPath(prim_path)
        if not prim:
            return error_response(f"Prim not found: {prim_path}")
            
        material_prim = stage.GetPrimAtPath(material_path)
        if not material_prim:
            return error_response(f"Material not found: {material_path}")
        
        # Bind material to prim
        from pxr import UsdShade
        material = UsdShade.Material(material_prim)
        UsdShade.MaterialBindingAPI(prim).Bind(material)
        
        # Mark stage as modified
        stage_modified[abs_path] = True
        
        # Save stage
        stage.GetRootLayer().Save()
        
        return success_response(
            f"Successfully bound material {material_path} to {prim_path}",
            {
                "stage_path": file_path,
                "prim_path": prim_path,
                "material_path": material_path
            }
        )
    except Exception as e:
        logger.exception(f"Error binding material: {str(e)}")
        return error_response(f"Error binding material: {str(e)}")

@mcp.tool()
def create_primitive(file_path: str, prim_type: str, prim_path: str, size: float = 1.0, position: tuple = (0, 0, 0)) -> str:
    """Create a geometric primitive in a USD stage
    
    Args:
        file_path: Path to the USD file
        prim_type: Type of primitive ('cube', 'sphere', 'cylinder', 'cone')
        prim_path: Path where to create the primitive
        size: Size of the primitive (default: 1.0)
        position: XYZ position tuple (default: origin)
        
    Returns:
        JSON string with success status and message
    """
    try:
        # Validate prim_type
        valid_types = {'cube', 'sphere', 'cylinder', 'cone'}
        if prim_type.lower() not in valid_types:
            raise ValueError(f"Invalid primitive type: {prim_type}. Must be one of {valid_types}")
        
        abs_path = os.path.abspath(file_path)
        # Use cached stage or open/create a new one
        if abs_path in stage_cache:
            stage = stage_cache[abs_path]
        else:
            if os.path.exists(file_path):
                stage = Usd.Stage.Open(file_path)
            else:
                stage = Usd.Stage.CreateNew(file_path)
            
            if not stage:
                raise StageError(f"Failed to open or create stage: {file_path}")
            
            stage_cache[abs_path] = stage
            stage_access_times[abs_path] = time.time()
        
        # Create the primitive
        with Sdf.ChangeBlock():
            if prim_type.lower() == 'cube':
                prim = UsdGeom.Cube.Define(stage, prim_path)
                prim.CreateSizeAttr(size)
            elif prim_type.lower() == 'sphere':
                prim = UsdGeom.Sphere.Define(stage, prim_path)
                prim.CreateRadiusAttr(size / 2.0)
            elif prim_type.lower() == 'cylinder':
                prim = UsdGeom.Cylinder.Define(stage, prim_path)
                prim.CreateRadiusAttr(size / 2.0)
                prim.CreateHeightAttr(size)
            elif prim_type.lower() == 'cone':
                prim = UsdGeom.Cone.Define(stage, prim_path)
                prim.CreateRadiusAttr(size / 2.0)
                prim.CreateHeightAttr(size)
            
            # Set position
            from pxr import Gf
            xform_api = UsdGeom.XformCommonAPI(prim)
            xform_api.SetTranslate(Gf.Vec3d(position))
        
        # Mark stage as modified
        stage_modified[abs_path] = True
        
        # Save stage
        stage.GetRootLayer().Save()
        
        return success_response(
            f"Successfully created {prim_type} at {prim_path}",
            {
                "stage_path": file_path,
                "prim_path": prim_path,
                "prim_type": prim_type,
                "size": size,
                "position": position
            }
        )
    except Exception as e:
        logger.exception(f"Error creating primitive: {str(e)}")
        return error_response(f"Error creating primitive: {str(e)}")

@mcp.tool()
def export_to_format(file_path: str, output_path: str, format: str = "usda") -> str:
    """Export a USD stage to a different format
    
    Args:
        file_path: Path to the source USD file
        output_path: Path where to save the exported file
        format: Target format ('usda', 'usdc', 'usdz')
        
    Returns:
        JSON string with success status and message
    """
    try:
        # Validate format
        if format.lower() not in ['usda', 'usdc', 'usdz']:
            raise ValueError(f"Invalid format: {format}. Must be 'usda', 'usdc', or 'usdz'")
        
        # Make sure source file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source file not found: {file_path}")
            
        # Ensure directory exists for output file
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.isdir(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Open the stage
        stage = None
        abs_path = os.path.abspath(file_path)
        
        if abs_path in stage_cache:
            # Use cached stage
            stage = stage_cache[abs_path]
            # Update access time
            stage_access_times[abs_path] = time.time()
            
            # Save if modified
            if stage_modified.get(abs_path, False):
                stage.GetRootLayer().Save()
        else:
            # Open a new stage
            stage = Usd.Stage.Open(file_path)
            if not stage:
                raise StageError(f"Failed to open stage: {file_path}")
        
        # Export to the requested format
        if format.lower() == 'usda':
            # ASCII format
            stage.Export(output_path, args={'format': 'usda'})
        elif format.lower() == 'usdc':
            # Binary format
            stage.Export(output_path, args={'format': 'usdc'})
        elif format.lower() == 'usdz':
            # USD zip archive format
            from pxr import UsdUtils
            # Create a new USDZ package
            result = UsdUtils.CreateNewARKitUsdzPackage(
                stage.GetRootLayer().realPath, 
                output_path
            )
            if not result:
                raise StageError(f"Failed to create USDZ package: {output_path}")
        
        return success_response(
            f"Successfully exported stage to {format.upper()} format at {output_path}",
            {
                "source_path": file_path,
                "output_path": output_path,
                "format": format.upper()
            }
        )
    except Exception as e:
        logger.exception(f"Error exporting stage: {str(e)}")
        return error_response(f"Error exporting stage: {str(e)}")

# =============================================================================
# Physics Tools
# =============================================================================

@mcp.tool()
def setup_physics_scene(file_path: str, gravity: tuple = (0, -9.81, 0)) -> str:
    """Setup physics scene in a USD stage
    
    Args:
        file_path: Path to the USD file
        gravity: XYZ gravity vector (default: Earth gravity)
        
    Returns:
        JSON string with success status and message
    """
    try:
        abs_path = os.path.abspath(file_path)
        # Use cached stage or open/create a new one
        if abs_path in stage_cache:
            stage = stage_cache[abs_path]
        else:
            if os.path.exists(file_path):
                stage = Usd.Stage.Open(file_path)
            else:
                stage = Usd.Stage.CreateNew(file_path)
            
            if not stage:
                raise StageError(f"Failed to open or create stage: {file_path}")
            
            stage_cache[abs_path] = stage
            stage_access_times[abs_path] = time.time()
        
        # Create the physics scene
        try:
            from pxr import UsdPhysics, PhysxSchema
        except ImportError:
            return error_response("UsdPhysics and PhysxSchema schemas are required for physics functionality")
        
        with Sdf.ChangeBlock():
            # Create physics scene
            scene_path = "/World/PhysicsScene"
            physics_scene = UsdPhysics.Scene.Define(stage, scene_path)
            
            # Set gravity
            physics_scene.CreateGravityDirectionAttr().Set(gravity)
            physics_scene.CreateGravityMagnitudeAttr().Set(9.81)  # m/s²
            
            # Setup physics scene properties
            physx_scene = PhysxSchema.PhysxSceneAPI.Apply(physics_scene.GetPrim())
            physx_scene.CreateEnableCCDAttr(True)
            physx_scene.CreateEnableStabilizationAttr(True)
            physx_scene.CreateEnableGPUDynamicsAttr(True)
            physx_scene.CreateBroadphaseTypeAttr("MBP")  # Multi Box Pruning
            physx_scene.CreateSolverTypeAttr("TGS")  # Temporal Gauss Seidel
        
        # Mark stage as modified
        stage_modified[abs_path] = True
        
        # Save stage
        stage.GetRootLayer().Save()
        
        return success_response(
            f"Successfully setup physics scene in {file_path}",
            {
                "stage_path": file_path,
                "scene_path": scene_path,
                "gravity": gravity
            }
        )
    except Exception as e:
        logger.exception(f"Error setting up physics scene: {str(e)}")
        return error_response(f"Error setting up physics scene: {str(e)}")

@mcp.tool()
def add_rigid_body(file_path: str, prim_path: str, mass: float = 1.0, is_dynamic: bool = True) -> str:
    """Add rigid body properties to a prim
    
    Args:
        file_path: Path to the USD file
        prim_path: Path to the prim to make a rigid body
        mass: Mass in kg (default: 1.0)
        is_dynamic: Whether the body is dynamic (true) or kinematic (false)
        
    Returns:
        JSON string with success status and message
    """
    try:
        # Validate parameters
        if mass <= 0:
            raise ValueError(f"Mass must be positive, got {mass}")
        
        abs_path = os.path.abspath(file_path)
        # Use cached stage or open a new one
        if abs_path in stage_cache:
            stage = stage_cache[abs_path]
        else:
            if not os.path.exists(file_path):
                return error_response(f"File not found: {file_path}")
            
            stage = Usd.Stage.Open(file_path)
            if not stage:
                return error_response(f"Failed to open stage: {file_path}")
            
            stage_cache[abs_path] = stage
            stage_access_times[abs_path] = time.time()
        
        # Get the prim
        prim = stage.GetPrimAtPath(prim_path)
        if not prim:
            return error_response(f"Prim not found: {prim_path}")
        
        # Apply rigid body API with physics schemas
        try:
            from pxr import UsdPhysics, PhysxSchema
        except ImportError:
            return error_response("UsdPhysics and PhysxSchema schemas are required for physics functionality")
        
        with Sdf.ChangeBlock():
            # Apply rigid body API
            rigid_body = UsdPhysics.RigidBodyAPI.Apply(prim)
            rigid_body.CreateRigidBodyEnabledAttr(True)
            
            # Set dynamics type
            if is_dynamic:
                # Dynamic body (affected by forces, gravity)
                rigid_body.CreateKinematicEnabledAttr(False)
            else:
                # Kinematic body (moved programmatically)
                rigid_body.CreateKinematicEnabledAttr(True)
            
            # Set mass properties
            mass_api = UsdPhysics.MassAPI.Apply(prim)
            mass_api.CreateMassAttr(mass)
            
            # Setup collider (if prim has geometry)
            if prim.IsA(UsdGeom.Boundable):
                UsdPhysics.CollisionAPI.Apply(prim)
        
        # Mark stage as modified
        stage_modified[abs_path] = True
        
        # Save stage
        stage.GetRootLayer().Save()
        
        return success_response(
            f"Successfully added {('dynamic' if is_dynamic else 'kinematic')} rigid body to {prim_path}",
            {
                "stage_path": file_path,
                "prim_path": prim_path,
                "mass": mass,
                "is_dynamic": is_dynamic
            }
        )
    except Exception as e:
        logger.exception(f"Error adding rigid body: {str(e)}")
        return error_response(f"Error adding rigid body: {str(e)}")

@mcp.tool()
def add_collider(file_path: str, prim_path: str, collider_type: str = "mesh", approximation: str = "none") -> str:
    """Add a physics collider to a prim
    
    Args:
        file_path: Path to the USD file
        prim_path: Path to the prim to add the collider to
        collider_type: Type of collider ('mesh', 'box', 'sphere', 'capsule')
        approximation: Collision approximation ('none', 'convexHull', 'convexDecomposition')
        
    Returns:
        JSON string with success status and message
    """
    try:
        # Validate parameters
        valid_types = {'mesh', 'box', 'sphere', 'capsule'}
        if collider_type.lower() not in valid_types:
            raise ValueError(f"Invalid collider type: {collider_type}. Must be one of {valid_types}")
            
        valid_approx = {'none', 'convexHull', 'convexDecomposition'}
        if approximation.lower() not in valid_approx:
            raise ValueError(f"Invalid approximation: {approximation}. Must be one of {valid_approx}")
        
        abs_path = os.path.abspath(file_path)
        # Use cached stage or open a new one
        if abs_path in stage_cache:
            stage = stage_cache[abs_path]
        else:
            if not os.path.exists(file_path):
                return error_response(f"File not found: {file_path}")
            
            stage = Usd.Stage.Open(file_path)
            if not stage:
                return error_response(f"Failed to open stage: {file_path}")
            
            stage_cache[abs_path] = stage
            stage_access_times[abs_path] = time.time()
        
        # Get the prim
        prim = stage.GetPrimAtPath(prim_path)
        if not prim:
            return error_response(f"Prim not found: {prim_path}")
        
        # Apply collision APIs with physics schemas
        try:
            from pxr import UsdPhysics, PhysxSchema
        except ImportError:
            return error_response("UsdPhysics and PhysxSchema schemas are required for physics functionality")
        
        with Sdf.ChangeBlock():
            # Apply collision API
            collision_api = UsdPhysics.CollisionAPI.Apply(prim)
            
            # Apply specific collider type
            if collider_type.lower() == 'mesh':
                mesh_collider = UsdPhysics.MeshCollisionAPI.Apply(prim)
                
                # Set approximation for mesh colliders
                if approximation.lower() != 'none':
                    physx_collision = PhysxSchema.PhysxCollisionAPI.Apply(prim)
                    physx_collision.CreateApproximationAttr(approximation)
                    
            elif collider_type.lower() == 'box':
                UsdPhysics.BoxCollisionAPI.Apply(prim)
                
            elif collider_type.lower() == 'sphere':
                UsdPhysics.SphereCollisionAPI.Apply(prim)
                
            elif collider_type.lower() == 'capsule':
                UsdPhysics.CapsuleCollisionAPI.Apply(prim)
        
        # Mark stage as modified
        stage_modified[abs_path] = True
        
        # Save stage
        stage.GetRootLayer().Save()
        
        return success_response(
            f"Successfully added {collider_type} collider to {prim_path}",
            {
                "stage_path": file_path,
                "prim_path": prim_path,
                "collider_type": collider_type,
                "approximation": approximation
            }
        )
    except Exception as e:
        logger.exception(f"Error adding collider: {str(e)}")
        return error_response(f"Error adding collider: {str(e)}")

@mcp.tool()
def add_joint(
    file_path: str, 
    joint_path: str, 
    body0_path: str, 
    body1_path: str, 
    joint_type: str = "fixed",
    local_pos0: tuple = (0, 0, 0),
    local_pos1: tuple = (0, 0, 0)
) -> str:
    """Add a physics joint between two rigid bodies
    
    Args:
        file_path: Path to the USD file
        joint_path: Path where to create the joint
        body0_path: Path to the first rigid body
        body1_path: Path to the second rigid body
        joint_type: Type of joint ('fixed', 'revolute', 'prismatic', 'spherical')
        local_pos0: Local position of joint in body0 space
        local_pos1: Local position of joint in body1 space
        
    Returns:
        JSON string with success status and message
    """
    try:
        # Validate parameters
        valid_types = {'fixed', 'revolute', 'prismatic', 'spherical'}
        if joint_type.lower() not in valid_types:
            raise ValueError(f"Invalid joint type: {joint_type}. Must be one of {valid_types}")
        
        abs_path = os.path.abspath(file_path)
        # Use cached stage or open a new one
        if abs_path in stage_cache:
            stage = stage_cache[abs_path]
        else:
            if not os.path.exists(file_path):
                return error_response(f"File not found: {file_path}")
            
            stage = Usd.Stage.Open(file_path)
            if not stage:
                return error_response(f"Failed to open stage: {file_path}")
            
            stage_cache[abs_path] = stage
            stage_access_times[abs_path] = time.time()
        
        # Verify the bodies exist
        body0 = stage.GetPrimAtPath(body0_path)
        if not body0:
            return error_response(f"Body 0 not found: {body0_path}")
            
        body1 = stage.GetPrimAtPath(body1_path)
        if not body1:
            return error_response(f"Body 1 not found: {body1_path}")
        
        # Create the joint using physics schemas
        try:
            from pxr import UsdPhysics, PhysxSchema, Gf
        except ImportError:
            return error_response("UsdPhysics, PhysxSchema, and Gf modules are required for physics joints")
        
        with Sdf.ChangeBlock():
            joint = None
            
            # Create appropriate joint type
            if joint_type.lower() == 'fixed':
                joint = UsdPhysics.FixedJoint.Define(stage, joint_path)
            elif joint_type.lower() == 'revolute':
                joint = UsdPhysics.RevoluteJoint.Define(stage, joint_path)
                # Set axis of rotation to Y by default
                joint.CreateAxisAttr().Set(Gf.Vec3f(0, 1, 0))
            elif joint_type.lower() == 'prismatic':
                joint = UsdPhysics.PrismaticJoint.Define(stage, joint_path)
                # Set axis of translation to Y by default
                joint.CreateAxisAttr().Set(Gf.Vec3f(0, 1, 0))
            elif joint_type.lower() == 'spherical':
                joint = UsdPhysics.SphericalJoint.Define(stage, joint_path)
            
            # Set the bodies
            joint.CreateBody0Rel().SetTargets([body0_path])
            joint.CreateBody1Rel().SetTargets([body1_path])
            
            # Set local positions
            joint.CreateLocalPos0Attr().Set(Gf.Vec3f(local_pos0))
            joint.CreateLocalPos1Attr().Set(Gf.Vec3f(local_pos1))
            
            # Set basic joint properties
            joint.CreateExcludeFromArticulationAttr(False)
            joint.CreateCollisionEnabledAttr(False)
        
        # Mark stage as modified
        stage_modified[abs_path] = True
        
        # Save stage
        stage.GetRootLayer().Save()
        
        return success_response(
            f"Successfully created {joint_type} joint between {body0_path} and {body1_path}",
            {
                "stage_path": file_path,
                "joint_path": joint_path,
                "joint_type": joint_type,
                "body0": body0_path,
                "body1": body1_path
            }
        )
    except Exception as e:
        logger.exception(f"Error creating joint: {str(e)}")
        return error_response(f"Error creating joint: {str(e)}")

# =============================================================================
# Animation Tools
# =============================================================================

@mcp.tool()
def set_transform(
    file_path: str, 
    prim_path: str, 
    translate: Optional[tuple] = None, 
    rotate: Optional[tuple] = None, 
    scale: Optional[tuple] = None,
    time_code: Optional[float] = None
) -> str:
    """Set or animate transform on a prim
    
    Args:
        file_path: Path to the USD file
        prim_path: Path to the prim to transform
        translate: Optional XYZ translation values
        rotate: Optional XYZ rotation values in degrees
        scale: Optional XYZ scale values
        time_code: Optional time code for animation (if None, not animated)
        
    Returns:
        JSON string with success status and message
    """
    try:
        # Validate input
        if translate is None and rotate is None and scale is None:
            raise ValueError("At least one of translate, rotate, or scale must be provided")
        
        abs_path = os.path.abspath(file_path)
        # Use cached stage or open a new one
        if abs_path in stage_cache:
            stage = stage_cache[abs_path]
        else:
            if not os.path.exists(file_path):
                return error_response(f"File not found: {file_path}")
            
            stage = Usd.Stage.Open(file_path)
            if not stage:
                return error_response(f"Failed to open stage: {file_path}")
            
            stage_cache[abs_path] = stage
            stage_access_times[abs_path] = time.time()
        
        # Get the prim
        prim = stage.GetPrimAtPath(prim_path)
        if not prim:
            return error_response(f"Prim not found: {prim_path}")
        
        # Need to import the Gf module for transform operations
        try:
            from pxr import Gf
        except ImportError:
            return error_response("Gf module is required for transform operations")
        
        # Apply the transform
        with Sdf.ChangeBlock():
            xform_api = UsdGeom.XformCommonAPI(prim)
            
            # Get existing transform
            translate_values, rotate_values, scale_values, rotation_order = xform_api.GetXformVectors(time_code)
            
            # Update with provided values
            if translate is not None:
                translate_values = Gf.Vec3d(translate)
            if rotate is not None:
                rotate_values = Gf.Vec3f(rotate)
            if scale is not None:
                scale_values = Gf.Vec3f(scale)
            
            # Set the transform
            xform_api.SetXformVectors(
                translation=translate_values,
                rotation=rotate_values,
                scale=scale_values,
                pivot=Gf.Vec3f(0, 0, 0),
                rotOrder=UsdGeom.XformCommonAPI.RotationOrderXYZ,
                time=time_code
            )
        
        # Mark stage as modified
        stage_modified[abs_path] = True
        
        # Save stage
        stage.GetRootLayer().Save()
        
        transform_data = {
            "translate": tuple(translate) if translate is not None else None,
            "rotate": tuple(rotate) if rotate is not None else None,
            "scale": tuple(scale) if scale is not None else None
        }
        
        if time_code is not None:
            transform_data["time_code"] = time_code
        
        return success_response(
            f"Successfully set transform on {prim_path}",
            {
                "stage_path": file_path,
                "prim_path": prim_path,
                "transform": transform_data
            }
        )
    except Exception as e:
        logger.exception(f"Error setting transform: {str(e)}")
        return error_response(f"Error setting transform: {str(e)}")

@mcp.tool()
def create_animation(
    file_path: str, 
    prim_path: str, 
    attribute_name: str, 
    key_frames: List[Dict],
    interpolation: str = "linear"
) -> str:
    """Create an animation for a prim attribute with keyframes
    
    Args:
        file_path: Path to the USD file
        prim_path: Path to the prim with the attribute to animate
        attribute_name: Name of the attribute to animate
        key_frames: List of dictionaries with 'time' and 'value' keys
        interpolation: Interpolation method ('linear', 'held', 'bezier')
        
    Returns:
        JSON string with success status and message
    """
    try:
        # Validate parameters
        if not key_frames:
            raise ValueError("Key frames list cannot be empty")
            
        valid_interpolation = {'linear', 'held', 'bezier'}
        if interpolation.lower() not in valid_interpolation:
            raise ValueError(f"Invalid interpolation: {interpolation}. Must be one of {valid_interpolation}")
        
        # Validate keyframes structure
        for i, kf in enumerate(key_frames):
            if 'time' not in kf or 'value' not in kf:
                raise ValueError(f"Keyframe at index {i} missing required 'time' or 'value' field")
        
        abs_path = os.path.abspath(file_path)
        # Use cached stage or open a new one
        if abs_path in stage_cache:
            stage = stage_cache[abs_path]
        else:
            if not os.path.exists(file_path):
                return error_response(f"File not found: {file_path}")
            
            stage = Usd.Stage.Open(file_path)
            if not stage:
                return error_response(f"Failed to open stage: {file_path}")
            
            stage_cache[abs_path] = stage
            stage_access_times[abs_path] = time.time()
        
        # Get the prim
        prim = stage.GetPrimAtPath(prim_path)
        if not prim:
            return error_response(f"Prim not found: {prim_path}")
        
        # Get the attribute
        attr = prim.GetAttribute(attribute_name)
        if not attr.IsValid():
            return error_response(f"Attribute '{attribute_name}' not found on prim {prim_path}")
        
        # Add keyframes
        with Sdf.ChangeBlock():
            # Set keyframes
            for kf in key_frames:
                time = kf['time']
                value = kf['value']
                attr.Set(value, time)
                
            # Set interpolation if not the default
            if interpolation.lower() != 'linear':
                # Import UsdRender to avoid module import errors
                from pxr import Usd
                
                # Apply the interpolation
                if interpolation.lower() == 'held':
                    attr.SetInterpolation(Usd.InterpolationTypeHeld)
                elif interpolation.lower() == 'bezier':
                    attr.SetInterpolation(Usd.InterpolationTypeCubic)
        
        # Make sure the stage has a valid time range
        start_time = min(kf['time'] for kf in key_frames)
        end_time = max(kf['time'] for kf in key_frames)
        
        # Only update time range if needed
        current_start = stage.GetStartTimeCode()
        current_end = stage.GetEndTimeCode()
        if current_start > start_time or current_start == 0:
            stage.SetStartTimeCode(start_time)
        if current_end < end_time:
            stage.SetEndTimeCode(end_time)
        
        # Mark stage as modified
        stage_modified[abs_path] = True
        
        # Save stage
        stage.GetRootLayer().Save()
        
        return success_response(
            f"Successfully created animation for {attribute_name} on {prim_path}",
            {
                "stage_path": file_path,
                "prim_path": prim_path,
                "attribute": attribute_name,
                "num_keyframes": len(key_frames),
                "time_range": [start_time, end_time],
                "interpolation": interpolation
            }
        )
    except Exception as e:
        logger.exception(f"Error creating animation: {str(e)}")
        return error_response(f"Error creating animation: {str(e)}")

@mcp.tool()
def create_skeleton(
    file_path: str, 
    skeleton_path: str, 
    joint_names: List[str], 
    joint_hierarchy: List[int],
    rest_transforms: List[Dict]
) -> str:
    """Create a skeleton for rigging and animation
    
    Args:
        file_path: Path to the USD file
        skeleton_path: Path where to create the skeleton
        joint_names: List of joint names
        joint_hierarchy: List of parent indices (-1 for root)
        rest_transforms: List of dictionaries with 'translate', 'rotate', and 'scale' keys
        
    Returns:
        JSON string with success status and message
    """
    try:
        # Validate parameters
        if not joint_names:
            raise ValueError("Joint names list cannot be empty")
            
        if len(joint_hierarchy) != len(joint_names):
            raise ValueError("Joint hierarchy list must be the same length as joint names list")
            
        if len(rest_transforms) != len(joint_names):
            raise ValueError("Rest transforms list must be the same length as joint names list")
        
        # Check for valid hierarchy (parents must come before children)
        for i, parent_idx in enumerate(joint_hierarchy):
            if parent_idx >= i:
                raise ValueError(f"Invalid hierarchy: parent index {parent_idx} at position {i} must be less than {i} or -1 for root")
        
        abs_path = os.path.abspath(file_path)
        # Use cached stage or open a new one
        if abs_path in stage_cache:
            stage = stage_cache[abs_path]
        else:
            if os.path.exists(file_path):
                stage = Usd.Stage.Open(file_path)
            else:
                stage = Usd.Stage.CreateNew(file_path)
            
            if not stage:
                raise StageError(f"Failed to open or create stage: {file_path}")
            
            stage_cache[abs_path] = stage
            stage_access_times[abs_path] = time.time()
        
        # Create the skeleton with UsdSkel
        try:
            from pxr import UsdSkel, Gf
        except ImportError:
            return error_response("UsdSkel module is required for skeleton operations")
        
        with Sdf.ChangeBlock():
            # Create the skeleton
            skeleton = UsdSkel.Skeleton.Define(stage, skeleton_path)
            
            # Set joint names
            skeleton.CreateJointsAttr().Set(joint_names)
            
            # Build bind transforms
            bind_transforms = []
            for transform in rest_transforms:
                translate = transform.get('translate', (0, 0, 0))
                rotate = transform.get('rotate', (0, 0, 0))
                scale = transform.get('scale', (1, 1, 1))
                
                # Create transformation matrix
                matrix = Gf.Matrix4d().SetTransform(
                    Gf.Vec3d(translate),
                    Gf.Rotation(Gf.Vec3d(1, 0, 0), rotate[0]) * 
                    Gf.Rotation(Gf.Vec3d(0, 1, 0), rotate[1]) * 
                    Gf.Rotation(Gf.Vec3d(0, 0, 1), rotate[2]),
                    Gf.Vec3d(scale)
                )
                bind_transforms.append(matrix)
            
            # Set bind transforms
            skeleton.CreateBindTransformsAttr().Set(bind_transforms)
            
            # Set rest transforms (same as bind transforms for setup)
            skeleton.CreateRestTransformsAttr().Set(bind_transforms)
            
            # Create a topology attribute to define the hierarchy
            skeleton.CreateTopologyAttr().Set(joint_hierarchy)
        
        # Mark stage as modified
        stage_modified[abs_path] = True
        
        # Save stage
        stage.GetRootLayer().Save()
        
        return success_response(
            f"Successfully created skeleton with {len(joint_names)} joints at {skeleton_path}",
            {
                "stage_path": file_path,
                "skeleton_path": skeleton_path,
                "num_joints": len(joint_names),
                "joint_names": joint_names
            }
        )
    except Exception as e:
        logger.exception(f"Error creating skeleton: {str(e)}")
        return error_response(f"Error creating skeleton: {str(e)}")

@mcp.tool()
def bind_skeleton(file_path: str, skeleton_path: str, mesh_path: str, joint_indices: List[int], joint_weights: List[float]) -> str:
    """Bind a skeleton to a mesh for skinning
    
    Args:
        file_path: Path to the USD file
        skeleton_path: Path to the skeleton
        mesh_path: Path to the mesh to bind
        joint_indices: List of joint indices for each vertex
        joint_weights: List of joint weights for each vertex
        
    Returns:
        JSON string with success status and message
    """
    try:
        # Validate parameters
        if not joint_indices:
            raise ValueError("Joint indices list cannot be empty")
            
        if len(joint_weights) != len(joint_indices):
            raise ValueError("Joint weights list must be the same length as joint indices list")
        
        abs_path = os.path.abspath(file_path)
        # Use cached stage or open a new one
        if abs_path in stage_cache:
            stage = stage_cache[abs_path]
        else:
            if not os.path.exists(file_path):
                return error_response(f"File not found: {file_path}")
            
            stage = Usd.Stage.Open(file_path)
            if not stage:
                return error_response(f"Failed to open stage: {file_path}")
            
            stage_cache[abs_path] = stage
            stage_access_times[abs_path] = time.time()
        
        # Get the skeleton and mesh
        skeleton_prim = stage.GetPrimAtPath(skeleton_path)
        if not skeleton_prim:
            return error_response(f"Skeleton not found at {skeleton_path}")
            
        mesh_prim = stage.GetPrimAtPath(mesh_path)
        if not mesh_prim:
            return error_response(f"Mesh not found at {mesh_path}")
        
        # Apply skin binding
        try:
            from pxr import UsdSkel
        except ImportError:
            return error_response("UsdSkel module is required for skeleton binding")
        
        with Sdf.ChangeBlock():
            # Create a SkelBindingAPI on the mesh
            binding_api = UsdSkel.BindingAPI.Apply(mesh_prim)
            
            # Create a skeleton relation
            binding_api.CreateSkeletonRel().SetTargets([skeleton_path])
            
            # Set joint indices and weights for the binding
            binding_api.CreateJointIndicesPrimvar(constant=False, elementSize=4).Set(joint_indices)
            binding_api.CreateJointWeightsPrimvar(constant=False, elementSize=4).Set(joint_weights)
            
            # Create a geometry binding prim
            geom_binding_path = f"{mesh_path}/SkelBinding"
            geom_binding = UsdSkel.SkelBindingAPI.Apply(stage.DefinePrim(geom_binding_path))
            
            # Create a bind transform (identity)
            from pxr import Gf
            identity = Gf.Matrix4d().SetIdentity()
            geom_binding.CreateBindTransformAttr().Set(identity)
        
        # Mark stage as modified
        stage_modified[abs_path] = True
        
        # Save stage
        stage.GetRootLayer().Save()
        
        return success_response(
            f"Successfully bound skeleton {skeleton_path} to mesh {mesh_path}",
            {
                "stage_path": file_path,
                "skeleton_path": skeleton_path,
                "mesh_path": mesh_path,
                "num_influences": len(joint_indices) // 4  # Assuming 4 weights per vertex
            }
        )
    except Exception as e:
        logger.exception(f"Error binding skeleton: {str(e)}")
        return error_response(f"Error binding skeleton: {str(e)}")

@mcp.tool()
def create_skeletal_animation(
    file_path: str, 
    animation_path: str, 
    skeleton_path: str,
    joint_names: List[str],
    transforms_by_time: Dict[float, List[Dict]]
) -> str:
    """Create a skeletal animation for a skeleton
    
    Args:
        file_path: Path to the USD file
        animation_path: Path where to create the animation
        skeleton_path: Path to the skeleton to animate
        joint_names: List of joint names in the skeleton
        transforms_by_time: Dictionary of time codes to lists of transform dictionaries
        
    Returns:
        JSON string with success status and message
    """
    try:
        # Validate parameters
        if not joint_names:
            raise ValueError("Joint names list cannot be empty")
            
        if not transforms_by_time:
            raise ValueError("Transforms by time dictionary cannot be empty")
        
        # Validate transform data structure
        for time, transforms in transforms_by_time.items():
            if len(transforms) != len(joint_names):
                raise ValueError(f"Transform list at time {time} must have {len(joint_names)} elements")
        
        abs_path = os.path.abspath(file_path)
        # Use cached stage or open a new one
        if abs_path in stage_cache:
            stage = stage_cache[abs_path]
        else:
            if os.path.exists(file_path):
                stage = Usd.Stage.Open(file_path)
            else:
                stage = Usd.Stage.CreateNew(file_path)
            
            if not stage:
                raise StageError(f"Failed to open or create stage: {file_path}")
            
            stage_cache[abs_path] = stage
            stage_access_times[abs_path] = time.time()
        
        # Verify the skeleton exists
        skeleton_prim = stage.GetPrimAtPath(skeleton_path)
        if not skeleton_prim:
            return error_response(f"Skeleton not found at {skeleton_path}")
        
        # Create the animation
        try:
            from pxr import UsdSkel, Gf
        except ImportError:
            return error_response("UsdSkel module is required for skeletal animation")
        
        with Sdf.ChangeBlock():
            # Create the animation
            skel_anim = UsdSkel.Animation.Define(stage, animation_path)
            
            # Set the joint names (must match the skeleton)
            skel_anim.CreateJointsAttr().Set(joint_names)
            
            # Create the animation data
            times = sorted(float(t) for t in transforms_by_time.keys())
            
            # Update stage time codes
            start_time = min(times)
            end_time = max(times)
            
            # Only update time range if needed
            current_start = stage.GetStartTimeCode()
            current_end = stage.GetEndTimeCode()
            if current_start > start_time or current_start == 0:
                stage.SetStartTimeCode(start_time)
            if current_end < end_time:
                stage.SetEndTimeCode(end_time)
            
            # Create attributes for translations, rotations, and scales
            translations_attr = skel_anim.CreateTranslationsAttr()
            rotations_attr = skel_anim.CreateRotationsAttr()
            scales_attr = skel_anim.CreateScalesAttr()
            
            # Set keyframes
            for time in times:
                transforms = transforms_by_time[time]
                
                # Extract translations, rotations, and scales
                translations = []
                rotations = []
                scales = []
                
                for transform in transforms:
                    # Get transform components with defaults
                    translate = transform.get('translate', (0, 0, 0))
                    rotate = transform.get('rotate', (0, 0, 0))
                    scale = transform.get('scale', (1, 1, 1))
                    
                    # Add to arrays
                    translations.append(Gf.Vec3f(translate))
                    
                    # Convert Euler angles to quaternion
                    rotation = Gf.Rotation(Gf.Vec3d(1, 0, 0), rotate[0]) * \
                              Gf.Rotation(Gf.Vec3d(0, 1, 0), rotate[1]) * \
                              Gf.Rotation(Gf.Vec3d(0, 0, 1), rotate[2])
                    rotations.append(rotation.GetQuat())
                    
                    scales.append(Gf.Vec3h(scale))
                
                # Set the values at the current time
                translations_attr.Set(translations, time)
                rotations_attr.Set(rotations, time)
                scales_attr.Set(scales, time)
            
            # Bind the animation to the skeleton
            skel_binding = UsdSkel.BindingAPI.Apply(skeleton_prim)
            skel_binding.CreateAnimationSourceRel().SetTargets([animation_path])
        
        # Mark stage as modified
        stage_modified[abs_path] = True
        
        # Save stage
        stage.GetRootLayer().Save()
        
        return success_response(
            f"Successfully created skeletal animation at {animation_path}",
            {
                "stage_path": file_path,
                "animation_path": animation_path,
                "skeleton_path": skeleton_path,
                "num_joints": len(joint_names),
                "num_keyframes": len(times),
                "time_range": [start_time, end_time]
            }
        )
    except Exception as e:
        logger.exception(f"Error creating skeletal animation: {str(e)}")
        return error_response(f"Error creating skeletal animation: {str(e)}")

# =============================================================================
# Documentation Resources
# =============================================================================

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
            "UsdSkel.Skeleton": "Joints and rest pose for skeletal animation",
            "UsdSkel.SkelAnimation": "Joint animation data",
            "UsdShade.Material": "Material definition for surfaces",
            "UsdShade.Shader": "Shader implementation for materials",
            "UsdPhysics.RigidBody": "Rigid body for physics simulations",
            "UsdPhysics.CollisionAPI": "API for collision detection in physics",
            "UsdPhysics.JointAPI": "API for joint constraints in physics"
        }
        return json.dumps(schema_info, indent=2)
    except Exception as e:
        logger.exception(f"Error retrieving USD schema information: {str(e)}")
        return error_response(f"Error retrieving USD schema information: {str(e)}")

@mcp.resource("omniverse://help")
def get_omniverse_help() -> str:
    """Return help information about Omniverse Kit and USD integration
    
    Returns:
        Markdown formatted help text
    """
    help_info = """
    # Omniverse Kit and USD Integration
    
    ## Basic Concepts
    
    - **USD (Universal Scene Description)**: Pixar's open-source scene description format that provides a rich toolset for describing, composing, and editing 3D scenes.
    
    - **Omniverse Kit**: NVIDIA's extensible application development framework for building custom Omniverse applications and services.
    
    - **Extensions**: Plugins that add functionality to Omniverse applications, developed using Python and the Omniverse Kit SDK.
    
    ## Common Workflows
    
    1. **Scene Loading/Saving**: 
       - Use `Usd.Stage.Open()` to open existing stages
       - Use `Usd.Stage.CreateNew()` to create new stages
       - Use `stage.GetRootLayer().Save()` to save changes
    
    2. **Prim Manipulation**: 
       - Use `stage.GetPrimAtPath()` to access prims
       - Use `UsdGeom.*` classes to create and manipulate geometry
       - Use `prim.GetAttributes()` to access attributes
    
    3. **Material Assignment**: 
       - Use `UsdShade` and MaterialX for surface appearances
       - Use `UsdShade.Material.Define()` to create materials
       - Use `UsdShade.MaterialBindingAPI().Bind()` to assign materials
    
    4. **Physics Setup**: 
       - Use `UsdPhysics` for physical simulations
       - Apply `UsdPhysics.RigidBodyAPI` for dynamic objects
       - Create colliders with `UsdPhysics.CollisionAPI`
    
    5. **Collaborative Workflows**: 
       - Use Nucleus server for multi-user editing
       - Use layer stacks for non-destructive editing
       - Use references and payloads for instancing
    
    ## Performance Tips
    
    - Use instancing for repeated geometry via `.SetInstanceable(True)`
    - Defer operations using change blocks with `with Sdf.ChangeBlock():`
    - Organize complex scenes with references and payloads
    - Optimize mesh topology for real-time viewing
    - Use purpose attributes to selectively load content
    """
    return help_info

@mcp.resource("omniverse://development-guide")
def get_omniverse_development_guide() -> str:
    """Return comprehensive development guide for Omniverse Kit and USD development
    
    Returns:
        Markdown formatted development guide
    """
    guide = """
    # Comprehensive Omniverse Development Guide
    
    ## Omniverse Kit Architecture
    
    ### Core Components
    
    - **Kit SDK**: The foundation of Omniverse applications built on a service-oriented architecture. Kit provides a plugin-based system allowing developers to extend functionality in modular ways.
    
    - **Carbonite**: Performance optimization SDK for real-time 3D workflows, handling memory management, threading, and resource allocation.
    
    - **Nucleus**: Collaborative database and asset management system, enabling real-time multi-user workflows and asset versioning.
    
    - **RTX Renderer**: Real-time ray tracing rendering engine leveraging NVIDIA RTX technology for physically accurate rendering.
    
    - **Physics**: PhysX integration for simulation of physical interactions, providing high-performance physics calculations.
    
    ### Extension System
    
    Omniverse Kit uses a modular plugin architecture where functionality is added through extensions.
    
    #### Extension Structure
    ```
    my_extension/
    ├── config/
    │   └── extension.toml       # Extension metadata
    ├── data/                    # Static assets
    ├── icons/                   # UI icons
    ├── omni/                    # Python module namespace
    │   └── my_extension/        # Extension code
    │       ├── __init__.py      # Entry point
    │       └── scripts/         # Additional scripts
    └── docs/                    # Documentation
    ```
    
    #### Extension Registration
    ```python
    import omni.ext
    
    class MyExtension(omni.ext.IExt):
        def on_startup(self, ext_id):
            # Initialize extension
            self._window = None
            self._menu_path = "Window/My Extension"
            
            # Create a menu item
            editor_menu = omni.kit.ui.get_editor_menu()
            if editor_menu:
                self._menu = editor_menu.add_item(
                    self._menu_path, self._on_menu_click, toggle=True, value=False
                )
        
        def on_shutdown(self):
            # Clean up resources
            if self._menu:
                editor_menu = omni.kit.ui.get_editor_menu()
                if editor_menu:
                    editor_menu.remove_item(self._menu)
            
            if self._window:
                self._window.destroy()
                self._window = None
    ```
    
    ## USD Python Development
    
    ### Stage Management
    
    #### Creating Stages
    ```python
    from pxr import Usd, UsdGeom
    
    # Create a new stage
    stage = Usd.Stage.CreateNew("my_stage.usda")
    
    # Define a default prim
    root_prim = UsdGeom.Xform.Define(stage, "/Root")
    stage.SetDefaultPrim(root_prim.GetPrim())
    
    # Save the stage
    stage.GetRootLayer().Save()
    ```
    
    #### Loading Stages
    ```python
    from pxr import Usd
    
    # Open an existing stage
    stage = Usd.Stage.Open("existing_stage.usda")
    
    # Open with specific load set
    stage = Usd.Stage.Open("heavy_stage.usda", Usd.Stage.LoadNone)
    
    # Load specific prims
    root = stage.GetPrimAtPath("/Root")
    stage.LoadAndUnload([root], [])  # Load root, unload nothing
    ```
    
    ### Prim Operations
    
    #### Creating and Modifying Prims
    ```python
    from pxr import Usd, UsdGeom, Gf
    
    # Create a sphere
    sphere = UsdGeom.Sphere.Define(stage, "/Root/Sphere")
    sphere.CreateRadiusAttr(2.0)
    
    # Create a transform
    xform = UsdGeom.Xform.Define(stage, "/Root/Group")
    
    # Set transform matrix
    op = xform.AddTranslateOp()
    op.Set(Gf.Vec3d(1.0, 2.0, 3.0))
    
    # Set visibility
    UsdGeom.Imageable(sphere.GetPrim()).CreateVisibilityAttr("invisible")
    ```
    
    #### Working with Attributes
    ```python
    # Create custom attributes
    prim = stage.GetPrimAtPath("/Root")
    attr = prim.CreateAttribute("customAttr", Sdf.ValueTypeNames.Float)
    attr.Set(1.0)
    
    # Time samples
    attr.Set(1.0, 0.0)  # value 1.0 at time 0
    attr.Set(2.0, 1.0)  # value 2.0 at time 1
    
    # Metadata
    attr.SetMetadata("documentation", "This is a custom attribute")
    ```
    
    ### USD Composition
    
    #### References and Payloads
    ```python
    # Add a reference
    prim = stage.GetPrimAtPath("/Root/ReferencedObject")
    prim.GetReferences().AddReference("external_asset.usd", "/SourcePrim")
    
    # Add a payload
    prim = stage.GetPrimAtPath("/Root/HeavyObject")
    prim.GetPayloads().AddPayload("heavy_asset.usd", "/SourcePrim")
    ```
    
    #### Layer Management
    ```python
    from pxr import Sdf
    
    # Create a new layer
    layer = Sdf.Layer.CreateNew("sublayer.usda")
    
    # Add a sublayer
    rootLayer = stage.GetRootLayer()
    rootLayer.subLayerPaths.append("sublayer.usda")
    
    # Edit in a specific layer
    with Usd.EditContext(stage, layer):
        UsdGeom.Sphere.Define(stage, "/Root/LayerSpecificSphere")
    ```
    
    ## Omniverse Kit UI Development
    
    ### UI Elements with omni.ui
    
    ```python
    import omni.ui as ui
    
    # Create a window
    self._window = ui.Window("My Extension", width=300, height=300)
    with self._window.frame:
        with ui.VStack(spacing=5):
            ui.Label("Hello Omniverse")
            
            def on_click():
                print("Button clicked!")
            
            ui.Button("Click Me", clicked_fn=on_click)
            
            with ui.HStack():
                self._slider = ui.FloatSlider(min=0, max=10)
                self._value_label = ui.Label("0.0")
            
                def on_slider_change(val):
                    self._value_label.text = f"{val:.1f}"
                
                self._slider.model.add_value_changed_fn(on_slider_change)
    ```
    
    ### Viewport Integration
    
    ```python
    import omni.kit.viewport.utility as vp_utils
    
    # Get active viewport
    viewport_api = vp_utils.get_active_viewport_window()
    
    # Register for selection changes
    self._selection_subscription = omni.usd.get_context().get_selection().create_subscription_to_pop(
        self._on_selection_changed
    )
    
    # Manipulator example
    self._manipulator = omni.kit.manipulator.create_manipulator("xform")
    self._manipulator.set_transform(position, rotation, scale)
    ```
    
    ## Performance Optimization
    
    ### USD Performance Tips
    
    1. **Use SdfChangeBlock for batched changes**
    ```python
    with Sdf.ChangeBlock():
        # Multiple USD operations here
        for i in range(1000):
            UsdGeom.Sphere.Define(stage, f"/Root/Sphere_{i}")
    ```
    
    2. **Leverage instanceable prims for repeated geometry**
    ```python
    prototype = UsdGeom.Scope.Define(stage, "/Prototypes/Cube")
    # ... add geometry to prototype
    
    instance = stage.OverridePrim("/Instances/Cube_1")
    instance.SetInstanceable(True)
    instance.GetReferences().AddReference("", "/Prototypes/Cube")
    ```
    
    3. **Use purpose attributes for optimization**
    ```python
    geom = UsdGeom.Mesh.Define(stage, "/Root/DetailMesh")
    UsdGeom.Imageable(geom).CreatePurposeAttr("proxy")
    ```
    
    ### Carbonite SDK for Optimization
    
    Carbonite provides optimized memory management and threading for high-performance applications:
    
    ```python
    import omni.carbonite as carbonite
    
    # Create a thread pool
    thread_pool = carbonite.ThreadPool(num_threads=4)
    
    # Submit task to thread pool
    future = thread_pool.submit(heavy_computation_function, arg1, arg2)
    
    # Wait for result
    result = future.get()
    ```
    
    ## Networking and Collaboration
    
    ### Omniverse Client Library
    
    ```python
    import omni.client
    
    # Connect to Nucleus server
    result = omni.client.connect("omniverse://localhost/Users")
    
    # List folder contents
    list_result, entries = omni.client.list("omniverse://localhost/Projects")
    for entry in entries:
        print(f"Found: {entry.relative_path}")
    
    # Live editing
    omni.client.live_process_status(
        "omniverse://localhost/Projects/MyProject.usd",
        True,  # Start live session
        cb_fn=self._on_live_update
    )
    
    def _on_live_update(self, update_info):
        # Handle real-time updates
        if update_info.status == omni.client.LiveUpdateStatus.LIVE_UPDATE:
            print(f"Updated: {update_info.path}")
    ```
    
    ## Physics and Simulation
    
    ### PhysX Integration
    
    ```python
    from pxr import PhysxSchema, UsdPhysics
    
    # Add physics scene
    physics_scene = UsdPhysics.Scene.Define(stage, "/World/physics")
    
    # Add rigid body
    rigid_body = UsdPhysics.RigidBody.Define(stage, "/World/Cube")
    
    # Add collider
    collider = UsdPhysics.SphereCollider.Define(stage, "/World/Cube/Collider")
    collider.CreateRadiusAttr(1.0)
    
    # Set mass properties
    mass_api = UsdPhysics.MassAPI.Apply(rigid_body.GetPrim())
    mass_api.CreateMassAttr(10.0)
    
    # Add force
    force = UsdPhysics.ForceAPI.Apply(rigid_body.GetPrim())
    force.CreateMagnitudeAttr(100.0)
    force.CreateDirectionAttr(Gf.Vec3f(0, 1, 0))
    ```
    
    ## Material and Rendering
    
    ### MDL Materials
    
    ```python
    from pxr import UsdShade, Sdf
    
    # Create material
    material = UsdShade.Material.Define(stage, "/Root/Materials/MyMaterial")
    
    # Create MDL shader
    mdl_shader = UsdShade.Shader.Define(stage, "/Root/Materials/MyMaterial/Shader")
    mdl_shader.CreateIdAttr("nvidia.mdl.OmniPBR")
    
    # Set inputs
    mdl_shader.CreateInput("diffuse_color", Sdf.ValueTypeNames.Color3f).Set((1.0, 0.0, 0.0))
    mdl_shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.8)
    mdl_shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.2)
    
    # Connect shader to material outputs
    material.CreateSurfaceOutput().ConnectToSource(mdl_shader.ConnectableAPI(), "surface")
    
    # Bind material to geometry
    UsdShade.MaterialBindingAPI(stage.GetPrimAtPath("/Root/Mesh")).Bind(material)
    ```
    
    ## Best Practices
    
    1. **Extension Organization**
       - Keep extension code modular and focused
       - Implement clear lifecycle management in on_startup/on_shutdown
       - Use namespaces to avoid conflicts
    
    2. **USD Data Management**
       - Use layers to organize scene data logically
       - Implement proper error handling for USD operations
       - Create utility functions for common operations
    
    3. **Performance**
       - Profile your code to identify bottlenecks
       - Batch USD operations when possible
       - Implement threading for heavy computations
       - Use instanceable prims for repeated elements
    
    4. **UI Design**
       - Follow Omniverse UI guidelines for consistency
       - Implement responsive layouts
       - Connect UI elements to data models properly
    
    5. **Versioning and Compatibility**
       - Document Omniverse Kit version requirements
       - Test against multiple versions
       - Use feature detection rather than version checks
    """
    return guide

@mcp.tool()
def search_omniverse_guide(topic: str) -> str:
    """Search the Comprehensive Omniverse Development Guide for specific topics
    
    Args:
        topic: The topic to search for (e.g., 'materials', 'physics', 'extension', etc.)
    
    Returns:
        Relevant sections from the development guide matching the topic
    """
    guide = get_omniverse_development_guide()
    
    # Split the guide into sections by headers
    sections = re.split(r'(?=#+\s)', guide)
    
    # Filter sections that match the topic
    matching_sections = []
    for section in sections:
        if topic.lower() in section.lower():
            # Clean up the section
            clean_section = section.strip()
            if clean_section:
                matching_sections.append(clean_section)
    
    if not matching_sections:
        return (f"No information found for topic: '{topic}'. Try different keywords like "
                f"'materials', 'extensions', 'physics', 'UI', 'performance', etc.")
    
    # Join the matching sections and return
    return "\n\n".join(matching_sections)

# =============================================================================
# Server Status and Management Tools
# =============================================================================

@mcp.tool()
def get_server_status() -> str:
    """Get the current status of the USD MCP server
    
    Returns:
        JSON string with server status information
    """
    try:
        # Calculate memory usage of stages
        stage_memory = {}
        total_stage_size = 0
        
        for path, stage in stage_cache.items():
            try:
                # Get an estimate of stage memory usage (this is approximate)
                layer_size = os.path.getsize(stage.GetRootLayer().realPath) if os.path.exists(stage.GetRootLayer().realPath) else 0
                num_prims = len(list(Usd.PrimRange.Stage(stage)))
                
                # Rough estimate of memory usage
                memory_estimate = layer_size + (num_prims * 1024)  # 1KB per prim as a rough estimate
                stage_memory[path] = {
                    "size_bytes": layer_size,
                    "num_prims": num_prims,
                    "memory_estimate_bytes": memory_estimate,
                    "last_accessed": stage_access_times.get(path, "unknown"),
                    "modified": stage_modified.get(path, False)
                }
                total_stage_size += memory_estimate
            except Exception as e:
                logger.warning(f"Error calculating memory for stage {path}: {e}")
        
        status = {
            "server": {
                "name": SERVER_NAME,
                "version": VERSION,
                "uptime_seconds": int(time.time() - server_start_time),
                "os": platform.system(),
                "python_version": platform.python_version(),
                "usd_version": getattr(Usd, "GetVersion", lambda: "unknown")()
            },
            "cache": {
                "stages_cached": len(stage_cache),
                "max_cache_size": MAX_CACHE_SIZE,
                "total_estimated_memory_bytes": total_stage_size,
                "cache_maintenance_interval_seconds": CACHE_MAINTENANCE_INTERVAL
            },
            "stages": stage_memory
        }
        
        return success_response("Server status", status)
    except Exception as e:
        logger.exception(f"Error getting server status: {e}")
        return error_response(f"Error getting server status: {str(e)}", "STATUS_ERROR")

@mcp.tool()
def get_registry_status() -> str:
    """Get the current status of the stage registry
    
    Returns:
        JSON string with registry status information
    """
    try:
        # Get registry statistics
        stats = stage_registry.get_stats()
        
        # Add additional information
        stats["server_uptime"] = int(time.time() - server_start_time)
        stats["server_version"] = VERSION
        
        # Get detailed information for each stage
        stage_details = []
        for stage_id in stats["stage_ids"]:
            file_path = stage_registry.get_stage_path(stage_id)
            is_modified = stage_registry.is_modified(stage_id)
            
            stage_details.append({
                "stage_id": stage_id,
                "file_path": file_path,
                "modified": is_modified
            })
        
        stats["stage_details"] = stage_details
        
        return success_response("Stage registry status", stats)
    except Exception as e:
        logger.exception(f"Error retrieving registry status: {str(e)}")
        return error_response(f"Error retrieving registry status: {str(e)}")

# =============================================================================
# Server Startup with CLI Arguments
# =============================================================================

def parse_arguments():
    """Parse command line arguments for the server
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(description="USD MCP Server")
    parser.add_argument('--host', default='127.0.0.1', help='Server host address')
    parser.add_argument('--port', type=int, default=5000, help='Server port')
    parser.add_argument('--protocol', default='stdio', choices=['stdio', 'http', 'sse', 'zmq'], 
                        help='Server protocol (stdio, http, sse, or zmq)')
    parser.add_argument('--log-level', default='INFO', 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
                        help='Logging level')
    return parser.parse_args()

# =============================================================================
# Scene Graph Visualization Tools
# =============================================================================

@mcp.tool()
def visualize_scene_graph(file_path: str, output_format: str = "text", output_path: Optional[str] = None, max_depth: int = -1, include_properties: bool = False) -> str:
    """Visualize the scene graph of a USD stage in various formats
    
    Args:
        file_path: Path to the USD stage file
        output_format: Format for visualization ('text', 'html', 'json', or 'network')
        output_path: Optional path for the output file
        max_depth: Maximum depth to visualize (-1 for unlimited)
        include_properties: Whether to include properties (for text format)
        
    Returns:
        JSON string with success status, message, and visualization data
    """
    try:
        # Ensure the file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Validate format
        if output_format not in ['text', 'html', 'json', 'network']:
            raise ValueError(f"Invalid format: {output_format}. Must be 'text', 'html', 'json', or 'network'")
            
        # Import the visualizer module
        try:
            from scene_graph_visualizer import UsdSceneGraphVisualizer
        except ImportError:
            raise ImportError("Scene graph visualizer module not found. Make sure scene_graph_visualizer.py is available.")
            
        # Create visualizer
        visualizer = UsdSceneGraphVisualizer(file_path, max_depth)
        
        # Generate output based on format
        if output_format == "text":
            visualization = visualizer.to_text(include_properties=include_properties)
            result_data = {"visualization": visualization}
            
            # Optionally save to file
            if output_path:
                with open(output_path, 'w') as f:
                    f.write(visualization)
                result_data["output_file"] = output_path
                
        elif output_format == "html":
            # Generate HTML file
            if not output_path:
                output_path = f"{os.path.splitext(file_path)[0]}_visualization.html"
                
            html_file = visualizer.to_html(output_path)
            result_data = {
                "output_file": html_file,
                "file_type": "html"
            }
            
        elif output_format == "json":
            # Generate JSON file or string
            if output_path:
                json_file = visualizer.to_json(output_path)
                result_data = {
                    "output_file": json_file,
                    "file_type": "json"
                }
            else:
                json_string = visualizer.to_json()
                result_data = {
                    "visualization": json_string,
                    "file_type": "json"
                }
                
        elif output_format == "network":
            # Generate network graph data
            if not output_path:
                output_path = f"{os.path.splitext(file_path)[0]}_network.json"
                
            network_data = visualizer.to_network_data(output_path)
            result_data = {
                "output_file": output_path,
                "file_type": "json",
                "node_count": len(network_data["nodes"]),
                "link_count": len(network_data["links"])
            }
            
        return success_response(
            f"Generated {output_format} visualization for {file_path}",
            result_data
        )
        
    except Exception as e:
        logger.exception(f"Error visualizing scene graph: {e}")
        return error_response(f"Failed to visualize scene graph: {str(e)}", "VISUALIZATION_ERROR")

@mcp.tool()
def visualize_scene_graph_by_id(
    stage_id: str, 
    output_format: str = "text", 
    output_path: Optional[str] = None, 
    max_depth: int = -1, 
    include_properties: bool = False,
    filter_type: Optional[str] = None,
    filter_path: Optional[str] = None
) -> str:
    """Generate a visualization of the USD scene graph using stage ID
    
    Args:
        stage_id: ID of the stage to visualize
        output_format: Format of the visualization ('text', 'html', 'json', 'network')
        output_path: Optional path to save the visualization output
        max_depth: Maximum depth to traverse (-1 for unlimited)
        include_properties: Whether to include prim properties
        filter_type: Optional filter to show only prims of a specific type
        filter_path: Optional regex pattern to filter prim paths
        
    Returns:
        JSON string with success status and visualization data
    """
    try:
        # Get the stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            return error_response(f"Stage with ID {stage_id} not found")
        
        # Get the file path
        file_path = stage_registry.get_stage_path(stage_id)
        
        # Process scene graph based on format
        valid_formats = ["text", "html", "json", "network"]
        if output_format.lower() not in valid_formats:
            return error_response(f"Invalid output format: {output_format}. Must be one of {valid_formats}")
        
        # Prepare filter functions
        type_filter = None
        path_filter = None
        
        if filter_type:
            type_filter = lambda prim: prim.GetTypeName() == filter_type
            
        if filter_path:
            import re
            path_pattern = re.compile(filter_path)
            path_filter = lambda prim: path_pattern.search(str(prim.GetPath())) is not None
            
        # Combine filters if both are present
        prim_filter = None
        if type_filter and path_filter:
            prim_filter = lambda prim: type_filter(prim) and path_filter(prim)
        elif type_filter:
            prim_filter = type_filter
        elif path_filter:
            prim_filter = path_filter
        
        # Create scene graph data structure
        scene_data = {"name": os.path.basename(file_path), "children": []}
        
        # Compute scene graph structure
        def process_prim(prim, parent_data, current_depth=0):
            # Check depth limit
            if max_depth >= 0 and current_depth > max_depth:
                return
                
            # Apply filter if specified
            if prim_filter and not prim_filter(prim):
                # If this prim doesn't match but might have children that do, continue
                for child in prim.GetChildren():
                    process_prim(child, parent_data, current_depth + 1)
                return
                
            # Create node for this prim
            prim_data = {
                "name": prim.GetName(),
                "path": str(prim.GetPath()),
                "type": prim.GetTypeName(),
                "children": []
            }
            
            # Add properties if requested
            if include_properties:
                props = {}
                for prop in prim.GetProperties():
                    try:
                        value = prop.Get()
                        if value is not None:
                            props[prop.GetName()] = str(value)
                    except:
                        props[prop.GetName()] = "<error retrieving value>"
                prim_data["properties"] = props
                
            # Add to parent's children
            parent_data["children"].append(prim_data)
            
            # Process children
            for child in prim.GetChildren():
                process_prim(child, prim_data, current_depth + 1)
        
        # Start processing with root prim
        default_prim = stage.GetDefaultPrim()
        if default_prim:
            process_prim(default_prim, scene_data)
        else:
            # Process all root prims if no default
            for root_prim in stage.GetPseudoRoot().GetChildren():
                process_prim(root_prim, scene_data)
        
        # Generate output based on format
        result = None
        if output_format.lower() == "text":
            # Generate text representation
            text_output = []
            
            def format_prim_text(prim_data, indent=0):
                line = " " * indent + f"- {prim_data['name']} ({prim_data['type']})"
                text_output.append(line)
                
                # Add properties if included
                if include_properties and "properties" in prim_data:
                    for name, value in prim_data["properties"].items():
                        prop_line = " " * (indent + 2) + f"{name}: {value}"
                        text_output.append(prop_line)
                
                # Process children
                for child in prim_data["children"]:
                    format_prim_text(child, indent + 2)
            
            # Start formatting from root
            text_output.append(f"Scene Graph for: {os.path.basename(file_path)}")
            for root_prim in scene_data["children"]:
                format_prim_text(root_prim)
                
            result = "\n".join(text_output)
            
        elif output_format.lower() == "html":
            # Generate HTML representation with collapsible tree
            html_output = [
                "<!DOCTYPE html>",
                "<html>",
                "<head>",
                "  <title>USD Scene Graph Visualization</title>",
                "  <style>",
                "    body { font-family: Arial, sans-serif; margin: 20px; }",
                "    .tree-node { margin-left: 20px; }",
                "    .node-content { cursor: pointer; padding: 2px; }",
                "    .node-content:hover { background-color: #f0f0f0; }",
                "    .properties { margin-left: 20px; color: #555; font-size: 0.9em; }",
                "    .prim-type { color: #888; font-style: italic; }",
                "    .collapsed .tree-node { display: none; }",
                "    .collapsed .properties { display: none; }",
                "    .expander { display: inline-block; width: 15px; }",
                "  </style>",
                "  <script>",
                "    function toggleNode(element) {",
                "      element.parentElement.classList.toggle('collapsed');",
                "    }",
                "  </script>",
                "</head>",
                "<body>",
                f"  <h2>USD Scene Graph: {os.path.basename(file_path)}</h2>"
            ]
            
            def format_prim_html(prim_data):
                has_children = len(prim_data["children"]) > 0 or ("properties" in prim_data and len(prim_data["properties"]) > 0)
                node_class = " collapsed" if has_children else ""
                
                html = [f"<div class='node{node_class}'>"]
                
                if has_children:
                    expander = "[-]"
                else:
                    expander = "&nbsp;&nbsp;"
                    
                html.append(f"  <div class='node-content' onclick='toggleNode(this)'>")
                html.append(f"    <span class='expander'>{expander}</span>")
                html.append(f"    {prim_data['name']} <span class='prim-type'>({prim_data['type']})</span>")
                html.append(f"  </div>")
                
                # Add properties
                if include_properties and "properties" in prim_data:
                    html.append(f"  <div class='properties'>")
                    for name, value in prim_data["properties"].items():
                        html.append(f"    <div>{name}: {value}</div>")
                    html.append(f"  </div>")
                
                # Add children
                if prim_data["children"]:
                    html.append(f"  <div class='tree-node'>")
                    for child in prim_data["children"]:
                        html.extend(format_prim_html(child))
                    html.append(f"  </div>")
                
                html.append("</div>")
                return html
            
            # Add all root prims
            for root_prim in scene_data["children"]:
                html_output.extend(format_prim_html(root_prim))
                
            # Close HTML
            html_output.extend(["</body>", "</html>"])
            result = "\n".join(html_output)
            
        elif output_format.lower() == "json":
            # Return the raw JSON data
            import json
            result = json.dumps(scene_data, indent=2)
            
        elif output_format.lower() == "network":
            # Generate a network graph format suitable for visualization tools
            network_data = {
                "nodes": [],
                "links": []
            }
            
            # Node ID counter
            node_id = 0
            path_to_id = {}
            
            def add_to_network(prim_data, parent_id=None):
                nonlocal node_id
                current_id = node_id
                node_id += 1
                
                # Store mapping from path to id
                path_to_id[prim_data["path"]] = current_id
                
                # Create node
                node = {
                    "id": current_id,
                    "name": prim_data["name"],
                    "path": prim_data["path"],
                    "type": prim_data["type"]
                }
                
                # Add properties if requested
                if include_properties and "properties" in prim_data:
                    node["properties"] = prim_data["properties"]
                    
                network_data["nodes"].append(node)
                
                # Create link to parent if exists
                if parent_id is not None:
                    network_data["links"].append({
                        "source": parent_id,
                        "target": current_id,
                        "type": "child"
                    })
                
                # Process children
                for child in prim_data["children"]:
                    add_to_network(child, current_id)
            
            # Process all root prims
            for root_prim in scene_data["children"]:
                add_to_network(root_prim)
                
            import json
            result = json.dumps(network_data, indent=2)
        
        # Save to file if output path provided
        if output_path and result:
            with open(output_path, 'w') as f:
                f.write(result)
        
        # Return result
        response_data = {
            "stage_id": stage_id,
            "file_path": file_path,
            "format": output_format
        }
        
        if output_path:
            response_data["output_path"] = output_path
        else:
            response_data["visualization"] = result
            
        return success_response(f"Successfully visualized scene graph for {os.path.basename(file_path)}", response_data)
    except Exception as e:
        logger.exception(f"Error visualizing scene graph: {str(e)}")
        return error_response(f"Error visualizing scene graph: {str(e)}", "VISUALIZATION_ERROR")

# =============================================================================
# Stage Registry (Level A: Basic MCP)
# =============================================================================

class StageRegistry:
    """Thread-safe registry for managing USD stages.
    
    This registry:
    1. Maintains a map of stage_id → Usd.Stage objects
    2. Tracks file paths associated with each stage
    3. Tracks modification status for each stage
    4. Implements LRU cache functionality with access times
    """
    
    def __init__(self, max_cache_size=10):
        """Initialize the stage registry with specified cache size.
        
        Args:
            max_cache_size: Maximum number of stages to keep in memory
        """
        self._stages = {}  # Map of stage_id → Usd.Stage
        self._stage_file_paths = {}  # Map of stage_id → file_path
        self._stage_access_times = {}  # Map of stage_id → last_access_time
        self._stage_modified = {}  # Map of stage_id → is_modified
        self._lock = threading.Lock()
        self.max_cache_size = max_cache_size
    
    def register_stage(self, file_path, stage):
        """Register a stage with the registry and return its unique ID.
        
        Args:
            file_path: Path to the USD file associated with this stage
            stage: The Usd.Stage object to register
            
        Returns:
            str: A unique stage_id for this stage
        """
        with self._lock:
            stage_id = str(uuid.uuid4())
            self._stages[stage_id] = stage
            self._stage_file_paths[stage_id] = file_path
            self._stage_access_times[stage_id] = time.time()
            self._stage_modified[stage_id] = False
            
            # Check if we need to clean up the cache
            if len(self._stages) > self.max_cache_size:
                self.perform_cache_cleanup()
                
            return stage_id
    
    def get_stage(self, stage_id):
        """Get a stage by its ID and update its access time.
        
        Args:
            stage_id: The unique ID of the stage to retrieve
            
        Returns:
            Usd.Stage or None: The stage if found, None otherwise
        """
        with self._lock:
            if stage_id in self._stages:
                # Update access time
                self._stage_access_times[stage_id] = time.time()
                return self._stages[stage_id]
            return None
    
    def get_stage_path(self, stage_id):
        """Get the file path associated with a stage.
        
        Args:
            stage_id: The unique ID of the stage
            
        Returns:
            str or None: The file path if found, None otherwise
        """
        with self._lock:
            return self._stage_file_paths.get(stage_id)
    
    def mark_as_modified(self, stage_id):
        """Mark a stage as having unsaved modifications.
        
        Args:
            stage_id: The unique ID of the stage
            
        Returns:
            bool: True if the stage was found and marked, False otherwise
        """
        with self._lock:
            if stage_id in self._stages:
                self._stage_modified[stage_id] = True
                return True
            return False
    
    def is_modified(self, stage_id):
        """Check if a stage has unsaved modifications.
        
        Args:
            stage_id: The unique ID of the stage
            
        Returns:
            bool: True if the stage has unsaved modifications, False otherwise
        """
        with self._lock:
            return self._stage_modified.get(stage_id, False)
    
    def save_stage(self, stage_id):
        """Save a stage if it has been modified.
        
        Args:
            stage_id: The unique ID of the stage
            
        Returns:
            bool: True if the stage was saved, False otherwise
        """
        with self._lock:
            if stage_id in self._stages and self._stage_modified.get(stage_id, False):
                try:
                    self._stages[stage_id].GetRootLayer().Save()
                    self._stage_modified[stage_id] = False
                    return True
                except Exception as e:
                    logger.exception(f"Error saving stage {stage_id}: {str(e)}")
                    return False
            return False
    
    def unregister_stage(self, stage_id, save_if_modified=True):
        """Unregister a stage and optionally save it if modified.
        
        Args:
            stage_id: The unique ID of the stage
            save_if_modified: Whether to save the stage if it has been modified
            
        Returns:
            bool: True if the stage was found and unregistered, False otherwise
        """
        with self._lock:
            if stage_id in self._stages:
                stage = self._stages[stage_id]
                
                # Save if modified and requested
                if save_if_modified and self._stage_modified.get(stage_id, False):
                    try:
                        stage.GetRootLayer().Save()
                    except Exception as e:
                        logger.exception(f"Error saving stage during unregister: {str(e)}")
                
                # Unload stage and remove from registry
                stage.Unload()
                del self._stages[stage_id]
                del self._stage_file_paths[stage_id]
                del self._stage_access_times[stage_id]
                del self._stage_modified[stage_id]
                
                return True
            return False
    
    def perform_cache_cleanup(self):
        """Clean up the stage cache based on LRU policy.
        
        This will unload and unregister the least recently used stages.
        """
        with self._lock:
            # No cleanup needed if under size limit
            if len(self._stages) <= self.max_cache_size:
                return 0
            
            # Sort stages by access time (oldest first)
            sorted_ids = sorted(self._stage_access_times.keys(), 
                               key=lambda k: self._stage_access_times[k])
            
            # Calculate how many stages to remove
            num_to_remove = len(self._stages) - self.max_cache_size
            stages_to_remove = sorted_ids[:num_to_remove]
            
            # Remove the oldest stages
            for stage_id in stages_to_remove:
                self.unregister_stage(stage_id, save_if_modified=True)
            
            return len(stages_to_remove)
    
    def get_all_stage_ids(self):
        """Get a list of all registered stage IDs.
        
        Returns:
            list: List of all stage IDs in the registry
        """
        with self._lock:
            return list(self._stages.keys())
    
    def get_stats(self):
        """Get statistics about the stage registry.
        
        Returns:
            dict: Statistics about the registry
        """
        with self._lock:
            return {
                "total_stages": len(self._stages),
                "max_cache_size": self.max_cache_size,
                "modified_stages": sum(1 for v in self._stage_modified.values() if v),
                "stage_ids": list(self._stages.keys())
            }

# Create the global stage registry
stage_registry = StageRegistry(max_cache_size=10)  # Adjust size as needed

# =============================================================================
# Helper Functions and Classes
# =============================================================================

# =============================================================================
# Level A: Basic USD Operations
# =============================================================================

@mcp.tool()
def open_stage(file_path: str, create_if_missing: bool = False) -> str:
    """Open an existing USD stage or create a new one if specified.
    
    Args:
        file_path: Path to the USD file to open
        create_if_missing: Whether to create the stage if it doesn't exist
        
    Returns:
        JSON string with success status, message, and stage data including stage_id
    """
    try:
        # Validate file_path
        if not file_path:
            raise ValueError("File path cannot be empty")
            
        abs_path = os.path.abspath(file_path)
        
        # Check if file exists
        file_exists = os.path.exists(file_path)
        
        if not file_exists and not create_if_missing:
            return error_response(f"File not found: {file_path}")
            
        # Open or create the stage
        stage = None
        if file_exists:
            stage = Usd.Stage.Open(file_path)
            if not stage:
                return error_response(f"Failed to open stage: {file_path}")
                
            logger.info(f"Opened existing stage: {file_path}")
        else:
            # Create new stage with minimal setup
            stage = Usd.Stage.CreateNew(file_path)
            if not stage:
                return error_response(f"Failed to create stage: {file_path}")
                
            # Set up a basic empty stage
            root_prim = UsdGeom.Xform.Define(stage, '/root')
            stage.SetDefaultPrim(root_prim.GetPrim())
            
            # Save the new stage
            stage.GetRootLayer().Save()
            logger.info(f"Created new stage: {file_path}")
        
        # Register the stage with the registry
        stage_id = stage_registry.register_stage(file_path, stage)
        
        # Get basic stage info
        stage_info = {
            "stage_id": stage_id,
            "file_path": file_path,
            "up_axis": UsdGeom.GetStageUpAxis(stage),
            "default_prim": str(stage.GetDefaultPrim().GetPath()) if stage.GetDefaultPrim() else None,
            "time_code_range": [stage.GetStartTimeCode(), stage.GetEndTimeCode()],
            "newly_created": not file_exists
        }
        
        return success_response(
            f"Successfully {'created' if not file_exists else 'opened'} USD stage at {file_path}",
            stage_info
        )
    except Exception as e:
        logger.exception(f"Error opening stage: {str(e)}")
        return error_response(f"Error opening stage: {str(e)}")

@mcp.tool()
def close_stage_by_id(stage_id: str, save_if_modified: bool = True) -> str:
    """Unload and release a USD stage from memory using its ID
    
    Args:
        stage_id: The unique ID of the stage to close
        save_if_modified: Whether to save the stage if it has unsaved modifications
        
    Returns:
        JSON string with success status and message
    """
    try:
        # Check if stage exists in registry
        file_path = stage_registry.get_stage_path(stage_id)
        if not file_path:
            return error_response(f"Stage with ID {stage_id} not found in registry")
        
        # Unregister the stage (this also unloads it)
        if stage_registry.unregister_stage(stage_id, save_if_modified):
            return success_response(f"Stage {file_path} (ID: {stage_id}) successfully closed")
        else:
            return error_response(f"Failed to close stage with ID {stage_id}")
    except Exception as e:
        logger.exception(f"Error closing stage: {str(e)}")
        return error_response(f"Error closing stage: {str(e)}")

# =============================================================================
# Level B: Advanced USD Operations Using Stage Registry
# =============================================================================

@mcp.tool()
def set_transform_by_id(
    stage_id: str, 
    prim_path: str, 
    translate: Optional[tuple] = None, 
    rotate: Optional[tuple] = None, 
    scale: Optional[tuple] = None,
    time_code: Optional[float] = None
) -> str:
    """Set or modify the transformation of a prim using the stage ID
    
    Args:
        stage_id: ID of the stage containing the prim
        prim_path: Path to the prim to transform
        translate: Optional XYZ translation values as tuple
        rotate: Optional XYZ rotation values in degrees as tuple
        scale: Optional XYZ scale values as tuple
        time_code: Optional time code for animation
        
    Returns:
        JSON string with success status and message
    """
    try:
        # Get the stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            return error_response(f"Stage with ID {stage_id} not found")
        
        # Get the file path for logging/response
        file_path = stage_registry.get_stage_path(stage_id)
            
        # Get the prim
        prim = stage.GetPrimAtPath(prim_path)
        if not prim:
            return error_response(f"Prim not found at path: {prim_path}")
        
        # Import modules for transform operations
        from pxr import UsdGeom, Gf
        
        # Check if prim can be transformed
        if not prim.IsA(UsdGeom.Xformable):
            return error_response(f"Prim at {prim_path} is not transformable")
        
        # Get the transform API
        xform_api = UsdGeom.XformCommonAPI(UsdGeom.Xformable(prim))
        
        # Preserve existing transforms if any parameter is None
        existing_translate, existing_rotate, existing_scale = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)
        try:
            result = xform_api.GetXformVectors(time_code)
            if result:
                existing_translate, existing_rotate, existing_scale = result[1:4]
        except:
            # Use defaults if we can't get existing transforms
            pass
        
        # Apply the transforms
        translate = translate or existing_translate
        rotate = rotate or existing_rotate
        scale = scale or existing_scale
        
        # Set the transform at given time or default time
        xform_api.SetXformVectors(
            Gf.Vec3d(translate), 
            Gf.Vec3f(rotate), 
            Gf.Vec3f(scale),
            UsdGeom.XformCommonAPI.RotationOrderXYZ, 
            time_code
        )
        
        # Mark stage as modified
        stage_registry.mark_as_modified(stage_id)
        
        # Save stage
        stage.GetRootLayer().Save()
        
        return success_response(
            f"Successfully applied transform to {prim_path}",
            {
                "stage_id": stage_id,
                "file_path": file_path,
                "prim_path": prim_path,
                "translate": translate,
                "rotate": rotate,
                "scale": scale,
                "time_code": time_code
            }
        )
    except Exception as e:
        logger.exception(f"Error setting transform: {str(e)}")
        return error_response(f"Error setting transform: {str(e)}")

@mcp.tool()
def analyze_stage_by_id(stage_id: str, include_attributes: bool = False) -> str:
    """Analyze a USD stage by ID and return information about its contents
    
    Args:
        stage_id: ID of the stage to analyze
        include_attributes: Whether to include detailed attribute information
        
    Returns:
        JSON string containing stage information or error description
    """
    try:
        # Get stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            return error_response(f"Stage with ID {stage_id} not found")
        
        # Get file path for response
        file_path = stage_registry.get_stage_path(stage_id)
        
        # Get basic stage information
        result = {
            "stage_id": stage_id,
            "file_path": file_path,
            "root_layer_path": stage.GetRootLayer().realPath,
            "up_axis": UsdGeom.GetStageUpAxis(stage),
            "time_code_range": [stage.GetStartTimeCode(), stage.GetEndTimeCode()],
            "default_prim": str(stage.GetDefaultPrim().GetPath()) if stage.GetDefaultPrim() else None,
            "prims": []
        }
        
        # Traverse prim hierarchy with SdfChangeBlock for better performance
        with Sdf.ChangeBlock():
            for prim in Usd.PrimRange.Stage(stage):
                prim_data = {
                    "path": str(prim.GetPath()),
                    "type": prim.GetTypeName(),
                    "active": prim.IsActive(),
                }
                
                # Add attributes if requested
                if include_attributes and prim.GetTypeName():
                    prim_data["attributes"] = []
                    
                    for attribute in prim.GetAttributes():
                        attr_data = {
                            "name": attribute.GetName(),
                            "type": str(attribute.GetTypeName())
                        }
                        
                        # Try to get the attribute value
                        try:
                            value = attribute.Get()
                            if value is not None:
                                attr_data["value"] = str(value)
                        except:
                            pass  # Skip if we can't get the value
                        
                        prim_data["attributes"].append(attr_data)
                
                result["prims"].append(prim_data)
        
        return success_response("Stage analysis complete", result)
    except Exception as e:
        logger.exception(f"Error analyzing stage: {str(e)}")
        return error_response(f"Error analyzing stage: {str(e)}")

@mcp.tool()
def create_mesh_by_id(
    stage_id: str, 
    prim_path: str, 
    points: List[tuple], 
    face_vertex_counts: List[int], 
    face_vertex_indices: List[int]
) -> str:
    """Create a mesh in a USD stage with specified geometry data using stage ID
    
    Args:
        stage_id: ID of the stage to modify
        prim_path: Path within the stage to create the mesh
        points: List of 3D points (vertices) as tuples
        face_vertex_counts: Number of vertices per face
        face_vertex_indices: Indices into the points array for each vertex of each face
        
    Returns:
        JSON string with success status and message
    """
    try:
        # Validate inputs
        if not points:
            raise MeshError("Points list cannot be empty")
        
        if not face_vertex_counts:
            raise MeshError("Face vertex counts list cannot be empty")
            
        if not face_vertex_indices:
            raise MeshError("Face vertex indices list cannot be empty")
            
        if len(face_vertex_indices) != sum(face_vertex_counts):
            raise MeshError(f"Face vertex indices count ({len(face_vertex_indices)}) does not match sum of face vertex counts ({sum(face_vertex_counts)})")
        
        # Get stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            return error_response(f"Stage with ID {stage_id} not found")
        
        # Get file path for response
        file_path = stage_registry.get_stage_path(stage_id)
        
        # Use a ChangeBlock for performance
        with Sdf.ChangeBlock():
            # Create mesh
            mesh = UsdGeom.Mesh.Define(stage, prim_path)
            
            # Set mesh data
            mesh.GetPointsAttr().Set(points)
            mesh.GetFaceVertexCountsAttr().Set(face_vertex_counts)
            mesh.GetFaceVertexIndicesAttr().Set(face_vertex_indices)
            
            # Add display color attribute if it doesn't exist
            if not mesh.GetDisplayColorAttr():
                mesh.CreateDisplayColorAttr()
                mesh.GetDisplayColorAttr().Set([(0.8, 0.8, 0.8)])  # Default gray color
        
        # Mark stage as modified
        stage_registry.mark_as_modified(stage_id)
        
        # Save stage
        stage.GetRootLayer().Save()
        
        return success_response(
            f"Successfully created mesh at {prim_path}",
            {
                "stage_id": stage_id,
                "file_path": file_path,
                "prim_path": prim_path
            }
        )
    except Exception as e:
        logger.exception(f"Error creating mesh: {str(e)}")
        return error_response(f"Error creating mesh: {str(e)}")

@mcp.tool()
def create_primitive_by_id(stage_id: str, prim_type: str, prim_path: str, size: float = 1.0, position: tuple = (0, 0, 0)) -> str:
    """Create a geometric primitive in a USD stage using stage ID
    
    Args:
        stage_id: ID of the stage to modify
        prim_type: Type of primitive ('cube', 'sphere', 'cylinder', 'cone')
        prim_path: Path where to create the primitive
        size: Size of the primitive (default: 1.0)
        position: XYZ position tuple (default: origin)
        
    Returns:
        JSON string with success status and message
    """
    try:
        # Validate prim_type
        valid_types = {'cube', 'sphere', 'cylinder', 'cone'}
        if prim_type.lower() not in valid_types:
            raise ValueError(f"Invalid primitive type: {prim_type}. Must be one of {valid_types}")
        
        # Get stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            return error_response(f"Stage with ID {stage_id} not found")
        
        # Get file path for response
        file_path = stage_registry.get_stage_path(stage_id)
        
        # Create the primitive
        with Sdf.ChangeBlock():
            if prim_type.lower() == 'cube':
                prim = UsdGeom.Cube.Define(stage, prim_path)
                prim.CreateSizeAttr(size)
            elif prim_type.lower() == 'sphere':
                prim = UsdGeom.Sphere.Define(stage, prim_path)
                prim.CreateRadiusAttr(size / 2.0)
            elif prim_type.lower() == 'cylinder':
                prim = UsdGeom.Cylinder.Define(stage, prim_path)
                prim.CreateRadiusAttr(size / 2.0)
                prim.CreateHeightAttr(size)
            elif prim_type.lower() == 'cone':
                prim = UsdGeom.Cone.Define(stage, prim_path)
                prim.CreateRadiusAttr(size / 2.0)
                prim.CreateHeightAttr(size)
            
            # Set position
            from pxr import Gf
            xform_api = UsdGeom.XformCommonAPI(prim)
            xform_api.SetTranslate(Gf.Vec3d(position))
        
        # Mark stage as modified
        stage_registry.mark_as_modified(stage_id)
        
        # Save stage
        stage.GetRootLayer().Save()
        
        return success_response(
            f"Successfully created {prim_type} at {prim_path}",
            {
                "stage_id": stage_id,
                "file_path": file_path,
                "prim_path": prim_path,
                "prim_type": prim_type,
                "size": size,
                "position": position
            }
        )
    except Exception as e:
        logger.exception(f"Error creating primitive: {str(e)}")
        return error_response(f"Error creating primitive: {str(e)}")

@mcp.tool()
def create_reference_by_id(stage_id: str, prim_path: str, reference_file_path: str, reference_prim_path: str = "") -> str:
    """Add a reference to an external USD file using stage ID
    
    Args:
        stage_id: ID of the stage to modify
        prim_path: Path where to create/add reference
        reference_file_path: Path to the referenced USD file
        reference_prim_path: Optional prim path within the referenced file (defaults to root)
        
    Returns:
        JSON string with success status and message
    """
    try:
        # Validate input
        if not os.path.exists(reference_file_path):
            raise ValueError(f"Referenced file does not exist: {reference_file_path}")
            
        # Get stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            return error_response(f"Stage with ID {stage_id} not found")
        
        # Get file path for response
        file_path = stage_registry.get_stage_path(stage_id)
        
        # Get or create the prim
        prim = stage.GetPrimAtPath(prim_path)
        if not prim:
            # Create the required prim if it doesn't exist
            prim = UsdGeom.Xform.Define(stage, prim_path).GetPrim()
        
        # Add the reference
        prim.GetReferences().AddReference(reference_file_path, reference_prim_path)
        
        # Mark stage as modified
        stage_registry.mark_as_modified(stage_id)
        
        # Save stage
        stage.GetRootLayer().Save()
        
        return success_response(
            f"Successfully added reference to {reference_file_path} at {prim_path}",
            {
                "stage_id": stage_id,
                "file_path": file_path,
                "prim_path": prim_path,
                "reference_path": reference_file_path,
                "reference_prim_path": reference_prim_path or "/"
            }
        )
    except Exception as e:
        logger.exception(f"Error adding reference: {str(e)}")
        return error_response(f"Error adding reference: {str(e)}")

@mcp.tool()
def create_material_by_id(stage_id: str, material_path: str, diffuse_color: tuple = (0.8, 0.8, 0.8), metallic: float = 0.0, roughness: float = 0.4) -> str:
    """Create an OmniPBR material in a USD stage using stage ID
    
    Args:
        stage_id: ID of the stage to modify
        material_path: Path where to create the material
        diffuse_color: RGB tuple for diffuse color (default: light gray)
        metallic: Metallic value between 0.0 and 1.0 (default: 0.0)
        roughness: Roughness value between 0.0 and 1.0 (default: 0.4)
        
    Returns:
        JSON string with success status and message
    """
    try:
        # Validate parameters
        if not (0 <= metallic <= 1):
            raise ValueError(f"Metallic value must be between 0 and 1, got {metallic}")
        if not (0 <= roughness <= 1): 
            raise ValueError(f"Roughness value must be between 0 and 1, got {roughness}")
            
        # Get stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            return error_response(f"Stage with ID {stage_id} not found")
        
        # Get file path for response
        file_path = stage_registry.get_stage_path(stage_id)
        
        # Create material with Sdf.ChangeBlock for better performance
        with Sdf.ChangeBlock():
            # Create material
            from pxr import UsdShade
            material = UsdShade.Material.Define(stage, material_path)
            
            # Create shader
            shader_path = f"{material_path}/Shader"
            shader = UsdShade.Shader.Define(stage, shader_path)
            shader.CreateIdAttr("OmniPBR")
            
            # Set shader inputs
            shader.CreateInput("diffuse_color", Sdf.ValueTypeNames.Color3f).Set(diffuse_color)
            shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(metallic)
            shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(roughness)
            
            # Connect shader to material
            material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
        
        # Mark stage as modified
        stage_registry.mark_as_modified(stage_id)
        
        # Save stage
        stage.GetRootLayer().Save()
        
        return success_response(
            f"Successfully created material at {material_path}",
            {
                "stage_id": stage_id,
                "file_path": file_path,
                "material_path": material_path,
                "properties": {
                    "diffuse_color": diffuse_color,
                    "metallic": metallic,
                    "roughness": roughness
                }
            }
        )
    except Exception as e:
        logger.exception(f"Error creating material: {str(e)}")
        return error_response(f"Error creating material: {str(e)}")

@mcp.tool()
def bind_material_by_id(stage_id: str, prim_path: str, material_path: str) -> str:
    """Bind a material to a prim in the USD stage using stage ID
    
    Args:
        stage_id: ID of the stage to modify
        prim_path: Path to the prim to bind the material to
        material_path: Path to the material to bind
        
    Returns:
        JSON string with success status and message
    """
    try:
        # Get stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            return error_response(f"Stage with ID {stage_id} not found")
        
        # Get file path for response
        file_path = stage_registry.get_stage_path(stage_id)
        
        # Get the prim and material
        prim = stage.GetPrimAtPath(prim_path)
        if not prim:
            return error_response(f"Prim not found: {prim_path}")
            
        material_prim = stage.GetPrimAtPath(material_path)
        if not material_prim:
            return error_response(f"Material not found: {material_path}")
        
        # Bind material to prim
        from pxr import UsdShade
        material = UsdShade.Material(material_prim)
        UsdShade.MaterialBindingAPI(prim).Bind(material)
        
        # Mark stage as modified
        stage_registry.mark_as_modified(stage_id)
        
        # Save stage
        stage.GetRootLayer().Save()
        
        return success_response(
            f"Successfully bound material {material_path} to {prim_path}",
            {
                "stage_id": stage_id,
                "file_path": file_path,
                "prim_path": prim_path,
                "material_path": material_path
            }
        )
    except Exception as e:
        logger.exception(f"Error binding material: {str(e)}")
        return error_response(f"Error binding material: {str(e)}")

@mcp.tool()
def setup_physics_scene_by_id(stage_id: str, gravity: tuple = (0, -9.81, 0)) -> str:
    """Setup a physics scene in a USD stage using stage ID
    
    Args:
        stage_id: ID of the stage
        gravity: XYZ gravity vector (default: Earth gravity)
        
    Returns:
        JSON string with success status and message
    """
    try:
        # Validate input
        if not stage_id:
            raise ValueError("Stage ID cannot be empty")
        
        # Get the stage from registry
        stage_registry = get_stage_registry()
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            return error_response(f"Stage not found with ID: {stage_id}")
        
        # Import physics schemas
        from pxr import PhysxSchema, UsdPhysics
        
        # Create a physics scene if it doesn't already exist
        physics_scene = None
        root_path = "/physics_scene"
        
        # Check if physics scene exists
        if stage.GetPrimAtPath(root_path):
            physics_scene = UsdPhysics.Scene.Get(stage, root_path)
            if not physics_scene:
                return error_response(f"Found prim at {root_path} but it's not a UsdPhysics.Scene")
        
        # Create the physics scene
        if not physics_scene:
            physics_scene = UsdPhysics.Scene.Define(stage, root_path)
        
        # Set gravity
        physics_scene.CreateGravityDirectionAttr().Set(gravity)
        physics_scene.CreateGravityMagnitudeAttr().Set(9.81)  # Default Earth gravity
        
        # Mark the stage as modified
        stage_registry.mark_as_modified(stage_id)
        
        return success_response(
            f"Successfully setup physics scene in stage {stage_id}",
            {
                "scene_path": root_path,
                "gravity": gravity
            }
        )
    except Exception as e:
        logger.exception(f"Error setting up physics scene: {str(e)}")
        return error_response(f"Error setting up physics scene: {str(e)}")

@mcp.tool()
def add_rigid_body_by_id(stage_id: str, prim_path: str, mass: float = 1.0, is_dynamic: bool = True) -> str:
    """Add rigid body physics to a prim in a USD stage using stage ID
    
    Args:
        stage_id: ID of the stage
        prim_path: Path to the prim to add rigid body to
        mass: Mass in kg (default: 1.0)
        is_dynamic: Whether the body is dynamic (true) or kinematic (false)
        
    Returns:
        JSON string with success status and message
    """
    try:
        # Validate input
        if not stage_id:
            raise ValueError("Stage ID cannot be empty")
        
        if not prim_path:
            raise ValueError("Prim path cannot be empty")
        
        if mass <= 0:
            raise ValueError(f"Mass must be positive, got {mass}")
        
        # Get the stage from registry
        stage_registry = get_stage_registry()
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            return error_response(f"Stage not found with ID: {stage_id}")
        
        # Check if prim exists
        prim = stage.GetPrimAtPath(prim_path)
        if not prim:
            return error_response(f"Prim not found: {prim_path}")
        
        # Import physics schemas
        from pxr import PhysxSchema, UsdPhysics
        
        # Add rigid body properties to the prim
        rigid_body = UsdPhysics.RigidBodyAPI.Apply(prim)
        
        # Set rigidBody properties
        rigid_body.CreateRigidBodyEnabledAttr(True)
        
        # Set the kinematic flag (dynamic vs. kinematic)
        rigid_body.CreateKinematicEnabledAttr(not is_dynamic)
        
        # Set mass properties
        mass_api = UsdPhysics.MassAPI.Apply(prim)
        mass_api.CreateMassAttr(mass)
        
        # Ensure a physics scene exists
        if not stage.GetPrimAtPath("/physics_scene"):
            setup_physics_scene_by_id(stage_id)
        
        # Mark the stage as modified
        stage_registry.mark_as_modified(stage_id)
        
        return success_response(
            f"Successfully added {'dynamic' if is_dynamic else 'kinematic'} rigid body to {prim_path}",
            {
                "prim_path": prim_path,
                "mass": mass,
                "is_dynamic": is_dynamic
            }
        )
    except Exception as e:
        logger.exception(f"Error adding rigid body: {str(e)}")
        return error_response(f"Error adding rigid body: {str(e)}")

if __name__ == "__main__":
    args = parse_arguments()
    
    # Set log level from args
    log_level = getattr(logging, args.log_level)
    logger.setLevel(log_level)
    
    logger.info(f"Starting USD MCP Server with {args.protocol} protocol")
    
    try:
        # Start the server based on protocol
        if args.protocol == 'stdio':
            logger.info("Starting with stdio transport")
            mcp.start_stdio()
        elif args.protocol == 'http':
            logger.info(f"Starting HTTP server on {args.host}:{args.port}")
            mcp.start_http(host=args.host, port=args.port)
        elif args.protocol == 'sse':
            logger.info(f"Starting SSE server on {args.host}:{args.port}")
            mcp.start_sse(host=args.host, port=args.port)
        elif args.protocol == 'zmq':
            logger.info(f"Starting ZMQ server on port {args.port}")
            # Implement ZMQ startup here if supported by your MCP framework
            logger.error("ZMQ protocol not yet implemented")
            sys.exit(1)
        else:
            logger.error(f"Unsupported protocol: {args.protocol}")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception(f"Error starting server: {e}")
        sys.exit(1)