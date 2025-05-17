#!/usr/bin/env python
"""
MCP Tester - A simple command-line tool to test and debug Omniverse_USD_MCPServer_byJPH2
"""

import asyncio
import argparse
import json
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

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
            
            print("\nServer test completed successfully!")

def main():
    parser = argparse.ArgumentParser(description='Test the Omniverse_USD_MCPServer_byJPH2')
    parser.add_argument('--command', default='python', help='Server command (default: python)')
    parser.add_argument('--args', nargs='*', default=['usd_mcp_server.py'], help='Server arguments')
    
    args = parser.parse_args()
    
    asyncio.run(test_server(args.command, args.args))

if __name__ == "__main__":
    main() 