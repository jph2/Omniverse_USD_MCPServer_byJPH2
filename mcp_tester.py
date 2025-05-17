#!/usr/bin/env python
"""
MCP Tester - A simple command-line tool to test and debug Omniverse_USD_MCPServer_byJPH2
"""

import asyncio
import argparse
import json
import logging
import os
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("mcp_tester.log")
    ]
)
logger = logging.getLogger(__name__)

async def test_server(server_command, server_args):
    """Connect to and test an MCP server"""
    print(f"Connecting to MCP server: {server_command} {' '.join(server_args)}")
    
    # Connect to the server
    server_params = StdioServerParameters(
        command=server_command,
        args=server_args,
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            print("✓ Connected to server")
            
            # Test server info
            server_info = session.server_info
            print("\nServer Information:")
            print(f"  Name: {server_info.name}")
            print(f"  Version: {server_info.version}")
            
            # Test capabilities
            capabilities = session.server_capabilities
            print("\nServer Capabilities:")
            for capability, value in capabilities.__dict__.items():
                if value is not None:
                    print(f"  {capability}: {value}")
            
            # List tools
            tools = await session.list_tools()
            print(f"\nTools ({len(tools.tools)}):")
            for tool in tools.tools:
                print(f"  • {tool.name}: {tool.description}")
                if hasattr(tool, "input_schema") and tool.input_schema:
                    try:
                        schema = json.loads(tool.input_schema)
                        if "properties" in schema:
                            print("    Parameters:")
                            for param, info in schema["properties"].items():
                                param_type = info.get("type", "any")
                                description = info.get("description", "")
                                print(f"      - {param} ({param_type}): {description}")
                    except (json.JSONDecodeError, AttributeError):
                        pass
            
            # List resources
            resources = await session.list_resources()
            print(f"\nResources ({len(resources.resources)}):")
            for resource in resources.resources:
                print(f"  • {resource.uri}")
                if hasattr(resource, "description") and resource.description:
                    print(f"    {resource.description}")
            
            # List prompts if supported
            try:
                prompts = await session.list_prompts()
                print(f"\nPrompts ({len(prompts.prompts)}):")
                for prompt in prompts.prompts:
                    print(f"  • {prompt.name}: {prompt.description}")
                    if prompt.arguments:
                        print("    Arguments:")
                        for arg in prompt.arguments:
                            required = "required" if arg.required else "optional"
                            print(f"      - {arg.name} ({required}): {arg.description}")
            except Exception:
                print("\nPrompts: Not supported by this server")

            # Test USD stage operations
            test_dir = "test_output"
            os.makedirs(test_dir, exist_ok=True)
            
            print("\n--- Testing USD stage operations ---")
            
            # Test create_stage
            test_file = os.path.join(test_dir, "test_stage.usda")
            print(f"\nCreating stage at {test_file}...")
            result = await session.call_tool("create_stage", {"file_path": test_file})
            
            try:
                response = json.loads(result.content)
                if response.get("ok", False):
                    print(f"  SUCCESS: {response.get('message', '')}")
                else:
                    print(f"  FAILED: {response.get('message', '')}")
            except json.JSONDecodeError:
                print(f"  Response: {result.content}")
            
            # Test create_mesh
            print("\nCreating cube mesh...")
            points = [
                (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)
            ]
            face_vertex_counts = [4, 4, 4, 4, 4, 4]  # 6 faces, 4 vertices each
            face_vertex_indices = [
                0, 1, 2, 3,  # bottom
                4, 5, 6, 7,  # top
                0, 1, 5, 4,  # front
                1, 2, 6, 5,  # right
                2, 3, 7, 6,  # back
                3, 0, 4, 7   # left
            ]
            
            mesh_result = await session.call_tool("create_mesh", {
                "file_path": test_file,
                "prim_path": "/root/test_cube",
                "points": points,
                "face_vertex_counts": face_vertex_counts,
                "face_vertex_indices": face_vertex_indices
            })
            
            try:
                response = json.loads(mesh_result.content)
                if response.get("ok", False):
                    print(f"  SUCCESS: {response.get('message', '')}")
                else:
                    print(f"  FAILED: {response.get('message', '')}")
            except json.JSONDecodeError:
                print(f"  Response: {mesh_result.content}")
            
            # Test analyze_stage
            print("\nAnalyzing stage...")
            analyze_result = await session.call_tool("analyze_stage", {"file_path": test_file})
            
            try:
                response = json.loads(analyze_result.content)
                if response.get("ok", False):
                    data = response.get("data", {})
                    print(f"  SUCCESS: Analysis returned {len(data.get('prims', []))} prims")
                    print(f"  Default prim: {data.get('default_prim', 'None')}")
                    print(f"  Up axis: {data.get('up_axis', 'Unknown')}")
                else:
                    print(f"  FAILED: {response.get('message', '')}")
            except json.JSONDecodeError:
                print(f"  Response: {analyze_result.content[:150]}...")
            
            # Test close_stage
            print("\nClosing stage...")
            close_result = await session.call_tool("close_stage", {"file_path": test_file})
            
            try:
                response = json.loads(close_result.content)
                if response.get("ok", False):
                    print(f"  SUCCESS: {response.get('message', '')}")
                else:
                    print(f"  FAILED: {response.get('message', '')}")
            except json.JSONDecodeError:
                print(f"  Response: {close_result.content}")
            
            print("\nServer test completed successfully!")

def main():
    parser = argparse.ArgumentParser(description='Test the Omniverse_USD_MCPServer_byJPH2')
    parser.add_argument('--command', default='python', help='Server command (default: python)')
    parser.add_argument('--args', nargs='*', default=['usd_mcp_server.py'], help='Server arguments')
    parser.add_argument('--host', default='127.0.0.1', help='Server host (for HTTP tests)')
    parser.add_argument('--port', type=int, default=5000, help='Server port (for HTTP tests)')
    parser.add_argument('--protocol', default='stdio', choices=['stdio', 'http', 'zmq'], 
                       help='Protocol to test (default: stdio)')
    
    args = parser.parse_args()
    
    # Adjust server args based on protocol if needed
    if args.protocol != 'stdio' and '--protocol' not in ' '.join(args.args):
        args.args.extend(['--protocol', args.protocol])
        if '--host' not in ' '.join(args.args):
            args.args.extend(['--host', args.host])
        if '--port' not in ' '.join(args.args):
            args.args.extend(['--port', str(args.port)])
    
    try:
        asyncio.run(test_server(args.command, args.args))
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        logger.exception("Error during testing")
        print(f"\nError during test: {e}")

if __name__ == "__main__":
    main() 