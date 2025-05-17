#!/usr/bin/env python3
"""
Claude Integration for Omniverse USD MCP Server

This script provides a command-line interface for interacting with the
Omniverse USD MCP Server through Claude's tool use capabilities.
"""

import argparse
import json
import os
import sys
import requests
import anthropic
from typing import Dict, Any, List

# Configuration
DEFAULT_MCP_URL = "http://127.0.0.1:5000"

# Define tools for Claude tool use
MCP_TOOLS = [
    {
        "name": "open_stage",
        "description": "Open or create a USD stage.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path where the USD stage should be created or opened"
                },
                "create_if_missing": {
                    "type": "boolean",
                    "description": "Whether to create a new stage if it doesn't exist"
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "close_stage_by_id",
        "description": "Close an open USD stage to free resources.",
        "input_schema": {
            "type": "object",
            "properties": {
                "stage_id": {
                    "type": "string",
                    "description": "ID of the stage to close"
                },
                "save_if_modified": {
                    "type": "boolean",
                    "description": "Whether to save the stage if it has been modified"
                }
            },
            "required": ["stage_id"]
        }
    },
    {
        "name": "define_prim_by_id",
        "description": "Define a new prim of the specified type at the given path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "stage_id": {
                    "type": "string",
                    "description": "ID of the stage"
                },
                "path": {
                    "type": "string",
                    "description": "Path where the new prim should be created"
                },
                "type": {
                    "type": "string",
                    "description": "Type of the prim (e.g., Xform, Mesh, Material)"
                }
            },
            "required": ["stage_id", "path", "type"]
        }
    },
    {
        "name": "create_primitive_by_id",
        "description": "Create a geometric primitive (sphere, cube, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "stage_id": {
                    "type": "string",
                    "description": "ID of the stage"
                },
                "prim_type": {
                    "type": "string",
                    "description": "Type of primitive (sphere, cube, cylinder, cone)",
                    "enum": ["sphere", "cube", "cylinder", "cone"]
                },
                "prim_path": {
                    "type": "string",
                    "description": "Path where the primitive should be created"
                },
                "size": {
                    "type": "number",
                    "description": "Size of the primitive"
                },
                "position": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Position [x, y, z]"
                }
            },
            "required": ["stage_id", "prim_type", "prim_path"]
        }
    },
    {
        "name": "create_material_by_id",
        "description": "Create a PBR material.",
        "input_schema": {
            "type": "object",
            "properties": {
                "stage_id": {
                    "type": "string",
                    "description": "ID of the stage"
                },
                "material_path": {
                    "type": "string",
                    "description": "Path where the material should be created"
                },
                "diffuse_color": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "RGB color as [r, g, b] with values from 0-1"
                },
                "metallic": {
                    "type": "number",
                    "description": "Metallic value (0-1)"
                },
                "roughness": {
                    "type": "number",
                    "description": "Roughness value (0-1)"
                }
            },
            "required": ["stage_id", "material_path"]
        }
    },
    {
        "name": "bind_material_by_id",
        "description": "Bind a material to a prim.",
        "input_schema": {
            "type": "object",
            "properties": {
                "stage_id": {
                    "type": "string",
                    "description": "ID of the stage"
                },
                "material_path": {
                    "type": "string",
                    "description": "Path to the material"
                },
                "prim_path": {
                    "type": "string",
                    "description": "Path to the prim that should receive the material"
                }
            },
            "required": ["stage_id", "material_path", "prim_path"]
        }
    },
    {
        "name": "visualize_scene_graph_by_id",
        "description": "Generate a visualization of the USD scene graph.",
        "input_schema": {
            "type": "object",
            "properties": {
                "stage_id": {
                    "type": "string",
                    "description": "ID of the stage"
                },
                "output_format": {
                    "type": "string",
                    "description": "Output format (text, html, json, network)",
                    "enum": ["text", "html", "json", "network"]
                },
                "output_path": {
                    "type": "string",
                    "description": "Path to save the output (required for non-text formats)"
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum depth to display"
                },
                "filter_type": {
                    "type": "string",
                    "description": "Filter to show only prims of a specific type"
                },
                "theme": {
                    "type": "string",
                    "description": "Visual theme (light, dark, contrast)",
                    "enum": ["light", "dark", "contrast"]
                }
            },
            "required": ["stage_id"]
        }
    },
    {
        "name": "set_transform_by_id",
        "description": "Set transform properties of a prim.",
        "input_schema": {
            "type": "object",
            "properties": {
                "stage_id": {
                    "type": "string",
                    "description": "ID of the stage"
                },
                "prim_path": {
                    "type": "string",
                    "description": "Path to the prim"
                },
                "translate": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Translation values as [x, y, z]"
                },
                "rotate": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Rotation values in degrees as [x, y, z]"
                },
                "scale": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Scale values as [x, y, z]"
                },
                "time_code": {
                    "type": "number",
                    "description": "Time code for animation (optional)"
                }
            },
            "required": ["stage_id", "prim_path"]
        }
    },
    {
        "name": "analyze_stage_by_id",
        "description": "Analyze a USD stage and return information about its contents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "stage_id": {
                    "type": "string",
                    "description": "ID of the stage to analyze"
                },
                "include_attributes": {
                    "type": "boolean",
                    "description": "Whether to include detailed attribute information"
                }
            },
            "required": ["stage_id"]
        }
    }
]

class ClaudeMcpClient:
    """Client for calling MCP server through Claude's tool use."""
    
    def __init__(self, mcp_url: str, api_key: str):
        """
        Initialize the Claude MCP client.
        
        Args:
            mcp_url: URL of the MCP server
            api_key: Anthropic API key
        """
        self.mcp_url = mcp_url
        self.client = anthropic.Anthropic(api_key=api_key)
        self.conversation_history = []
        
        # Add introduction to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": (
                "You are an AI assistant specialized in Omniverse USD development. "
                "You can help create and modify USD scenes through the Omniverse USD MCP Server. "
                "You have access to tools for creating stages, primitives, materials, physics, "
                "and animations in USD format. Please confirm your understanding."
            )
        })
        
        # Get initial response from Claude
        initial_response = self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            messages=self.conversation_history
        )
        
        # Add Claude's response to conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": initial_response.content[0].text
        })
    
    def call_mcp_server(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP server endpoint.
        
        Args:
            tool_name: Name of the tool to call
            params: Parameters to send to the tool
            
        Returns:
            The server response
        """
        try:
            response = requests.post(f"{self.mcp_url}/{tool_name}", json=params)
            response.raise_for_status()
            result = response.json()
            
            # Handle both new and legacy response formats
            if isinstance(result, dict) and "ok" in result:
                return result
            else:
                # Legacy format - wrap in standard format
                return {"ok": True, "data": result, "message": "Success"}
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Error calling MCP server: {str(e)}"
            print(f"ERROR: {error_msg}", file=sys.stderr)
            return {"ok": False, "message": error_msg}
    
    def process_user_message(self, user_message: str) -> str:
        """
        Process a user message using Claude's tool use.
        
        Args:
            user_message: User's message
            
        Returns:
            Assistant's response
        """
        # Add user message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Call Claude with tool definitions
        response = self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            tools=MCP_TOOLS,
            messages=self.conversation_history
        )
        
        # Check if Claude wants to use a tool
        if response.tool_use:
            tool_uses = response.tool_use
            tool_name = tool_uses.name
            tool_args = tool_uses.input
            
            try:
                # Print what tool Claude is using
                print(f"\n[Calling USD MCP tool: {tool_name}]\n")
                
                # Call the MCP server
                result = self.call_mcp_server(tool_name, tool_args)
                
                # Add Claude's response and tool result to conversation history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response.content[0].text
                })
                
                self.conversation_history.append({
                    "role": "user",
                    "content": f"Result of {tool_name}: {json.dumps(result)}"
                })
                
                # Get the final response from Claude
                second_response = self.client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1000,
                    messages=self.conversation_history
                )
                
                final_message = second_response.content[0].text
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_message
                })
                
                return final_message
            
            except Exception as e:
                error_msg = f"Error in tool execution: {str(e)}"
                print(f"ERROR: {error_msg}", file=sys.stderr)
                return f"I encountered an error while trying to help you: {error_msg}"
        
        else:
            # No tool use, just return Claude's response
            self.conversation_history.append({
                "role": "assistant",
                "content": response.content[0].text
            })
            return response.content[0].text


def main():
    parser = argparse.ArgumentParser(description="Claude Integration for Omniverse USD MCP Server")
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL, help=f"URL of the MCP server (default: {DEFAULT_MCP_URL})")
    parser.add_argument("--api-key", help="Anthropic API key (or set ANTHROPIC_API_KEY environment variable)")
    args = parser.parse_args()
    
    # Get API key from args or environment
    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: Anthropic API key must be provided via --api-key or ANTHROPIC_API_KEY environment variable", file=sys.stderr)
        sys.exit(1)
    
    try:
        client = ClaudeMcpClient(args.mcp_url, api_key)
        
        print(f"Claude Integration for Omniverse USD MCP Server")
        print(f"MCP Server URL: {args.mcp_url}")
        print(f"Type 'exit' or 'quit' to end the session\n")
        
        while True:
            try:
                user_input = input("\nYou: ")
                if user_input.lower() in ("exit", "quit"):
                    break
                    
                if not user_input.strip():
                    continue
                    
                print("\nThinking...", end="", flush=True)
                assistant_response = client.process_user_message(user_input)
                print("\r" + " " * 10 + "\r", end="")  # Clear "Thinking..." message
                print(f"\nClaude: {assistant_response}")
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
                
            except Exception as e:
                print(f"\nERROR: {str(e)}", file=sys.stderr)
                
    except Exception as e:
        print(f"ERROR initializing Claude client: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 