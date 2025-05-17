# Omniverse USD MCP Server

[![Python](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-compatible-green)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An MCP (Model Context Protocol) server for working with USD (Universal Scene Description) and NVIDIA Omniverse. This server enables AI assistants and other clients to create, manipulate, and analyze USD scenes through a standardized API.

## Features

- **Advanced Stage Management**: Create, open, analyze, and close USD stages with memory-efficient caching
- **Geometry Creation**: Add meshes, primitives, and references to USD stages
- **Materials & Shading**: Create and assign OmniPBR materials with full PBR properties
- **Physics Support**: Create physics scenes, rigid bodies, colliders, and constraints
- **Animation Tools**: Create keyframe animations and skeletal animations
- **Documentation**: Access comprehensive USD schema documentation and Omniverse development guides
- **Multiple Transport Protocols**: Supports stdio, HTTP, SSE, and more
- **Cache Management**: Efficient resource handling with automatic cleanup
- **Server Status**: Monitor resource usage and server health

## Getting Started

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server in stdio mode (for Claude Desktop App)
python usd_mcp_server.py

# Start the server in HTTP/SSE mode (for web clients and Cursor)
python usd_mcp_server.py --protocol=http --host=0.0.0.0 --port=5000
```

### AI Integration Options

This MCP server can be integrated with multiple AI platforms:

#### 1. Cursor (Primary Focus)
- An AI-powered code editor that can use the server for USD scene creation through the HTTP protocol
- Use the provided `cursor_integration.py` for easy integration
- See the [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for detailed setup instructions

#### 2. Claude Desktop App
- Supports native MCP protocol integration through stdio
1. Start the server in stdio mode
2. Open Claude Desktop App
3. Go to Settings > MCP Servers
4. Add a new server with the command `python` and arguments `usd_mcp_server.py`
5. Ask Claude to help you with USD operations

#### 3. ChatGPT
- Supports integration through OpenAI's function calling API or as a plugin
- Use the provided `chatgpt_integration.py` for function calling
- Use the `ai-plugin.json` and `openapi.json` files for plugin setup
- See the [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for detailed setup instructions

For comprehensive setup guides for all platforms, refer to [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md).

## MCP Tool Reference

The server provides several tools that can be used through the Model Context Protocol:

### Basic Stage Tools

#### create_stage
Create a new USD stage at the specified file path with optional template.

```javascript
{
  "file_path": "path/to/new_stage.usda",
  "template": "basic",  // Options: "empty", "basic", "full"
  "up_axis": "Y"  // Options: "Y", "Z"
}
```

#### close_stage
Unload a stage from memory to free resources.

```javascript
{
  "file_path": "path/to/stage.usda"
}
```

#### analyze_stage
Get detailed information about a USD stage and its contents.

```javascript
{
  "file_path": "path/to/stage.usda"
}
```

### Geometry Tools

#### create_mesh
Create a mesh with custom vertices and faces.

```javascript
{
  "file_path": "path/to/stage.usda",
  "prim_path": "/World/Geometry/MyMesh",
  "points": [[0,0,0], [1,0,0], [1,1,0], [0,1,0]],  // Vertices
  "face_vertex_counts": [4],  // Vertices per face
  "face_vertex_indices": [0, 1, 2, 3]  // Vertex indices for faces
}
```

#### create_primitive
Create a geometric primitive like a cube, sphere, cylinder, or cone.

```javascript
{
  "file_path": "path/to/stage.usda",
  "prim_type": "cube",  // Options: "cube", "sphere", "cylinder", "cone"
  "prim_path": "/World/Geometry/MyCube",
  "size": 2.0,  // Size or radius of the primitive
  "position": [0, 0, 0]  // Position in stage coordinates
}
```

#### create_reference
Add a reference to another USD file or a prim within it.

```javascript
{
  "file_path": "path/to/stage.usda",
  "prim_path": "/World/References/MyReference",
  "reference_file_path": "path/to/referenced_file.usda",
  "reference_prim_path": "/SomePrim"  // Optional, defaults to root
}
```

### Material Tools

#### create_material
Create an OmniPBR material with customizable properties.

```javascript
{
  "file_path": "path/to/stage.usda",
  "material_path": "/World/Materials/MyMaterial",
  "diffuse_color": [1.0, 0.0, 0.0],  // RGB values (red)
  "metallic": 0.0,  // 0.0 to 1.0
  "roughness": 0.4  // 0.0 to 1.0
}
```

#### bind_material
Assign a material to a prim.

```javascript
{
  "file_path": "path/to/stage.usda",
  "prim_path": "/World/Geometry/MyMesh",
  "material_path": "/World/Materials/MyMaterial"
}
```

### Physics Tools

#### setup_physics_scene
Create a physics scene with customizable properties.

```javascript
{
  "file_path": "path/to/stage.usda",
  "gravity": [0, -9.81, 0]  // XYZ gravity vector
}
```

#### add_rigid_body
Add rigid body physics to a prim.

```javascript
{
  "file_path": "path/to/stage.usda",
  "prim_path": "/World/Geometry/MyMesh",
  "mass": 1.0,  // Mass in kg
  "is_dynamic": true  // true for dynamic bodies, false for kinematic
}
```

#### add_collider
Add collision geometry to a prim.

```javascript
{
  "file_path": "path/to/stage.usda",
  "prim_path": "/World/Geometry/MyMesh",
  "collider_type": "mesh",  // Options: "mesh", "box", "sphere", "capsule"
  "approximation": "none"  // Options: "none", "convexHull", "convexDecomposition"
}
```

#### add_joint
Create a physics joint between two prims.

```javascript
{
  "file_path": "path/to/stage.usda",
  "joint_path": "/World/Joints/MyJoint",
  "body0_path": "/World/Geometry/Body1",
  "body1_path": "/World/Geometry/Body2",
  "joint_type": "revolute",  // Options: "fixed", "revolute", "prismatic", "spherical"
  "local_pos0": [0, 0, 0],  // Joint position in body0 space
  "local_pos1": [0, 0, 0]  // Joint position in body1 space
}
```

### Animation Tools

#### set_transform
Set or animate a prim's transform properties.

```javascript
{
  "file_path": "path/to/stage.usda",
  "prim_path": "/World/Geometry/MyMesh",
  "translate": [0, 5, 0],  // Optional: XYZ translation
  "rotate": [0, 45, 0],  // Optional: XYZ rotation in degrees
  "scale": [1, 1, 1],  // Optional: XYZ scale
  "time_code": 1.0  // Optional: time code for animation
}
```

#### create_animation
Create keyframe animation for any attribute.

```javascript
{
  "file_path": "path/to/stage.usda",
  "prim_path": "/World/Geometry/MyMesh",
  "attribute_name": "xformOp:translate",
  "key_frames": [
    {"time": 1, "value": [0, 0, 0]},
    {"time": 24, "value": [0, 5, 0]},
    {"time": 48, "value": [0, 0, 0]}
  ],
  "interpolation": "linear"  // Options: "linear", "held", "bezier"
}
```

### Utility Tools

#### export_to_format
Export a USD stage to a different format.

```javascript
{
  "file_path": "path/to/stage.usda",
  "output_path": "path/to/output.usdz",
  "format": "usdz"  // Options: "usda", "usdc", "usdz"
}
```

#### get_server_status
Get diagnostic information about the server.

```javascript
{}  // No parameters needed
```

## Using with AI Assistants

AI assistants like Claude can leverage these tools to help users create and manipulate USD scenes based on natural language descriptions. Here are some examples of user queries and the corresponding tool calls:

### Creating a Basic Scene

User request: "Create a new USD scene with a red cube"

Tool sequence:
1. `create_stage` to create a new USD stage
2. `create_primitive` to add a cube
3. `create_material` to create a red material
4. `bind_material` to apply the material to the cube

### Setting Up a Physics Simulation

User request: "Create a physics simulation with a falling cube"

Tool sequence:
1. `create_stage` to create a new USD stage
2. `create_primitive` to add a cube
3. `setup_physics_scene` to create physics scene
4. `add_rigid_body` to make the cube dynamic

### Creating an Animation

User request: "Make a sphere that bounces up and down"

Tool sequence:
1. `create_stage` to create a new USD stage
2. `create_primitive` to add a sphere
3. `set_transform` with time_code=1 for starting position
4. `set_transform` with time_code=24 for highest position
5. `set_transform` with time_code=48 for ending position

## Available Resources

| Resource URI | Description |
|--------------|-------------|
| `usd://schema` | Information about common USD schema types |
| `omniverse://help` | Help content about Omniverse Kit and USD |
| `omniverse://development-guide` | Comprehensive Omniverse development guide |

## Example Client Usage

```python
from usd_mcp_client import UsdMcpClient

# Create client
client = UsdMcpClient("python", ["usd_mcp_server.py"])

# Connect to server
await client.connect()

# Create a stage
result = await client.create_test_stage("my_stage.usda")

# Add geometry
await client.create_cube_mesh("my_stage.usda", "/root/cube")

# Analyze the stage
analysis = await client.analyze_stage("my_stage.usda")

# Close the stage
await client.close_stage("my_stage.usda")
```

## AI Integration Example

The included `ai_integration_example.py` demonstrates how to build a natural language interface to USD operations:

```bash
python ai_integration_example.py
```

This simulated assistant can:
- Create stages with natural language commands like "Create a new USD stage"
- Add geometry with commands like "Add a cube to the stage"
- Analyze USD files with "Tell me about this USD stage"
- Provide development guidance with "How do I work with materials in Omniverse?"

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Pixar USD](https://openusd.org) team for the USD core libraries
- [NVIDIA Omniverse](https://developer.nvidia.com/omniverse) team for the Omniverse platform
- The [Model Context Protocol](https://modelcontextprotocol.io) team for enabling AI-to-tool integration 