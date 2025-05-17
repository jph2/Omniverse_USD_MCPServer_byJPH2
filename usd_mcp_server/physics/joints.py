"""
Physics joints utilities for USD stages.

This module provides functions for setting up various types of joints between rigid bodies.
"""

from pxr import Usd, UsdPhysics, UsdGeom, Sdf
import logging
from typing import Dict, Any, Optional, List, Tuple

from ..core.registry import stage_registry

logger = logging.getLogger(__name__)

def create_joint(stage, joint_path: str, joint_type: str, body0_path: str, body1_path: str, 
                local_pos0: Optional[Tuple[float, float, float]] = None,
                local_pos1: Optional[Tuple[float, float, float]] = None,
                local_rot0: Optional[Tuple[float, float, float, float]] = None,
                local_rot1: Optional[Tuple[float, float, float, float]] = None,
                break_force: Optional[float] = None,
                break_torque: Optional[float] = None) -> bool:
    """Create a joint between two rigid bodies
    
    Args:
        stage: The USD stage
        joint_path: Path where the joint prim will be created
        joint_type: Type of joint ("fixed", "revolute", "prismatic", "spherical", "distance")
        body0_path: Path to the first body
        body1_path: Path to the second body
        local_pos0: Optional local position for the joint on the first body
        local_pos1: Optional local position for the joint on the second body
        local_rot0: Optional local rotation for the joint on the first body
        local_rot1: Optional local rotation for the joint on the second body
        break_force: Optional break force for the joint
        break_torque: Optional break torque for the joint
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Map joint_type to USD schema class
        joint_schema_map = {
            "fixed": UsdPhysics.FixedJoint,
            "revolute": UsdPhysics.RevoluteJoint,
            "prismatic": UsdPhysics.PrismaticJoint,
            "spherical": UsdPhysics.SphericalJoint,
            "distance": UsdPhysics.DistanceJoint
        }
        
        # Get the schema class
        joint_schema = joint_schema_map.get(joint_type.lower())
        if not joint_schema:
            logger.error(f"Unsupported joint type: {joint_type}")
            return False
        
        # Get the two bodies
        body0 = stage.GetPrimAtPath(body0_path)
        body1 = stage.GetPrimAtPath(body1_path)
        
        if not body0.IsValid() or not body1.IsValid():
            logger.error(f"Invalid body paths: {body0_path} or {body1_path}")
            return False
        
        # Create the joint
        joint = joint_schema.Define(stage, joint_path)
        
        # Set the relationship to the bodies
        joint.CreateBody0Rel().SetTargets([body0_path])
        joint.CreateBody1Rel().SetTargets([body1_path])
        
        # Set joint local frames if provided
        if local_pos0:
            joint.CreateLocalPos0Attr().Set(local_pos0)
        
        if local_pos1:
            joint.CreateLocalPos1Attr().Set(local_pos1)
        
        if local_rot0:
            joint.CreateLocalRot0Attr().Set(local_rot0)
        
        if local_rot1:
            joint.CreateLocalRot1Attr().Set(local_rot1)
        
        # Set break parameters if provided
        if break_force is not None:
            joint.CreateBreakForceAttr().Set(break_force)
        
        if break_torque is not None:
            joint.CreateBreakTorqueAttr().Set(break_torque)
        
        # Set specific parameters based on joint type
        if joint_type == "revolute":
            # Default axis is Z
            joint.CreateAxisAttr().Set((0, 0, 1))
        
        elif joint_type == "prismatic":
            # Default axis is X
            joint.CreateAxisAttr().Set((1, 0, 0))
        
        return True
    
    except Exception as e:
        logger.exception(f"Error creating {joint_type} joint: {str(e)}")
        return False

def create_joint_by_id(stage_id: str, joint_path: str, joint_type: str, body0_path: str, body1_path: str,
                     local_pos0: Optional[List[float]] = None, local_pos1: Optional[List[float]] = None,
                     local_rot0: Optional[List[float]] = None, local_rot1: Optional[List[float]] = None,
                     break_force: Optional[float] = None, break_torque: Optional[float] = None) -> str:
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
    try:
        # Get the stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            from ..core.stage_operations import error_response
            return error_response(f"Stage not found: {stage_id}")
        
        # Convert position and rotation to tuples if provided
        pos0_tuple = tuple(local_pos0) if local_pos0 else None
        pos1_tuple = tuple(local_pos1) if local_pos1 else None
        rot0_tuple = tuple(local_rot0) if local_rot0 else None
        rot1_tuple = tuple(local_rot1) if local_rot1 else None
        
        # Create the joint
        success = create_joint(
            stage, joint_path, joint_type, body0_path, body1_path,
            pos0_tuple, pos1_tuple, rot0_tuple, rot1_tuple,
            break_force, break_torque
        )
        
        if success:
            # Mark stage as modified
            stage_registry.mark_as_modified(stage_id)
            
            from ..core.stage_operations import success_response
            return success_response(f"{joint_type.capitalize()} joint created successfully", {
                "stage_id": stage_id,
                "joint_path": joint_path,
                "joint_type": joint_type,
                "body0_path": body0_path,
                "body1_path": body1_path,
                "local_pos0": local_pos0,
                "local_pos1": local_pos1
            })
        else:
            from ..core.stage_operations import error_response
            return error_response(f"Failed to create {joint_type} joint at {joint_path}")
        
    except Exception as e:
        logger.exception(f"Error in create_joint_by_id: {str(e)}")
        from ..core.stage_operations import error_response
        return error_response(f"Error creating joint: {str(e)}")

def configure_joint_by_id(stage_id: str, joint_path: str, 
                         axis: Optional[List[float]] = None,
                         limits: Optional[Dict[str, Any]] = None) -> str:
    """Configure parameters for an existing joint by stage ID
    
    Args:
        stage_id: The ID of the stage
        joint_path: Path to the joint prim
        axis: Optional axis direction as [x, y, z] (for revolute and prismatic joints)
        limits: Optional limits configuration dictionary with keys like "low", "high", "softness", etc.
        
    Returns:
        JSON string with result information
    """
    try:
        # Get the stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            from ..core.stage_operations import error_response
            return error_response(f"Stage not found: {stage_id}")
        
        # Get the joint prim
        joint_prim = stage.GetPrimAtPath(joint_path)
        if not joint_prim.IsValid():
            from ..core.stage_operations import error_response
            return error_response(f"Invalid joint path: {joint_path}")
        
        # Determine the type of joint
        joint_type = None
        if UsdPhysics.RevoluteJoint.Get(stage, joint_path):
            joint_type = "revolute"
            joint = UsdPhysics.RevoluteJoint.Get(stage, joint_path)
        elif UsdPhysics.PrismaticJoint.Get(stage, joint_path):
            joint_type = "prismatic"
            joint = UsdPhysics.PrismaticJoint.Get(stage, joint_path)
        elif UsdPhysics.SphericalJoint.Get(stage, joint_path):
            joint_type = "spherical"
            joint = UsdPhysics.SphericalJoint.Get(stage, joint_path)
        elif UsdPhysics.FixedJoint.Get(stage, joint_path):
            joint_type = "fixed"
            joint = UsdPhysics.FixedJoint.Get(stage, joint_path)
        elif UsdPhysics.DistanceJoint.Get(stage, joint_path):
            joint_type = "distance"
            joint = UsdPhysics.DistanceJoint.Get(stage, joint_path)
        else:
            from ..core.stage_operations import error_response
            return error_response(f"Prim is not a recognized joint type: {joint_path}")
        
        updated = {}
        
        # Set axis for revolute and prismatic joints
        if axis and joint_type in ["revolute", "prismatic"]:
            joint.CreateAxisAttr().Set(tuple(axis))
            updated["axis"] = axis
        
        # Configure limits based on joint type
        if limits:
            if joint_type == "revolute":
                # Angular limits
                if "low" in limits:
                    joint.CreateLowerLimitAttr().Set(limits["low"])
                    updated["lower_limit"] = limits["low"]
                
                if "high" in limits:
                    joint.CreateUpperLimitAttr().Set(limits["high"])
                    updated["upper_limit"] = limits["high"]
            
            elif joint_type == "prismatic":
                # Linear limits
                if "low" in limits:
                    joint.CreateLowerLimitAttr().Set(limits["low"])
                    updated["lower_limit"] = limits["low"]
                
                if "high" in limits:
                    joint.CreateUpperLimitAttr().Set(limits["high"])
                    updated["upper_limit"] = limits["high"]
            
            elif joint_type == "distance":
                # Min/max distance
                if "min" in limits:
                    joint.CreateMinDistanceAttr().Set(limits["min"])
                    updated["min_distance"] = limits["min"]
                
                if "max" in limits:
                    joint.CreateMaxDistanceAttr().Set(limits["max"])
                    updated["max_distance"] = limits["max"]
        
        # Mark stage as modified
        stage_registry.mark_as_modified(stage_id)
        
        from ..core.stage_operations import success_response
        return success_response(f"{joint_type.capitalize()} joint configured successfully", {
            "stage_id": stage_id,
            "joint_path": joint_path,
            "joint_type": joint_type,
            "updated": updated
        })
        
    except Exception as e:
        logger.exception(f"Error in configure_joint_by_id: {str(e)}")
        from ..core.stage_operations import error_response
        return error_response(f"Error configuring joint: {str(e)}") 

def remove_joint_by_id(stage_id: str, joint_path: str) -> str:
    """Remove a joint by stage ID
    
    Args:
        stage_id: The ID of the stage
        joint_path: Path to the joint to remove
        
    Returns:
        JSON string with result information
    """
    try:
        # Get the stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            from ..core.stage_operations import error_response
            return error_response(f"Stage not found: {stage_id}")
        
        # Get the joint prim
        joint_prim = stage.GetPrimAtPath(joint_path)
        if not joint_prim.IsValid():
            from ..core.stage_operations import error_response
            return error_response(f"Invalid joint path: {joint_path}")
        
        # Check if it's a joint
        joint_type = None
        if UsdPhysics.RevoluteJoint.Get(stage, joint_path):
            joint_type = "revolute"
        elif UsdPhysics.PrismaticJoint.Get(stage, joint_path):
            joint_type = "prismatic"
        elif UsdPhysics.SphericalJoint.Get(stage, joint_path):
            joint_type = "spherical"
        elif UsdPhysics.FixedJoint.Get(stage, joint_path):
            joint_type = "fixed"
        elif UsdPhysics.DistanceJoint.Get(stage, joint_path):
            joint_type = "distance"
        else:
            from ..core.stage_operations import error_response
            return error_response(f"Prim is not a recognized joint type: {joint_path}")
        
        # Remove the joint
        joint_prim.SetActive(False)
        
        # Mark stage as modified
        stage_registry.mark_as_modified(stage_id)
        
        from ..core.stage_operations import success_response
        return success_response("Joint removed successfully", {
            "stage_id": stage_id,
            "joint_path": joint_path,
            "joint_type": joint_type
        })
        
    except Exception as e:
        logger.exception(f"Error in remove_joint_by_id: {str(e)}")
        from ..core.stage_operations import error_response
        return error_response(f"Error removing joint: {str(e)}") 