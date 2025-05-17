"""
Physics rigid body utilities for USD stages.

This module provides functions for setting up rigid bodies for physics simulations.
"""

from pxr import Usd, UsdPhysics, UsdGeom, Sdf
import logging
from typing import Dict, Any, Optional, List, Tuple

from ..core.registry import stage_registry

logger = logging.getLogger(__name__)

def add_rigid_body(stage, prim_path: str, mass: float = 1.0, dynamic: bool = True, 
                  initial_velocity: Optional[Tuple[float, float, float]] = None) -> bool:
    """Add rigid body behavior to an existing prim
    
    Args:
        stage: The USD stage
        prim_path: Path to the prim to make a rigid body
        mass: Mass of the rigid body in kg
        dynamic: Whether the body is dynamic (affected by physics) or static
        initial_velocity: Optional initial linear velocity for the rigid body
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get the prim
        prim = stage.GetPrimAtPath(prim_path)
        if not prim.IsValid():
            logger.error(f"Invalid prim path: {prim_path}")
            return False
        
        # Apply rigid body API
        rigid_body = UsdPhysics.RigidBodyAPI.Apply(prim)
        
        # Set rigid body properties
        rigid_body.CreateMassAttr().Set(mass)
        
        # Create velocity if provided
        if initial_velocity:
            rigid_body.CreateVelocityAttr().Set(initial_velocity)
        
        # Set rigid body type
        if dynamic:
            rigid_body.CreateRigidBodyEnabledAttr().Set(True)
        else:
            # Static objects are kinematic and don't respond to physics
            kinematic = UsdPhysics.RigidBodyAPI.Get(prim)
            kinematic.CreateKinematicEnabledAttr().Set(True)
            kinematic.CreateRigidBodyEnabledAttr().Set(False)
        
        # Make sure it has a collision API
        if not UsdPhysics.CollisionAPI.HasAPI(prim):
            UsdPhysics.CollisionAPI.Apply(prim)
        
        return True
    
    except Exception as e:
        logger.exception(f"Error adding rigid body: {str(e)}")
        return False

def add_rigid_body_by_id(stage_id: str, prim_path: str, mass: float = 1.0, dynamic: bool = True,
                         initial_velocity: Optional[List[float]] = None) -> str:
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
    try:
        # Get the stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            from ..core.stage_operations import error_response
            return error_response(f"Stage not found: {stage_id}")
        
        # Convert velocity to tuple if provided
        velocity_tuple = tuple(initial_velocity) if initial_velocity else None
        
        # Add the rigid body
        success = add_rigid_body(stage, prim_path, mass, dynamic, velocity_tuple)
        
        if success:
            # Mark stage as modified
            stage_registry.mark_as_modified(stage_id)
            
            from ..core.stage_operations import success_response
            return success_response("Rigid body added successfully", {
                "stage_id": stage_id,
                "prim_path": prim_path,
                "mass": mass,
                "dynamic": dynamic,
                "initial_velocity": initial_velocity
            })
        else:
            from ..core.stage_operations import error_response
            return error_response(f"Failed to add rigid body to {prim_path}")
        
    except Exception as e:
        logger.exception(f"Error in add_rigid_body_by_id: {str(e)}")
        from ..core.stage_operations import error_response
        return error_response(f"Error adding rigid body: {str(e)}")

def update_rigid_body_by_id(stage_id: str, prim_path: str, mass: Optional[float] = None,
                           dynamic: Optional[bool] = None, velocity: Optional[List[float]] = None) -> str:
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
        
        # Check for rigid body API
        rigid_body = UsdPhysics.RigidBodyAPI.Get(prim)
        if not rigid_body:
            from ..core.stage_operations import error_response
            return error_response(f"Prim is not a rigid body: {prim_path}")
        
        # Update properties if provided
        updated = {}
        
        if mass is not None:
            rigid_body.CreateMassAttr().Set(mass)
            updated["mass"] = mass
        
        if dynamic is not None:
            if dynamic:
                rigid_body.CreateRigidBodyEnabledAttr().Set(True)
                rigid_body.CreateKinematicEnabledAttr().Set(False)
            else:
                rigid_body.CreateRigidBodyEnabledAttr().Set(False)
                rigid_body.CreateKinematicEnabledAttr().Set(True)
            updated["dynamic"] = dynamic
        
        if velocity is not None:
            rigid_body.CreateVelocityAttr().Set(tuple(velocity))
            updated["velocity"] = velocity
        
        # Mark stage as modified
        stage_registry.mark_as_modified(stage_id)
        
        from ..core.stage_operations import success_response
        return success_response("Rigid body updated successfully", {
            "stage_id": stage_id,
            "prim_path": prim_path,
            "updated": updated
        })
        
    except Exception as e:
        logger.exception(f"Error in update_rigid_body_by_id: {str(e)}")
        from ..core.stage_operations import error_response
        return error_response(f"Error updating rigid body: {str(e)}")

def remove_rigid_body_by_id(stage_id: str, prim_path: str) -> str:
    """Remove rigid body behavior from a prim by stage ID
    
    Args:
        stage_id: The ID of the stage
        prim_path: Path to the prim to remove rigid body from
        
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
        
        # Check for rigid body API
        has_rigid_body = UsdPhysics.RigidBodyAPI.HasAPI(prim)
        
        # Remove the rigid body API
        if has_rigid_body:
            UsdPhysics.RigidBodyAPI.RemoveAPI(prim)
        
        # Mark stage as modified
        stage_registry.mark_as_modified(stage_id)
        
        from ..core.stage_operations import success_response
        return success_response("Rigid body removed successfully", {
            "stage_id": stage_id,
            "prim_path": prim_path,
            "had_rigid_body": has_rigid_body
        })
        
    except Exception as e:
        logger.exception(f"Error in remove_rigid_body_by_id: {str(e)}")
        from ..core.stage_operations import error_response
        return error_response(f"Error removing rigid body: {str(e)}") 