from pxr import Usd, UsdGeom, Sdf
import os
import json
import logging
from typing import Dict, Any, Optional, List
from .registry import stage_registry, stage_cache

logger = logging.getLogger(__name__)

def success_response(message: str, data: Optional[Dict[str, Any]] = None) -> str:
    """Format a successful response as JSON"""
    from datetime import datetime
    response = {
        "ok": True,
        "message": message,
        "data": data or {},
        "timestamp": datetime.now().isoformat()
    }
    return json.dumps(response)

def error_response(message: str, error_code: Optional[str] = None) -> str:
    """Format an error response as JSON"""
    from datetime import datetime
    response = {
        "ok": False,
        "message": message,
        "error_code": error_code or "UNKNOWN_ERROR",
        "data": {},
        "timestamp": datetime.now().isoformat()
    }
    return json.dumps(response)

def create_stage(file_path: str, template: str = "empty", up_axis: str = "Y") -> str:
    """Create a new USD stage with optional template and return its ID
    
    Args:
        file_path: Path to save the new USD file
        template: Template to use ('empty', 'basic', 'physics', etc.)
        up_axis: Up axis for the stage ('Y' or 'Z')
        
    Returns:
        JSON string with stage ID or error description
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # Create a new stage
        stage = Usd.Stage.CreateNew(file_path)
        if not stage:
            return error_response(f"Failed to create stage at {file_path}")
        
        # Set the up axis
        if up_axis.upper() == "Z":
            UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        else:
            UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
        
        # Create stage content based on template
        if not template or template == "empty":
            # Just create an empty root prim
            root_prim = UsdGeom.Xform.Define(stage, "/root")
            stage.SetDefaultPrim(root_prim.GetPrim())
        elif template == "basic":
            # Create basic scene structure
            root_prim = UsdGeom.Xform.Define(stage, "/World")
            stage.SetDefaultPrim(root_prim.GetPrim())
            
            # Add a camera
            camera = UsdGeom.Camera.Define(stage, "/World/Camera")
            camera.CreateFocalLengthAttr(24.0)
            camera.CreateClippingRangeAttr((0.01, 10000.0))
            camera.CreateFocusDistanceAttr(5.0)
            
            # Add a light
            light = UsdGeom.Xform.Define(stage, "/World/Light")
            
            # Add a ground plane
            plane = UsdGeom.Mesh.Define(stage, "/World/GroundPlane")
            plane.CreatePointsAttr([(-50, 0, -50), (50, 0, -50), (50, 0, 50), (-50, 0, 50)])
            plane.CreateFaceVertexCountsAttr([4])
            plane.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
            plane.CreateNormalsAttr([(0, 1, 0), (0, 1, 0), (0, 1, 0), (0, 1, 0)])
            plane.CreateExtentAttr([(-50, 0, -50), (50, 0, 50)])
            
        elif template == "physics":
            # Create physics-ready scene structure
            from ..physics.setup import create_physics_scene
            root_prim = UsdGeom.Xform.Define(stage, "/World")
            stage.SetDefaultPrim(root_prim.GetPrim())
            
            # Initialize physics scene
            create_physics_scene(stage, "/World/PhysicsScene")
            
            # Add a ground plane with collision
            plane = UsdGeom.Mesh.Define(stage, "/World/GroundPlane")
            plane.CreatePointsAttr([(-50, 0, -50), (50, 0, -50), (50, 0, 50), (-50, 0, 50)])
            plane.CreateFaceVertexCountsAttr([4])
            plane.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
            plane.CreateNormalsAttr([(0, 1, 0), (0, 1, 0), (0, 1, 0), (0, 1, 0)])
            plane.CreateExtentAttr([(-50, 0, -50), (50, 0, 50)])
            
            # Add collision to ground plane
            from ..physics.collisions import add_collision
            add_collision(stage, "/World/GroundPlane", collision_type="plane")
            
        else:
            return error_response(f"Unknown template: {template}")
        
        # Save the stage
        stage.GetRootLayer().Save()
        
        # Register the stage with the registry
        stage_id = stage_registry.register_stage(file_path, stage)
        
        return success_response("Stage created successfully", {
            "stage_id": stage_id,
            "file_path": file_path,
            "template": template,
            "up_axis": up_axis
        })
        
    except Exception as e:
        logger.exception(f"Error creating stage: {str(e)}")
        return error_response(f"Error creating stage: {str(e)}")

def open_stage(file_path: str, create_if_missing: bool = False) -> str:
    """Open an existing USD stage or create it if requested
    
    Args:
        file_path: Path to the USD file to open
        create_if_missing: Whether to create the file if it doesn't exist
        
    Returns:
        JSON string with stage ID or error description
    """
    try:
        abs_path = os.path.abspath(file_path)
        
        # Check if stage is already in cache
        if abs_path in stage_cache:
            # Get the stage from cache
            stage = stage_cache[abs_path]
            # Find the stage_id in registry
            for sid, path in stage_registry._stage_file_paths.items():
                if path == abs_path:
                    return success_response("Stage loaded from cache", {
                        "stage_id": sid,
                        "file_path": file_path,
                        "cached": True
                    })
        
        # Check if file exists
        if not os.path.exists(file_path):
            if create_if_missing:
                return create_stage(file_path)
            else:
                return error_response(f"File not found: {file_path}")
        
        # Open the stage
        stage = Usd.Stage.Open(file_path)
        if not stage:
            return error_response(f"Failed to open stage: {file_path}")
        
        # Register the stage with the registry
        stage_id = stage_registry.register_stage(file_path, stage)
        
        # Add to cache
        stage_cache[abs_path] = stage
        
        return success_response("Stage opened successfully", {
            "stage_id": stage_id,
            "file_path": file_path
        })
        
    except Exception as e:
        logger.exception(f"Error opening stage: {str(e)}")
        return error_response(f"Error opening stage: {str(e)}")

def save_stage(stage_id: str) -> str:
    """Save a stage if it has been modified
    
    Args:
        stage_id: The ID of the stage to save
        
    Returns:
        JSON string with success or error description
    """
    try:
        # Get the stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            return error_response(f"Stage not found: {stage_id}")
        
        # Save the stage
        result = stage_registry.save_stage(stage_id)
        
        if result:
            file_path = stage_registry.get_stage_path(stage_id)
            return success_response("Stage saved successfully", {
                "stage_id": stage_id,
                "file_path": file_path
            })
        else:
            return error_response(f"Stage not modified or error saving: {stage_id}")
        
    except Exception as e:
        logger.exception(f"Error saving stage: {str(e)}")
        return error_response(f"Error saving stage: {str(e)}")

def list_prims(stage_id: str, prim_path: str = "/") -> str:
    """List all prims under a given path in the stage
    
    Args:
        stage_id: The ID of the stage to query
        prim_path: The path to start listing prims from
        
    Returns:
        JSON string with list of prims or error description
    """
    try:
        # Get the stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            return error_response(f"Stage not found: {stage_id}")
        
        # Get the starting prim
        start_prim = stage.GetPrimAtPath(prim_path)
        if not start_prim.IsValid():
            return error_response(f"Invalid prim path: {prim_path}")
        
        # List prims
        prims_list = []
        for prim in Usd.PrimRange(start_prim):
            prim_data = {
                "path": str(prim.GetPath()),
                "type": prim.GetTypeName(),
                "children": [str(child.GetPath()).split("/")[-1] for child in prim.GetChildren()],
                "active": prim.IsActive()
            }
            prims_list.append(prim_data)
        
        return success_response("Prims listed successfully", {
            "stage_id": stage_id,
            "start_path": prim_path,
            "prims": prims_list
        })
        
    except Exception as e:
        logger.exception(f"Error listing prims: {str(e)}")
        return error_response(f"Error listing prims: {str(e)}")

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

def define_prim(stage_id: str, prim_path: str, prim_type: str = "Xform") -> str:
    """Define a new prim on the stage
    
    Args:
        stage_id: The ID of the stage to modify
        prim_path: The path where the new prim should be created
        prim_type: The type of prim to create (Xform, Mesh, Sphere, etc.)
        
    Returns:
        JSON string with success or error description
    """
    try:
        # Get the stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            return error_response(f"Stage not found: {stage_id}")
        
        # Map prim_type to appropriate schema class
        schema_map = {
            "Xform": UsdGeom.Xform,
            "Mesh": UsdGeom.Mesh,
            "Sphere": UsdGeom.Sphere,
            "Cube": UsdGeom.Cube,
            "Cylinder": UsdGeom.Cylinder,
            "Cone": UsdGeom.Cone,
            "Capsule": UsdGeom.Capsule,
            "Points": UsdGeom.Points,
            "Camera": UsdGeom.Camera,
            # Add more schema mappings as needed
        }
        
        # Get the schema class
        schema_class = schema_map.get(prim_type)
        if not schema_class:
            return error_response(f"Unsupported prim type: {prim_type}")
        
        # Make sure parent path exists
        parent_path = os.path.dirname(prim_path)
        if parent_path != "/":
            parent_prim = stage.GetPrimAtPath(parent_path)
            if not parent_prim.IsValid():
                # Create parent path if it doesn't exist
                UsdGeom.Xform.Define(stage, parent_path)
        
        # Define the prim
        schema_class.Define(stage, prim_path)
        
        # Mark stage as modified
        stage_registry.mark_as_modified(stage_id)
        
        return success_response(f"{prim_type} prim defined successfully", {
            "stage_id": stage_id,
            "prim_path": prim_path,
            "prim_type": prim_type
        })
        
    except Exception as e:
        logger.exception(f"Error defining prim: {str(e)}")
        return error_response(f"Error defining prim: {str(e)}")

def create_reference(stage_id: str, prim_path: str, reference_file_path: str, reference_prim_path: str = "") -> str:
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
        # Get the stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            return error_response(f"Stage not found: {stage_id}")
        
        # Get the prim
        prim = stage.GetPrimAtPath(prim_path)
        if not prim.IsValid():
            # Create the prim if it doesn't exist
            UsdGeom.Xform.Define(stage, prim_path)
            prim = stage.GetPrimAtPath(prim_path)
        
        # Add the reference
        references = prim.GetReferences()
        
        if reference_prim_path:
            references.AddReference(reference_file_path, reference_prim_path)
        else:
            references.AddReference(reference_file_path)
        
        # Mark stage as modified
        stage_registry.mark_as_modified(stage_id)
        
        return success_response("Reference added successfully", {
            "stage_id": stage_id,
            "prim_path": prim_path,
            "reference_file": reference_file_path,
            "reference_prim_path": reference_prim_path
        })
        
    except Exception as e:
        logger.exception(f"Error creating reference: {str(e)}")
        return error_response(f"Error creating reference: {str(e)}")

def create_mesh(stage_id: str, prim_path: str, points: List[List[float]], 
               face_vertex_counts: List[int], face_vertex_indices: List[int]) -> str:
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
        # Get the stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            return error_response(f"Stage not found: {stage_id}")
        
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
        
        return success_response("Mesh created successfully", {
            "stage_id": stage_id,
            "prim_path": prim_path,
            "num_points": len(points),
            "num_faces": len(face_vertex_counts)
        })
        
    except Exception as e:
        logger.exception(f"Error creating mesh: {str(e)}")
        return error_response(f"Error creating mesh: {str(e)}") 