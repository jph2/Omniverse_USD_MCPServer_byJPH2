"""
Basic example of using the USD MCP Server.

This example demonstrates the basic functionality of the USD MCP Server:
1. Creating a new stage
2. Adding prims to the stage
3. Creating and applying a simple mesh
4. Examining the scene structure
5. Saving and cleaning up resources
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
            print(f"❌ Error: {result.get('error', '')}")
            print(f"  Message: {result.get('message', '')}")
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
        
        # Step 3: Create a simple mesh
        print("\n3. Creating a simple mesh...")
        # Define a simple pyramid mesh
        points = [
            [0, 0, 0],  # base point 1
            [1, 0, 0],  # base point 2
            [1, 1, 0],  # base point 3
            [0, 1, 0],  # base point 4
            [0.5, 0.5, 1]  # top point
        ]
        face_vertex_counts = [4, 3, 3, 3, 3]  # base (quad) + 4 triangular sides
        face_vertex_indices = [
            0, 1, 2, 3,  # base (counter-clockwise)
            0, 1, 4,     # side 1
            1, 2, 4,     # side 2
            2, 3, 4,     # side 3
            3, 0, 4      # side 4
        ]
        
        await call_and_print(client, "create_stage_mesh", {
            "stage_id": stage_id,
            "prim_path": "/World/Pyramid",
            "points": points,
            "face_vertex_counts": face_vertex_counts,
            "face_vertex_indices": face_vertex_indices
        })
        
        # Step 4: Examine the scene
        print("\n4. Listing prims in the scene...")
        await call_and_print(client, "list_stage_prims", {
            "stage_id": stage_id,
            "prim_path": "/World"
        })
        
        # Step 5: Analyze the stage
        print("\n5. Analyzing stage health...")
        await call_and_print(client, "get_health", {})
        
        # Step 6: Save the stage
        print("\n6. Saving the stage...")
        await call_and_print(client, "save_usd_stage", {
            "stage_id": stage_id
        })
        
        # Step 7: Close and cleanup
        print("\n7. Closing the stage and cleaning up...")
        await call_and_print(client, "close_stage", {
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