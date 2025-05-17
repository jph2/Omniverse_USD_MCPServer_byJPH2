# Omniverse USD MCP Server Integration Guide

This guide provides detailed instructions for integrating the Omniverse USD MCP Server with three AI platforms:
- **Cursor** (AI-powered code editor) - **PRIMARY FOCUS**
- Claude (Anthropic's AI assistant)
- ChatGPT (OpenAI's AI assistant)

## Why Cursor?

Cursor is our primary focus for integration because it offers unique benefits for USD development:

1. **Code-first approach**: Cursor provides a code-centric environment that aligns perfectly with USD's programmatic nature
2. **In-editor AI assistance**: Get context-aware help for USD development directly in your coding environment
3. **Practical workflows**: The integration allows you to seamlessly create and modify USD scenes while writing Python scripts
4. **Developer-friendly**: Built for programmers, Cursor offers a familiar IDE experience with enhanced AI capabilities

The included `cursor_integration.py` module and examples like `cursor_example.py` demonstrate how to leverage this integration for productive USD development.

## Prerequisites

Before integrating with any platform, complete these steps:

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the MCP Server**
   - For local AI tools (Cursor):
     ```bash
     python usd_mcp_server.py --host 0.0.0.0 --port 5000
     ```
   - For web-based AI tools (ChatGPT, Claude web):
     ```bash
     python usd_mcp_server.py --host 0.0.0.0 --port 5000
     ```

## 1. Integrating with Cursor

Cursor is an AI-powered code editor that can leverage the USD MCP Server for USD scene creation and manipulation.

### Setup Steps

1. **Install Cursor**
   - Download and install Cursor from [https://cursor.sh/](https://cursor.sh/)

2. **Run the USD MCP Server**
   ```bash
   python usd_mcp_server.py --host 0.0.0.0 --port 5000
   ```

3. **Use the Cursor Integration Module**
   The `cursor_integration.py` module provides a comprehensive Python API for working with USD through the MCP server. Import this module in your Cursor projects:

   ```python
   from cursor_integration import CursorUsdTools
   
   # Initialize the tools
   usd_tools = CursorUsdTools()
   
   # Create a stage
   usd_tools.create_stage("my_stage.usda")
   
   # Add geometry, materials, physics, etc.
   usd_tools.create_primitive("my_stage.usda", "cube", "/World/Cube")
   ```

4. **Try the Example Script**
   Run the `cursor_example.py` script to see the integration in action:
   ```bash
   python cursor_example.py
   ```
   This creates a complete physics simulation with multiple objects, materials, and exports it to different formats.

5. **Use Cursor's AI Features**
   With the integration in place, you can use Cursor's AI features to generate USD-related code:
   - Ask Cursor to help create scenes and components
   - Request guidance on USD concepts and workflows
   - Generate complex USD operations with simple natural language

### Example Cursor Prompts

- "Create a stage with a red cube and a blue sphere using the USD MCP Server."
- "Write a function to create a physics scene with falling cubes using the USD MCP Server."
- "Update this script to add an animation to the cube using the USD MCP Server."
- "How can I create a character rig in USD using the MCP Server's skeletal animation tools?"

## 2. Integrating with Claude

### Method A: Claude Desktop App with stdio Protocol

1. **Install Claude Desktop App**
   - Download and install from [https://claude.ai/desktop](https://claude.ai/desktop)

2. **Configure MCP Server**
   - Open Claude Desktop App
   - Go to Settings > MCP Servers
   - Add a new server with:
     - Name: `USD MCP Server`
     - Command: `python`
     - Arguments: `usd_mcp_server.py`

3. **Use with Claude**
   - Start a new conversation
   - Ask Claude to use USD MCP Server tools to create and manipulate USD scenes

### Method B: Web-based Claude with HTTP Protocol

1. **Run the MCP Server with HTTP**
   ```bash
   python usd_mcp_server.py --protocol=http --host=0.0.0.0 --port=5000
   ```

2. **Expose Your Server** (for development)
   Using ngrok or similar tool:
   ```bash
   ngrok http 5000
   ```
   Note the generated URL (e.g., `https://abcd1234.ngrok.io`)

3. **Create OpenAPI Specification**
   Create a file named `openapi.json` with an OpenAPI spec describing your MCP server endpoints.

4. **Create an API Wrapper Script**
   ```python
   import requests
   import json
   from typing import Dict, Any

   class ClaudeUsdWrapper:
       def __init__(self, server_url):
           self.server_url = server_url
       
       def call_function(self, function_name, params):
           """Call MCP tool and return result to Claude"""
           try:
               url = f"{self.server_url}/{function_name}"
               response = requests.post(url, json=params)
               response.raise_for_status()
               return response.json()
           except Exception as e:
               return {"error": str(e)}
   ```

5. **Use with Claude Web**
   - Share the OpenAPI spec or provide your wrapper script
   - Ask Claude to generate code that uses your wrapper to interact with the USD MCP Server

### Example Claude Prompts

- "Create a USD stage with a physics simulation of a ball bouncing on a plane."
- "How can I create a character rig in USD using the MCP Server's skeletal animation tools?"
- "Generate a script that creates a USD scene with animated materials using the MCP Server."

## 3. Integrating with ChatGPT

### Method A: ChatGPT Plugin (GPT-4 with Plugins)

1. **Run the MCP Server with HTTP**
   ```bash
   python usd_mcp_server.py --protocol=http --host=0.0.0.0 --port=5000
   ```

2. **Expose Your Server** (for development)
   Using ngrok or similar tool:
   ```bash
   ngrok http 5000
   ```
   Note the generated URL (e.g., `https://abcd1234.ngrok.io`)

3. **Create AI Plugin Manifest**
   Create a file named `ai-plugin.json` with the following content:

   ```json
   {
     "schema_version": "v1",
     "name_for_human": "USD MCP Tools",
     "name_for_model": "usd_mcp_tools",
     "description_for_human": "Plugin for creating and manipulating USD scenes with Pixar's Universal Scene Description.",
     "description_for_model": "This plugin allows you to create, edit, and analyze USD scenes through the MCP server. You can create geometry, materials, physics simulations, and animations in USD format.",
     "auth": {
       "type": "none"
     },
     "api": {
       "type": "openapi",
       "url": "https://your-server-url/openapi.json"
     },
     "logo_url": "https://your-server-url/logo.png",
     "contact_email": "your-email@example.com",
     "legal_info_url": "https://your-website.com/legal"
   }
   ```

4. **Create OpenAPI Specification**
   Create a file named `openapi.json` with an OpenAPI spec for your server's endpoints.

5. **Host the Plugin Files**
   - Host `ai-plugin.json` at `https://your-server-url/.well-known/ai-plugin.json`
   - Host `openapi.json` at `https://your-server-url/openapi.json`

6. **Install in ChatGPT**
   - Go to ChatGPT (GPT-4)
   - Click on "GPT-4" > "Plugins" > "Plugin store"
   - Click "Develop your own plugin"
   - Enter your server URL
   - Follow the prompts to install your plugin

### Method B: Function Calling API

1. **Run the MCP Server**
   ```bash
   python usd_mcp_server.py --protocol=http --host=0.0.0.0 --port=5000
   ```

2. **Create Integration Script**
   Create a file named `chatgpt_integration.py` with the following content:

   ```python
   import openai
   import requests
   import json
   from typing import Dict, Any, List

   # Configure OpenAI API
   openai.api_key = "YOUR_OPENAI_API_KEY"
   MCP_SERVER_URL = "http://localhost:5000"

   # Define functions for OpenAI function calling
   functions = [
     {
       "name": "create_stage",
       "description": "Create a new USD stage at the specified file path",
       "parameters": {
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
     # Add more functions here...
   ]

   def call_mcp_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
       """Call the MCP server tool and return the result"""
       try:
           response = requests.post(f"{MCP_SERVER_URL}/{tool_name}", json=params)
           response.raise_for_status()
           return response.json()
       except Exception as e:
           return {"ok": False, "message": f"Error calling {tool_name}: {str(e)}"}

   def process_user_request(user_message: str) -> str:
       """Process a user request using OpenAI function calling"""
       messages = [{"role": "user", "content": user_message}]
       
       response = openai.ChatCompletion.create(
           model="gpt-4o",
           messages=messages,
           functions=functions,
           function_call="auto"
       )
       
       message = response.choices[0].message

       if message.get("function_call"):
           function_name = message["function_call"]["name"]
           arguments = json.loads(message["function_call"]["arguments"])
           
           # Call the MCP server
           result = call_mcp_tool(function_name, arguments)
           
           # Send the result back to OpenAI
           messages.append(message)
           messages.append({
               "role": "function",
               "name": function_name,
               "content": json.dumps(result)
           })
           
           second_response = openai.ChatCompletion.create(
               model="gpt-4o",
               messages=messages
           )
           
           return second_response.choices[0].message["content"]
       else:
           return message["content"]

   # Example usage
   user_query = "Create a new USD stage with a red cube"
   result = process_user_request(user_query)
   print(result)
   ```

3. **Run the Integration Script**
   ```bash
   python chatgpt_integration.py
   ```

### Example ChatGPT Prompts

- "Create a new stage called scene.usda and add a sphere with a metallic material."
- "Set up a physical simulation with a ball dropping onto a plane, then export it as USDZ."
- "Create a keyframe animation of a cube moving in a circle, with 30 frames."

## Common MCP Server Commands

Here are some common operations you can perform with the USD MCP Server across all platforms:

### Creating and Analyzing Stages

```
Create a new USD stage at /path/to/stage.usda using the basic template.
Analyze the stage at /path/to/stage.usda and show me its contents.
Close the stage at /path/to/stage.usda to free up resources.
```

### Adding Geometry and Materials

```
Add a cube at /World/Geometry/Cube1 with size 2.0 and position (0, 1, 0).
Create a red metallic material at /World/Materials/RedMetal with roughness 0.2.
Bind the material at /World/Materials/RedMetal to the prim at /World/Geometry/Cube1.
```

### Physics Simulations

```
Set up a physics scene with gravity (0, -9.8, 0).
Make the cube at /World/Geometry/Cube1 a dynamic rigid body with mass 5.0.
Add a sphere collider to the prim at /World/Geometry/Sphere1.
Create a revolute joint between /World/Geometry/Part1 and /World/Geometry/Part2.
```

### Animations and Transforms

```
Set the transform of /World/Geometry/Cube1 to position (0, 5, 0) at time 0.
Create an animation for the position of /World/Geometry/Cube1 from (0, 0, 0) to (0, 5, 0) over 48 frames.
Create a skeleton at /World/Character/Skeleton with the specified joint hierarchy.
Bind the skeleton to the mesh at /World/Character/Mesh.
```

## Physics Simulation

USD MCP Server provides physics simulation capabilities through the following tools:

- `setup_physics_scene` - Initialize physics properties for a stage
- `add_rigid_body` - Add rigid body properties to a prim
- `add_collider` - Add collision shape to a prim
- `add_joint` - Create a joint between two rigid bodies

Example physics workflow:
```python
from cursor_integration import CursorUsdTools

usd = CursorUsdTools()

# Create a stage
usd.create_stage("physics_demo.usda")

# Set up physics scene with custom gravity
usd.setup_physics_scene("physics_demo.usda", gravity=(0, -9.81, 0))

# Create a ground plane
usd.create_primitive("physics_demo.usda", "cube", "/World/Ground", size=10.0, position=(0, -0.5, 0))
usd.set_transform("physics_demo.usda", "/World/Ground", scale=(1.0, 0.1, 1.0))
usd.add_rigid_body("physics_demo.usda", "/World/Ground", mass=0.0, is_dynamic=False)

# Create a dynamic sphere
usd.create_primitive("physics_demo.usda", "sphere", "/World/Sphere", size=1.0, position=(0, 5.0, 0))
usd.add_rigid_body("physics_demo.usda", "/World/Sphere", mass=1.0, is_dynamic=True)
```

## Scene Graph Visualization

The USD MCP Server now includes powerful scene graph visualization capabilities that allow you to:

1. Generate ASCII text representations of the USD scene hierarchy
2. Create interactive HTML visualizations with search and collapsible nodes
3. Export JSON scene graph data for custom applications
4. Generate network graph data for visualization in third-party tools

### Visualization in Cursor Integration

You can use the Cursor integration to generate visualizations:

```python
from cursor_integration import CursorUsdTools

usd = CursorUsdTools()

# Create or load a USD stage
usd.create_stage("demo_scene.usda", template="full")

# Add some content to the stage
usd.create_primitive("demo_scene.usda", "sphere", "/World/Geometry/Sphere", size=1.0)
usd.create_primitive("demo_scene.usda", "cube", "/World/Geometry/Cube", size=1.0, position=(2, 0, 0))

# Generate text visualization
result = usd.visualize_scene_graph(
    "demo_scene.usda",
    output_format="text",
    include_properties=True
)

# Generate HTML visualization with interactive tree view
result = usd.visualize_scene_graph(
    "demo_scene.usda",
    output_format="html",
    output_path="scene_visualization.html"
)

# Export JSON data for custom processing
result = usd.visualize_scene_graph(
    "demo_scene.usda",
    output_format="json",
    output_path="scene_data.json"
)
```

### Advanced Visualization with the Optimizer

For more advanced visualization options and optimized performance, use the scene graph optimizer:

```python
from scene_graph_optimizer import UsdSceneGraphOptimizer

# Create optimizer for a USD stage
optimizer = UsdSceneGraphOptimizer("complex_scene.usda")

# Generate optimized visualization with dark theme and material filtering
result = optimizer.visualize(
    output_format="html",
    output_path="materials_visualization.html",
    filter_types=["Material"],  # Only show materials
    theme="dark",               # Use dark theme
    open_browser=True           # Open in browser automatically
)

# Generate visualization focused on specific path pattern
result = optimizer.visualize(
    output_format="html",
    output_path="building_visualization.html",
    filter_pattern="Building",  # Show only prims with "Building" in the path
    theme="contrast",           # Use high contrast theme
    max_depth=3                 # Limit display depth
)
```

### Visualization Features

- **Text Format**: Simple ASCII tree representation of the scene hierarchy
  - Optional property details
  - Configurable depth limit
  - Color-coded by prim type (in terminals that support color)

- **HTML Format**: Interactive web-based visualization
  - Collapsible/expandable tree nodes
  - Search functionality to quickly find prims and properties
  - Color-coded by prim type (materials, geometries, transforms, physics)
  - Property inspection for each prim
  - Multiple visual themes (light, dark, high-contrast)
  - Filtering capabilities for specific prim types or path patterns
  - Works in any modern web browser

- **JSON Format**: Structured data for programmatic use
  - Complete scene graph hierarchy
  - All prim properties
  - Specialized information for different prim types (meshes, materials, etc.)
  - Can be used for custom visualization or analysis tools

- **Network Format**: Graph data for network visualization tools
  - Nodes represent prims
  - Edges represent parent-child relationships and material bindings
  - Specialized node types for different prim categories
  - Compatible with D3.js and other network visualization libraries

### Performance Optimization

The scene graph optimizer includes several optimizations for handling large USD scenes:

- **Automatic Complexity Detection**: Analyzes scene size and applies appropriate optimizations
- **Lazy Loading**: Defers loading of deep hierarchies until needed
- **Type Filtering**: Focus visualization on specific prim types
- **Path Filtering**: Use regular expressions to filter scene elements
- **Depth Limiting**: Control visualization depth to avoid overwhelming displays
- **Property Filtering**: Selectively display only the most relevant properties

### Example Visualization Script

For a complete example that demonstrates creating a complex scene and generating multiple visualizations:

```bash
# Create and visualize a demo scene
python optimized_visualization_example.py

# Visualize an existing stage with specific options
python optimized_visualization_example.py --stage path/to/stage.usda --format html --filter-types Material --theme dark

# Generate multiple visualization formats for comparison
python optimized_visualization_example.py --stage path/to/stage.usda --no-demo
```

### Benchmark Different Approaches

Compare visualization performance:

```bash
# Run benchmarks on test stages of different sizes
python benchmark_visualizers.py --generate small medium large

# Compare different visualization approaches
python benchmark_visualizers.py --stages my_stage.usda complex_stage.usda --approaches basic_visualizer optimizer direct_mcp_call

# Benchmark specific formats
python benchmark_visualizers.py --generate medium --formats html json text
```

## Troubleshooting

- **Server Connection Issues**: Ensure the MCP server is running and accessible at the expected host and port.
- **Permissions Problems**: Check that the server has permission to create and modify files in the specified locations.
- **USD Library Errors**: Verify that the Pixar USD library is correctly installed and accessible.
- **Tool Parameter Errors**: Ensure that the parameters passed to each tool match the expected format and types.

## Additional Resources

- See [README.md](README.md) for a complete overview of the USD MCP Server
- See [MCP_README.md](MCP_README.md) for detailed tool reference
- Check [ai_integration_example.py](ai_integration_example.py) for more integration examples 