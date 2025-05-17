#!/usr/bin/env python3
"""
Cursor Integration Example for Omniverse USD MCP Server

This script demonstrates how to use the CursorUsdTools class to create and
manipulate USD scenes, including the usage of the scene graph visualization
feature.
"""

import os
import time
from cursor_integration import CursorUsdTools

def main():
    """Run the example script demonstrating Cursor USD integration."""
    
    # Initialize the tools with the server URL
    tools = CursorUsdTools(server_url="http://127.0.0.1:5000")
    print("Connected to USD MCP Server")
    
    # Create a demo scene file path
    demo_file = os.path.join(os.path.dirname(__file__), "cursor_demo_scene.usda")
    
    # Create a new stage
    print("\n1. Creating a new USD stage...")
    stage_result = tools.open_stage(demo_file, create_new=True)
    
    if not stage_result["ok"]:
        print(f"Error creating stage: {stage_result['message']}")
        return
        
    stage_id = stage_result["data"]["stage_id"]
    print(f"Stage created with ID: {stage_id}")
    
    # Create a complex scene with multiple primitives and materials
    print("\n2. Adding primitives to the scene...")
    
    # Create a ground plane
    tools.create_primitive(
        stage_id=stage_id,
        primitive_type="cube",
        prim_path="/World/Ground",
        size=10.0,
        position=[0, -0.5, 0]
    )
    
    # Set scale to make it a flat ground
    tools.set_transform(
        stage_id=stage_id,
        prim_path="/World/Ground",
        scale=[1.0, 0.1, 1.0]
    )
    
    # Create a red sphere
    tools.create_primitive(
        stage_id=stage_id,
        primitive_type="sphere",
        prim_path="/World/RedSphere",
        size=1.0,
        position=[0, 1, 0]
    )
    
    # Create a blue cube
    tools.create_primitive(
        stage_id=stage_id,
        primitive_type="cube",
        prim_path="/World/BlueCube",
        size=1.0,
        position=[2, 0.5, 0]
    )
    
    # Create a green cylinder
    tools.create_primitive(
        stage_id=stage_id,
        primitive_type="cylinder", 
        prim_path="/World/GreenCylinder",
        size=1.0,
        position=[-2, 0.5, 0]
    )
    
    print("Primitives created successfully")
    
    # Create materials folder
    print("\n3. Creating materials...")
    tools.define_prim(
        stage_id=stage_id,
        prim_path="/World/Materials",
        prim_type="Scope"
    )
    
    # Create a red material
    tools.create_material(
        stage_id=stage_id,
        material_path="/World/Materials/RedMaterial",
        diffuse_color=[1, 0, 0],
        metallic=0.0,
        roughness=0.2
    )
    
    # Create a blue material
    tools.create_material(
        stage_id=stage_id,
        material_path="/World/Materials/BlueMaterial",
        diffuse_color=[0, 0, 1],
        metallic=0.1,
        roughness=0.3
    )
    
    # Create a green material
    tools.create_material(
        stage_id=stage_id,
        material_path="/World/Materials/GreenMaterial",
        diffuse_color=[0, 1, 0],
        metallic=0.0,
        roughness=0.5
    )
    
    # Bind materials to primitives
    print("\n4. Binding materials to primitives...")
    tools.bind_material(
        stage_id=stage_id,
        material_path="/World/Materials/RedMaterial",
        prim_path="/World/RedSphere"
    )
    
    tools.bind_material(
        stage_id=stage_id,
        material_path="/World/Materials/BlueMaterial",
        prim_path="/World/BlueCube"
    )
    
    tools.bind_material(
        stage_id=stage_id,
        material_path="/World/Materials/GreenMaterial",
        prim_path="/World/GreenCylinder"
    )
    
    # Save the stage
    print("\n5. Saving the stage...")
    tools.save_stage(stage_id)
    
    # Generate different visualizations of the scene graph
    print("\n6. Visualizing the scene graph in different formats...")
    
    # Text visualization
    print("\nGenerating text visualization...")
    text_result = tools.visualize_scene_graph(
        stage_id=stage_id,
        format="text"
    )
    
    if text_result["ok"] and "data" in text_result:
        print("\nTEXT VISUALIZATION:")
        print(text_result["data"]["visualization"])
    
    # HTML visualization
    print("\nGenerating HTML visualization...")
    html_path = os.path.join(os.path.dirname(__file__), "cursor_demo_visualization.html")
    html_result = tools.visualize_scene_graph(
        stage_id=stage_id,
        format="html",
        output_path=html_path,
        theme="dark"
    )
    
    if html_result["ok"]:
        print(f"HTML visualization saved to: {html_path}")
    
    # JSON visualization
    print("\nGenerating JSON visualization...")
    json_path = os.path.join(os.path.dirname(__file__), "cursor_demo_visualization.json")
    json_result = tools.visualize_scene_graph(
        stage_id=stage_id,
        format="json",
        output_path=json_path
    )
    
    if json_result["ok"]:
        print(f"JSON visualization saved to: {json_path}")
    
    # Filtered visualization (only show materials)
    print("\nGenerating filtered visualization (materials only)...")
    materials_path = os.path.join(os.path.dirname(__file__), "cursor_demo_materials.html")
    materials_result = tools.visualize_scene_graph(
        stage_id=stage_id,
        format="html",
        output_path=materials_path,
        filter_types=["Material"],
        theme="light"
    )
    
    if materials_result["ok"]:
        print(f"Materials visualization saved to: {materials_path}")
    
    # Close the stage to free resources
    print("\n7. Closing the stage...")
    tools.close_stage(stage_id)
    
    print("\nCursor USD integration example completed successfully!")
    print(f"The demo scene was saved to: {demo_file}")
    print("The following visualization files were created:")
    print(f"  - {html_path} (HTML visualization with dark theme)")
    print(f"  - {json_path} (JSON visualization)")
    print(f"  - {materials_path} (HTML visualization of materials only)")


if __name__ == "__main__":
    main() 