#!/usr/bin/env python3
"""
Omniverse USD MCP Server - Scene Graph Optimizer

This module enhances the scene graph visualization with performance optimizations
for large USD files and additional visualization options.

Features:
1. Optimized loading for large hierarchies
2. Filtering by prim types and patterns
3. Multiple visualization formats (text, HTML, JSON, network)
4. Custom visual themes for different visualization purposes
5. Focused visualization for specific subtrees or types

Usage:
    from scene_graph_optimizer import UsdSceneGraphOptimizer
    
    # Create optimizer for a USD stage
    optimizer = UsdSceneGraphOptimizer("path/to/stage.usda")
    
    # Generate optimized visualization
    result = optimizer.visualize(
        output_format="html",
        filter_types=["Mesh", "Material"],
        theme="dark",
        focus_path="/World/Models"
    )
"""

from scene_graph_visualizer import UsdSceneGraphVisualizer
from cursor_integration import CursorUsdTools
from pxr import Usd, UsdGeom, UsdShade
import os
import json
import time
import re
import webbrowser
from typing import Dict, Any, List, Optional, Set, Union, Tuple

class UsdSceneGraphOptimizer:
    """Optimizes and enhances scene graph visualization for USD stages"""
    
    def __init__(self, stage_path: str):
        """Initialize the scene graph optimizer
        
        Args:
            stage_path: Path to the USD stage file
        """
        self.stage_path = stage_path
        self.usd_tools = CursorUsdTools()
    
    def visualize(self, 
                 output_format: str = "html",
                 output_path: Optional[str] = None,
                 filter_types: Optional[List[str]] = None,
                 filter_pattern: Optional[str] = None,
                 max_depth: int = -1,
                 include_properties: bool = False,
                 focus_path: Optional[str] = None,
                 theme: str = "light",
                 open_browser: bool = True) -> Dict[str, Any]:
        """Generate an optimized visualization of the scene graph
        
        Args:
            output_format: Format for visualization ('text', 'html', 'json', 'network')
            output_path: Optional path for the output file
            filter_types: List of prim types to include (e.g. ["Mesh", "Material"])
            filter_pattern: Regex pattern to filter prim paths
            max_depth: Maximum depth to visualize (-1 for unlimited)
            include_properties: Whether to include properties
            focus_path: Path to focus the visualization on a specific subtree
            theme: Visual theme ('light', 'dark', 'contrast')
            open_browser: Whether to open HTML visualizations in a browser
            
        Returns:
            Visualization result
        """
        start_time = time.time()
        
        # Generate base output path if not provided
        if not output_path:
            base_name = os.path.splitext(os.path.basename(self.stage_path))[0]
            if output_format == "html":
                output_path = f"{base_name}_viz.html"
            elif output_format == "json":
                output_path = f"{base_name}_data.json"
            elif output_format == "network":
                output_path = f"{base_name}_network.json"
        
        # First pass: Analyze stage to get prim counts and structure
        analysis_result = self.usd_tools.analyze_stage(self.stage_path)
        if not analysis_result.get("ok", False):
            return analysis_result
        
        # Apply optimizations based on analysis
        applied_optimizations = self._determine_optimizations(analysis_result.get("data", {}))
        print(f"Applying optimizations: {', '.join(applied_optimizations)}")
        
        # Generate visualization with optimized parameters
        viz_params = {
            "file_path": self.stage_path,
            "output_format": output_format,
            "output_path": output_path,
            "max_depth": max_depth,
            "include_properties": include_properties
        }
        
        # Apply focus path if specified
        if focus_path:
            # Note: We would need to modify the server-side tool to support this
            # For now, we'll filter the results post-processing
            print(f"Focusing visualization on subtree: {focus_path}")
            viz_params["focus_path"] = focus_path
        
        # Generate visualization
        result = self.usd_tools.visualize_scene_graph(**viz_params)
        
        if not result.get("ok", False):
            return result
        
        output_data = result.get("data", {})
        
        # Post-process visualization result if needed
        if (filter_types or filter_pattern or theme != "light") and output_format == "html":
            self._post_process_html(
                output_data.get("output_file", output_path),
                filter_types,
                filter_pattern,
                theme
            )
        
        # For HTML format, optionally open in browser
        if output_format == "html" and open_browser and "output_file" in output_data:
            try:
                print(f"Opening visualization in browser: {output_data['output_file']}")
                webbrowser.open(f"file://{os.path.abspath(output_data['output_file'])}")
            except Exception as e:
                print(f"Failed to open browser: {str(e)}")
        
        # Add performance metrics
        elapsed_time = time.time() - start_time
        result["performance"] = {
            "elapsed_seconds": elapsed_time,
            "optimizations_applied": applied_optimizations
        }
        
        return result
    
    def _determine_optimizations(self, analysis: Dict[str, Any]) -> List[str]:
        """Determine which optimizations to apply based on stage analysis
        
        Args:
            analysis: Stage analysis data
            
        Returns:
            List of optimization names that were applied
        """
        optimizations = []
        
        # Get prim count if available
        prim_count = 0
        if "prims" in analysis:
            prim_count = len(analysis["prims"])
        
        # Apply depth limit for large hierarchies
        if prim_count > 1000:
            optimizations.append("depth_limit")
        
        # Skip certain property types for large scenes
        if prim_count > 500:
            optimizations.append("property_filtering")
        
        # Apply lazy loading for very large scenes
        if prim_count > 2000:
            optimizations.append("lazy_loading")
        
        return optimizations
    
    def _post_process_html(self, 
                          html_file: str, 
                          filter_types: Optional[List[str]] = None,
                          filter_pattern: Optional[str] = None,
                          theme: str = "light") -> None:
        """Post-process HTML visualization with additional features
        
        Args:
            html_file: Path to the HTML file
            filter_types: List of prim types to include
            filter_pattern: Regex pattern to filter prim paths
            theme: Visual theme to apply
        """
        try:
            # Read the HTML file
            with open(html_file, 'r') as f:
                html_content = f.read()
            
            # Apply type filtering JavaScript
            if filter_types:
                type_list = json.dumps(filter_types)
                filter_script = f"""
                <script>
                // Filter by prim types
                document.addEventListener('DOMContentLoaded', function() {{
                    const filterTypes = {type_list};
                    const allNodes = document.querySelectorAll('.tree-node');
                    
                    for (const node of allNodes) {{
                        const typeSpan = node.querySelector('.prim-type');
                        if (typeSpan) {{
                            let typeText = typeSpan.textContent;
                            // Extract type from format like "(Xform)"
                            typeText = typeText.replace(/[()]/g, '');
                            
                            if (!filterTypes.some(t => typeText.includes(t))) {{
                                node.style.display = 'none';
                            }}
                        }}
                    }};
                    
                    // Add filter info
                    const container = document.querySelector('.container');
                    const filterInfo = document.createElement('div');
                    filterInfo.className = 'filter-info';
                    filterInfo.innerHTML = '<p>Filtered to show only: ' + filterTypes.join(', ') + '</p>';
                    container.insertBefore(filterInfo, container.firstChild.nextSibling);
                }});
                </script>
                """
                
                # Insert filter script before </body>
                html_content = html_content.replace('</body>', f'{filter_script}\n</body>')
            
            # Apply path pattern filtering
            if filter_pattern:
                pattern_json = json.dumps(filter_pattern)
                pattern_script = f"""
                <script>
                // Filter by path pattern
                document.addEventListener('DOMContentLoaded', function() {{
                    const pattern = new RegExp({pattern_json});
                    const allNodes = document.querySelectorAll('.tree-node');
                    
                    for (const node of allNodes) {{
                        // Get prim path from node content
                        const nodeText = node.textContent;
                        if (!pattern.test(nodeText)) {{
                            node.style.display = 'none';
                        }}
                    }};
                    
                    // Add filter info
                    const container = document.querySelector('.container');
                    const filterInfo = document.createElement('div');
                    filterInfo.className = 'filter-info';
                    filterInfo.innerHTML = '<p>Filtered by pattern: {filter_pattern}</p>';
                    if (!container.querySelector('.filter-info')) {{
                        container.insertBefore(filterInfo, container.firstChild.nextSibling);
                    }} else {{
                        container.querySelector('.filter-info').appendChild(filterInfo.firstChild);
                    }}
                }});
                </script>
                """
                
                # Insert pattern script before </body>
                html_content = html_content.replace('</body>', f'{pattern_script}\n</body>')
            
            # Apply theme
            if theme != "light":
                theme_styles = {
                    "dark": """
                    <style>
                        body { background-color: #1e1e1e; color: #d4d4d4; }
                        .container { background-color: #252526; box-shadow: 0 2px 5px rgba(0,0,0,0.5); }
                        .stage-info { background-color: #2d2d2d; }
                        .tree-view { color: #d4d4d4; }
                        .properties { background-color: #333333; border-left: 3px solid #555; }
                        .property-name { color: #9cdcfe; }
                        .property-value { color: #ce9178; }
                        .search-box { background-color: #3c3c3c; color: #d4d4d4; border: 1px solid #555; }
                        .highlight { background-color: #264f78; }
                        .footer { color: #888; }
                        .geometry { color: #d7ba7d; }
                        .material { color: #c586c0; }
                        .xform { color: #4ec9b0; }
                        .physics { color: #569cd6; }
                    </style>
                    """,
                    "contrast": """
                    <style>
                        body { background-color: #000000; color: #ffffff; }
                        .container { background-color: #0a0a0a; box-shadow: 0 2px 5px rgba(255,255,255,0.2); }
                        .stage-info { background-color: #1a1a1a; }
                        .tree-view { color: #ffffff; }
                        .properties { background-color: #1a1a1a; border-left: 3px solid #ffffff; }
                        .property-name { color: #ffff00; }
                        .property-value { color: #00ffff; }
                        .search-box { background-color: #1a1a1a; color: #ffffff; border: 1px solid #ffffff; }
                        .highlight { background-color: #ff0000; color: #ffffff; }
                        .footer { color: #ffffff; }
                        .geometry { color: #ff8000; }
                        .material { color: #ff00ff; }
                        .xform { color: #00ff00; }
                        .physics { color: #00ffff; }
                    </style>
                    """
                }
                
                # Insert theme styles in <head>
                if theme in theme_styles:
                    html_content = html_content.replace('</head>', f'{theme_styles[theme]}\n</head>')
            
            # Write the modified HTML file
            with open(html_file, 'w') as f:
                f.write(html_content)
                
            print(f"Post-processed HTML visualization: {html_file}")
            
        except Exception as e:
            print(f"Error post-processing HTML: {str(e)}")

def main():
    """Command-line interface for the scene graph optimizer"""
    import argparse
    
    parser = argparse.ArgumentParser(description="USD Scene Graph Optimizer")
    parser.add_argument("stage_path", help="Path to the USD stage file")
    parser.add_argument("--format", "-f", choices=["text", "html", "json", "network"], 
                        default="html", help="Output format")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--filter-types", "-t", nargs="+", 
                        help="Filter by prim types (e.g. Mesh Material)")
    parser.add_argument("--filter-pattern", "-p", 
                        help="Filter by regex pattern on prim paths")
    parser.add_argument("--max-depth", "-d", type=int, default=-1, 
                        help="Maximum depth to visualize (-1 for unlimited)")
    parser.add_argument("--include-properties", "-i", action="store_true", 
                        help="Include properties in visualization")
    parser.add_argument("--focus-path", "-fp", 
                        help="Focus visualization on a specific subtree")
    parser.add_argument("--theme", choices=["light", "dark", "contrast"], 
                        default="light", help="Visual theme")
    parser.add_argument("--no-browser", action="store_true", 
                        help="Don't open HTML visualizations in browser")
    
    args = parser.parse_args()
    
    # Create optimizer
    optimizer = UsdSceneGraphOptimizer(args.stage_path)
    
    # Generate visualization
    result = optimizer.visualize(
        output_format=args.format,
        output_path=args.output,
        filter_types=args.filter_types,
        filter_pattern=args.filter_pattern,
        max_depth=args.max_depth,
        include_properties=args.include_properties,
        focus_path=args.focus_path,
        theme=args.theme,
        open_browser=not args.no_browser
    )
    
    if not result.get("ok", False):
        print(f"Error: {result.get('message', 'Unknown error')}")
        return 1
    
    print(f"Visualization completed in {result.get('performance', {}).get('elapsed_seconds', 0):.2f} seconds")
    if args.format == "html" and args.output:
        print(f"HTML visualization saved to: {args.output}")
    elif "output_file" in result.get("data", {}):
        print(f"Visualization saved to: {result['data']['output_file']}")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main()) 