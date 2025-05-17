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
from typing import Dict, Any, List, Optional, Tuple
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

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
            Response message with analysis results
        """
        # Extract file path or use default
        file_path = "ai_created_stage.usda"
        if "file" in query_lower:
            parts = query_lower.split("file")
            if len(parts) > 1:
                potential_path = parts[1].strip().split()[0]
                if os.path.exists(potential_path):
                    file_path = potential_path
        
        if os.path.exists(file_path):
            # Use MCP tool to analyze stage
            result = await self.session.call_tool("analyze_stage", {"file_path": file_path})
            
            # Parse the JSON response
            try:
                stage_info = json.loads(result.content)
                prim_count = len(stage_info["prims"])
                up_axis = stage_info.get("up_axis", "Unknown")
                default_prim = stage_info.get("default_prim", "None")
                
                summary = (
                    f"I've analyzed the USD stage at {file_path}. Here's what I found:\n\n"
                    f"- Contains {prim_count} prims\n"
                    f"- Up axis is {up_axis}\n"
                    f"- Default prim: {default_prim}\n"
                    f"- Time code range: {stage_info.get('time_code_range', ['Unknown', 'Unknown'])}\n\n"
                    f"Would you like more detailed information about specific prims?"
                )
                return summary
            except json.JSONDecodeError:
                return f"I've analyzed the stage, but couldn't parse the results: {result.content}"
        else:
            return (f"I couldn't find the USD stage at {file_path}. "
                   f"Please check the file path or create a stage first.")
    
    async def _handle_omniverse_help(self) -> str:
        """Handle a request for Omniverse help
        
        Returns:
            Response message with Omniverse help information
        """
        # Fetch Omniverse help resource
        help_text, _ = await self.session.read_resource("omniverse://help")
        return f"Here's some information about Omniverse Kit and USD integration:\n\n{help_text}"
    
    async def _handle_usd_schema(self) -> str:
        """Handle a request for USD schema information
        
        Returns:
            Response message with USD schema information
        """
        # Fetch USD schema resource
        schema_info, _ = await self.session.read_resource("usd://schema")
        try:
            schema_dict = json.loads(schema_info)
            # Format a sample of schema types
            examples = list(schema_dict.items())[:5]
            examples_text = "\n".join([f"- {name}: {desc}" for name, desc in examples])
            return (f"Here are some common USD schema types:\n\n{examples_text}\n\n"
                   f"(Plus {len(schema_dict) - 5} more types. Ask me about specific types for more details.)")
        except json.JSONDecodeError:
            return f"Here's information about USD schema types: {schema_info}"
    
    async def _handle_development_guide_query(self, query_lower: str) -> str:
        """Handle a query about the development guide
        
        Args:
            query_lower: Lowercase query string
            
        Returns:
            Response message with development guide information
        """
        # Check if there's a specific topic the user is asking about
        potential_topics = [
            "extension", "material", "physics", "ui", "performance", 
            "layer", "prim", "stage", "carbonite", "nucleus"
        ]
        matching_topics = [topic for topic in potential_topics if topic in query_lower]
        
        if matching_topics:
            # Search for specific topics in the guide
            return await self._handle_specific_topic(matching_topics[0])
        else:
            # Give an overview of the development guide
            return (
                "The Comprehensive Omniverse Development Guide covers many topics including:\n\n"
                "- Omniverse Kit Architecture\n"
                "- Extension System\n"
                "- USD Python Development\n"
                "- UI Development\n"
                "- Performance Optimization\n"
                "- Networking and Collaboration\n"
                "- Physics and Simulation\n"
                "- Materials and Rendering\n\n"
                "You can ask me about any of these specific topics for more detailed information."
            )
    
    async def _handle_specific_topic(self, topic: str) -> str:
        """Handle a query about a specific development topic
        
        Args:
            topic: The topic to search for
            
        Returns:
            Response message with topic-specific information
        """
        result = await self.session.call_tool("search_omniverse_guide", {"topic": topic})
        return f"Here's information about {topic} in Omniverse development:\n\n{result.content}"
    
    def _get_default_response(self) -> str:
        """Get a default response when no specific handler matches
        
        Returns:
            Default response message
        """
        return (
            "I'm your USD and Omniverse assistant. I can help with:\n\n"
            "- Creating and manipulating USD stages\n"
            "- Adding geometry to stages\n"
            "- Analyzing USD files\n"
            "- Providing information about USD schemas\n"
            "- Offering guidance on Omniverse development\n\n"
            "Try asking me to:\n"
            "- 'Create a new USD stage'\n"
            "- 'Add a cube to the stage'\n"
            "- 'Analyze the USD stage'\n"
            "- 'Help me with Omniverse'\n"
            "- 'Tell me about USD schema types'\n"
            "- 'How do I create an Omniverse extension?'\n"
            "- 'Tell me about performance optimization in USD'"
        )

async def run_assistant(server_cmd='python', server_args=['usd_mcp_server.py']):
    """Run the AI assistant with USD MCP integration
    
    Args:
        server_cmd: Command to start the MCP server
        server_args: Arguments for the server command
    """
    print("Starting AI Assistant with Omniverse_USD_MCPServer_byJPH2 Integration...")
    
    # Connect to the MCP server
    server_params = StdioServerParameters(
        command=server_cmd,
        args=server_args,
        env=None
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                print("✓ Connected to Omniverse_USD_MCPServer_byJPH2")
                
                # Create the AI assistant
                assistant = SimulatedAIAssistant(session)
                
                # Simple interactive chat loop
                print("\n" + "="*80)
                print("Omniverse_USD_MCPServer_byJPH2 AI Assistant Ready! Type 'exit' to quit.")
                print("="*80)
                print("\nExample queries:")
                print("- Create a new USD stage")
                print("- Add a cube to the stage")
                print("- Analyze the USD stage")
                print("- Help me with Omniverse")
                print("- Tell me about USD schema types")
                print("- Show me the Omniverse Development Guide")
                print("- How do I create an Omniverse extension?")
                print("- Tell me about performance optimization in USD")
                print("- How do I work with materials in Omniverse?")
                
                while True:
                    user_input = input("\nYou: ")
                    if user_input.lower() in ["exit", "quit"]:
                        print("\nThank you for using the Omniverse_USD_MCPServer_byJPH2 AI Assistant. Goodbye!")
                        break
                    
                    response = await assistant.process_query(user_input)
                    print(f"\nAssistant: {response}")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description='Omniverse_USD_MCPServer_byJPH2 AI Assistant')
    parser.add_argument('--server-cmd', default='python',
                        help='Server command (default: python)')
    parser.add_argument('--server-args', nargs='+', default=['usd_mcp_server.py'],
                        help='Server arguments (default: usd_mcp_server.py)')
    return parser.parse_args()

if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_arguments()
    
    # Run the AI assistant
    try:
        asyncio.run(run_assistant(args.server_cmd, args.server_args))
    except KeyboardInterrupt:
        print("\nAssistant stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 