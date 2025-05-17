#!/usr/bin/env python3
"""
Omniverse USD MCP Server - Scene Graph Visualization Example

This example demonstrates how to use the scene graph visualization tools
to analyze and visualize the structure of USD stages.

Prerequisites:
1. Run the USD MCP Server: python usd_mcp_server.py --host 0.0.0.0 --port 5000
2. Create a USD stage to visualize (or use the physics example to generate one)
"""

from cursor_integration import CursorUsdTools
import os
import sys
import json
import argparse
import webbrowser
from typing import Dict, Any, Optional

def create_demo_scene(output_path: str) -> Dict[str, Any]:
    """Create a demo scene to visualize
    
    Args:
        output_path: Path where to save the USD stage
        
    Returns:
        Result of the operation
    """
    # Initialize the Cursor USD tools
    usd_tools = CursorUsdTools()
    
    # Check if server is running
    status = usd_tools.get_server_status()
    if not status.get("ok", False):
        print("Failed to connect to USD MCP Server. Make sure it's running with:")
        print("python usd_mcp_server.py --host 0.0.0.0 --port 5000")
        return {"ok": False, "message": "Server not running"}
    
    print(f"Connected to USD MCP Server: {status.get('data', {}).get('server_name', '')}")
    
    # Create a more complex hierarchical scene for interesting visualization
    result = usd_tools.create_stage(output_path, template="full")
    if not result.get("ok", False):
        print(f"Failed to create stage: {result.get('message', '')}")
        return result
    
    print(f"Created new stage at {output_path}")
    
    # Add a group for models
    models_path = "/World/Models"
    
    # Add a car model with hierarchy
    car_path = f"{models_path}/Car"
    
    # Car body
    usd_tools.create_primitive(
        output_path,
        "cube",
        f"{car_path}/Body",
        size=2.0,
        position=(0, 1.0, 0)
    )
    
    # Scale the car body
    usd_tools.set_transform(
        output_path,
        f"{car_path}/Body",
        scale=(2.0, 0.7, 1.0)
    )
    
    # Create four wheels
    wheel_positions = [
        (1.0, 0.5, 0.7),   # front right
        (1.0, 0.5, -0.7),  # front left
        (-1.0, 0.5, 0.7),  # back right
        (-1.0, 0.5, -0.7)  # back left
    ]
    
    for i, pos in enumerate(wheel_positions):
        wheel_name = f"Wheel_{i+1}"
        usd_tools.create_primitive(
            output_path,
            "cylinder",
            f"{car_path}/Wheels/{wheel_name}",
            size=0.5,
            position=pos
        )
        
        # Rotate wheels to the correct orientation
        usd_tools.set_transform(
            output_path,
            f"{car_path}/Wheels/{wheel_name}",
            rotate=(0, 0, 90)
        )
    
    # Create materials
    # Car body material
    usd_tools.create_material(
        output_path,
        "/World/Materials/CarBodyMaterial",
        diffuse_color=(0.8, 0.2, 0.2),  # Red
        metallic=0.8,
        roughness=0.2
    )
    
    # Wheel material
    usd_tools.create_material(
        output_path,
        "/World/Materials/WheelMaterial",
        diffuse_color=(0.1, 0.1, 0.1),  # Black
        metallic=0.1,
        roughness=0.9
    )
    
    # Bind materials
    usd_tools.bind_material(
        output_path,
        f"{car_path}/Body",
        "/World/Materials/CarBodyMaterial"
    )
    
    for i in range(4):
        usd_tools.bind_material(
            output_path,
            f"{car_path}/Wheels/Wheel_{i+1}",
            "/World/Materials/WheelMaterial"
        )
    
    # Create a simple building
    building_path = f"{models_path}/Building"
    
    # Building base
    usd_tools.create_primitive(
        output_path,
        "cube",
        f"{building_path}/Base",
        size=5.0,
        position=(10, 2.5, 0)
    )
    
    # Building roof
    usd_tools.create_primitive(
        output_path,
        "cone",
        f"{building_path}/Roof",
        size=3.0,
        position=(10, 6.5, 0)
    )
    
    # Create materials for building
    usd_tools.create_material(
        output_path,
        "/World/Materials/BuildingMaterial",
        diffuse_color=(0.8, 0.8, 0.6),  # Beige
        metallic=0.0,
        roughness=0.8
    )
    
    usd_tools.create_material(
        output_path,
        "/World/Materials/RoofMaterial",
        diffuse_color=(0.6, 0.3, 0.1),  # Brown
        metallic=0.0,
        roughness=0.7
    )
    
    # Bind building materials
    usd_tools.bind_material(
        output_path,
        f"{building_path}/Base",
        "/World/Materials/BuildingMaterial"
    )
    
    usd_tools.bind_material(
        output_path,
        f"{building_path}/Roof",
        "/World/Materials/RoofMaterial"
    )
    
    # Create some terrain
    usd_tools.create_primitive(
        output_path,
        "cube",
        "/World/Environment/Terrain",
        size=30.0,
        position=(0, -1.0, 0)
    )
    
    # Scale the terrain to make it flat
    usd_tools.set_transform(
        output_path,
        "/World/Environment/Terrain",
        scale=(1.0, 0.05, 1.0)
    )
    
    # Create and bind terrain material
    usd_tools.create_material(
        output_path,
        "/World/Materials/TerrainMaterial",
        diffuse_color=(0.3, 0.5, 0.2),  # Green
        metallic=0.0,
        roughness=1.0
    )
    
    usd_tools.bind_material(
        output_path,
        "/World/Environment/Terrain",
        "/World/Materials/TerrainMaterial"
    )
    
    # Set up physics
    usd_tools.setup_physics_scene(output_path)
    
    # Add physics to objects
    usd_tools.add_rigid_body(
        output_path,
        "/World/Environment/Terrain",
        mass=0.0,  # Static
        is_dynamic=False
    )
    
    usd_tools.add_rigid_body(
        output_path,
        f"{car_path}/Body",
        mass=1000.0,
        is_dynamic=True
    )
    
    for i in range(4):
        usd_tools.add_rigid_body(
            output_path,
            f"{car_path}/Wheels/Wheel_{i+1}",
            mass=50.0,
            is_dynamic=True
        )
    
    # Analyze stage
    analysis = usd_tools.analyze_stage(output_path)
    
    return {
        "ok": True,
        "message": f"Created demo scene at {output_path}",
        "stage_path": output_path,
        "analysis": analysis.get("data", {})
    }

def visualize_scene_graph(stage_path: str, format: str = "html", max_depth: int = -1, 
                         include_properties: bool = False, open_browser: bool = True) -> Dict[str, Any]:
    """Visualize the scene graph of a USD stage
    
    Args:
        stage_path: Path to the USD stage file
        format: Visualization format ('text', 'html', 'json', or 'network')
        max_depth: Maximum depth to visualize (-1 for unlimited)
        include_properties: Whether to include properties
        open_browser: Whether to open HTML visualizations in a browser
        
    Returns:
        Visualization result
    """
    # Initialize the Cursor USD tools
    usd_tools = CursorUsdTools()
    
    # Generate the visualization
    result = usd_tools.visualize_scene_graph(
        stage_path,
        output_format=format,
        max_depth=max_depth,
        include_properties=include_properties
    )
    
    if not result.get("ok", False):
        print(f"Failed to visualize scene graph: {result.get('message', '')}")
        return result
    
    output_data = result.get("data", {})
    
    # For HTML format, optionally open in browser
    if format == "html" and open_browser and "output_file" in output_data:
        output_file = output_data["output_file"]
        try:
            print(f"Opening visualization in browser: {output_file}")
            webbrowser.open(f"file://{os.path.abspath(output_file)}")
        except Exception as e:
            print(f"Failed to open browser: {str(e)}")
    
    # For text format, print the visualization
    if format == "text" and "visualization" in output_data:
        print("\nScene Graph Visualization:")
        print(output_data["visualization"])
    
    return result

def main():
    """Main function for command line interface"""
    parser = argparse.ArgumentParser(description="USD Scene Graph Visualization Example")
    parser.add_argument("--stage", "-s", help="Path to existing USD stage file. If not provided, a demo scene will be created.")
    parser.add_argument("--format", "-f", choices=["text", "html", "json", "network"], default="html",
                        help="Visualization format (default: html)")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--max-depth", "-d", type=int, default=-1,
                        help="Maximum depth to visualize (-1 for unlimited)")
    parser.add_argument("--properties", "-p", action="store_true",
                        help="Include properties in visualization")
    parser.add_argument("--no-browser", action="store_true",
                        help="Don't open HTML visualizations in browser")
    
    args = parser.parse_args()
    
    # Create or use existing stage
    stage_path = args.stage
    if not stage_path:
        # Create a demo scene
        demo_path = "scene_graph_demo.usda"
        result = create_demo_scene(demo_path)
        if not result.get("ok", False):
            print(f"Failed to create demo scene: {result.get('message', '')}")
            return 1
        
        stage_path = demo_path
        print(f"\nCreated demo scene with {result.get('analysis', {}).get('prim_count', 0)} prims")
    
    # Visualize the scene graph
    result = visualize_scene_graph(
        stage_path,
        format=args.format,
        max_depth=args.max_depth,
        include_properties=args.properties,
        open_browser=not args.no_browser
    )
    
    if not result.get("ok", False):
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main()) 