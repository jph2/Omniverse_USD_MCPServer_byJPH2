#!/usr/bin/env python3
"""
Omniverse USD MCP Server - Scene Graph Visualizer

This module provides visualization tools for USD scene graphs. It can generate:
1. ASCII text representations of the scene hierarchy
2. HTML visualizations with interactive elements
3. JSON structure for programmatic use
4. Network graph data for visualization in third-party tools

Usage:
    from scene_graph_visualizer import UsdSceneGraphVisualizer
    
    # Create visualizer for a USD stage
    visualizer = UsdSceneGraphVisualizer("path/to/stage.usda")
    
    # Get ASCII text representation
    text_graph = visualizer.to_text()
    print(text_graph)
    
    # Generate HTML visualization
    html_file = visualizer.to_html("scene_graph.html")
    print(f"HTML visualization saved to {html_file}")
"""

from pxr import Usd, UsdGeom, UsdShade, UsdPhysics
import json
import os
import argparse
import sys
from typing import Dict, List, Any, Optional, Union, Set
import html
import datetime
import textwrap

class UsdSceneGraphVisualizer:
    """Visualizes USD scene graph structure in multiple formats"""
    
    def __init__(self, stage_path: str, max_depth: int = -1):
        """Initialize the scene graph visualizer
        
        Args:
            stage_path: Path to USD stage file
            max_depth: Maximum depth to traverse (-1 for unlimited)
        """
        self.stage_path = stage_path
        self.max_depth = max_depth
        self.stage = Usd.Stage.Open(stage_path)
        
        if not self.stage:
            raise ValueError(f"Failed to open USD stage at {stage_path}")
            
        self.graph_data = None
        self._build_graph_data()
        
    def _build_graph_data(self):
        """Build the internal scene graph data structure"""
        self.graph_data = {
            "name": os.path.basename(self.stage_path),
            "path": "/",
            "type": "stage",
            "properties": self._get_stage_properties(),
            "children": []
        }
        
        # Process all root prims
        root_prims = [self.stage.GetPseudoRoot()]
        self._process_prims(root_prims, self.graph_data["children"], depth=0)
    
    def _get_stage_properties(self) -> Dict[str, Any]:
        """Get stage-level properties
        
        Returns:
            Dictionary of stage properties
        """
        props = {
            "up_axis": UsdGeom.GetStageUpAxis(self.stage),
            "meters_per_unit": UsdGeom.GetStageMetersPerUnit(self.stage),
            "start_time_code": self.stage.GetStartTimeCode(),
            "end_time_code": self.stage.GetEndTimeCode(),
            "time_codes_per_second": self.stage.GetTimeCodesPerSecond(),
            "frame_rate": self.stage.GetFramesPerSecond(),
            "default_prim": str(self.stage.GetDefaultPrim().GetPath()) if self.stage.GetDefaultPrim() else None,
            "documentation": self.stage.GetRootLayer().GetDocumentation(),
            "file_format": self.stage.GetRootLayer().GetFileFormat().GetFormatId(),
        }
        return props
    
    def _process_prims(self, prims, children_list, depth=0):
        """Process a list of prims and add them to the children list
        
        Args:
            prims: List of Usd.Prim objects to process
            children_list: List to add the processed prim data to
            depth: Current depth in the hierarchy
        """
        if self.max_depth >= 0 and depth > self.max_depth:
            return
        
        for prim in prims:
            # Skip the pseudoroot for the actual visualization
            if prim.IsPseudoRoot() and depth == 0:
                # Continue with its children but don't add it to the graph
                self._process_prims(prim.GetChildren(), children_list, depth)
                continue
                
            # Create node for this prim
            prim_data = {
                "name": prim.GetName(),
                "path": str(prim.GetPath()),
                "type": prim.GetTypeName(),
                "active": prim.IsActive(),
                "defined": prim.IsDefined(),
                "abstract": prim.IsAbstract(),
                "properties": self._get_prim_properties(prim),
                "children": []
            }
            
            # Add specialized information based on prim type
            if prim.IsA(UsdGeom.Imageable):
                self._add_imageable_data(prim, prim_data)
            elif prim.IsA(UsdShade.Material):
                self._add_material_data(prim, prim_data)
            elif prim.IsA(UsdPhysics.RigidBody):
                self._add_physics_data(prim, prim_data)
                
            # Add this prim to the children list
            children_list.append(prim_data)
            
            # Process children of this prim
            if prim.GetChildren():
                self._process_prims(prim.GetChildren(), prim_data["children"], depth + 1)
    
    def _get_prim_properties(self, prim) -> Dict[str, Any]:
        """Get properties of a prim
        
        Args:
            prim: The Usd.Prim to extract properties from
            
        Returns:
            Dictionary of prim properties
        """
        properties = {}
        
        # Process attributes
        for attr in prim.GetAttributes():
            if attr.HasValue():
                try:
                    value = attr.Get()
                    # Convert Vt array types to lists for JSON serialization
                    if hasattr(value, '_values'):
                        value = list(value)
                    properties[attr.GetName()] = str(value)
                except Exception as e:
                    properties[attr.GetName()] = f"<error: {str(e)}>"
        
        # Process relationships
        for rel in prim.GetRelationships():
            targets = rel.GetTargets()
            if targets:
                properties[rel.GetName()] = [str(target) for target in targets]
        
        return properties
    
    def _add_imageable_data(self, prim, prim_data):
        """Add specialized data for UsdGeom.Imageable prims
        
        Args:
            prim: The UsdGeom.Imageable prim
            prim_data: The data dictionary for this prim
        """
        imageable = UsdGeom.Imageable(prim)
        prim_data["visibility"] = str(imageable.GetVisibilityAttr().Get())
        prim_data["purpose"] = str(imageable.GetPurposeAttr().Get())
        
        # Check if it's a defined geometry type and add type-specific info
        if prim.IsA(UsdGeom.Mesh):
            mesh = UsdGeom.Mesh(prim)
            face_count = 0
            if mesh.GetFaceVertexCountsAttr().HasValue():
                face_counts = mesh.GetFaceVertexCountsAttr().Get()
                face_count = len(face_counts) if face_counts else 0
            
            point_count = 0
            if mesh.GetPointsAttr().HasValue():
                points = mesh.GetPointsAttr().Get()
                point_count = len(points) if points else 0
                
            prim_data["geometry_data"] = {
                "face_count": face_count,
                "point_count": point_count,
                "has_normals": mesh.GetNormalsAttr().HasValue(),
                "has_primvars": len(list(mesh.GetPrimvars())) > 0
            }
            
        elif prim.IsA(UsdGeom.Xform):
            xform = UsdGeom.Xform(prim)
            prim_data["transform_ops"] = xform.GetXformOpOrderAttr().HasValue()
    
    def _add_material_data(self, prim, prim_data):
        """Add specialized data for UsdShade.Material prims
        
        Args:
            prim: The UsdShade.Material prim
            prim_data: The data dictionary for this prim
        """
        material = UsdShade.Material(prim)
        surface_output = material.GetSurfaceOutput()
        prim_data["material_data"] = {
            "has_surface": surface_output.HasConnectedSource(),
            "has_displacement": material.GetDisplacementOutput().HasConnectedSource(),
            "has_volume": material.GetVolumeOutput().HasConnectedSource()
        }
    
    def _add_physics_data(self, prim, prim_data):
        """Add specialized data for UsdPhysics.RigidBody prims
        
        Args:
            prim: The UsdPhysics.RigidBody prim
            prim_data: The data dictionary for this prim
        """
        rigid_body = UsdPhysics.RigidBody(prim)
        prim_data["physics_data"] = {
            "mass": str(rigid_body.GetMassAttr().Get()) if rigid_body.GetMassAttr().HasValue() else "default",
            "is_dynamic": rigid_body.GetDisabledAttr().Get() if rigid_body.GetDisabledAttr().HasValue() else True,
        }
                
    def to_text(self, include_properties: bool = False) -> str:
        """Generate a text representation of the USD scene graph
        
        Args:
            include_properties: Whether to include property details
            
        Returns:
            ASCII text representation of the scene graph
        """
        lines = [f"USD Scene Graph: {self.stage_path}"]
        lines.append("=" * 80)
        
        # Add stage properties
        stage_props = self.graph_data["properties"]
        lines.append(f"Up Axis: {stage_props['up_axis']}")
        lines.append(f"Meters Per Unit: {stage_props['meters_per_unit']}")
        lines.append(f"Time Range: {stage_props['start_time_code']} to {stage_props['end_time_code']}")
        lines.append(f"Default Prim: {stage_props['default_prim'] or 'None'}")
        lines.append("=" * 80)
        
        # Build the tree
        def add_node(node, prefix="", is_last=True, depth=0):
            if depth > 0:  # Skip root node
                # Create the branch graphics
                branch = "└── " if is_last else "├── "
                lines.append(f"{prefix}{branch}{node['name']} ({node['type']})")
                
                # Add properties if requested
                if include_properties and node['properties'] and depth > 0:
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    for key, value in node['properties'].items():
                        # Only show non-empty and important properties
                        if value and key not in ["typeName", "active", "defined"]:
                            # Truncate long values
                            if isinstance(value, str) and len(value) > 50:
                                value = value[:47] + "..."
                            lines.append(f"{new_prefix}    {key}: {value}")
            
            # Process children
            if node['children']:
                new_prefix = prefix
                if depth > 0:
                    new_prefix = prefix + ("    " if is_last else "│   ")
                
                for i, child in enumerate(node['children']):
                    is_last_child = (i == len(node['children']) - 1)
                    add_node(child, new_prefix, is_last_child, depth + 1)
        
        # Process all root children
        for i, child in enumerate(self.graph_data["children"]):
            is_last_child = (i == len(self.graph_data["children"]) - 1)
            add_node(child, "", is_last_child)
            
        return "\n".join(lines)
    
    def to_json(self, output_file: Optional[str] = None) -> Union[str, Dict]:
        """Generate a JSON representation of the USD scene graph
        
        Args:
            output_file: Optional file path to save JSON output
            
        Returns:
            JSON string or dictionary of the scene graph
        """
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(self.graph_data, f, indent=2)
            return output_file
        else:
            return json.dumps(self.graph_data, indent=2)
    
    def to_html(self, output_file: str) -> str:
        """Generate an HTML visualization of the USD scene graph
        
        Args:
            output_file: File path to save the HTML output
            
        Returns:
            Path to the generated HTML file
        """
        # Create HTML content
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>USD Scene Graph: {html.escape(os.path.basename(self.stage_path))}</title>
    <style>
        body {{{{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}}}
        .container {{{{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}}}
        h1 {{{{
            color: #333;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }}}}
        .stage-info {{{{
            background-color: #f9f9f9;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}}}
        .stage-info table {{{{
            width: 100%;
        }}}}
        .stage-info th {{{{
            text-align: left;
            width: 200px;
        }}}}
        .tree-view {{{{
            font-family: monospace;
        }}}}
        .tree-node {{{{
            margin: 2px 0;
        }}}}
        .collapsible {{{{
            cursor: pointer;
            user-select: none;
        }}}}
        .collapsible::before {{{{
            content: "▶";
            display: inline-block;
            margin-right: 5px;
            transition: transform 0.2s;
        }}}}
        .active::before {{{{
            transform: rotate(90deg);
        }}}}
        .content {{{{
            display: none;
            padding-left: 20px;
            overflow: hidden;
        }}}}
        .open {{{{
            display: block;
        }}}}
        .prim-type {{{{
            color: #777;
            font-size: 0.9em;
        }}}}
        .properties {{{{
            font-size: 0.9em;
            padding: 5px 0 5px 20px;
            background-color: #f9f9f9;
            border-left: 3px solid #ddd;
            margin: 5px 0 5px 20px;
        }}}}
        .property-name {{{{
            color: #0066cc;
        }}}}
        .property-value {{{{
            color: #009900;
        }}}}
        .footer {{{{
            text-align: center;
            margin-top: 30px;
            font-size: 0.8em;
            color: #777;
        }}}}
        .geometry {{{{
            color: #ff6600;
        }}}}
        .material {{{{
            color: #9900cc;
        }}}}
        .xform {{{{
            color: #0099cc;
        }}}}
        .physics {{{{
            color: #cc0000;
        }}}}
        .search-box {{{{
            width: 100%;
            padding: 10px;
            margin-bottom: 20px;
            box-sizing: border-box;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}}}
        .highlight {{{{
            background-color: yellow;
        }}}}
    </style>
</head>
<body>
    <div class="container">
        <h1>USD Scene Graph Visualization</h1>
        
        <div class="stage-info">
            <h2>Stage Information: {html.escape(os.path.basename(self.stage_path))}</h2>
            <table>
                <tr>
                    <th>File Path</th>
                    <td>{html.escape(self.stage_path)}</td>
                </tr>
                <tr>
                    <th>Up Axis</th>
                    <td>{self.graph_data["properties"]["up_axis"]}</td>
                </tr>
                <tr>
                    <th>Meters Per Unit</th>
                    <td>{self.graph_data["properties"]["meters_per_unit"]}</td>
                </tr>
                <tr>
                    <th>Time Range</th>
                    <td>{self.graph_data["properties"]["start_time_code"]} to {self.graph_data["properties"]["end_time_code"]}</td>
                </tr>
                <tr>
                    <th>Default Prim</th>
                    <td>{html.escape(str(self.graph_data["properties"]["default_prim"] or "None"))}</td>
                </tr>
                <tr>
                    <th>File Format</th>
                    <td>{html.escape(str(self.graph_data["properties"]["file_format"]))}</td>
                </tr>
            </table>
        </div>
        
        <input type="text" id="searchBox" class="search-box" placeholder="Search for prims or properties...">
        
        <div class="tree-view" id="sceneGraph">
            {self._generate_html_tree()}
        </div>
        
        <div class="footer">
            Generated by Omniverse USD MCP Server Scene Graph Visualizer on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        </div>
    </div>
    
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        // Make all nodes with children collapsible
        var nodes = document.getElementsByClassName("collapsible");
        for (var i = 0; i < nodes.length; i++) {{
            nodes[i].addEventListener("click", function() {{
                this.classList.toggle("active");
                var content = this.nextElementSibling;
                if (content.classList.contains("content")) {{
                    content.classList.toggle("open");
                }}
            }});
        }}
        
        // Expand the first level by default
        var rootNodes = document.querySelectorAll('#sceneGraph > .tree-node > .collapsible');
        for (var i = 0; i < rootNodes.length; i++) {{
            rootNodes[i].click();
        }}
        
        // Search functionality
        document.getElementById('searchBox').addEventListener('input', function() {{
            var searchText = this.value.toLowerCase();
            
            // Remove all highlights first
            var highlighted = document.querySelectorAll('.highlight');
            for (var i = 0; i < highlighted.length; i++) {{
                highlighted[i].classList.remove('highlight');
            }}
            
            if (searchText.length < 2) return; // Don't search for very short texts
            
            // Find all tree nodes containing the search text
            var allNodes = document.querySelectorAll('.tree-node');
            var matchFound = false;
            
            for (var i = 0; i < allNodes.length; i++) {{
                var nodeContent = allNodes[i].textContent.toLowerCase();
                if (nodeContent.indexOf(searchText) > -1) {{
                    // Highlight this node
                    allNodes[i].classList.add('highlight');
                    matchFound = true;
                    
                    // Expand all parent nodes
                    var parent = allNodes[i].parentElement;
                    while (parent && !parent.classList.contains('tree-view')) {{
                        if (parent.classList.contains('content') && !parent.classList.contains('open')) {{
                            parent.classList.add('open');
                            var collapsible = parent.previousElementSibling;
                            if (collapsible && collapsible.classList.contains('collapsible')) {{
                                collapsible.classList.add('active');
                            }}
                        }}
                        parent = parent.parentElement;
                    }}
                }}
            }}
            
            // Scroll to the first match
            if (matchFound) {{
                var firstMatch = document.querySelector('.highlight');
                firstMatch.scrollIntoView({{behavior: 'smooth', block: 'center'}});
            }}
        }});
    }});
    </script>
</body>
</html>"""
        
        # Write the HTML file
        with open(output_file, 'w') as f:
            f.write(html_content)
            
        return output_file
    
    def _generate_html_tree(self) -> str:
        """Generate the HTML for the tree view
        
        Returns:
            HTML string for the tree view
        """
        html_parts = []
        
        def add_node(node, depth=0):
            node_class = ""
            
            # Assign classes based on prim type
            if 'Mesh' in node['type'] or 'Cube' in node['type'] or 'Sphere' in node['type']:
                node_class = "geometry"
            elif 'Material' in node['type']:
                node_class = "material"
            elif 'Xform' in node['type']:
                node_class = "xform"
            elif 'PhysicsRigidBody' in node['type'] or 'Physics' in node['type']:
                node_class = "physics"
            
            # Skip the pseudoroot
            if depth == 0 and node['path'] == '/':
                for child in node['children']:
                    add_node(child, depth)
                return
            
            has_children = bool(node['children'])
            collapsible = 'collapsible' if has_children else ''
            
            html_parts.append(f'<div class="tree-node">')
            
            if has_children:
                html_parts.append(f'<div class="{collapsible} {node_class}">')
            else:
                html_parts.append(f'<div class="{node_class}">')
                
            # Node name and type
            html_parts.append(f'{html.escape(node["name"])} <span class="prim-type">({html.escape(node["type"])})</span>')
            
            if not node['active']:
                html_parts.append(' <em>(inactive)</em>')
                
            html_parts.append('</div>')
            
            # Properties section
            if node['properties']:
                html_parts.append('<div class="properties">')
                for key, value in node['properties'].items():
                    # Skip internal properties and long values
                    if key.startswith('__') or not value:
                        continue
                        
                    # Truncate long values
                    if isinstance(value, str) and len(value) > 100:
                        display_value = html.escape(value[:97]) + "..."
                    else:
                        display_value = html.escape(str(value))
                        
                    html_parts.append(f'<div><span class="property-name">{html.escape(key)}:</span> <span class="property-value">{display_value}</span></div>')
                html_parts.append('</div>')
            
            # Children nodes
            if has_children:
                html_parts.append('<div class="content">')
                for child in node['children']:
                    add_node(child, depth + 1)
                html_parts.append('</div>')
                
            html_parts.append('</div>')
        
        # Process all root children
        for child in self.graph_data["children"]:
            add_node(child)
            
        return '\n'.join(html_parts)
        
    def to_network_data(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate network graph data for visualization in tools like d3.js
        
        Args:
            output_file: Optional file path to save the network data
            
        Returns:
            Dictionary with nodes and links data
        """
        nodes = []
        links = []
        node_idx_map = {}  # Map from path to index in nodes array
        
        # Function to process a node and its children
        def process_node(node, parent_idx=None):
            # Create a node
            current_idx = len(nodes)
            node_idx_map[node['path']] = current_idx
            
            # Determine node type for visualization
            node_type = "default"
            if 'Mesh' in node['type'] or 'Cube' in node['type'] or 'Sphere' in node['type']:
                node_type = "geometry"
            elif 'Material' in node['type']:
                node_type = "material"
            elif 'Xform' in node['type']:
                node_type = "xform"
            elif 'PhysicsRigidBody' in node['type'] or 'Physics' in node['type']:
                node_type = "physics"
            
            nodes.append({
                "id": current_idx,
                "name": node['name'],
                "path": node['path'],
                "type": node['type'],
                "node_type": node_type,
                "active": node['active']
            })
            
            # Create link to parent if applicable
            if parent_idx is not None:
                links.append({
                    "source": parent_idx,
                    "target": current_idx,
                    "type": "parent-child"
                })
            
            # Add material bindings as links
            if 'properties' in node:
                for key, value in node['properties'].items():
                    if 'material:binding' in key.lower() and value:
                        # This is a material binding
                        if isinstance(value, list):
                            for material_path in value:
                                # Add when we encounter the material
                                if material_path in node_idx_map:
                                    links.append({
                                        "source": current_idx,
                                        "target": node_idx_map[material_path],
                                        "type": "material-binding"
                                    })
            
            # Process children
            for child in node.get('children', []):
                process_node(child, current_idx)
        
        # Process the entire graph
        process_node(self.graph_data)
        
        network_data = {
            "nodes": nodes,
            "links": links
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(network_data, f, indent=2)
                
        return network_data

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description="USD Scene Graph Visualizer")
    parser.add_argument("stage_path", help="Path to the USD stage file")
    parser.add_argument("--format", "-f", choices=["text", "html", "json", "network"], 
                        default="text", help="Output format")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout for text, auto-generated for others)")
    parser.add_argument("--max-depth", "-d", type=int, default=-1, 
                        help="Maximum depth to visualize (-1 for unlimited)")
    parser.add_argument("--properties", "-p", action="store_true", 
                        help="Include properties in text output")
    
    args = parser.parse_args()
    
    try:
        visualizer = UsdSceneGraphVisualizer(args.stage_path, args.max_depth)
        
        if args.format == "text":
            text_output = visualizer.to_text(include_properties=args.properties)
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(text_output)
                print(f"Text visualization saved to {args.output}")
            else:
                print(text_output)
                
        elif args.format == "html":
            output_file = args.output or f"{os.path.splitext(args.stage_path)[0]}_visualization.html"
            html_file = visualizer.to_html(output_file)
            print(f"HTML visualization saved to {html_file}")
            
        elif args.format == "json":
            output_file = args.output or f"{os.path.splitext(args.stage_path)[0]}_graph.json"
            json_file = visualizer.to_json(output_file)
            print(f"JSON data saved to {output_file}")
            
        elif args.format == "network":
            output_file = args.output or f"{os.path.splitext(args.stage_path)[0]}_network.json"
            visualizer.to_network_data(output_file)
            print(f"Network graph data saved to {output_file}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main()) 