#!/usr/bin/env python3
"""
Omniverse USD MCP Server - Optimized Scene Graph Visualization Example

This example demonstrates the enhanced scene graph visualization capabilities
with performance optimizations for large USD files.

Prerequisites:
1. Run the USD MCP Server: python usd_mcp_server.py --host 0.0.0.0 --port 5000
2. You can use an existing USD file or the example will create a demo scene
"""

from scene_graph_optimizer import UsdSceneGraphOptimizer
from cursor_integration import CursorUsdTools
import os
import sys
import argparse
import time
from typing import Dict, Any

def create_complex_demo_scene(output_path: str) -> Dict[str, Any]:
    """Create a complex scene with many elements to demonstrate optimization
    
    Args:
        output_path: Path where to save the USD stage
        
    Returns:
        Result of the operation
    """
    print(f"Creating complex demo scene at {output_path}...")
    usd_tools = CursorUsdTools()
    
    # Check if server is running
    status = usd_tools.get_server_status()
    if not status.get("ok", False):
        print("Failed to connect to USD MCP Server. Make sure it's running with:")
        print("python usd_mcp_server.py --host 0.0.0.0 --port 5000")
        return {"ok": False, "message": "Server not running"}
    
    # Create a complex scene with many objects
    result = usd_tools.create_stage(output_path, template="full")
    if not result.get("ok", False):
        return result
    
    # Add many primitives and materials to demonstrate optimization
    for x in range(-5, 6, 2):
        for z in range(-5, 6, 2):
            # Create a building at this position
            building_base = f"/World/Buildings/Building_{x}_{z}"
            
            # Main structure
            usd_tools.create_primitive(
                output_path,
                "cube",
                f"{building_base}/Structure",
                size=1.5,
                position=(x, 0.75, z)
            )
            
            # Roof
            roof_type = "cone" if (x + z) % 2 == 0 else "cube"
            usd_tools.create_primitive(
                output_path,
                roof_type,
                f"{building_base}/Roof",
                size=1.0,
                position=(x, 1.75, z)
            )
            
            # Create a unique material for this building
            hue_value = ((x + 5) * 10 + (z + 5) * 5) % 100 / 100.0
            r, g, b = _hsv_to_rgb(hue_value, 0.7, 0.8)
            
            usd_tools.create_material(
                output_path,
                f"/World/Materials/Building_{x}_{z}_Material",
                diffuse_color=(r, g, b),
                metallic=0.1,
                roughness=0.8
            )
            
            # Bind material
            usd_tools.bind_material(
                output_path,
                f"{building_base}/Structure",
                f"/World/Materials/Building_{x}_{z}_Material"
            )
    
    # Add a complex road network
    for x in range(-6, 7, 2):
        # East-West roads
        usd_tools.create_primitive(
            output_path,
            "cube",
            f"/World/Roads/EW_Road_{x}",
            size=12.0,
            position=(x, 0.05, 0)
        )
        usd_tools.set_transform(
            output_path,
            f"/World/Roads/EW_Road_{x}",
            scale=(0.2, 0.05, 1.0)
        )
    
    for z in range(-6, 7, 2):
        # North-South roads
        usd_tools.create_primitive(
            output_path,
            "cube",
            f"/World/Roads/NS_Road_{z}",
            size=12.0,
            position=(0, 0.05, z)
        )
        usd_tools.set_transform(
            output_path,
            f"/World/Roads/NS_Road_{z}",
            scale=(1.0, 0.05, 0.2)
        )
    
    # Add road material
    usd_tools.create_material(
        output_path,
        "/World/Materials/RoadMaterial",
        diffuse_color=(0.2, 0.2, 0.2),
        metallic=0.0,
        roughness=0.9
    )
    
    # Bind road material to all roads
    for x in range(-6, 7, 2):
        usd_tools.bind_material(
            output_path,
            f"/World/Roads/EW_Road_{x}",
            "/World/Materials/RoadMaterial"
        )
    
    for z in range(-6, 7, 2):
        usd_tools.bind_material(
            output_path,
            f"/World/Roads/NS_Road_{z}",
            "/World/Materials/RoadMaterial"
        )
    
    # Add ground plane
    usd_tools.create_primitive(
        output_path,
        "cube",
        "/World/Environment/Ground",
        size=20.0,
        position=(0, -0.1, 0)
    )
    usd_tools.set_transform(
        output_path,
        "/World/Environment/Ground",
        scale=(1.0, 0.05, 1.0)
    )
    
    # Add ground material
    usd_tools.create_material(
        output_path,
        "/World/Materials/GroundMaterial",
        diffuse_color=(0.3, 0.5, 0.2),
        metallic=0.0,
        roughness=1.0
    )
    
    usd_tools.bind_material(
        output_path,
        "/World/Environment/Ground",
        "/World/Materials/GroundMaterial"
    )
    
    # Setup physics for the environment
    usd_tools.setup_physics_scene(output_path)
    
    # Add physics to ground
    usd_tools.add_rigid_body(
        output_path,
        "/World/Environment/Ground",
        mass=0.0,
        is_dynamic=False
    )
    
    # Analyze the stage to get prim count
    analysis = usd_tools.analyze_stage(output_path)
    
    return {
        "ok": True,
        "message": f"Created complex demo scene at {output_path}",
        "stage_path": output_path,
        "prim_count": len(analysis.get("data", {}).get("prims", [])) if analysis.get("ok", False) else 0
    }

def _hsv_to_rgb(h: float, s: float, v: float) -> tuple:
    """Convert HSV color to RGB
    
    Args:
        h: Hue (0-1)
        s: Saturation (0-1)
        v: Value (0-1)
        
    Returns:
        RGB tuple (0-1)
    """
    if s == 0.0:
        return (v, v, v)
    
    i = int(h * 6)
    f = (h * 6) - i
    p = v * (1 - s)
    q = v * (1 - s * f)
    t = v * (1 - s * (1 - f))
    
    i %= 6
    
    if i == 0:
        return (v, t, p)
    elif i == 1:
        return (q, v, p)
    elif i == 2:
        return (p, v, t)
    elif i == 3:
        return (p, q, v)
    elif i == 4:
        return (t, p, v)
    else:
        return (v, p, q)

def demonstrate_optimization_formats(stage_path: str):
    """Demonstrate different visualization formats with optimization
    
    Args:
        stage_path: Path to the USD stage file
    """
    optimizer = UsdSceneGraphOptimizer(stage_path)
    
    print("\n1. Text Format Visualization (Basic)")
    text_result = optimizer.visualize(
        output_format="text",
        max_depth=2,  # Limit depth for text format
        include_properties=False
    )
    
    print("\n2. HTML Visualization (Dark Theme, Material Filter)")
    html_result = optimizer.visualize(
        output_format="html",
        output_path="materials_visualization.html",
        filter_types=["Material"],
        theme="dark",
        open_browser=True
    )
    print(f"HTML visualization time: {html_result.get('performance', {}).get('elapsed_seconds', 0):.2f} seconds")
    
    print("\n3. HTML Visualization (Light Theme, Full Scene)")
    html_full_result = optimizer.visualize(
        output_format="html",
        output_path="full_visualization.html",
        theme="light",
        open_browser=True
    )
    print(f"Full HTML visualization time: {html_full_result.get('performance', {}).get('elapsed_seconds', 0):.2f} seconds")
    
    print("\n4. HTML Visualization (Contrast Theme, Buildings Focus)")
    html_buildings_result = optimizer.visualize(
        output_format="html",
        output_path="buildings_visualization.html",
        filter_pattern="Building",
        theme="contrast",
        open_browser=True
    )
    print(f"Buildings visualization time: {html_buildings_result.get('performance', {}).get('elapsed_seconds', 0):.2f} seconds")
    
    print("\n5. JSON Data Export")
    json_result = optimizer.visualize(
        output_format="json",
        output_path="scene_data.json",
        include_properties=True
    )
    
    print("\n6. Network Graph Data")
    network_result = optimizer.visualize(
        output_format="network",
        output_path="scene_network.json"
    )
    
    print("\nAll visualizations completed.")

def main():
    """Main function for the example"""
    parser = argparse.ArgumentParser(description="Optimized Scene Graph Visualization Example")
    parser.add_argument("--stage", "-s", help="Path to an existing USD stage file. If not provided, a demo scene will be created.")
    parser.add_argument("--no-demo", action="store_true", help="Skip the multi-format demonstration")
    parser.add_argument("--format", "-f", choices=["text", "html", "json", "network"], default="html", 
                        help="Output format if not running the demo")
    parser.add_argument("--filter-types", "-t", nargs="+", help="Filter by prim types")
    parser.add_argument("--theme", choices=["light", "dark", "contrast"], default="light", help="Visual theme")
    
    args = parser.parse_args()
    
    # Create or use existing stage
    stage_path = args.stage
    if not stage_path:
        # Create a demo scene
        demo_path = "complex_city_demo.usda"
        start_time = time.time()
        result = create_complex_demo_scene(demo_path)
        create_time = time.time() - start_time
        
        if not result.get("ok", False):
            print(f"Failed to create demo scene: {result.get('message', '')}")
            return 1
        
        stage_path = demo_path
        print(f"Created demo scene with {result.get('prim_count', 0)} prims in {create_time:.2f} seconds")
    
    # Run optimization demonstrations or a single visualization
    if not args.no_demo:
        demonstrate_optimization_formats(stage_path)
    else:
        # Create optimizer
        optimizer = UsdSceneGraphOptimizer(stage_path)
        
        # Generate a single visualization
        result = optimizer.visualize(
            output_format=args.format,
            filter_types=args.filter_types,
            theme=args.theme
        )
        
        if not result.get("ok", False):
            print(f"Error: {result.get('message', 'Unknown error')}")
            return 1
        
        print(f"Visualization completed in {result.get('performance', {}).get('elapsed_seconds', 0):.2f} seconds")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 