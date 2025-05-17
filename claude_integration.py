#!/usr/bin/env python3
"""
Omniverse USD MCP Server - Claude Integration

This module provides integration between the Omniverse USD MCP Server and Claude.
It enables using Anthropic's API to create and manipulate USD scenes using natural
language through Claude.

Usage:
1. Run the USD MCP Server: python usd_mcp_server.py --host 0.0.0.0 --port 5000
2. Set your Anthropic API key below
3. Run this script: python claude_integration.py
4. Enter USD creation/manipulation prompts when prompted
"""

import requests
import json
import os
import argparse
import sys
import logging
import anthropic
from typing import Dict, Any, List, Optional, Union, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("claude_integration.log")
    ]
)
logger = logging.getLogger(__name__)

# Configuration
ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_API_KEY"  # Replace with your actual API key
MCP_SERVER_URL = "http://localhost:5000"  # Default MCP server URL

# Tool schemas for Claude
usd_tools = [
    {
        "name": "create_stage",
        "description": "Create a new USD stage at the specified file path",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path where the USD stage should be saved"
                },
                "template": {
                    "type": "string",
                    "enum": ["empty", "basic", "full"],
                    "description": "Template to use for the stage"
                },
                "up_axis": {
                    "type": "string",
                    "enum": ["Y", "Z"],
                    "description": "Up axis for the stage"
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "analyze_stage",
        "description": "Get detailed information about a USD stage and its contents",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the USD stage file to analyze"
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "create_primitive",
        "description": "Create a geometric primitive (cube, sphere, cylinder, cone) in a USD stage",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the USD stage file"
                },
                "prim_type": {
                    "type": "string",
                    "enum": ["cube", "sphere", "cylinder", "cone"],
                    "description": "Type of primitive to create"
                },
                "prim_path": {
                    "type": "string",
                    "description": "Path for the primitive in the USD hierarchy (e.g., /World/Cube)"
                },
                "size": {
                    "type": "number",
                    "description": "Size or radius of the primitive"
                },
                "position": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Position of the primitive as [x, y, z]"
                }
            },
            "required": ["file_path", "prim_type", "prim_path"]
        }
    },
    {
        "name": "create_material",
        "description": "Create a PBR material in a USD stage",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the USD stage file"
                },
                "material_path": {
                    "type": "string",
                    "description": "Path for the material in the USD hierarchy (e.g., /World/Materials/Red)"
                },
                "diffuse_color": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "RGB color values as [r, g, b] with values from 0.0 to 1.0"
                },
                "metallic": {
                    "type": "number",
                    "description": "Metallic property from 0.0 (non-metallic) to 1.0 (metallic)"
                },
                "roughness": {
                    "type": "number",
                    "description": "Roughness property from 0.0 (smooth) to 1.0 (rough)"
                }
            },
            "required": ["file_path", "material_path"]
        }
    },
    {
        "name": "bind_material",
        "description": "Bind a material to a primitive in a USD stage",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the USD stage file"
                },
                "prim_path": {
                    "type": "string",
                    "description": "Path to the primitive in the USD hierarchy"
                },
                "material_path": {
                    "type": "string",
                    "description": "Path to the material in the USD hierarchy"
                }
            },
            "required": ["file_path", "prim_path", "material_path"]
        }
    },
    {
        "name": "set_transform",
        "description": "Set transformation properties (translation, rotation, scale) for a primitive",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the USD stage file"
                },
                "prim_path": {
                    "type": "string",
                    "description": "Path to the primitive in the USD hierarchy"
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
            "required": ["file_path", "prim_path"]
        }
    },
    {
        "name": "setup_physics_scene",
        "description": "Create a physics scene in a USD stage",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the USD stage file"
                },
                "gravity": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Gravity vector as [x, y, z], typically [0, -9.81, 0]"
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "add_rigid_body",
        "description": "Add rigid body physics to a primitive",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the USD stage file"
                },
                "prim_path": {
                    "type": "string",
                    "description": "Path to the primitive in the USD hierarchy"
                },
                "mass": {
                    "type": "number",
                    "description": "Mass of the rigid body in kg"
                },
                "is_dynamic": {
                    "type": "boolean",
                    "description": "Whether the body is dynamic (true) or kinematic (false)"
                }
            },
            "required": ["file_path", "prim_path"]
        }
    },
    {
        "name": "export_to_format",
        "description": "Export a USD stage to a different format (usda, usdc, usdz)",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the source USD stage file"
                },
                "output_path": {
                    "type": "string",
                    "description": "Path where the converted file should be saved"
                },
                "format": {
                    "type": "string",
                    "enum": ["usda", "usdc", "usdz"],
                    "description": "Output format for the USD stage"
                }
            },
            "required": ["file_path", "output_path"]
        }
    }
]


class ClaudeUsdMcpClient:
    """Client for integrating Claude with the USD MCP Server"""
    
    def __init__(self, anthropic_api_key: str, mcp_server_url: str):
        """Initialize the client
        
        Args:
            anthropic_api_key: Anthropic API key
            mcp_server_url: URL of the MCP server
        """
        self.anthropic_api_key = anthropic_api_key
        self.mcp_server_url = mcp_server_url
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        
        # Chat history for maintaining context
        self.messages = []
        self.system_prompt = """You are an expert in Universal Scene Description (USD) and 3D graphics.
You have access to an Omniverse USD MCP Server that provides tools for creating and manipulating USD scenes.
Your role is to help users create and manipulate 3D content using USD.

When a user asks about creating or modifying USD scenes, you should use the appropriate tools.
You have tools for:
- Creating USD stages
- Adding geometry like cubes, spheres, cylinders, and cones
- Creating and binding materials
- Setting up physics simulations
- Creating animations
- Analyzing USD scenes
- Converting USD to different formats (usda, usdc, usdz)

When you use a tool, think step by step:
1. Understand what the user is asking for
2. Determine which tool is appropriate
3. Call the tool with the necessary parameters
4. Explain the results to the user in a clear, conversational way

Always maintain a helpful, supportive tone and provide explanations that help users understand USD concepts.
"""
    
    def call_mcp_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool and return the result
        
        Args:
            tool_name: Name of the tool to call
            parameters: Parameters for the tool
            
        Returns:
            Tool response
        """
        try:
            url = f"{self.mcp_server_url}/{tool_name}"
            response = requests.post(url, json=parameters)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {str(e)}")
            return {"ok": False, "message": f"Error calling tool {tool_name}: {str(e)}"}
    
    def process_user_query(self, user_query: str) -> str:
        """Process a user query through Claude and the MCP server
        
        Args:
            user_query: Natural language query about USD operations
            
        Returns:
            Response from Claude after processing the query
        """
        # Add user message to history
        self.messages.append({"role": "user", "content": user_query})
        
        try:
            # Get Claude's response with tools
            response = self.client.messages.create(
                model="claude-3-opus-20240229",  # or use "claude-3-sonnet-20240229" for a more economical option
                system=self.system_prompt,
                messages=self.messages,
                tools=usd_tools,
                max_tokens=2000,
                temperature=0.0
            )
            
            # Extract the response content and tool calls
            message = response.content
            tool_calls = []
            
            # Process each message part
            for content in message:
                if content.type == "text":
                    # Store the text response
                    text_response = content.text
                elif content.type == "tool_use":
                    # Store the tool call
                    tool_calls.append({
                        "name": content.name,
                        "input": content.input
                    })
            
            # Process any tool calls
            tool_outputs = []
            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_input = tool_call["input"]
                
                logger.info(f"Claude selected tool: {tool_name}")
                logger.info(f"With input: {tool_input}")
                
                # Call the MCP server
                result = self.call_mcp_tool(tool_name, tool_input)
                tool_outputs.append({
                    "tool_call_id": tool_name,
                    "output": json.dumps(result)
                })
            
            # If there were tool calls, send the outputs back to Claude
            if tool_outputs:
                self.messages.append({
                    "role": "assistant",
                    "content": [{"type": "tool_use", "name": tc["name"], "input": tc["input"]} for tc in tool_calls]
                })
                
                self.messages.append({
                    "role": "user", 
                    "content": [{"type": "tool_result", "tool_call_id": to["tool_call_id"], "content": to["output"]} for to in tool_outputs]
                })
                
                # Get Claude's final response after tool results
                final_response = self.client.messages.create(
                    model="claude-3-opus-20240229",  # or use "claude-3-sonnet-20240229"
                    system=self.system_prompt,
                    messages=self.messages,
                    max_tokens=2000,
                    temperature=0.0
                )
                
                # Extract the final text response
                final_text = ""
                for content in final_response.content:
                    if content.type == "text":
                        final_text += content.text
                
                # Add the assistant's response to messages
                self.messages.append({"role": "assistant", "content": final_text})
                return final_text
            else:
                # No tool calls, just return the original text response
                self.messages.append({"role": "assistant", "content": text_response})
                return text_response
                
        except Exception as e:
            logger.error(f"Error processing query with Anthropic API: {str(e)}")
            return f"Error processing your query: {str(e)}"
    
    def interactive_session(self):
        """Start an interactive session with the user"""
        print("\nOmniverse USD MCP Claude Integration")
        print("====================================")
        print("Type your USD-related questions or commands. Type 'exit' to quit.\n")
        
        while True:
            user_input = input("\nYou: ")
            
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break
            
            print("\nProcessing...")
            response = self.process_user_query(user_input)
            print(f"\nClaude: {response}")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Claude integration for Omniverse USD MCP Server")
    parser.add_argument("--server", default="http://localhost:5000", help="MCP server URL")
    parser.add_argument("--api-key", default=ANTHROPIC_API_KEY, help="Anthropic API key")
    return parser.parse_args()


def main():
    """Main function"""
    args = parse_arguments()
    
    if args.api_key == "YOUR_ANTHROPIC_API_KEY":
        print("Please set your Anthropic API key in the script or provide it with --api-key")
        return
    
    # Check if the MCP server is accessible
    try:
        response = requests.get(f"{args.server}/get_server_status")
        if response.status_code != 200:
            print(f"Error: MCP server not responding properly at {args.server}")
            return
    except Exception as e:
        print(f"Error connecting to MCP server at {args.server}: {str(e)}")
        print("Please make sure the server is running with: python usd_mcp_server.py --host 0.0.0.0 --port 5000")
        return
    
    # Create the Claude client and start interactive session
    client = ClaudeUsdMcpClient(args.api_key, args.server)
    client.interactive_session()


if __name__ == "__main__":
    main() 