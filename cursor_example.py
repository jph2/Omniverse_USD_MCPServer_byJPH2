#!/usr/bin/env python3
"""
Cursor USD MCP Server Example - Physics Simulation

This example demonstrates how to use the Cursor integration with the USD MCP Server
to create a physics simulation with multiple objects and materials.

Prerequisites:
1. Run the USD MCP Server: python usd_mcp_server.py --host 0.0.0.0 --port 5000
2. Have cursor_integration.py in the same directory
"""

from cursor_integration import CursorUsdTools
import time
import json

def create_physics_demo(output_path="cursor_physics_demo.usda"):
    """Create a simple physics simulation with multiple objects
    
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
    
    # Create a new USD stage
    result = usd_tools.create_stage(output_path, template="basic")
    if not result.get("ok", False):
        print(f"Failed to create stage: {result.get('message', '')}")
        return result
    
    print(f"Created new stage at {output_path}")
    
    # Set up physics scene with slightly stronger gravity
    physics_result = usd_tools.setup_physics_scene(output_path, gravity=(0, -15.0, 0))
    print(f"Set up physics scene: {physics_result.get('message', '')}")
    
    # Create a ground plane
    ground_result = usd_tools.create_primitive(
        output_path,
        "cube",
        "/World/Ground",
        size=10.0,
        position=(0, -2.5, 0)
    )
    
    # Scale the ground to make it flat
    usd_tools.set_transform(
        output_path,
        "/World/Ground",
        scale=(1.0, 0.5, 1.0)
    )
    
    # Create a static rigid body for the ground
    usd_tools.add_rigid_body(
        output_path,
        "/World/Ground",
        mass=0.0,  # Mass of 0 makes it static
        is_dynamic=False
    )
    
    # Create a material for the ground
    usd_tools.create_material(
        output_path,
        "/World/Materials/GroundMaterial",
        diffuse_color=(0.2, 0.5, 0.2),  # Green
        roughness=0.7
    )
    
    # Bind the material to the ground
    usd_tools.bind_material(
        output_path,
        "/World/Ground",
        "/World/Materials/GroundMaterial"
    )
    
    # Create several objects that will fall
    object_types = [
        {"type": "sphere", "name": "Sphere", "size": 1.0, "position": (-3, 5, 0), "color": (1, 0, 0)},
        {"type": "cube", "name": "Cube", "size": 1.0, "position": (0, 7, 0), "color": (0, 0, 1)},
        {"type": "cylinder", "name": "Cylinder", "size": 0.7, "position": (3, 9, 0), "color": (1, 1, 0)},
        {"type": "cone", "name": "Cone", "size": 0.8, "position": (0, 11, 2), "color": (1, 0, 1)}
    ]
    
    # Create each object
    for obj in object_types:
        # Create primitive
        prim_path = f"/World/DynamicObjects/{obj['name']}"
        usd_tools.create_primitive(
            output_path,
            obj["type"],
            prim_path,
            size=obj["size"],
            position=obj["position"]
        )
        
        # Create material for this object
        material_path = f"/World/Materials/{obj['name']}Material"
        usd_tools.create_material(
            output_path,
            material_path,
            diffuse_color=obj["color"],
            metallic=0.1,
            roughness=0.3
        )
        
        # Bind the material
        usd_tools.bind_material(
            output_path,
            prim_path,
            material_path
        )
        
        # Add rigid body physics (with random mass)
        mass = obj["size"] * 2.0  # Mass proportional to size
        usd_tools.add_rigid_body(
            output_path,
            prim_path,
            mass=mass,
            is_dynamic=True
        )
        
        print(f"Created {obj['type']} '{obj['name']}' with physics")
    
    # Analyze the completed stage
    analysis = usd_tools.analyze_stage(output_path)
    
    # Export to different formats for compatibility
    usd_tools.export_to_format(output_path, output_path.replace(".usda", ".usdz"), "usdz")
    
    return {
        "ok": True, 
        "message": f"Created physics simulation at {output_path}",
        "stage_path": output_path,
        "analysis": analysis.get("data", {})
    }

if __name__ == "__main__":
    print("Creating USD physics simulation with Cursor integration...")
    result = create_physics_demo()
    
    if result.get("ok", False):
        print("\nSuccessfully created physics simulation!")
        print(f"Stage file: {result.get('stage_path')}")
        print("\nStage analysis summary:")
        
        analysis = result.get("analysis", {})
        prim_count = analysis.get("prim_count", 0)
        material_count = analysis.get("material_count", 0)
        print(f"- Total prims: {prim_count}")
        print(f"- Materials: {material_count}")
        print(f"- Physics-enabled objects: {len(analysis.get('physics_prims', []))}")
        
        print("\nOpen this USD file in your preferred USD viewer or Omniverse app to see the simulation.")
    else:
        print(f"\nFailed to create simulation: {result.get('message', 'Unknown error')}") 