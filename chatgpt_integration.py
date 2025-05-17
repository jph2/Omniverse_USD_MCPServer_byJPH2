#!/usr/bin/env python3
"""
Omniverse USD MCP Server - ChatGPT Integration

This module provides integration between the Omniverse USD MCP Server and ChatGPT.
It enables using OpenAI's function calling API to create and manipulate USD scenes
using natural language through ChatGPT.

Usage:
1. Run the USD MCP Server: python usd_mcp_server.py --host 0.0.0.0 --port 5000
2. Set your OpenAI API key below
3. Run this script: python chatgpt_integration.py
4. Enter USD creation/manipulation prompts when prompted
"""

import openai
import requests
import json
import os
import argparse
import sys
import logging
from typing import Dict, Any, List, Optional, Union, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("chatgpt_integration.log")
    ]
)
logger = logging.getLogger(__name__)

# Configuration
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"  # Replace with your actual API key
MCP_SERVER_URL = "http://localhost:5000"  # Default MCP server URL

# Available USD tools as function definitions for OpenAI
usd_functions = [
    {
        "name": "open_stage",
        "description": "Open an existing USD stage or create a new one, returning a unique stage ID",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the USD file to open or create"
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
        "description": "Close a USD stage by its ID and free resources",
        "parameters": {
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
        "name": "analyze_stage_by_id",
        "description": "Get detailed information about a USD stage and its contents",
        "parameters": {
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
    },
    {
        "name": "create_primitive_by_id",
        "description": "Create a geometric primitive (cube, sphere, cylinder, cone) in a USD stage",
        "parameters": {
            "type": "object",
            "properties": {
                "stage_id": {
                    "type": "string",
                    "description": "ID of the stage"
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
            "required": ["stage_id", "prim_type", "prim_path"]
        }
    },
    {
        "name": "create_material_by_id",
        "description": "Create a PBR material in a USD stage",
        "parameters": {
            "type": "object",
            "properties": {
                "stage_id": {
                    "type": "string",
                    "description": "ID of the stage"
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
            "required": ["stage_id", "material_path"]
        }
    },
    {
        "name": "bind_material_by_id",
        "description": "Bind a material to a primitive in a USD stage",
        "parameters": {
            "type": "object",
            "properties": {
                "stage_id": {
                    "type": "string",
                    "description": "ID of the stage"
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
            "required": ["stage_id", "prim_path", "material_path"]
        }
    },
    {
        "name": "set_transform_by_id",
        "description": "Set transformation properties (translation, rotation, scale) for a primitive",
        "parameters": {
            "type": "object",
            "properties": {
                "stage_id": {
                    "type": "string",
                    "description": "ID of the stage"
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
            "required": ["stage_id", "prim_path"]
        }
    },
    {
        "name": "setup_physics_scene_by_id",
        "description": "Create a physics scene in a USD stage",
        "parameters": {
            "type": "object",
            "properties": {
                "stage_id": {
                    "type": "string",
                    "description": "ID of the stage"
                },
                "gravity": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Gravity vector as [x, y, z], typically [0, -9.81, 0]"
                }
            },
            "required": ["stage_id"]
        }
    },
    {
        "name": "add_rigid_body_by_id",
        "description": "Add rigid body physics to a primitive",
        "parameters": {
            "type": "object",
            "properties": {
                "stage_id": {
                    "type": "string",
                    "description": "ID of the stage"
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
            "required": ["stage_id", "prim_path"]
        }
    },
    {
        "name": "visualize_scene_graph_by_id",
        "description": "Generate a visualization of the USD scene graph",
        "parameters": {
            "type": "object",
            "properties": {
                "stage_id": {
                    "type": "string",
                    "description": "ID of the stage to visualize"
                },
                "output_format": {
                    "type": "string",
                    "enum": ["text", "html", "json", "network"],
                    "description": "Output format for the visualization"
                },
                "output_path": {
                    "type": "string",
                    "description": "Path where the visualization file should be saved"
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum depth of the hierarchy to visualize"
                },
                "filter_type": {
                    "type": "string",
                    "description": "Filter to show only prims of a specific type"
                }
            },
            "required": ["stage_id"]
        }
    }
]


class ChatGptUsdMcpClient:
    """Client for integrating ChatGPT with the USD MCP Server"""
    
    def __init__(self, openai_api_key: str, mcp_server_url: str):
        """Initialize the client
        
        Args:
            openai_api_key: OpenAI API key
            mcp_server_url: URL of the MCP server
        """
        self.openai_api_key = openai_api_key
        self.mcp_server_url = mcp_server_url
        openai.api_key = openai_api_key
        
        # Chat history for maintaining context
        self.conversation_history = []
    
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
        """Process a user query through ChatGPT and the MCP server
        
        Args:
            user_query: Natural language query about USD operations
            
        Returns:
            Response from ChatGPT after processing the query
        """
        # Add user query to conversation history
        self.conversation_history.append({"role": "user", "content": user_query})
        
        # Get function call from ChatGPT
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",  # or "gpt-3.5-turbo" if preferred
                messages=self.conversation_history,
                functions=usd_functions,
                function_call="auto"
            )
            
            message = response.choices[0].message
            self.conversation_history.append(message)
            
            # Check if the model wants to call a function
            if message.get("function_call"):
                function_name = message["function_call"]["name"]
                arguments = json.loads(message["function_call"]["arguments"])
                
                logger.info(f"ChatGPT selected function: {function_name}")
                logger.info(f"With arguments: {arguments}")
                
                # Call the MCP server
                result = self.call_mcp_tool(function_name, arguments)
                
                # Add the function result to the conversation
                self.conversation_history.append({
                    "role": "function",
                    "name": function_name,
                    "content": json.dumps(result)
                })
                
                # Get ChatGPT's response to the function result
                second_response = openai.ChatCompletion.create(
                    model="gpt-4o",  # or "gpt-3.5-turbo" if preferred
                    messages=self.conversation_history
                )
                
                final_message = second_response.choices[0].message
                self.conversation_history.append(final_message)
                
                return final_message["content"]
            else:
                # No function call, just return the message content
                return message["content"]
                
        except Exception as e:
            logger.error(f"Error processing query with OpenAI: {str(e)}")
            return f"Error processing your query: {str(e)}"
    
    def interactive_session(self):
        """Start an interactive session with the user"""
        print("\nOmniverse USD MCP ChatGPT Integration")
        print("======================================")
        print("Type your USD-related questions or commands. Type 'exit' to quit.\n")
        
        while True:
            user_input = input("\nYou: ")
            
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break
            
            print("\nProcessing...")
            response = self.process_user_query(user_input)
            print(f"\nChatGPT: {response}")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="ChatGPT integration for Omniverse USD MCP Server")
    parser.add_argument("--server", default="http://localhost:5000", help="MCP server URL")
    parser.add_argument("--api-key", default=OPENAI_API_KEY, help="OpenAI API key")
    return parser.parse_args()


def main():
    """Main function"""
    args = parse_arguments()
    
    if args.api_key == "YOUR_OPENAI_API_KEY":
        print("Please set your OpenAI API key in the script or provide it with --api-key")
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
    
    # Create the ChatGPT client and start interactive session
    client = ChatGptUsdMcpClient(args.api_key, args.server)
    client.interactive_session()


if __name__ == "__main__":
    main() 