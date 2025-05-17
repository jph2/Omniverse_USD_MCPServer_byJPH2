# Omniverse USD MCP Server

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-compatible-green)](https://docs.modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A powerful Model Context Protocol (MCP) server for working with Universal Scene Description (USD) and NVIDIA Omniverse. This server provides a standardized API for creating, manipulating, and analyzing USD scenes programmatically.

## Features

The server is organized into specialized modules that provide various USD capabilities:

### Core USD Operations
- Thread-safe stage registry with lifecycle management
- Stage creation, opening, saving, and analysis
- Prim creation, traversal, and querying
- Mesh creation and manipulation
- References and layer composition

### Physics
- Physics scene setup with gravity customization
- Rigid body simulation with dynamic/kinematic objects
- Collision shapes (mesh, box, sphere, capsule, plane)
- Joint system (revolute, prismatic, spherical, fixed, distance)

### Materials
- PBR material creation and binding
- Shader parameters (diffuse, emissive, metallic, roughness, opacity)
- Texture loading and mapping to material channels

### Animation
- Keyframe animation with interpolation types
- Transform animation (translate, rotate, scale)
- Timeline management and range setting

### Visualization
- Scene graph visualization in multiple formats (HTML, JSON, text)
- Hierarchy inspection and attribute display

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/omniverse-usd-mcp-server.git
cd omniverse-usd-mcp-server

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
# Start the server with stdio protocol (for CLI interaction)
python -m usd_mcp_server

# Start the server with HTTP protocol (for web clients)
python -m usd_mcp_server --protocol=http --host=0.0.0.0 --port=5000
```

## Using the Server

The server can be used with any Model Context Protocol (MCP) client. Here's an example using the Python client included:

```python
import asyncio
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from usd_mcp_client import UsdMcpClient

async def run_example():
    # Create client and connect
    client = UsdMcpClient("stdio", ["python", "-m", "usd_mcp_server"])
    await client.connect()
    
    try:
        # Create a new stage
        result = await client.call_tool("create_new_stage", {
            "file_path": "example.usda",
            "template": "basic",
            "up_axis": "Y"
        })
        stage_id = result["data"]["stage_id"]
        
        # Add a cube
        await client.call_tool("define_stage_prim", {
            "stage_id": stage_id,
            "prim_path": "/World/Cube",
            "prim_type": "Cube"
        })
        
        # Add physics
        await client.call_tool("setup_physics_scene", {
            "stage_id": stage_id,
            "scene_path": "/World/PhysicsScene"
        })
        
        await client.call_tool("add_rigid_body", {
            "stage_id": stage_id,
            "prim_path": "/World/Cube",
            "mass": 1.0,
            "dynamic": True
        })
        
        # Save the stage
        await client.call_tool("save_usd_stage", {
            "stage_id": stage_id
        })
        
    finally:
        await client.close()

# Run the example
asyncio.run(run_example())
```

## Server Protocols

The server supports multiple communication protocols:

- `stdio`: Standard input/output (default, for embedding in applications)
- `http`: HTTP protocol for web clients
- `websocket`: WebSocket protocol for real-time applications
- `sse`: Server-Sent Events for one-way real-time updates
- `tcp`: Raw TCP protocol
- `zmq`: ZeroMQ protocol for high-performance applications

## Available Tools

The server provides a rich set of tools for USD operations:

### Core USD Tools

- `create_new_stage`: Create a new USD stage
- `open_usd_stage`: Open an existing USD stage
- `save_usd_stage`: Save changes to a stage
- `list_stage_prims`: List all prims in a stage
- `analyze_usd_stage`: Analyze stage content
- `define_stage_prim`: Create a new prim
- `create_stage_reference`: Create a reference to another USD file
- `create_stage_mesh`: Create a mesh with geometry data

### Physics Tools

- `setup_physics_scene`: Create a physics scene
- `add_collision`: Add collision to a prim
- `remove_collision`: Remove collision from a prim
- `add_rigid_body`: Make a prim a rigid body
- `update_rigid_body`: Update rigid body properties
- `remove_rigid_body`: Remove rigid body behavior
- `create_joint`: Create a joint between two prims
- `configure_joint`: Configure joint properties
- `remove_joint`: Remove a joint

### Material Tools

- `create_material`: Create a new material
- `assign_material`: Assign a material to a prim
- `update_material`: Update material properties
- `create_texture_material`: Create a material with a texture

### Animation Tools

- `set_keyframe`: Set a keyframe for an attribute
- `create_animation`: Create animation with multiple keyframes
- `create_transform_animation`: Create a transform animation

### Visualization Tools

- `visualize_scene_graph`: Generate a visualization of the scene graph

### Server Management Tools

- `get_health`: Get server health information
- `get_available_tools`: Get information about available tools

## Resources

The server also provides additional resources:

- `usd://schema`: Information about USD schema
- `usd://help`: Help information for the server

## Project Structure

```
usd_mcp_server/
├── __init__.py           # Package initialization
├── __main__.py           # Main entry point
├── core/                 # Core USD operations
│   ├── __init__.py
│   ├── registry.py       # Thread-safe stage registry
│   └── stage_operations.py # Basic USD operations
├── physics/              # Physics simulation
│   ├── __init__.py
│   ├── setup.py          # Physics scene setup
│   ├── collisions.py     # Collision shapes
│   ├── rigid_bodies.py   # Rigid body dynamics
│   └── joints.py         # Joints and constraints
├── materials/            # Material and shader support
│   ├── __init__.py
│   └── shaders.py        # Material creation and binding
├── animation/            # Animation support
│   ├── __init__.py
│   └── keyframes.py      # Keyframe animation
├── visualization/        # Visualization utilities
│   ├── __init__.py
│   └── scene_graph.py    # Scene graph visualization
└── tests/                # Unit tests
    ├── __init__.py
    └── test_basic.py     # Basic functionality tests
```

## Example Scripts

In the `examples/` directory, you'll find example scripts demonstrating how to use the server:

- `basic_example.py`: Shows basic stage creation and manipulation
- Additional examples for specific areas (physics, materials, etc.)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Pixar USD](https://openusd.org) team for the USD core libraries
- [NVIDIA Omniverse](https://developer.nvidia.com/omniverse) team for the Omniverse platform
- The [Model Context Protocol](https://modelcontextprotocol.io) team for enabling AI-to-tool integration

---

*Maintained by Jan Haluszka*
