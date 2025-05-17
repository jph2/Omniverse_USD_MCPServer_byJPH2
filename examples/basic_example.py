"""
Basic example of using the USD MCP Server.

This example demonstrates the basic functionality of the USD MCP Server:
1. Creating a new stage
2. Adding prims to the stage
3. Setting up physics
4. Creating materials and applying them
5. Creating a simple animation
6. Visualizing the scene graph
7. Saving the stage
"""

import os
import asyncio
import json
import subprocess
import time
import sys

# Add the parent directory to the path so we can import the client
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from usd_mcp_client import UsdMcpClient

async def call_and_print(client, tool, params):
    """Call a tool and print the result nicely"""
    result = await client.call_tool(tool, params)
    print(f"\n----- {tool} result -----")
    if isinstance(result, dict) and "ok" in result:
        if result["ok"]:
            print(f"✅ Success: {result.get('message', '')}")
            data = result.get("data", {})
            # Print the data with some indentation
            for key, value in data.items():
                if isinstance(value, dict) or isinstance(value, list):
                    print(f"  {key}: {json.dumps(value, indent=2)[:200]}...")
                else:
                    print(f"  {key}: {value}")
        else:
            print(f"❌ Error: {result.get('message', '')}")
    else:
        print(result)
    print("-" * 30)
    return result

async def run_example():
    """Run the example"""
    # Create a output directory
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Stage file path
    stage_file = os.path.join(output_dir, "example_scene.usda")
    
    # Start the server as a subprocess
    server_process = None
    
    try:
        # Start the server process
        print("Starting server...")
        server_command = [
            sys.executable,
            "-m",
            "usd_mcp_server",
            "--protocol=stdio"
        ]
        server_process = subprocess.Popen(
            server_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Wait a bit for the server to start
        time.sleep(1)
        
        # Create client and connect
        print("Connecting to server...")
        client = UsdMcpClient("stdio", stdin=server_process.stdout, stdout=server_process.stdin)
        await client.connect()
        print("Connected!")
        
        # Step 1: Create a new stage
        print("\n1. Creating a new stage...")
        stage_result = await call_and_print(client, "create_new_stage", {
            "file_path": stage_file,
            "template": "basic",
            "up_axis": "Y"
        })
        stage_id = stage_result["data"]["stage_id"]
        
        # Step 2: Add a cube
        print("\n2. Adding a cube...")
        await call_and_print(client, "define_stage_prim", {
            "stage_id": stage_id,
            "prim_path": "/World/Cube",
            "prim_type": "Cube"
        })
        
        # Step 3: Set up physics
        print("\n3. Setting up physics...")
        # Create a physics scene
        await call_and_print(client, "setup_physics_scene", {
            "stage_id": stage_id,
            "scene_path": "/World/PhysicsScene"
        })
        
        # Make the cube a rigid body
        await call_and_print(client, "add_rigid_body", {
            "stage_id": stage_id,
            "prim_path": "/World/Cube",
            "mass": 1.0,
            "dynamic": True,
            "initial_velocity": [0, 0, 0]
        })
        
        # Add collision to the cube
        await call_and_print(client, "add_collision", {
            "stage_id": stage_id,
            "prim_path": "/World/Cube",
            "collision_type": "box",
            "dimensions": [1.0, 1.0, 1.0]
        })

        # Step 4: Create a material and apply it
        print("\n4. Creating and applying a material...")
        # Create a red material
        await call_and_print(client, "create_material", {
            "stage_id": stage_id,
            "material_path": "/World/Materials/RedMaterial",
            "diffuse_color": [1.0, 0.0, 0.0],
            "metallic": 0.1,
            "roughness": 0.3
        })
        
        # Assign the material to the cube
        await call_and_print(client, "assign_material", {
            "stage_id": stage_id,
            "prim_path": "/World/Cube",
            "material_path": "/World/Materials/RedMaterial"
        })
        
        # Step 5: Create an animation
        print("\n5. Creating an animation...")
        # Create a simple translation animation
        translate_keyframes = [
            {"time": 0, "value": [0, 0, 0]},
            {"time": 24, "value": [5, 0, 0]},
            {"time": 48, "value": [0, 0, 0]}
        ]
        
        await call_and_print(client, "create_transform_animation", {
            "stage_id": stage_id,
            "prim_path": "/World/Cube",
            "translate_keyframes": translate_keyframes,
            "time_range": [0, 48]
        })
        
        # Step 6: Visualize the scene graph
        print("\n6. Visualizing the scene graph...")
        viz_result = await call_and_print(client, "visualize_scene_graph", {
            "stage_id": stage_id,
            "format": "text"
        })
        
        # Save the visualization to a file
        viz_file = os.path.join(output_dir, "scene_graph.txt")
        with open(viz_file, "w") as f:
            f.write(viz_result["data"]["visualization"])
        print(f"Scene graph visualization saved to: {viz_file}")
        
        # Step 7: Save the stage
        print("\n7. Saving the stage...")
        await call_and_print(client, "save_usd_stage", {
            "stage_id": stage_id
        })
        
        print(f"\nExample completed successfully! Stage saved to: {stage_file}")
        print("You can open this USD file in an Omniverse application or USD viewer.")
        
    finally:
        # Clean up
        print("\nCleaning up...")
        if server_process:
            server_process.terminate()
            server_process.wait()
            print("Server process terminated.")

if __name__ == "__main__":
    asyncio.run(run_example()) 