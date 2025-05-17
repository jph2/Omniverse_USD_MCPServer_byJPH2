[![Python](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-compatible-green)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Implementation Status](https://img.shields.io/badge/implementation-beta-orange)](REFACTORING.md)

> **IMPORTANT: Implementation Status**
> 
> This project is under active development. The README documents both implemented features and planned features.
> See the "Currently Implemented" section below for a precise list of available functionality.

An MCP (Model Context Protocol) server for working with USD (Universal Scene Description) and NVIDIA Omniverse. This server enables AI assistants and other clients to create, manipulate, and analyze USD scenes through a standardized API.

## Currently Implemented Features

The following features are fully implemented and available in the current version:

### Stage Management
- ✅ Create and open USD stages (`create_stage`, `open_stage`)
- ✅ Close and release stages from memory (`close_stage`, `close_stage_by_id`)
- ✅ Analyze stage contents (`analyze_stage`, `analyze_stage_by_id`) 
- ✅ Thread-safe stage registry with unique stage IDs

### Geometry Creation
- ✅ Create mesh geometry (`create_mesh`, `create_mesh_by_id`)
- ✅ Add primitive shapes (`create_primitive`, `create_primitive_by_id`)
- ✅ Add references to external USD files (`create_reference`, `create_reference_by_id`)
- ✅ Export to different USD formats (`export_to_format`)

### Materials & Appearance
- ✅ Create PBR materials (`create_material`, `create_material_by_id`) 
- ✅ Bind materials to geometry (`bind_material`, `bind_material_by_id`)

### Physics
- ✅ Setup physics scenes (`setup_physics_scene`, `setup_physics_scene_by_id`)
- ✅ Add rigid bodies (`add_rigid_body`, `add_rigid_body_by_id`)
- ✅ Add colliders with different shapes (`add_collider`)
- ✅ Create joints between rigid bodies (`add_joint`)

### Animation
- ✅ Set transforms with animation support (`set_transform`, `set_transform_by_id`)
- ✅ Create keyframe animations (`create_animation`)
- ✅ Create skeletons and skinning (`create_skeleton`, `bind_skeleton`)
- ✅ Define skeletal animations (`create_skeletal_animation`)

### Utilities
- ✅ Scene graph visualization (`visualize_scene_graph`, `visualize_scene_graph_by_id`)
- ✅ Server status monitoring (`get_server_status`, `get_registry_status`)
- ✅ Search Omniverse development guide (`search_omniverse_guide`)

### Resources
- ✅ USD schema information (`usd://schema`)
- ✅ Omniverse help (`omniverse://help`)
- ✅ Omniverse development guide (`omniverse://development-guide`)

## Planned Features

The following features are planned but not yet fully implemented:

- 🔄 Expanded physics capabilities (constraints, forces, etc.)
- 🔄 Extended animation tooling (blend shapes, motion clips)
- 🔄 Material variants and shading networks
- 🔄 Procedural geometry creation
- 🔄 USD Composition advanced features (variants, inherits)
- 🔄 Multi-stage operations

## Primary Focus: Cursor Integration

This project provides seamless integration with **Cursor**, the AI-powered code editor, allowing for a powerful USD development workflow:

- **Code-centric USD development**: Create and modify USD scenes directly from your Python code
- **AI-assisted workflows**: Leverage Cursor's AI capabilities to generate USD operations using natural language
- **Complete Python API**: Access all USD features through the `cursor_integration.py` module
- **Example scripts**: Start with the provided examples like `cursor_example.py` to learn the basics

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server in stdio mode (for Claude Desktop App)
python usd_mcp_server.py

# Start the server in HTTP mode (for web clients)
python usd_mcp_server.py --protocol=http --host=0.0.0.0 --port=5000
```

### Basic Usage with Python Client

```python
from usd_mcp_client import UsdMcpClient
import asyncio

async def run_example():
    # Create client and connect
    client = UsdMcpClient("python", ["usd_mcp_server.py"])
    await client.connect()
    
    try:
        # Open a stage
        stage_id_result = await client.open_stage("example.usda", create_if_missing=True)
        stage_id = stage_id_result  # Extract stage_id from response
        
        # Create a primitive
        await client.create_primitive_by_id(
            stage_id,
            "cube",
            "/World/Cube",
            size=2.0,
            position=(0, 1, 0)
        )
        
        # Add a material
        await client.create_material_by_id(
            stage_id,
            "/World/Materials/RedMaterial",
            diffuse_color=(1, 0, 0),
            metallic=0.1,
            roughness=0.3
        )
        
        # Bind material to geometry
        await client.bind_material_by_id(
            stage_id,
            "/World/Cube",
            "/World/Materials/RedMaterial"
        )
        
        # Visualize the scene graph
        await client.visualize_scene_graph_by_id(
            stage_id,
            output_format="text",
            include_properties=True
        )
        
        # Close the stage
        await client.close_stage_by_id(stage_id)
    finally:
        # Disconnect from server
        await client.disconnect()

# Run the example
asyncio.run(run_example())
```

## AI Integration

This project provides integration with AI assistants using the Model Context Protocol (MCP):

### Available Integrations

- **Cursor AI Integration**: Direct integration with Cursor for USD creation and manipulation
- **Claude Integration**: Connect to Anthropic's Claude model for advanced reasoning
- **ChatGPT Integration**: Use OpenAI's function calling capabilities

See [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) for setup instructions.

## Architecture

### Two-Level Architecture

The server is structured in two distinct layers for clarity and maintainability:

#### Level A: Basic USD Operations
- **StageRegistry**: Thread-safe registry for centralized stage management
- **Stage IDs**: All stages are assigned unique IDs for reference
- **Memory Management**: Efficient LRU caching

#### Level B: Advanced USD Operations
- **Stage ID-based API**: Higher-level operations using the stage registry
- **Domain-specific Tools**: Physics, animation, materials, etc.

```
Client → Level B (stage_id-based tools) → Level A (StageRegistry) → USD/Omniverse APIs
```

## Server Configuration

The server supports multiple transport protocols and configuration options:

| Argument | Description | Default |
|----------|-------------|---------|
| `--host` | Bind address | `127.0.0.1` |
| `--port` | Server port | `5000` |
| `--protocol` | Protocol (`stdio`, `http`, `sse`) | `stdio` |
| `--log-level` | Logging level | `INFO` |

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Pixar USD](https://openusd.org) team for the USD core libraries
- [NVIDIA Omniverse](https://developer.nvidia.com/omniverse) team for the Omniverse platform
- The [Model Context Protocol](https://modelcontextprotocol.io) team for enabling AI-to-tool integration

---

*Maintained by Jan Haluszka · [GitHub/jph2](https://github.com/jph2)*
