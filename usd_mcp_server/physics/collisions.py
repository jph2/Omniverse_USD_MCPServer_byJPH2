"""
Physics collision utilities for USD stages.

This module provides functions for setting up collision shapes and meshes.
"""

from pxr import Usd, UsdPhysics, UsdGeom, Sdf
import logging
from typing import Dict, Any, Optional, List, Tuple

from ..core.registry import stage_registry

logger = logging.getLogger(__name__)

def add_collision(stage, prim_path: str, collision_type: str = "mesh", 
                 approximation: str = "convexHull", dimensions: Optional[Tuple[float, float, float]] = None) -> bool:
    """Add a collision shape to an existing prim
    
    Args:
        stage: The USD stage
        prim_path: Path to the prim to add collision to
        collision_type: Type of collision shape ("mesh", "box", "sphere", "capsule", "plane")
        approximation: Collision approximation method ("convexHull", "meshSimplification", "none")
        dimensions: Optional dimensions for primitive shapes
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get the prim
        prim = stage.GetPrimAtPath(prim_path)
        if not prim.IsValid():
            logger.error(f"Invalid prim path: {prim_path}")
            return False
        
        # Create a collision API
        collision_api = UsdPhysics.CollisionAPI.Apply(prim)
        
        # Handle different collision types
        if collision_type == "mesh":
            # For meshes, we need to set up mesh collision
            mesh_api = UsdPhysics.MeshCollisionAPI.Apply(prim)
            
            # Set approximation
            if approximation == "convexHull":
                mesh_api.CreateApproximationAttr().Set(UsdPhysics.Tokens.convexHull)
            elif approximation == "meshSimplification":
                mesh_api.CreateApproximationAttr().Set(UsdPhysics.Tokens.meshSimplification)
            else:
                mesh_api.CreateApproximationAttr().Set(UsdPhysics.Tokens.none)
        
        elif collision_type == "box":
            # Create a box collision
            if not dimensions:
                dimensions = (1.0, 1.0, 1.0)
            
            # If it's not already a cube, create a cube collision shape
            if not prim.IsA(UsdGeom.Cube):
                # Create a collision shape underneath
                collision_path = f"{prim_path}/Collision"
                box = UsdGeom.Cube.Define(stage, collision_path)
                box.CreateSizeAttr().Set(dimensions[0])  # Size for cube
                
                # Apply collision API to the box
                UsdPhysics.CollisionAPI.Apply(box.GetPrim())
        
        elif collision_type == "sphere":
            # Create a sphere collision
            radius = dimensions[0] if dimensions else 1.0
            
            # If it's not already a sphere, create a sphere collision shape
            if not prim.IsA(UsdGeom.Sphere):
                # Create a collision shape underneath
                collision_path = f"{prim_path}/Collision"
                sphere = UsdGeom.Sphere.Define(stage, collision_path)
                sphere.CreateRadiusAttr().Set(radius)
                
                # Apply collision API to the sphere
                UsdPhysics.CollisionAPI.Apply(sphere.GetPrim())
        
        elif collision_type == "capsule":
            # Create a capsule collision
            radius = dimensions[0] if dimensions else 0.5
            height = dimensions[1] if dimensions and len(dimensions) > 1 else 2.0
            
            # If it's not already a capsule, create a capsule collision shape
            if not prim.IsA(UsdGeom.Capsule):
                # Create a collision shape underneath
                collision_path = f"{prim_path}/Collision"
                capsule = UsdGeom.Capsule.Define(stage, collision_path)
                capsule.CreateRadiusAttr().Set(radius)
                capsule.CreateHeightAttr().Set(height)
                
                # Apply collision API to the capsule
                UsdPhysics.CollisionAPI.Apply(capsule.GetPrim())
        
        elif collision_type == "plane":
            # Just add collision API for planes
            # This handles infinite ground planes
            pass
        
        else:
            logger.error(f"Unsupported collision type: {collision_type}")
            return False
        
        return True
    
    except Exception as e:
        logger.exception(f"Error adding collision: {str(e)}")
        return False

def add_collision_by_id(stage_id: str, prim_path: str, collision_type: str = "mesh",
                     approximation: str = "convexHull", dimensions: Optional[List[float]] = None) -> str:
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
    try:
        # Get the stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            from ..core.stage_operations import error_response
            return error_response(f"Stage not found: {stage_id}")
        
        # Convert dimensions to tuple if provided
        dims_tuple = tuple(dimensions) if dimensions else None
        
        # Add the collision
        success = add_collision(stage, prim_path, collision_type, approximation, dims_tuple)
        
        if success:
            # Mark stage as modified
            stage_registry.mark_as_modified(stage_id)
            
            from ..core.stage_operations import success_response
            return success_response("Collision added successfully", {
                "stage_id": stage_id,
                "prim_path": prim_path,
                "collision_type": collision_type,
                "approximation": approximation,
                "dimensions": dimensions
            })
        else:
            from ..core.stage_operations import error_response
            return error_response(f"Failed to add collision to {prim_path}")
        
    except Exception as e:
        logger.exception(f"Error in add_collision_by_id: {str(e)}")
        from ..core.stage_operations import error_response
        return error_response(f"Error adding collision: {str(e)}")

def remove_collision_by_id(stage_id: str, prim_path: str) -> str:
    """Remove collision from a prim by stage ID
    
    Args:
        stage_id: The ID of the stage
        prim_path: Path to the prim to remove collision from
        
    Returns:
        JSON string with result information
    """
    try:
        # Get the stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            from ..core.stage_operations import error_response
            return error_response(f"Stage not found: {stage_id}")
        
        # Get the prim
        prim = stage.GetPrimAtPath(prim_path)
        if not prim.IsValid():
            from ..core.stage_operations import error_response
            return error_response(f"Invalid prim path: {prim_path}")
        
        # Check for collision API
        has_collision = UsdPhysics.CollisionAPI.HasAPI(prim)
        has_mesh_collision = UsdPhysics.MeshCollisionAPI.HasAPI(prim)
        
        # Remove the collision APIs
        if has_collision:
            UsdPhysics.CollisionAPI.RemoveAPI(prim)
        
        if has_mesh_collision:
            UsdPhysics.MeshCollisionAPI.RemoveAPI(prim)
        
        # Check for collision child
        collision_path = f"{prim_path}/Collision"
        collision_prim = stage.GetPrimAtPath(collision_path)
        if collision_prim.IsValid():
            # Remove the collision child
            collision_prim.SetActive(False)
        
        # Mark stage as modified
        stage_registry.mark_as_modified(stage_id)
        
        from ..core.stage_operations import success_response
        return success_response("Collision removed successfully", {
            "stage_id": stage_id,
            "prim_path": prim_path,
            "had_collision": has_collision or has_mesh_collision or collision_prim.IsValid()
        })
        
    except Exception as e:
        logger.exception(f"Error in remove_collision_by_id: {str(e)}")
        from ..core.stage_operations import error_response
        return error_response(f"Error removing collision: {str(e)}") 