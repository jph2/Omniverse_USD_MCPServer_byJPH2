"""
Materials and shaders utilities for USD stages.

This module provides functions for creating and applying materials and shaders to prims.
"""

from pxr import Usd, UsdShade, UsdGeom, Sdf
import logging
from typing import Dict, Any, Optional, List, Tuple

from ..core.registry import stage_registry

logger = logging.getLogger(__name__)

def create_preview_surface_material(stage, material_path: str, 
                                  diffuse_color: Optional[Tuple[float, float, float]] = None,
                                  emissive_color: Optional[Tuple[float, float, float]] = None,
                                  metallic: Optional[float] = None,
                                  roughness: Optional[float] = None,
                                  opacity: Optional[float] = None) -> bool:
    """Create a UsdPreviewSurface material with the specified properties
    
    Args:
        stage: The USD stage
        material_path: Path where the material will be created
        diffuse_color: Optional diffuse color as (r, g, b)
        emissive_color: Optional emissive color as (r, g, b)
        metallic: Optional metallic value (0-1)
        roughness: Optional roughness value (0-1)
        opacity: Optional opacity value (0-1)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create the material
        material = UsdShade.Material.Define(stage, material_path)
        
        # Create the UsdPreviewSurface shader
        shader_path = f"{material_path}/PreviewSurface"
        preview_surface = UsdShade.Shader.Define(stage, shader_path)
        preview_surface.CreateIdAttr("UsdPreviewSurface")
        
        # Create the material output
        material.CreateSurfaceOutput().ConnectToSource(preview_surface.ConnectableAPI(), "surface")
        
        # Set shader parameters
        if diffuse_color is not None:
            diffuse_input = preview_surface.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f)
            diffuse_input.Set(diffuse_color)
        
        if emissive_color is not None:
            emissive_input = preview_surface.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f)
            emissive_input.Set(emissive_color)
        
        if metallic is not None:
            metallic_input = preview_surface.CreateInput("metallic", Sdf.ValueTypeNames.Float)
            metallic_input.Set(metallic)
        
        if roughness is not None:
            roughness_input = preview_surface.CreateInput("roughness", Sdf.ValueTypeNames.Float)
            roughness_input.Set(roughness)
        
        if opacity is not None:
            opacity_input = preview_surface.CreateInput("opacity", Sdf.ValueTypeNames.Float)
            opacity_input.Set(opacity)
        
        return True
    
    except Exception as e:
        logger.exception(f"Error creating material: {str(e)}")
        return False

def create_material_by_id(stage_id: str, material_path: str, material_type: str = "preview_surface",
                        diffuse_color: Optional[List[float]] = None,
                        emissive_color: Optional[List[float]] = None,
                        metallic: Optional[float] = None,
                        roughness: Optional[float] = None,
                        opacity: Optional[float] = None) -> str:
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
    try:
        # Get the stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            from ..core.stage_operations import error_response
            return error_response(f"Stage not found: {stage_id}")
        
        # Convert colors to tuples if provided
        diffuse_tuple = tuple(diffuse_color) if diffuse_color else None
        emissive_tuple = tuple(emissive_color) if emissive_color else None
        
        # Create the material based on the material type
        success = False
        if material_type == "preview_surface":
            success = create_preview_surface_material(
                stage, material_path, diffuse_tuple, emissive_tuple, metallic, roughness, opacity
            )
        else:
            from ..core.stage_operations import error_response
            return error_response(f"Unsupported material type: {material_type}")
        
        if success:
            # Mark stage as modified
            stage_registry.mark_as_modified(stage_id)
            
            from ..core.stage_operations import success_response
            return success_response("Material created successfully", {
                "stage_id": stage_id,
                "material_path": material_path,
                "material_type": material_type,
                "properties": {
                    "diffuse_color": diffuse_color,
                    "emissive_color": emissive_color,
                    "metallic": metallic,
                    "roughness": roughness,
                    "opacity": opacity
                }
            })
        else:
            from ..core.stage_operations import error_response
            return error_response(f"Failed to create material at {material_path}")
        
    except Exception as e:
        logger.exception(f"Error in create_material_by_id: {str(e)}")
        from ..core.stage_operations import error_response
        return error_response(f"Error creating material: {str(e)}")

def assign_material_by_id(stage_id: str, prim_path: str, material_path: str) -> str:
    """Assign a material to a prim by stage ID
    
    Args:
        stage_id: The ID of the stage
        prim_path: Path to the prim to assign the material to
        material_path: Path to the material to assign
        
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
        
        # Get the material
        material = UsdShade.Material.Get(stage, material_path)
        if not material:
            from ..core.stage_operations import error_response
            return error_response(f"Invalid material path: {material_path}")
        
        # Create a material binding
        binding_api = UsdShade.MaterialBindingAPI(prim)
        binding_api.Bind(material)
        
        # Mark stage as modified
        stage_registry.mark_as_modified(stage_id)
        
        from ..core.stage_operations import success_response
        return success_response("Material assigned successfully", {
            "stage_id": stage_id,
            "prim_path": prim_path,
            "material_path": material_path
        })
        
    except Exception as e:
        logger.exception(f"Error in assign_material_by_id: {str(e)}")
        from ..core.stage_operations import error_response
        return error_response(f"Error assigning material: {str(e)}")

def update_material_by_id(stage_id: str, material_path: str,
                        diffuse_color: Optional[List[float]] = None,
                        emissive_color: Optional[List[float]] = None,
                        metallic: Optional[float] = None,
                        roughness: Optional[float] = None,
                        opacity: Optional[float] = None) -> str:
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
    try:
        # Get the stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            from ..core.stage_operations import error_response
            return error_response(f"Stage not found: {stage_id}")
        
        # Get the material
        material = UsdShade.Material.Get(stage, material_path)
        if not material:
            from ..core.stage_operations import error_response
            return error_response(f"Invalid material path: {material_path}")
        
        # Get the shader
        shader_path = f"{material_path}/PreviewSurface"
        shader = UsdShade.Shader.Get(stage, shader_path)
        if not shader:
            from ..core.stage_operations import error_response
            return error_response(f"Material does not have a PreviewSurface shader: {material_path}")
        
        # Update shader parameters
        updated = {}
        
        if diffuse_color is not None:
            diffuse_input = shader.GetInput("diffuseColor")
            if not diffuse_input:
                diffuse_input = shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f)
            diffuse_input.Set(tuple(diffuse_color))
            updated["diffuse_color"] = diffuse_color
        
        if emissive_color is not None:
            emissive_input = shader.GetInput("emissiveColor")
            if not emissive_input:
                emissive_input = shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f)
            emissive_input.Set(tuple(emissive_color))
            updated["emissive_color"] = emissive_color
        
        if metallic is not None:
            metallic_input = shader.GetInput("metallic")
            if not metallic_input:
                metallic_input = shader.CreateInput("metallic", Sdf.ValueTypeNames.Float)
            metallic_input.Set(metallic)
            updated["metallic"] = metallic
        
        if roughness is not None:
            roughness_input = shader.GetInput("roughness")
            if not roughness_input:
                roughness_input = shader.CreateInput("roughness", Sdf.ValueTypeNames.Float)
            roughness_input.Set(roughness)
            updated["roughness"] = roughness
        
        if opacity is not None:
            opacity_input = shader.GetInput("opacity")
            if not opacity_input:
                opacity_input = shader.CreateInput("opacity", Sdf.ValueTypeNames.Float)
            opacity_input.Set(opacity)
            updated["opacity"] = opacity
        
        # Mark stage as modified
        stage_registry.mark_as_modified(stage_id)
        
        from ..core.stage_operations import success_response
        return success_response("Material updated successfully", {
            "stage_id": stage_id,
            "material_path": material_path,
            "updated": updated
        })
        
    except Exception as e:
        logger.exception(f"Error in update_material_by_id: {str(e)}")
        from ..core.stage_operations import error_response
        return error_response(f"Error updating material: {str(e)}")

def create_texture_material_by_id(stage_id: str, material_path: str, 
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
    try:
        # Get the stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            from ..core.stage_operations import error_response
            return error_response(f"Stage not found: {stage_id}")
        
        # Create the material
        material = UsdShade.Material.Define(stage, material_path)
        
        # Create the UsdPreviewSurface shader
        shader_path = f"{material_path}/PreviewSurface"
        preview_surface = UsdShade.Shader.Define(stage, shader_path)
        preview_surface.CreateIdAttr("UsdPreviewSurface")
        
        # Create the material output
        material.CreateSurfaceOutput().ConnectToSource(preview_surface.ConnectableAPI(), "surface")
        
        # Create the texture reader shader
        texture_path = f"{material_path}/Texture"
        texture_reader = UsdShade.Shader.Define(stage, texture_path)
        texture_reader.CreateIdAttr("UsdUVTexture")
        
        # Set the file path
        file_input = texture_reader.CreateInput("file", Sdf.ValueTypeNames.Asset)
        file_input.Set(texture_file_path)
        
        # Set the ST (UV) coordinates
        texture_reader.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(
            UsdShade.Shader.Get(stage, material_path).ConnectableAPI(), "primvar:st"
        )
        
        # Connect the texture to the material based on texture type
        if texture_type == "diffuse":
            # Connect to diffuseColor
            rgb_output = texture_reader.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)
            diffuse_input = preview_surface.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f)
            diffuse_input.ConnectToSource(rgb_output)
        
        elif texture_type == "normal":
            # Connect to normal
            rgb_output = texture_reader.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)
            normal_input = preview_surface.CreateInput("normal", Sdf.ValueTypeNames.Normal3f)
            normal_input.ConnectToSource(rgb_output)
        
        elif texture_type == "roughness":
            # Connect to roughness (using red channel)
            r_output = texture_reader.CreateOutput("r", Sdf.ValueTypeNames.Float)
            roughness_input = preview_surface.CreateInput("roughness", Sdf.ValueTypeNames.Float)
            roughness_input.ConnectToSource(r_output)
        
        elif texture_type == "metallic":
            # Connect to metallic (using red channel)
            r_output = texture_reader.CreateOutput("r", Sdf.ValueTypeNames.Float)
            metallic_input = preview_surface.CreateInput("metallic", Sdf.ValueTypeNames.Float)
            metallic_input.ConnectToSource(r_output)
        
        elif texture_type == "opacity":
            # Connect to opacity (using alpha channel)
            a_output = texture_reader.CreateOutput("a", Sdf.ValueTypeNames.Float)
            opacity_input = preview_surface.CreateInput("opacity", Sdf.ValueTypeNames.Float)
            opacity_input.ConnectToSource(a_output)
        
        else:
            from ..core.stage_operations import error_response
            return error_response(f"Unsupported texture type: {texture_type}")
        
        # Mark stage as modified
        stage_registry.mark_as_modified(stage_id)
        
        from ..core.stage_operations import success_response
        return success_response("Texture material created successfully", {
            "stage_id": stage_id,
            "material_path": material_path,
            "texture_file_path": texture_file_path,
            "texture_type": texture_type
        })
        
    except Exception as e:
        logger.exception(f"Error in create_texture_material_by_id: {str(e)}")
        from ..core.stage_operations import error_response
        return error_response(f"Error creating texture material: {str(e)}") 