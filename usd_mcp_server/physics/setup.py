"""
Physics scene setup utilities for USD stages.

This module provides functions for setting up physics scenes and simulations.
"""

from pxr import Usd, UsdPhysics, PhysicsSchemaTools, Sdf
import logging
from typing import Dict, Any, Optional

from ..core.registry import stage_registry

logger = logging.getLogger(__name__)

def create_physics_scene(stage, scene_path: str) -> bool:
    """Create a physics scene at the specified path
    
    Args:
        stage: The USD stage
        scene_path: Path where the physics scene will be created
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create a physics scene
        physics_scene = UsdPhysics.Scene.Define(stage, scene_path)
        
        # Set standard physics properties
        physics_scene.CreateGravityDirectionAttr().Set((0.0, -1.0, 0.0))
        physics_scene.CreateGravityMagnitudeAttr().Set(9.81)
        physics_scene.CreateTimeScaleAttr().Set(1.0)
        
        return True
    except Exception as e:
        logger.exception(f"Error creating physics scene: {str(e)}")
        return False

def setup_physics_scene_by_id(stage_id: str, scene_path: str) -> str:
    """Create a physics scene on a stage identified by ID
    
    Args:
        stage_id: The ID of the stage
        scene_path: Path where the physics scene will be created
        
    Returns:
        JSON string with result information
    """
    try:
        # Get the stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            from ..core.stage_operations import error_response
            return error_response(f"Stage not found: {stage_id}")
        
        # Create the physics scene
        success = create_physics_scene(stage, scene_path)
        
        if success:
            # Mark stage as modified
            stage_registry.mark_as_modified(stage_id)
            
            from ..core.stage_operations import success_response
            return success_response("Physics scene created successfully", {
                "stage_id": stage_id,
                "scene_path": scene_path
            })
        else:
            from ..core.stage_operations import error_response
            return error_response(f"Failed to create physics scene at {scene_path}")
        
    except Exception as e:
        logger.exception(f"Error in setup_physics_scene_by_id: {str(e)}")
        from ..core.stage_operations import error_response
        return error_response(f"Error setting up physics scene: {str(e)}")

def configure_physics_scene(stage_id: str, scene_path: str, gravity: Optional[Dict[str, float]] = None,
                          time_scale: Optional[float] = None) -> str:
    """Configure a physics scene's properties
    
    Args:
        stage_id: The ID of the stage
        scene_path: Path to the physics scene
        gravity: Optional dictionary with 'direction' (list of 3 floats) and 'magnitude' (float)
        time_scale: Optional time scale factor
        
    Returns:
        JSON string with result information
    """
    try:
        # Get the stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            from ..core.stage_operations import error_response
            return error_response(f"Stage not found: {stage_id}")
        
        # Get the physics scene
        physics_scene = UsdPhysics.Scene.Get(stage, scene_path)
        if not physics_scene:
            # Try to create it if it doesn't exist
            physics_scene = UsdPhysics.Scene.Define(stage, scene_path)
        
        # Update the physics scene properties
        if gravity:
            if 'direction' in gravity:
                physics_scene.CreateGravityDirectionAttr().Set(gravity['direction'])
            if 'magnitude' in gravity:
                physics_scene.CreateGravityMagnitudeAttr().Set(gravity['magnitude'])
        
        if time_scale is not None:
            physics_scene.CreateTimeScaleAttr().Set(time_scale)
        
        # Mark stage as modified
        stage_registry.mark_as_modified(stage_id)
        
        from ..core.stage_operations import success_response
        return success_response("Physics scene configured successfully", {
            "stage_id": stage_id,
            "scene_path": scene_path,
            "updated_properties": {
                "gravity": gravity,
                "time_scale": time_scale
            }
        })
        
    except Exception as e:
        logger.exception(f"Error in configure_physics_scene: {str(e)}")
        from ..core.stage_operations import error_response
        return error_response(f"Error configuring physics scene: {str(e)}")

def get_physics_scene_properties(stage_id: str, scene_path: str) -> str:
    """Get the properties of a physics scene
    
    Args:
        stage_id: The ID of the stage
        scene_path: Path to the physics scene
        
    Returns:
        JSON string with physics scene properties
    """
    try:
        # Get the stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            from ..core.stage_operations import error_response
            return error_response(f"Stage not found: {stage_id}")
        
        # Get the physics scene
        physics_scene = UsdPhysics.Scene.Get(stage, scene_path)
        if not physics_scene:
            from ..core.stage_operations import error_response
            return error_response(f"Physics scene not found at {scene_path}")
        
        # Get the physics scene properties
        properties = {
            "gravity_direction": physics_scene.GetGravityDirectionAttr().Get() if physics_scene.GetGravityDirectionAttr() else None,
            "gravity_magnitude": physics_scene.GetGravityMagnitudeAttr().Get() if physics_scene.GetGravityMagnitudeAttr() else None,
            "time_scale": physics_scene.GetTimeScaleAttr().Get() if physics_scene.GetTimeScaleAttr() else None
        }
        
        from ..core.stage_operations import success_response
        return success_response("Physics scene properties", {
            "stage_id": stage_id,
            "scene_path": scene_path,
            "properties": properties
        })
        
    except Exception as e:
        logger.exception(f"Error in get_physics_scene_properties: {str(e)}")
        from ..core.stage_operations import error_response
        return error_response(f"Error getting physics scene properties: {str(e)}") 