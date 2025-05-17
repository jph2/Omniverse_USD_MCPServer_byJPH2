"""
Animation keyframes utilities for USD stages.

This module provides functions for creating and manipulating keyframe animations.
"""

from pxr import Usd, UsdGeom, UsdSkel, Sdf, Gf
import logging
from typing import Dict, Any, Optional, List, Tuple, Union

from ..core.registry import stage_registry

logger = logging.getLogger(__name__)

def set_keyframe(stage, prim_path: str, attribute_name: str, 
                time: float, value: Union[float, Tuple, List],
                interpolation: str = "linear") -> bool:
    """Set a keyframe for an attribute at a specific time
    
    Args:
        stage: The USD stage
        prim_path: Path to the prim
        attribute_name: Name of the attribute to animate
        time: Time code for the keyframe
        value: Value at the keyframe
        interpolation: Interpolation type ("linear", "held", "bezier")
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get the prim
        prim = stage.GetPrimAtPath(prim_path)
        if not prim.IsValid():
            logger.error(f"Invalid prim path: {prim_path}")
            return False
        
        # Get or create the attribute
        attrib = None
        if attribute_name.startswith("xformOp:"):
            # Handle transform operations
            xformable = UsdGeom.Xformable(prim)
            
            if attribute_name == "xformOp:translate":
                # Create or get translate op
                translate_op = xformable.AddTranslateOp()
                attrib = translate_op.GetAttr()
            
            elif attribute_name == "xformOp:rotateXYZ":
                # Create or get rotate op
                rotate_op = xformable.AddRotateXYZOp()
                attrib = rotate_op.GetAttr()
            
            elif attribute_name == "xformOp:scale":
                # Create or get scale op
                scale_op = xformable.AddScaleOp()
                attrib = scale_op.GetAttr()
            
            else:
                logger.error(f"Unsupported transform operation: {attribute_name}")
                return False
        else:
            # Regular attribute
            attrib = prim.GetAttribute(attribute_name)
            if not attrib:
                logger.error(f"Attribute not found: {attribute_name}")
                return False
        
        # Set the keyframe
        attrib.Set(value, time)
        
        # Set interpolation
        if interpolation != "linear":
            # Get or create the layer for animation data
            anim_layer = stage.GetRootLayer()
            
            # Set the interpolation
            interpolation_map = {
                "held": Sdf.ValueTypeNames.Token, 
                "bezier": Sdf.ValueTypeNames.Token
            }
            
            # This requires lower-level Sdf API access which is complex
            # For simplicity in this example, we'll skip the full implementation of custom interpolation
            # In a real implementation, you would need to:
            # 1. Get or create the SdfPath for the attribute
            # 2. Get or create the SdfAttributeSpec for that path
            # 3. Set its interpolation metadata
            
            logger.info(f"Note: Custom interpolation '{interpolation}' requested but implementation is limited")
        
        return True
    
    except Exception as e:
        logger.exception(f"Error setting keyframe: {str(e)}")
        return False

def set_keyframe_by_id(stage_id: str, prim_path: str, attribute_name: str,
                     time: float, value: Union[List, float],
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
    try:
        # Get the stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            from ..core.stage_operations import error_response
            return error_response(f"Stage not found: {stage_id}")
        
        # Prepare the value - convert lists to tuples if needed
        prepared_value = value
        if isinstance(value, list):
            prepared_value = tuple(value)
        
        # Set the keyframe
        success = set_keyframe(stage, prim_path, attribute_name, time, prepared_value, interpolation)
        
        if success:
            # Mark stage as modified
            stage_registry.mark_as_modified(stage_id)
            
            from ..core.stage_operations import success_response
            return success_response("Keyframe set successfully", {
                "stage_id": stage_id,
                "prim_path": prim_path,
                "attribute": attribute_name,
                "time": time,
                "value": value,
                "interpolation": interpolation
            })
        else:
            from ..core.stage_operations import error_response
            return error_response(f"Failed to set keyframe for {prim_path}.{attribute_name}")
        
    except Exception as e:
        logger.exception(f"Error in set_keyframe_by_id: {str(e)}")
        from ..core.stage_operations import error_response
        return error_response(f"Error setting keyframe: {str(e)}")

def create_animation_by_id(stage_id: str, prim_path: str, attribute_name: str,
                         keyframes: List[Dict[str, Any]],
                         time_range: Optional[Tuple[float, float]] = None) -> str:
    """Create a complete animation with multiple keyframes by stage ID
    
    Args:
        stage_id: The ID of the stage
        prim_path: Path to the prim
        attribute_name: Name of the attribute to animate
        keyframes: List of keyframe dictionaries with 'time', 'value', and optional 'interpolation'
        time_range: Optional explicit time range for the animation as (start, end)
        
    Returns:
        JSON string with result information
    """
    try:
        # Get the stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            from ..core.stage_operations import error_response
            return error_response(f"Stage not found: {stage_id}")
        
        # Set the stage's time range if provided
        if time_range:
            stage.SetStartTimeCode(time_range[0])
            stage.SetEndTimeCode(time_range[1])
        else:
            # Automatically determine time range from keyframes
            times = [kf["time"] for kf in keyframes]
            if times:
                stage.SetStartTimeCode(min(times))
                stage.SetEndTimeCode(max(times))
        
        # Set each keyframe
        successful_keyframes = 0
        for kf in keyframes:
            # Get required values
            time = kf["time"]
            value = kf["value"]
            
            # Get optional values with defaults
            interpolation = kf.get("interpolation", "linear")
            
            # Prepare the value - convert lists to tuples if needed
            prepared_value = value
            if isinstance(value, list):
                prepared_value = tuple(value)
            
            # Set the keyframe
            success = set_keyframe(stage, prim_path, attribute_name, time, prepared_value, interpolation)
            if success:
                successful_keyframes += 1
        
        # Check if any keyframes were set successfully
        if successful_keyframes > 0:
            # Mark stage as modified
            stage_registry.mark_as_modified(stage_id)
            
            from ..core.stage_operations import success_response
            return success_response("Animation created successfully", {
                "stage_id": stage_id,
                "prim_path": prim_path,
                "attribute": attribute_name,
                "keyframes_set": successful_keyframes,
                "keyframes_total": len(keyframes),
                "time_range": [stage.GetStartTimeCode(), stage.GetEndTimeCode()]
            })
        else:
            from ..core.stage_operations import error_response
            return error_response(f"Failed to set any keyframes for {prim_path}.{attribute_name}")
        
    except Exception as e:
        logger.exception(f"Error in create_animation_by_id: {str(e)}")
        from ..core.stage_operations import error_response
        return error_response(f"Error creating animation: {str(e)}")

def create_transform_animation_by_id(stage_id: str, prim_path: str,
                                   translate_keyframes: Optional[List[Dict[str, Any]]] = None,
                                   rotate_keyframes: Optional[List[Dict[str, Any]]] = None,
                                   scale_keyframes: Optional[List[Dict[str, Any]]] = None,
                                   time_range: Optional[Tuple[float, float]] = None) -> str:
    """Create a complete transform animation (translation, rotation, scale) by stage ID
    
    Args:
        stage_id: The ID of the stage
        prim_path: Path to the prim
        translate_keyframes: Optional list of translation keyframe dictionaries
        rotate_keyframes: Optional list of rotation keyframe dictionaries
        scale_keyframes: Optional list of scale keyframe dictionaries
        time_range: Optional explicit time range for the animation as (start, end)
        
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
        
        # Make sure it's a xformable prim
        xformable = UsdGeom.Xformable(prim)
        if not xformable:
            from ..core.stage_operations import error_response
            return error_response(f"Prim is not xformable: {prim_path}")
        
        # Determine time range from all keyframes
        all_times = []
        if translate_keyframes:
            all_times.extend([kf["time"] for kf in translate_keyframes])
        if rotate_keyframes:
            all_times.extend([kf["time"] for kf in rotate_keyframes])
        if scale_keyframes:
            all_times.extend([kf["time"] for kf in scale_keyframes])
        
        # Set the stage's time range
        if time_range:
            stage.SetStartTimeCode(time_range[0])
            stage.SetEndTimeCode(time_range[1])
        elif all_times:
            stage.SetStartTimeCode(min(all_times))
            stage.SetEndTimeCode(max(all_times))
        
        # Add translate keyframes
        successful_keyframes = 0
        if translate_keyframes:
            translate_op = xformable.AddTranslateOp()
            for kf in translate_keyframes:
                time = kf["time"]
                value = kf["value"]
                if isinstance(value, list):
                    value = tuple(value)
                interpolation = kf.get("interpolation", "linear")
                
                # Set keyframe
                translate_op.GetAttr().Set(value, time)
                successful_keyframes += 1
        
        # Add rotate keyframes
        if rotate_keyframes:
            rotate_op = xformable.AddRotateXYZOp()
            for kf in rotate_keyframes:
                time = kf["time"]
                value = kf["value"]
                if isinstance(value, list):
                    value = tuple(value)
                interpolation = kf.get("interpolation", "linear")
                
                # Set keyframe
                rotate_op.GetAttr().Set(value, time)
                successful_keyframes += 1
        
        # Add scale keyframes
        if scale_keyframes:
            scale_op = xformable.AddScaleOp()
            for kf in scale_keyframes:
                time = kf["time"]
                value = kf["value"]
                if isinstance(value, list):
                    value = tuple(value)
                interpolation = kf.get("interpolation", "linear")
                
                # Set keyframe
                scale_op.GetAttr().Set(value, time)
                successful_keyframes += 1
        
        # Check if any keyframes were set successfully
        if successful_keyframes > 0:
            # Mark stage as modified
            stage_registry.mark_as_modified(stage_id)
            
            from ..core.stage_operations import success_response
            return success_response("Transform animation created successfully", {
                "stage_id": stage_id,
                "prim_path": prim_path,
                "keyframes_set": successful_keyframes,
                "time_range": [stage.GetStartTimeCode(), stage.GetEndTimeCode()],
                "animated_transforms": {
                    "translate": bool(translate_keyframes),
                    "rotate": bool(rotate_keyframes),
                    "scale": bool(scale_keyframes)
                }
            })
        else:
            from ..core.stage_operations import error_response
            return error_response(f"No keyframes provided for {prim_path}")
        
    except Exception as e:
        logger.exception(f"Error in create_transform_animation_by_id: {str(e)}")
        from ..core.stage_operations import error_response
        return error_response(f"Error creating transform animation: {str(e)}") 