#!/usr/bin/env python3
"""
Omniverse_USD_MCPServer_byJPH2 Client

This module provides a client for the Model Context Protocol (MCP) server that offers
tools and resources for working with Universal Scene Description (USD) and NVIDIA Omniverse.

This client demonstrates how to:
- Connect to the MCP server
- List available tools and resources
- Create and manipulate USD stages and prims
- Access documentation and development guides
"""

import asyncio
import os
import argparse
import sys
from typing import List, Dict, Any, Optional
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
import json

class UsdMcpClient:
    """A client for the Omniverse_USD_MCPServer_byJPH2"""
    
    def __init__(self, command: str, args: List[str], env: Optional[Dict[str, str]] = None):
        """Initialize the client with server connection parameters
        
        Args:
            command: Command to start the server
            args: Arguments for the server command
            env: Environment variables for the server process
        """
        self.server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env
        )
        self.session = None
    
    async def connect(self):
        """Connect to the MCP server"""
        self.stdio, self.write = await stdio_client(self.server_params)
        self.session = await ClientSession(self.stdio, self.write)
        await self.session.initialize()
        return self.session
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self.session:
            # The session will be closed by the context manager
            self.session = None
    
    async def list_capabilities(self):
        """List the server's capabilities"""
        if not self.session:
            raise ValueError("Not connected to server")
        
        server_info = self.session.server_info
        server_capabilities = self.session.server_capabilities
        
        print("\nServer Information:")
        print(f"  Name: {server_info.name}")
        print(f"  Version: {server_info.version}")
        
        print("\nServer Capabilities:")
        for capability, value in server_capabilities.__dict__.items():
            if value is not None:
                print(f"  {capability}: {value}")
    
    async def list_tools(self):
        """List available tools from the server"""
        if not self.session:
            raise ValueError("Not connected to server")
        
        tools = await self.session.list_tools()
        print("\nAvailable Tools:")
        for tool in tools.tools:
            print(f"- {tool.name}: {tool.description}")
    
    async def list_resources(self):
        """List available resources from the server"""
        if not self.session:
            raise ValueError("Not connected to server")
        
        resources = await self.session.list_resources()
        print("\nAvailable Resources:")
        for resource in resources.resources:
            print(f"- {resource.uri}")
    
    async def create_test_stage(self, file_path: str):
        """Create a test USD stage
        
        Args:
            file_path: Path where the stage should be saved
        """
        if not self.session:
            raise ValueError("Not connected to server")
        
        print(f"\n--- Creating a test USD stage at {file_path} ---")
        create_result = await self.session.call_tool("create_stage", {"file_path": file_path})
        print(create_result.content)
        return create_result.content
    
    async def create_cube_mesh(self, file_path: str, prim_path: str = "/root/cube"):
        """Create a simple cube mesh in a USD stage
        
        Args:
            file_path: Path to the USD file
            prim_path: Path within the stage to create the mesh
        """
        if not self.session:
            raise ValueError("Not connected to server")
        
        print(f"\n--- Creating a cube mesh at {prim_path} ---")
        
        # Define a simple cube
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
        
        mesh_result = await self.session.call_tool("create_mesh", {
            "file_path": file_path,
            "prim_path": prim_path,
            "points": points,
            "face_vertex_counts": face_vertex_counts,
            "face_vertex_indices": face_vertex_indices
        })
        print(mesh_result.content)
        return mesh_result.content
    
    async def analyze_stage(self, file_path: str):
        """Analyze a USD stage and print information about its contents
        
        Args:
            file_path: Path to the USD file to analyze
        """
        if not self.session:
            raise ValueError("Not connected to server")
        
        print(f"\n--- Analyzing stage {file_path} ---")
        analyze_result = await self.session.call_tool("analyze_stage", {"file_path": file_path})
        
        # Pretty-print the JSON result
        try:
            stage_info = json.loads(analyze_result.content)
            print(json.dumps(stage_info, indent=2))
        except:
            print(analyze_result.content)
        
        return analyze_result.content
    
    async def get_usd_schema(self):
        """Get information about common USD schema types"""
        if not self.session:
            raise ValueError("Not connected to server")
        
        print("\n--- Fetching USD schema information ---")
        schema_info, _ = await self.session.read_resource("usd://schema")
        
        # Pretty-print the JSON result
        try:
            schema_dict = json.loads(schema_info)
            print(json.dumps(schema_dict, indent=2))
        except:
            print(schema_info)
        
        return schema_info
    
    async def get_omniverse_help(self):
        """Get help information about Omniverse Kit and USD integration"""
        if not self.session:
            raise ValueError("Not connected to server")
        
        print("\n--- Getting Omniverse help ---")
        omni_help, _ = await self.session.read_resource("omniverse://help")
        print(omni_help)
        return omni_help
    
    async def get_development_guide(self, preview_chars: int = 500):
        """Get the Comprehensive Omniverse Development Guide
        
        Args:
            preview_chars: Number of characters to preview (0 for all)
        """
        if not self.session:
            raise ValueError("Not connected to server")
        
        print("\n--- Accessing Omniverse Development Guide ---")
        guide, _ = await self.session.read_resource("omniverse://development-guide")
        
        if preview_chars > 0 and len(guide) > preview_chars:
            print(f"First {preview_chars} characters:")
            print(guide[:preview_chars] + "...\n")
            print(f"(Full guide is {len(guide)} characters)")
        else:
            print(guide)
        
        return guide
    
    async def search_guide(self, topics: List[str]):
        """Search the Omniverse Development Guide for specific topics
        
        Args:
            topics: List of topics to search for
        """
        if not self.session:
            raise ValueError("Not connected to server")
        
        print("\n--- Searching Omniverse Guide ---")
        for topic in topics:
            print(f"\nSearching for '{topic}':")
            search_result = await self.session.call_tool("search_omniverse_guide", {"topic": topic})
            
            # Limit result size for display
            content = search_result.content
            if len(content) > 300:
                result_preview = content[:300] + "..."
                print(result_preview)
                print(f"(Full result is {len(content)} characters)")
            else:
                print(content)

async def run_demo():
    """Run the full client demo"""
    print("Starting Omniverse_USD_MCPServer_byJPH2 Client...")
    
    # Create client
    client = UsdMcpClient(
        command="python",
        args=["usd_mcp_server.py"],
        env=None
    )
    
    try:
        # Connect to the server
        async with stdio_client(client.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                client.session = session
                
                # Initialize the session
                await session.initialize()
                print("✓ Connected to server")
                
                # List server capabilities
                await client.list_capabilities()
                
                # List available tools and resources
                await client.list_tools()
                await client.list_resources()
                
                # Create a test stage
                test_stage_path = os.path.abspath("test_stage.usda")
                await client.create_test_stage(test_stage_path)
                
                # Create a cube mesh
                await client.create_cube_mesh(test_stage_path)
                
                # Analyze the stage
                await client.analyze_stage(test_stage_path)
                
                # Get USD schema information
                await client.get_usd_schema()
                
                # Get Omniverse help
                await client.get_omniverse_help()
                
                # Access the development guide
                await client.get_development_guide()
                
                # Search the guide for topics
                await client.search_guide(["extensions", "materials", "performance"])
                
                print("\nOmniverse_USD_MCPServer_byJPH2 Client completed successfully.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description='Omniverse_USD_MCPServer_byJPH2 Client')
    parser.add_argument('--server-cmd', default='python',
                        help='Server command (default: python)')
    parser.add_argument('--server-args', nargs='+', default=['usd_mcp_server.py'],
                        help='Server arguments (default: usd_mcp_server.py)')
    return parser.parse_args()

if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_arguments()
    
    # Run the demo
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\nClient stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 