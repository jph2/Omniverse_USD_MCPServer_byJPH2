"""
Main entry point for the USD MCP server.

This module initializes the MCP server and registers core USD operations.
"""

import os
import sys
import argparse
import json
import logging
import threading
import time
import uuid
from datetime import datetime

import mcp
from pxr import Usd, UsdGeom, Sdf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Global server start time for uptime tracking
server_start_time = time.time()

# Global stage registry (thread-safe with lock)
stage_registry = {}  # Map of stage_id → Usd.Stage
stage_file_paths = {}  # Map of stage_id → file_path
stage_modified = {}  # Map of stage_id → is_modified
registry_lock = threading.Lock()

# Standard response formatting
def success_response(message: str, data=None):
    """Format a successful response as JSON"""
    response = {
        "ok": True,
        "message": message,
        "data": data or {},
        "timestamp": datetime.now().isoformat()
    }
    return json.dumps(response)

def error_response(message: str, error_code=None):
    """Format an error response as JSON"""
    response = {
        "ok": False,
        "message": message,
        "error_code": error_code or "UNKNOWN_ERROR",
        "data": {},
        "timestamp": datetime.now().isoformat()
    }
    return json.dumps(response)

# Register core tools
@mcp.tool()
def create_new_stage(file_path: str, template: str = "empty", up_axis: str = "Y") -> str:
    """Create a new USD stage with optional template
    
    Args:
        file_path: Path to save the new USD file
        template: Template to use ('empty', 'basic')
        up_axis: Up axis for the stage ('Y' or 'Z')
        
    Returns:
        JSON string with stage ID or error description
    """
    try:
        # Create new stage
        stage = Usd.Stage.CreateNew(file_path)
        if not stage:
            return error_response(f"Failed to create stage: {file_path}")
        
        # Set up axis
        if up_axis.upper() in ["Y", "Z"]:
            UsdGeom.SetStageUpAxis(stage, up_axis.upper())
        else:
            return error_response(f"Invalid up axis: {up_axis}. Must be 'Y' or 'Z'")
        
        # Apply template
        if template == "basic":
            # Create a simple scene with basic elements
            UsdGeom.Xform.Define(stage, "/World")
            UsdGeom.Xform.Define(stage, "/World/Lights")
            light = UsdGeom.Xform.Define(stage, "/World/Lights/MainLight")
            
            # Add a ground plane
            ground = UsdGeom.Xform.Define(stage, "/World/Ground")
            ground_mesh = UsdGeom.Mesh.Define(stage, "/World/Ground/Mesh")
            
            # Set default time codes
            stage.SetStartTimeCode(1)
            stage.SetEndTimeCode(100)
        
        # Save the stage
        stage.GetRootLayer().Save()
        
        # Register the stage
        with registry_lock:
            stage_id = str(uuid.uuid4())
            stage_registry[stage_id] = stage
            stage_file_paths[stage_id] = file_path
            stage_modified[stage_id] = False
        
        return success_response("Stage created successfully", {
            "stage_id": stage_id,
            "file_path": file_path,
            "up_axis": up_axis,
            "template": template
        })
        
    except Exception as e:
        logger.exception(f"Error creating stage: {str(e)}")
        return error_response(f"Error creating stage: {str(e)}")

@mcp.tool()
def open_usd_stage(file_path: str, create_if_missing: bool = False) -> str:
    """Open an existing USD stage or create it if requested
    
    Args:
        file_path: Path to the USD file to open
        create_if_missing: Whether to create the file if it doesn't exist
        
    Returns:
        JSON string with stage ID or error description
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            if create_if_missing:
                return create_new_stage(file_path)
            else:
                return error_response(f"File not found: {file_path}")
        
        # Open the stage
        stage = Usd.Stage.Open(file_path)
        if not stage:
            return error_response(f"Failed to open stage: {file_path}")
        
        # Register the stage
        with registry_lock:
            stage_id = str(uuid.uuid4())
            stage_registry[stage_id] = stage
            stage_file_paths[stage_id] = file_path
            stage_modified[stage_id] = False
        
        return success_response("Stage opened successfully", {
            "stage_id": stage_id,
            "file_path": file_path
        })
        
    except Exception as e:
        logger.exception(f"Error opening stage: {str(e)}")
        return error_response(f"Error opening stage: {str(e)}")

@mcp.tool()
def save_usd_stage(stage_id: str) -> str:
    """Save a stage if it has been modified
    
    Args:
        stage_id: The ID of the stage to save
        
    Returns:
        JSON string with success or error description
    """
    try:
        # Get the stage
        with registry_lock:
            if stage_id not in stage_registry:
                return error_response(f"Stage not found: {stage_id}")
            
            stage = stage_registry[stage_id]
            is_modified = stage_modified.get(stage_id, False)
        
        # Save the stage if modified
        if is_modified:
            stage.GetRootLayer().Save()
            
            with registry_lock:
                stage_modified[stage_id] = False
            
            return success_response("Stage saved successfully", {
                "stage_id": stage_id,
                "file_path": stage_file_paths.get(stage_id)
            })
        else:
            return success_response("Stage not modified, no save required", {
                "stage_id": stage_id,
                "file_path": stage_file_paths.get(stage_id)
            })
        
    except Exception as e:
        logger.exception(f"Error saving stage: {str(e)}")
        return error_response(f"Error saving stage: {str(e)}")

@mcp.tool()
def close_stage(stage_id: str, save_if_modified: bool = True) -> str:
    """Close and unload a stage, freeing resources
    
    Args:
        stage_id: The ID of the stage to close
        save_if_modified: Whether to save the stage if it has been modified
        
    Returns:
        JSON string with success or error description
    """
    try:
        with registry_lock:
            if stage_id not in stage_registry:
                return error_response(f"Stage not found: {stage_id}")
            
            stage = stage_registry[stage_id]
            is_modified = stage_modified.get(stage_id, False)
            file_path = stage_file_paths.get(stage_id)
        
        # Save if modified and requested
        if save_if_modified and is_modified:
            try:
                stage.GetRootLayer().Save()
            except Exception as e:
                logger.warning(f"Error saving stage during close: {str(e)}")
        
        # Unload stage
        stage.Unload()
        
        # Remove from registry
        with registry_lock:
            del stage_registry[stage_id]
            if stage_id in stage_file_paths:
                del stage_file_paths[stage_id]
            if stage_id in stage_modified:
                del stage_modified[stage_id]
        
        return success_response("Stage closed successfully", {
            "stage_id": stage_id,
            "file_path": file_path
        })
        
    except Exception as e:
        logger.exception(f"Error closing stage: {str(e)}")
        return error_response(f"Error closing stage: {str(e)}")

@mcp.tool()
def list_stage_prims(stage_id: str, prim_path: str = "/") -> str:
    """List all prims under a given path in the stage
    
    Args:
        stage_id: The ID of the stage to query
        prim_path: The path to start listing prims from
        
    Returns:
        JSON string with list of prims or error description
    """
    try:
        # Get the stage
        with registry_lock:
            if stage_id not in stage_registry:
                return error_response(f"Stage not found: {stage_id}")
            
            stage = stage_registry[stage_id]
        
        # Get the root prim
        root_prim = stage.GetPrimAtPath(prim_path)
        if not root_prim.IsValid():
            return error_response(f"Invalid prim path: {prim_path}")
        
        # Get all prims under the root
        prims = []
        for prim in Usd.PrimRange(root_prim):
            prim_data = {
                "path": str(prim.GetPath()),
                "type": str(prim.GetTypeName()),
                "active": prim.IsActive(),
                "defined": prim.IsDefined(),
                "has_children": len(list(prim.GetChildren())) > 0
            }
            prims.append(prim_data)
        
        return success_response("Prims retrieved successfully", {
            "stage_id": stage_id,
            "root_path": prim_path,
            "prims": prims
        })
        
    except Exception as e:
        logger.exception(f"Error listing prims: {str(e)}")
        return error_response(f"Error listing prims: {str(e)}")

@mcp.tool()
def analyze_usd_stage(file_path: str) -> str:
    """Analyze a USD stage and return information about its contents
    
    Args:
        file_path: Path to the USD file to analyze
        
    Returns:
        JSON string containing stage information or error description
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return error_response(f"File not found: {file_path}")
        
        # Open the stage
        stage = Usd.Stage.Open(file_path)
        if not stage:
            return error_response(f"Failed to open stage: {file_path}")
        
        # Get stage metadata
        root_layer = stage.GetRootLayer()
        up_axis = UsdGeom.GetStageUpAxis(stage)
        
        # Count prims by type
        prim_counts = {}
        total_prims = 0
        max_depth = 0
        
        for prim in Usd.PrimRange(stage.GetPseudoRoot()):
            # Skip pseudo root
            if prim.GetPath() == Sdf.Path.absoluteRootPath:
                continue
                
            # Count by type
            prim_type = str(prim.GetTypeName()) or "undefined"
            prim_counts[prim_type] = prim_counts.get(prim_type, 0) + 1
            total_prims += 1
            
            # Track max depth
            depth = len(str(prim.GetPath()).split('/')) - 1
            max_depth = max(max_depth, depth)
        
        # Get time codes
        start_time = stage.GetStartTimeCode()
        end_time = stage.GetEndTimeCode()
        
        # Get layers
        layer_info = []
        for layer in stage.GetLayerStack():
            layer_info.append({
                "identifier": layer.identifier,
                "path": layer.realPath,
                "anonymous": layer.anonymous
            })
        
        # Collect analysis
        analysis = {
            "file_path": file_path,
            "file_size_bytes": os.path.getsize(file_path),
            "up_axis": str(up_axis),
            "total_prims": total_prims,
            "max_depth": max_depth,
            "prim_types": prim_counts,
            "time_range": {
                "start": start_time,
                "end": end_time,
                "has_animation": start_time != end_time and stage.HasAuthoredTimeCodeRange()
            },
            "layers": layer_info
        }
        
        return success_response("Stage analyzed successfully", analysis)
        
    except Exception as e:
        logger.exception(f"Error analyzing stage: {str(e)}")
        return error_response(f"Error analyzing stage: {str(e)}")

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
    try:
        # Get the stage
        with registry_lock:
            if stage_id not in stage_registry:
                return error_response(f"Stage not found: {stage_id}")
            
            stage = stage_registry[stage_id]
        
        # Create the prim based on type
        prim = None
        
        if prim_type == "Xform":
            prim = UsdGeom.Xform.Define(stage, prim_path).GetPrim()
        elif prim_type == "Sphere":
            prim = UsdGeom.Sphere.Define(stage, prim_path).GetPrim()
        elif prim_type == "Cube":
            prim = UsdGeom.Cube.Define(stage, prim_path).GetPrim()
        elif prim_type == "Cylinder":
            prim = UsdGeom.Cylinder.Define(stage, prim_path).GetPrim()
        elif prim_type == "Cone":
            prim = UsdGeom.Cone.Define(stage, prim_path).GetPrim()
        elif prim_type == "Capsule":
            prim = UsdGeom.Capsule.Define(stage, prim_path).GetPrim()
        elif prim_type == "Mesh":
            prim = UsdGeom.Mesh.Define(stage, prim_path).GetPrim()
        elif prim_type == "Points":
            prim = UsdGeom.Points.Define(stage, prim_path).GetPrim()
        elif prim_type == "Camera":
            prim = UsdGeom.Camera.Define(stage, prim_path).GetPrim()
        else:
            # Generic prim definition
            prim = stage.DefinePrim(prim_path, prim_type)
        
        if not prim or not prim.IsValid():
            return error_response(f"Failed to create prim: {prim_path} of type {prim_type}")
        
        # Mark stage as modified
        with registry_lock:
            stage_modified[stage_id] = True
        
        return success_response("Prim created successfully", {
            "stage_id": stage_id,
            "prim_path": prim_path,
            "prim_type": prim_type
        })
        
    except Exception as e:
        logger.exception(f"Error defining prim: {str(e)}")
        return error_response(f"Error defining prim: {str(e)}")

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
    try:
        # Get the stage
        with registry_lock:
            if stage_id not in stage_registry:
                return error_response(f"Stage not found: {stage_id}")
            
            stage = stage_registry[stage_id]
        
        # Check if the reference file exists
        if not os.path.exists(reference_file_path):
            return error_response(f"Reference file not found: {reference_file_path}")
        
        # Get or create the prim
        prim = stage.GetPrimAtPath(prim_path)
        if not prim.IsValid():
            prim = stage.DefinePrim(prim_path)
            if not prim.IsValid():
                return error_response(f"Failed to create prim: {prim_path}")
        
        # Add the reference
        references = prim.GetReferences()
        if reference_prim_path:
            references.AddReference(reference_file_path, reference_prim_path)
        else:
            references.AddReference(reference_file_path)
        
        # Mark stage as modified
        with registry_lock:
            stage_modified[stage_id] = True
        
        return success_response("Reference added successfully", {
            "stage_id": stage_id,
            "prim_path": prim_path,
            "reference_file_path": reference_file_path,
            "reference_prim_path": reference_prim_path
        })
        
    except Exception as e:
        logger.exception(f"Error creating reference: {str(e)}")
        return error_response(f"Error creating reference: {str(e)}")

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
    try:
        # Get the stage
        with registry_lock:
            if stage_id not in stage_registry:
                return error_response(f"Stage not found: {stage_id}")
            
            stage = stage_registry[stage_id]
        
        # Create the mesh
        mesh = UsdGeom.Mesh.Define(stage, prim_path)
        
        # Set points
        mesh.CreatePointsAttr().Set(points)
        
        # Set face vertex counts
        mesh.CreateFaceVertexCountsAttr().Set(face_vertex_counts)
        
        # Set face vertex indices
        mesh.CreateFaceVertexIndicesAttr().Set(face_vertex_indices)
        
        # Mark stage as modified
        with registry_lock:
            stage_modified[stage_id] = True
        
        return success_response("Mesh created successfully", {
            "stage_id": stage_id,
            "prim_path": prim_path,
            "points_count": len(points),
            "faces_count": len(face_vertex_counts)
        })
        
    except Exception as e:
        logger.exception(f"Error creating mesh: {str(e)}")
        return error_response(f"Error creating mesh: {str(e)}")

@mcp.tool()
def get_health() -> str:
    """Get server health information
    
    Returns:
        JSON string with health metrics
    """
    try:
        # Calculate uptime
        uptime_seconds = int(time.time() - server_start_time)
        
        # Get stage count
        with registry_lock:
            total_stages = len(stage_registry)
            stage_ids = list(stage_registry.keys())
        
        # Basic health data
        health_data = {
            "status": "healthy",
            "uptime_seconds": uptime_seconds,
            "stages": {
                "total": total_stages,
                "ids": stage_ids
            },
            "version": "0.1.0"
        }
        
        return success_response("Server is healthy", health_data)
    except Exception as e:
        logger.exception(f"Error getting health information: {str(e)}")
        return error_response(f"Error getting health information: {str(e)}")

@mcp.tool()
def get_available_tools() -> str:
    """Get information about all available tools
    
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

def parse_args():
    """Parse command line arguments for the server"""
    parser = argparse.ArgumentParser(description='USD MCP Server')
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