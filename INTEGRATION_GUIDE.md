# Omniverse USD MCP Server Integration Guide

This guide provides detailed instructions for integrating the Omniverse USD MCP Server with various AI assistants:

- [Cursor Integration](#cursor-integration) (Primary Focus)
- [ChatGPT Integration](#chatgpt-integration)
- [Claude Integration](#claude-integration)

## Prerequisites

- Python 3.7+
- Omniverse USD MCP Server installed and configured
- Access credentials for your AI assistant of choice

## Cursor Integration

[Cursor](https://cursor.sh/) is the primary and recommended integration platform for the Omniverse USD MCP Server, providing seamless integration with USD workflows.

### Setup

1. **Start the MCP Server**

   ```bash
   python usd_mcp_server.py --host 127.0.0.1 --port 5000
   ```

2. **Configure Cursor**

   Create a file named `.cursor/settings.json` in your project directory:

   ```json
   {
     "ai": {
       "tools": {
         "mcp_server": {
           "url": "http://127.0.0.1:5000",
           "toolName": "Omniverse USD MCP Server",
           "endpoints": [
             {
               "name": "open_stage",
               "description": "Open or create a USD stage",
               "parameters": {
                 "type": "object",
                 "properties": {
                   "file_path": {"type":"string", "description": "Path to the USD file"},
                   "createNew": {"type":"boolean", "description": "Whether to create a new stage if it doesn't exist"}
                 },
                 "required": ["file_path"]
               }
             },
             {
               "name": "visualize_scene_graph",
               "description": "Generate a visualization of the USD scene graph hierarchy",
               "parameters": {
                 "type": "object",
                 "properties": {
                   "stage_id": {"type":"string", "description": "ID of the stage to visualize"},
                   "format": {"type":"string", "description": "Output format (text, html, json, network)"},
                   "max_depth": {"type":"integer", "description": "Maximum hierarchy depth to display"}
                 },
                 "required": ["stage_id"]
               }
             }
             // Additional endpoints can be configured here
           ]
         }
       }
     }
   }
   ```

3. **Import the Cursor Integration Module**

   In your Python code, import and use the Cursor integration:

   ```python
   from cursor_integration import CursorUsdTools
   
   # Initialize with the MCP server URL
   tools = CursorUsdTools(server_url="http://127.0.0.1:5000")
   
   # Use the tools through natural language instructions
   result = tools.execute("Create a new USD stage at /tmp/example.usda with a red sphere")
   ```

### Example Usage in Cursor

1. Open Cursor IDE and load your USD project
2. Use `Cmd+K` (Mac) or `Ctrl+K` (Windows/Linux) to open the AI command interface
3. Type natural language requests to work with USD:

   ```
   Create a new USD stage with a red cube at position (0,2,0)
   ```

4. Cursor will use the MCP server to execute the command and generate the USD content

### Advanced Cursor Integration

For more complex USD operations, you can use the scene graph visualization to understand and navigate the structure:

```
Visualize the scene graph of my current stage in HTML format
```

Cursor will generate an interactive visualization of the scene hierarchy that you can explore.

## ChatGPT Integration

### Option 1: Using the Web API

1. **Start the MCP Server**

   ```bash
   python usd_mcp_server.py --host 0.0.0.0 --port 5000
   ```

2. **Use the ChatGPT Integration Script**

   ```bash
   python chatgpt_integration.py --api-key YOUR_OPENAI_API_KEY
   ```

3. **Chat with GPT About USD**

   The integration script provides a terminal interface where you can ask ChatGPT to perform USD operations, which are executed through the MCP server.

### Option 2: As a ChatGPT Plugin

1. **Host the Plugin Files**

   Ensure the `ai-plugin.json` and `openapi.json` files are hosted on a web server.

2. **Install the Plugin in ChatGPT**

   - Open ChatGPT (GPT-4 or later)
   - Go to Plugin Store → Develop your own plugin
   - Enter the URL to your `ai-plugin.json` file

3. **Use the Plugin**

   Simply chat with GPT about USD operations, and it will execute them through the MCP server.

## Claude Integration

### Option 1: Claude APIs

1. **Start the MCP Server**

   ```bash
   python usd_mcp_server.py --host 0.0.0.0 --port 5000
   ```

2. **Use the Claude Integration Script**

   ```bash
   python claude_integration.py --api-key YOUR_ANTHROPIC_API_KEY
   ```

3. **Chat with Claude About USD**

   The integration script provides a terminal interface where you can ask Claude to perform USD operations, which are executed through the MCP server.

### Option 2: Manual Function Calling

For Claude 3 Opus and above, you can use function calling directly:

```python
from anthropic import Anthropic
import requests
import json

client = Anthropic(api_key="YOUR_API_KEY")

tools = [{
    "name": "open_stage",
    "description": "Open or create a USD stage",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string"},
            "createNew": {"type": "boolean"}
        },
        "required": ["file_path"]
    }
}]

response = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    tools=tools,
    messages=[
        {"role": "user", "content": "Create a new USD stage at /tmp/example.usda"}
    ]
)

if response.tool_use:
    tool_name = response.tool_use.name
    tool_args = response.tool_use.input
    
    # Call the MCP server
    result = requests.post(
        f"http://localhost:5000/{tool_name}",
        json=tool_args
    ).json()
    
    # Send the result back to Claude
    followup = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": "Create a new USD stage at /tmp/example.usda"},
            {"role": "assistant", "content": response.content},
            {"role": "user", "content": f"Result: {json.dumps(result)}"}
        ]
    )
    print(followup.content)
```

## Common Operations

Here are examples of USD operations you can perform through any of the AI integrations:

### Creating a Simple Scene

```
Create a new USD stage at /tmp/scene.usda with a red sphere at (0,1,0) and a blue cube at (2,0,0)
```

### Adding Physics

```
Add physics to the sphere in my scene, making it a rigid body with density 1.0
```

### Creating an Animation

```
Create a 5-second animation where the cube moves from position (0,0,0) to (5,0,0)
```

### Using the Scene Graph Visualizer

```
Generate an HTML visualization of my scene graph, limited to depth 3, focusing only on mesh and material types
```

## Troubleshooting

- **Connection Issues**: Make sure the MCP server is running and accessible from the client
- **Authentication Errors**: Verify API keys for OpenAI or Anthropic services
- **Visualization Errors**: Check that any visualization output directories are writable

## Additional Resources

- [Scene Graph Visualization Documentation](VISUALIZATION_README.md)
- [USD MCP Server API Reference](MCP_README.md)
- [Autopoietic Development Documentation](SCENE_GRAPH_GENESIS.md)

For more details on the scene graph visualization capabilities, refer to the specific [Scene Graph Visualization Documentation](VISUALIZATION_README.md). 