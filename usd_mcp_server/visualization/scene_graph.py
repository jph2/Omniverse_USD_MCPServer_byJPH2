"""
Scene graph visualization utilities for USD stages.

This module provides functions for visualizing USD scene graphs in various formats.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
import html

from pxr import Usd, UsdGeom
from ..core.registry import stage_registry

logger = logging.getLogger(__name__)

def generate_html_scene_graph(stage, root_path: str = "/") -> str:
    """Generate an HTML representation of a stage's scene graph
    
    Args:
        stage: The USD stage
        root_path: The root path to start visualization from
        
    Returns:
        HTML string representation of the scene graph
    """
    try:
        # Get the root prim
        root_prim = stage.GetPrimAtPath(root_path)
        if not root_prim.IsValid():
            return f"<div class='error'>Invalid root path: {root_path}</div>"
        
        # CSS styles for the HTML
        css = """
        <style>
            .scene-graph {
                font-family: Arial, sans-serif;
                margin: 20px;
            }
            .prim {
                margin-bottom: 5px;
            }
            .prim-header {
                display: flex;
                align-items: center;
                cursor: pointer;
                padding: 5px;
                background-color: #f8f9fa;
                border-radius: 4px;
            }
            .prim-header:hover {
                background-color: #e9ecef;
            }
            .prim-name {
                font-weight: bold;
                margin-right: 10px;
            }
            .prim-type {
                color: #6c757d;
                font-size: 0.9em;
            }
            .prim-children {
                margin-left: 20px;
                padding-left: 10px;
                border-left: 1px solid #dee2e6;
            }
            .attribute {
                font-size: 0.9em;
                color: #495057;
                margin-left: 20px;
                margin-top: 3px;
            }
            .attribute-name {
                color: #6610f2;
            }
            .attribute-type {
                color: #6c757d;
                font-style: italic;
                margin-left: 5px;
            }
            .attribute-value {
                margin-left: 5px;
                color: #28a745;
            }
            .collapsed {
                display: none;
            }
            .xform-icon {
                color: #fd7e14;
                margin-right: 5px;
            }
            .mesh-icon {
                color: #17a2b8;
                margin-right: 5px;
            }
            .camera-icon {
                color: #dc3545;
                margin-right: 5px;
            }
            .light-icon {
                color: #ffc107;
                margin-right: 5px;
            }
            .material-icon {
                color: #20c997;
                margin-right: 5px;
            }
            .default-icon {
                color: #6c757d;
                margin-right: 5px;
            }
        </style>
        """
        
        # JavaScript for toggle functionality
        js = """
        <script>
            function togglePrim(id) {
                const children = document.getElementById(id + '-children');
                const attributes = document.getElementById(id + '-attributes');
                if (children) {
                    children.classList.toggle('collapsed');
                }
                if (attributes) {
                    attributes.classList.toggle('collapsed');
                }
            }
        </script>
        """
        
        # Generate HTML for the scene graph
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>USD Scene Graph: {os.path.basename(stage.GetRootLayer().realPath)}</title>
            {css}
        </head>
        <body>
            <div class="scene-graph">
                <h1>USD Scene Graph: {os.path.basename(stage.GetRootLayer().realPath)}</h1>
                {_generate_prim_html(root_prim, 0)}
            </div>
            {js}
        </body>
        </html>
        """
        
        return html_content
    
    except Exception as e:
        logger.exception(f"Error generating HTML scene graph: {str(e)}")
        return f"<div class='error'>Error generating scene graph: {str(e)}</div>"

def _generate_prim_html(prim, prim_id: int) -> str:
    """Generate HTML for a prim and its children
    
    Args:
        prim: The USD prim
        prim_id: A unique ID for this prim (for JS toggling)
        
    Returns:
        HTML string for this prim
    """
    prim_path = prim.GetPath()
    prim_name = prim_path.name
    prim_type = prim.GetTypeName()
    
    # Determine the icon based on prim type
    icon = "default-icon"
    icon_symbol = "●"
    
    if prim.IsA(UsdGeom.Xform):
        icon = "xform-icon"
        icon_symbol = "◆"
    elif prim.IsA(UsdGeom.Mesh):
        icon = "mesh-icon"
        icon_symbol = "▲"
    elif prim.IsA(UsdGeom.Camera):
        icon = "camera-icon"
        icon_symbol = "◉"
    elif prim.IsA(UsdGeom.Light) or "Light" in prim_type:
        icon = "light-icon"
        icon_symbol = "★"
    elif "Material" in prim_type or "Shader" in prim_type:
        icon = "material-icon"
        icon_symbol = "◇"
    
    # Generate HTML for this prim
    html_content = f"""
    <div class="prim">
        <div class="prim-header" onclick="togglePrim('{prim_id}')">
            <span class="{icon}">{icon_symbol}</span>
            <span class="prim-name">{html.escape(prim_name)}</span>
            <span class="prim-type">{html.escape(prim_type)}</span>
        </div>
    """
    
    # Generate HTML for attributes
    attributes_html = ""
    for attribute in prim.GetAttributes():
        attr_name = attribute.GetName()
        attr_type = attribute.GetTypeName()
        
        # Try to get the attribute value
        try:
            attr_value = attribute.Get()
            attr_value_str = str(attr_value)
        except:
            attr_value_str = "<unable to get value>"
        
        attributes_html += f"""
        <div class="attribute">
            <span class="attribute-name">{html.escape(attr_name)}</span>
            <span class="attribute-type">{html.escape(str(attr_type))}</span>
            <span class="attribute-value">{html.escape(attr_value_str)}</span>
        </div>
        """
    
    if attributes_html:
        html_content += f"""
        <div id="{prim_id}-attributes" class="prim-attributes collapsed">
            {attributes_html}
        </div>
        """
    
    # Generate HTML for children recursively
    children_html = ""
    child_id = prim_id
    for child in prim.GetChildren():
        child_id += 1
        children_html += _generate_prim_html(child, child_id)
    
    if children_html:
        html_content += f"""
        <div id="{prim_id}-children" class="prim-children collapsed">
            {children_html}
        </div>
        """
    
    html_content += "</div>"
    return html_content

def visualize_scene_graph_by_id(stage_id: str, root_path: str = "/", format: str = "html") -> str:
    """Generate a visualization of a stage's scene graph by stage ID
    
    Args:
        stage_id: The ID of the stage
        root_path: The root path to start visualization from
        format: Output format ("html", "json", "text")
        
    Returns:
        Visualization in the requested format or error response
    """
    try:
        # Get the stage from registry
        stage = stage_registry.get_stage(stage_id)
        if not stage:
            from ..core.stage_operations import error_response
            return error_response(f"Stage not found: {stage_id}")
        
        # Generate visualization based on requested format
        if format == "html":
            visualization = generate_html_scene_graph(stage, root_path)
            
            from ..core.stage_operations import success_response
            return success_response("Scene graph visualization generated", {
                "stage_id": stage_id,
                "root_path": root_path,
                "format": format,
                "visualization": visualization
            })
            
        elif format == "json":
            # Generate JSON visualization (simplified implementation)
            root_prim = stage.GetPrimAtPath(root_path)
            if not root_prim.IsValid():
                from ..core.stage_operations import error_response
                return error_response(f"Invalid root path: {root_path}")
            
            json_data = _prim_to_dict(root_prim)
            
            from ..core.stage_operations import success_response
            return success_response("Scene graph visualization generated", {
                "stage_id": stage_id,
                "root_path": root_path,
                "format": format,
                "visualization": json_data
            })
            
        elif format == "text":
            # Generate text visualization (simplified implementation)
            root_prim = stage.GetPrimAtPath(root_path)
            if not root_prim.IsValid():
                from ..core.stage_operations import error_response
                return error_response(f"Invalid root path: {root_path}")
            
            text_data = _generate_text_scene_graph(root_prim)
            
            from ..core.stage_operations import success_response
            return success_response("Scene graph visualization generated", {
                "stage_id": stage_id,
                "root_path": root_path,
                "format": format,
                "visualization": text_data
            })
            
        else:
            from ..core.stage_operations import error_response
            return error_response(f"Unsupported visualization format: {format}")
            
    except Exception as e:
        logger.exception(f"Error in visualize_scene_graph_by_id: {str(e)}")
        from ..core.stage_operations import error_response
        return error_response(f"Error visualizing scene graph: {str(e)}")

def _prim_to_dict(prim) -> Dict[str, Any]:
    """Convert a USD prim to a dictionary for JSON output
    
    Args:
        prim: The USD prim
        
    Returns:
        Dictionary representation of the prim
    """
    result = {
        "name": prim.GetName(),
        "path": str(prim.GetPath()),
        "type": prim.GetTypeName(),
        "attributes": [],
        "children": []
    }
    
    # Add attributes
    for attribute in prim.GetAttributes():
        attr_dict = {
            "name": attribute.GetName(),
            "type": str(attribute.GetTypeName())
        }
        
        # Try to get the attribute value
        try:
            attr_value = attribute.Get()
            # Convert to JSON-serializable format
            if hasattr(attr_value, "__iter__") and not isinstance(attr_value, str):
                attr_value = list(attr_value)
            attr_dict["value"] = attr_value
        except:
            attr_dict["value"] = None
        
        result["attributes"].append(attr_dict)
    
    # Add children recursively
    for child in prim.GetChildren():
        result["children"].append(_prim_to_dict(child))
    
    return result

def _generate_text_scene_graph(prim, indent: int = 0) -> str:
    """Generate a text representation of a prim and its children
    
    Args:
        prim: The USD prim
        indent: Indentation level
        
    Returns:
        Text representation of the prim
    """
    result = ""
    indent_str = "  " * indent
    
    # Add this prim
    result += f"{indent_str}{prim.GetName()} ({prim.GetTypeName()})\n"
    
    # Add attributes
    for attribute in prim.GetAttributes():
        try:
            value = attribute.Get()
            value_str = str(value)
            if len(value_str) > 50:
                value_str = value_str[:47] + "..."
        except:
            value_str = "<unable to get value>"
        
        result += f"{indent_str}  {attribute.GetName()} ({attribute.GetTypeName()}): {value_str}\n"
    
    # Add children recursively
    for child in prim.GetChildren():
        result += _generate_text_scene_graph(child, indent + 1)
    
    return result 