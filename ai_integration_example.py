#!/usr/bin/env python3
"""
Omniverse_USD_MCPServer_byJPH2 - AI Assistant Integration Example

This module demonstrates how to integrate the Omniverse_USD_MCPServer_byJPH2
with an AI assistant to create a natural language interface for USD operations.

The simulated AI assistant can:
- Create and manipulate USD stages
- Add 3D geometry to stages
- Analyze USD files
- Provide information about USD schema types
- Access the Omniverse Development Guide to provide guidance on development topics
"""

import asyncio
import os
import json
import argparse
import sys
import logging
from typing import Dict, Any, List, Optional, Tuple
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from pxr import Usd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("ai_integration.log")
    ]
)
logger = logging.getLogger(__name__)

class SimulatedAIAssistant:
    """Simulated AI assistant that processes queries and uses the MCP server tools.
    
    In a real implementation, you would connect to an actual LLM API like Claude or GPT.
    This simulation uses keyword matching to route queries to the appropriate MCP tools.
    """
    
    def __init__(self, mcp_session):
        """Initialize the AI assistant
        
        Args:
            mcp_session: An initialized MCP client session
        """
        self.session = mcp_session
        self.conversation_history = []
    
    def _add_to_history(self, role: str, content: str) -> None:
        """Add a message to the conversation history
        
        Args:
            role: Either 'user' or 'assistant'
            content: The message content
        """
        self.conversation_history.append({"role": role, "content": content})
    
    async def process_query(self, query: str) -> str:
        """Process a user query and return a response
        
        Args:
            query: The user's natural language query
            
        Returns:
            The assistant's response
        """
        print(f"User query: {query}")
        self._add_to_history("user", query)
        
        # Extract query keywords for routing
        query_lower = query.lower()
        
        # ====================================================================
        # USD Stage Operations
        # ====================================================================
        
        if "create" in query_lower and "stage" in query_lower:
            response = await self._handle_create_stage(query_lower)
        
        elif "add" in query_lower and any(shape in query_lower for shape in ["cube", "sphere", "mesh"]):
            response = await self._handle_add_geometry(query_lower)
        
        elif "analyze" in query_lower and ("stage" in query_lower or "file" in query_lower):
            response = await self._handle_analyze_stage(query_lower)
        
        # ====================================================================
        # Documentation and Help
        # ====================================================================
        
        elif "help" in query_lower and "omniverse" in query_lower:
            response = await self._handle_omniverse_help()
        
        elif "schema" in query_lower and "usd" in query_lower:
            response = await self._handle_usd_schema()
        
        # ====================================================================
        # Development Guide Queries
        # ====================================================================
        
        elif any(term in query_lower for term in ["development guide", "documentation", "developer", "how to"]):
            response = await self._handle_development_guide_query(query_lower)
        
        # Specific development topics
        elif any(term in query_lower for term in ["extension", "plugin"]):
            response = await self._handle_specific_topic("extension")
        
        elif any(term in query_lower for term in ["material", "shader", "rendering"]):
            response = await self._handle_specific_topic("material")
        
        elif any(term in query_lower for term in ["physics", "simulation", "rigid body"]):
            response = await self._handle_specific_topic("physics")
        
        elif any(term in query_lower for term in ["ui", "interface", "window"]):
            response = await self._handle_specific_topic("ui")
        
        elif any(term in query_lower for term in ["performance", "optimization", "speed"]):
            response = await self._handle_specific_topic("performance")
        
        elif any(term in query_lower for term in ["nucleus", "collaboration", "network"]):
            response = await self._handle_specific_topic("collaboration")
        
        # ====================================================================
        # Default Response
        # ====================================================================
        
        else:
            response = self._get_default_response()
        
        self._add_to_history("assistant", response)
        return response
    
    async def _handle_create_stage(self, query_lower: str) -> str:
        """Handle a request to create a USD stage
        
        Args:
            query_lower: Lowercase query string
            
        Returns:
            Response message
        """
        # Extract file path from query or use default
        file_path = "ai_created_stage.usda"
        if "save" in query_lower and "as" in query_lower:
            parts = query_lower.split("save as")
            if len(parts) > 1:
                potential_path = parts[1].strip().split()[0]
                if potential_path.endswith(".usd") or potential_path.endswith(".usda"):
                    file_path = potential_path
        
        # Use MCP tool to create stage
        result = await self.session.call_tool("create_stage", {"file_path": file_path})
        
        # Parse JSON response
        try:
            response = json.loads(result.content)
            if response.get("ok", False):
                return f"I've created a new USD stage at {file_path}. {response.get('message', '')}"
            else:
                return f"I wasn't able to create the stage: {response.get('message', 'Unknown error')}"
        except json.JSONDecodeError:
            # Fallback for non-JSON responses
            return f"I've created a new USD stage at {file_path}.\n\n{result.content}"
    
    async def _handle_add_geometry(self, query_lower: str) -> str:
        """Handle a request to add geometry to a USD stage
        
        Args:
            query_lower: Lowercase query string
            
        Returns:
            Response message
        """
        # Extract file path or use default
        file_path = "ai_created_stage.usda"
        if os.path.exists(file_path):
            # Default to a cube since it's the simplest shape
            shape_type = "cube"
            prim_path = "/root/cube"
            
            if "sphere" in query_lower:
                shape_type = "sphere"
                prim_path = "/root/sphere"
            
            # For this example, we only implement cube mesh creation
            if shape_type == "cube":
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
                
                # Use MCP tool to create mesh
                result = await self.session.call_tool("create_mesh", {
                    "file_path": file_path,
                    "prim_path": prim_path,
                    "points": points,
                    "face_vertex_counts": face_vertex_counts,
                    "face_vertex_indices": face_vertex_indices
                })
                
                # Parse JSON response
                try:
                    response = json.loads(result.content)
                    if response.get("ok", False):
                        return f"I've added a cube to the stage at {prim_path}. {response.get('message', '')}"
                    else:
                        return f"I wasn't able to add the cube: {response.get('message', 'Unknown error')}"
                except json.JSONDecodeError:
                    # Fallback for non-JSON responses
                    return f"I've added a cube to the stage at {prim_path}.\n\n{result.content}"
            else:
                return (f"I can only create cubes right now. Other shapes like spheres "
                       f"would require additional implementation.")
        else:
            return (f"I couldn't find the USD stage at {file_path}. "
                   f"Please create a stage first with 'Create a new USD stage'.")
    
    async def _handle_analyze_stage(self, query_lower: str) -> str:
        """Handle a request to analyze a USD stage
        
        Args:
            query_lower: Lowercase query string
            
        Returns:
            Response message
        """
        # Extract file path or use default
        file_path = "ai_created_stage.usda"
        
        # Check if the file exists
        if not os.path.exists(file_path):
            return f"I couldn't find the USD stage at {file_path}. Please create a stage first."
        
        # Use MCP tool to analyze stage
        result = await self.session.call_tool("analyze_stage", {"file_path": file_path})
        
        # Parse JSON response
        try:
            response = json.loads(result.content)
            if response.get("ok", False):
                stage_data = response.get("data", {})
                
                # Format a user-friendly response
                analysis = "Here's what I found in the USD stage:\n\n"
                
                if "default_prim" in stage_data:
                    analysis += f"- Default prim: {stage_data['default_prim']}\n"
                
                if "up_axis" in stage_data:
                    analysis += f"- Up axis: {stage_data['up_axis']}\n"
                
                if "prims" in stage_data:
                    prim_count = len(stage_data["prims"])
                    analysis += f"- Contains {prim_count} prims\n"
                    
                    # List the types of prims present
                    prim_types = set()
                    for prim in stage_data["prims"]:
                        if prim.get("type"):
                            prim_types.add(prim.get("type"))
                    
                    if prim_types:
                        analysis += f"- Prim types: {', '.join(prim_types)}\n"
                
                return analysis
            else:
                return f"I wasn't able to analyze the stage: {response.get('message', 'Unknown error')}"
        except json.JSONDecodeError:
            # Try to parse as direct JSON (legacy format)
            try:
                stage_info = json.loads(result.content)
                analysis = "Here's what I found in the USD stage:\n\n"
                
                if "default_prim" in stage_info:
                    analysis += f"- Default prim: {stage_info['default_prim']}\n"
                
                if "up_axis" in stage_info:
                    analysis += f"- Up axis: {stage_info['up_axis']}\n"
                
                if "prims" in stage_info:
                    analysis += f"- Contains {len(stage_info['prims'])} prims\n"
                
                return analysis
            except:
                return f"I analyzed the stage and here are the results:\n\n{result.content}"
    
    async def _handle_omniverse_help(self) -> str:
        """Handle a request for Omniverse help information
        
        Returns:
            Response message
        """
        help_info, _ = await self.session.read_resource("omniverse://help")
        return f"Here's some helpful information about Omniverse Kit and USD:\n\n{help_info}"
    
    async def _handle_usd_schema(self) -> str:
        """Handle a request for USD schema information
        
        Returns:
            Response message
        """
        schema_info, _ = await self.session.read_resource("usd://schema")
        
        try:
            schema_dict = json.loads(schema_info)
            
            # Format a user-friendly response
            response = "Here's an overview of some common USD schema types:\n\n"
            
            for schema_type, description in schema_dict.items():
                response += f"**{schema_type}**: {description}\n\n"
            
            return response
        except:
            # Fallback if parsing fails
            return f"Here are the USD schema details:\n\n{schema_info}"
    
    async def _handle_development_guide_query(self, query_lower: str) -> str:
        """Handle a request for Omniverse development guide information
        
        Args:
            query_lower: Lowercase query string
            
        Returns:
            Response message
        """
        # Extract topics from the query
        guide_topics = []
        
        if "extension" in query_lower:
            guide_topics.append("extension")
        if "material" in query_lower or "shader" in query_lower:
            guide_topics.append("material")
        if "physics" in query_lower:
            guide_topics.append("physics")
        if "ui" in query_lower or "interface" in query_lower:
            guide_topics.append("ui")
        if "performance" in query_lower or "optimization" in query_lower:
            guide_topics.append("performance")
        if "nucleus" in query_lower or "network" in query_lower:
            guide_topics.append("nucleus")
        
        # If no specific topics were found, provide general guide
        if not guide_topics:
            # Get general development guide
            guide, _ = await self.session.read_resource("omniverse://development-guide")
            
            # Return a preview of the guide
            preview_length = min(500, len(guide))
            return (f"Here's a preview of the Omniverse Development Guide:\n\n"
                   f"{guide[:preview_length]}...\n\n"
                   f"You can ask about specific topics like 'extensions', 'materials', 'UI', etc.")
        
        # Search for specific topics
        topics_str = ", ".join(guide_topics)
        result = await self.session.call_tool("search_omniverse_guide", {"topic": topics_str})
        
        return f"Here's information about {topics_str} from the Omniverse Development Guide:\n\n{result.content}"
    
    async def _handle_specific_topic(self, topic: str) -> str:
        """Handle a request for a specific development topic
        
        Args:
            topic: The specific topic to search for
            
        Returns:
            Response message
        """
        # Search the development guide for this topic
        result = await self.session.call_tool("search_omniverse_guide", {"topic": topic})
        
        return f"Here's information about {topic} development in Omniverse:\n\n{result.content}"
    
    def _get_default_response(self) -> str:
        """Generate a default response when no specific handler matches
        
        Returns:
            Default response message
        """
        return """I can help you with several USD and Omniverse tasks:

1. **USD Operations**:
   - Create a new USD stage
   - Add a cube or other geometry
   - Analyze a USD stage

2. **Documentation**:
   - Get information about USD schema types
   - Access the Omniverse Development Guide
   - Find help on specific topics (extensions, materials, physics, UI)

What would you like to do?"""

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the full conversation history
        
        Returns:
            List of message dictionaries with 'role' and 'content' keys
        """
        return self.conversation_history


async def run_assistant(server_cmd='python', server_args=['usd_mcp_server.py']):
    """Run the AI assistant with an MCP server
    
    Args:
        server_cmd: Command to start the server
        server_args: Arguments for the server command
    """
    # Setup server parameters
    server_params = StdioServerParameters(
        command=server_cmd,
        args=server_args,
        env=None
    )
    
    # Connect to the server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize session
            await session.initialize()
            print("✓ Connected to MCP server")
            
            # Create AI assistant
            assistant = SimulatedAIAssistant(session)
            
            # Welcome message
            print("\n" + "="*50)
            print("AI Assistant for Omniverse USD")
            print("="*50)
            print("\nYou can ask questions about USD, Omniverse development,")
            print("or ask the assistant to create and manipulate USD content.")
            print("\nType 'exit' to quit.")
            
            # Main interaction loop
            while True:
                try:
                    # Get user input
                    user_query = input("\nYou: ")
                    
                    # Check for exit command
                    if user_query.lower() in ['exit', 'quit', 'bye']:
                        print("\nExiting assistant. Goodbye!")
                        break
                    
                    # Process the query
                    response = await assistant.process_query(user_query)
                    
                    # Display the response
                    print("\nAssistant:", response)
                    
                except KeyboardInterrupt:
                    print("\n\nInterrupted by user. Exiting...")
                    break
                except Exception as e:
                    logger.exception("Error in assistant interaction")
                    print(f"\nAn error occurred: {e}")
                    print("Let's try again.")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='AI Assistant for Omniverse USD')
    parser.add_argument('--server', default='python', 
                        help='Server command (default: python)')
    parser.add_argument('--args', nargs='*', default=['usd_mcp_server.py'], 
                        help='Server arguments (default: usd_mcp_server.py)')
    return parser.parse_args()


if __name__ == "__main__":
    # Parse arguments
    args = parse_arguments()
    
    try:
        # Run the assistant
        asyncio.run(run_assistant(args.server, args.args))
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        logger.exception("Error in main")
        print(f"Fatal error: {e}")
        sys.exit(1) 