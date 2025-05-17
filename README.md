[![Python](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-compatible-green)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

# Omniverse USD MCP Server

An MCP (Model Context Protocol) server for working with USD (Universal Scene Description) and NVIDIA Omniverse. This server enables AI assistants and other clients to create, manipulate, and analyze USD scenes through a standardized API.

## Primary Focus: Cursor Integration

This project provides seamless integration with **Cursor**, the AI-powered code editor, allowing for a powerful USD development workflow:

- **Code-centric USD development**: Create and modify USD scenes directly from your Python code
- **AI-assisted workflows**: Leverage Cursor's AI capabilities to generate USD operations using natural language
- **Complete Python API**: Access all USD features through the `cursor_integration.py` module
- **Example scripts**: Start with the provided examples like `cursor_example.py` to learn the basics

### Quick Start with Cursor

```python
# Import the Cursor USD tools
from cursor_integration import CursorUsdTools

# Initialize the tools
usd_tools = CursorUsdTools()

# Create a stage and add a primitive
usd_tools.create_stage("my_scene.usda")
usd_tools.create_primitive("my_scene.usda", "cube", "/World/Cube", size=2.0)

# Try the example script to see more advanced features
# python cursor_example.py
```

Additional integrations for Claude and ChatGPT are also included. See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for detailed setup instructions.

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

## Feature Highlights

- **USD Stage Creation and Manipulation**: Create, edit, and analyze USD stages with comprehensive tooling
- **Geospatial Data Support**: Import and visualize geospatial data in USD format
- **Physics Simulation**: Set up physics scenes with rigid bodies, colliders, and joints
- **Animation**: Create keyframe animations and skeletal animations
- **AI Integration**: Connect to AI assistants like Cursor, Claude, and ChatGPT for natural language USD development
- **Scene Graph Visualization**: Interactive visualization of USD scene graphs in multiple formats (text, HTML, JSON, network)
  - **Performance-Optimized Visualizer**: Handles large USD scenes efficiently with smart filtering and lazy loading
  - **Multiple Themes**: Choose from light, dark, or high-contrast visual themes
  - **Type Filtering**: Focus on specific prim types like materials, meshes, or physics objects
  - **Path Filtering**: Use regex patterns to filter scene elements by path
  - **Visualization Formats**: Export as text, interactive HTML, JSON data, or network graph format
- **Omniverse Development Resources**: Access documentation and development guides directly through the server

## AI Integration Options

The MCP server provides three AI integration options:

1. **Cursor AI Integration** (Primary): Direct integration with Cursor for USD creation and manipulation
2. **Claude Integration**: Connect to Anthropic's Claude model for advanced reasoning
3. **ChatGPT Integration**: Use OpenAI's function calling capabilities

See [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) for detailed instructions.

## Advanced Visualization Tools

The MCP server includes powerful scene graph visualization capabilities that allow you to:

### Basic Visualization

```python
from cursor_integration import CursorUsdTools

usd = CursorUsdTools()
usd.visualize_scene_graph(
    "my_stage.usda",
    output_format="html",
    include_properties=True
)
```

### Optimized Visualization

For more advanced visualization options, use the optimized visualizer:

```python
from scene_graph_optimizer import UsdSceneGraphOptimizer

# Create optimizer for a USD stage
optimizer = UsdSceneGraphOptimizer("my_stage.usda")

# Create filtered visualization with dark theme
optimizer.visualize(
    output_format="html",
    filter_types=["Material"],  # Show only materials
    theme="dark",
    open_browser=True
)

# Create pattern-filtered visualization
optimizer.visualize(
    output_format="html",
    filter_pattern="Building",  # Show only prims with "Building" in the path
    theme="contrast"
)
```

### Performance Benchmarking

Compare different visualization approaches:

```bash
# Run benchmarks on test stages
python benchmark_visualizers.py --generate small medium large

# Run benchmarks with specific formats
python benchmark_visualizers.py --stages my_stage.usda --formats html json 

# Generate comparison report
python benchmark_visualizers.py --generate medium large --report comparison.html
```

## Getting Started

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server in stdio mode (for Claude Desktop App)
python usd_mcp_server.py

# Start the server in HTTP mode (for Cursor and web clients)
python usd_mcp_server.py --protocol=http --host=0.0.0.0 --port=5000
```

### Usage with Cursor

1. Start the server in HTTP mode
2. Import the Cursor integration module in your Python script:
   ```python
   from cursor_integration import CursorUsdTools
   ```
3. Use the provided methods to create and manipulate USD scenes
4. Run the example script to see a full demo:
   ```bash
   python cursor_example.py
   ```

## USD Tools

### Basic Stage Operations
| Tool Name | Description |
|-----------|-------------|
| `create_stage` | Create a new USD stage with optional templates |
| `close_stage` | Unload and release a USD stage |
| `analyze_stage` | Get detailed information about stage contents |

### Geometry & Scene Composition
| Tool Name | Description |
|-----------|-------------|
| `create_mesh` | Add a mesh to a USD stage |
| `create_primitive` | Create geometric primitives (cube, sphere, cylinder, cone) |
| `create_reference` | Add a reference to an external USD file |
| `export_to_format` | Export a USD stage to a different format (usda, usdc, usdz) |

### Materials & Shading
| Tool Name | Description |
|-----------|-------------|
| `create_material` | Create an OmniPBR material with PBR parameters |
| `bind_material` | Bind a material to geometry |

### Physics
| Tool Name | Description |
|-----------|-------------|
| `setup_physics_scene` | Create a physics scene with configurable properties |
| `add_rigid_body` | Add rigid body properties to geometry |
| `add_collider` | Add collision geometry with customizable shapes |
| `add_joint` | Create joints between rigid bodies (fixed, revolute, prismatic, spherical) |

### Animation
| Tool Name | Description |
|-----------|-------------|
| `set_transform` | Set or animate transform properties (translate, rotate, scale) |
| `create_animation` | Create keyframe animations for any prim attribute |
| `create_skeleton` | Create a skeleton for character rigging |
| `bind_skeleton` | Bind a skeleton to a mesh for skinning |
| `create_skeletal_animation` | Create skeletal animations with joint transformations |

### Utilities
| Tool Name | Description |
|-----------|-------------|
| `search_omniverse_guide` | Search development documentation |
| `get_server_status` | Get current server information and resource usage |

## Available Resources

| Resource URI | Description |
|--------------|-------------|
| `usd://schema` | Information about common USD schema types |
| `omniverse://help` | Help content about Omniverse Kit and USD |
| `omniverse://development-guide` | Comprehensive Omniverse development guide |

## Example Client Usage

```python
from cursor_integration import CursorUsdTools

# Initialize tools
usd_tools = CursorUsdTools()

# Create a stage and add a cube
usd_tools.create_stage("my_stage.usda")
usd_tools.create_primitive("my_stage.usda", "cube", "/World/Cube", size=2.0, position=(0, 1, 0))

# Add a material
usd_tools.create_material(
    "my_stage.usda", 
    "/World/Materials/RedMaterial", 
    diffuse_color=(1, 0, 0), 
    metallic=0.1, 
    roughness=0.3
)
usd_tools.bind_material("my_stage.usda", "/World/Cube", "/World/Materials/RedMaterial")

# Setup physics
usd_tools.setup_physics_scene("my_stage.usda")
usd_tools.add_rigid_body("my_stage.usda", "/World/Cube", mass=5.0)

# Add animation
keyframes = [
    {"time": 1, "value": [0, 5, 0]},
    {"time": 48, "value": [0, 0, 0]},
    {"time": 96, "value": [0, 5, 0]}
]
usd_tools.create_animation(
    "my_stage.usda",
    "/World/Cube",
    "xformOp:translate",
    keyframes,
    interpolation="linear"
)

# Analyze and export
analysis = usd_tools.analyze_stage("my_stage.usda")
usd_tools.export_to_format("my_stage.usda", "my_stage.usdz", "usdz")
```

## AI Integration Examples

The included AI integration files demonstrate how to build natural language interfaces for USD operations:

- **Cursor**: `cursor_integration.py` and `cursor_example.py`
- **Claude**: `claude_integration.py`
- **ChatGPT**: `chatgpt_integration.py`

See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for detailed setup instructions for each platform.

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Pixar USD](https://openusd.org) team for the USD core libraries
- [NVIDIA Omniverse](https://developer.nvidia.com/omniverse) team for the Omniverse platform
- The [Model Context Protocol](https://modelcontextprotocol.io) team for enabling AI-to-tool integration

---

## 🚀 Table of Contents

- [Features](#features)  
- [Architecture](#architecture)  
- [Getting Started](#getting-started)  
  - [Prerequisites](#prerequisites)  
  - [Installation](#installation)  
- [Usage](#usage)  
  - [Start the Server](#start-the-server)  
  - [Client Example](#client-example)  
  - [AI Integration](#ai-integration)  
- [Configuration](#configuration)  
- [API Reference](#api-reference)  
- [Testing](#testing)  
- [Contributing](#contributing)  
- [License](#license)  
- [Acknowledgments](#acknowledgments)  

---

## 🏗 Architecture

```
┌─────────────┐       ┌───────────────┐       ┌────────────────────────┐
│  Client /   │  RPC  │    MCP Server  │  USD  │   Omniverse / USD API   │
│  AI Agent   ├──────►│  (Flask/zmq)   ├──────►│  (pxr.Usd, omni.client)  │
└─────────────┘       └───────────────┘       └────────────────────────┘
```

1. **Client**  
   Sends JSON‐RPC calls (e.g. `open_stage`, `list_prims`, `edit_prim`).  
2. **MCP Server** (`usd_mcp_server.py`)  
   - Parses requests  
   - Dispatches to internal Python handlers  
   - Returns JSON responses with data or error codes  
3. **USD / Omniverse APIs**  
   - Under the hood uses `pxr.Usd`, `pxr.Sdf`, and `omni.client`  
   - Manages stages, layers, references, payloads, and Omniverse Nucleus sessions  

---

## 🛠 Getting Started

### Prerequisites

- Python 3.7 or higher  
- [Omniverse Kit Python](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/latest/guide/installation.html) (if you plan to use live Nucleus features)  
- Access to an Omniverse Nucleus server (for streaming/collaboration)

### Installation

Clone and install dependencies:

```bash
git clone https://github.com/jph2/Omniverse_USD_MCPServer_byJPH2.git
cd Omniverse_USD_MCPServer_byJPH2
pip install -r requirements.txt
```

---

## 🚀 Usage

### Start the Server

```bash
python usd_mcp_server.py --host 0.0.0.0 --port 5000
```

* `--host`: bind address (default `127.0.0.1`)
* `--port`: HTTP port (default `5000`)
* `--protocol`: `http` (Flask) or `zmq` (ZeroMQ)

### Client Example

```python
from usd_mcp_client import MCPClient

client = MCPClient("http://localhost:5000")

# Open or create a stage
resp = client.open_stage("/tmp/example.usda", createNew=True)
print("Stage ID:", resp["stage_id"])

# List all prims
prims = client.list_prims(stage_id=resp["stage_id"])
print("Prims:", prims)

# Define a new Xform
client.define_prim(stage_id=resp["stage_id"], path="/World/MyXform", type="Xform")
```

### AI Integration

See [`ai_integration_example.py`](ai_integration_example.py) for a demo of calling the MCP server from an LLM-based assistant, handling prompts like "Create a new material and bind it to `/World/Looks/MyMat`."

---

## ⚙️ Configuration

You can override defaults via environment variables or a `config.yaml`:

| Variable          | Default        | Description                      |
| ----------------- | -------------- | -------------------------------- |
| `MCP_HOST`        | `127.0.0.1`    | Server bind address              |
| `MCP_PORT`        | `5000`         | HTTP or ZMQ port                 |
| `MCP_PROTOCOL`    | `http`         | `http` or `zmq`                  |
| `LOG_LEVEL`       | `INFO`         | `DEBUG`, `INFO`, `WARN`, `ERROR` |
| `OMNI_CLIENT_URL` | `omniverse://` | Nucleus connection string        |

> **Note:** If you plan to authenticate with Omniverse Nucleus, set `OMNI_CLIENT_TOKEN` accordingly.

---

## 📖 API Reference

| Endpoint                 | Method | Description                                 |
| ------------------------ | ------ | ------------------------------------------- |
| `/open_stage`            | POST   | Open or create a USD stage.                 |
| `/close_stage`           | POST   | Unload and release a stage.                 |
| `/list_prims`            | GET    | Return all prim paths under a given root.   |
| `/define_prim`           | POST   | Define a new prim at `path` with `type`.    |
| `/get_attribute`         | GET    | Read an attribute's current value.          |
| `/set_attribute`         | POST   | Write an attribute value (with validation). |
| `/execute_command`       | POST   | Run a custom registered command (undoable). |
| *…plus extension points* |        |                                             |

*For full endpoint details, see [API\_DOCS.md](API_DOCS.md).*

---

## 🧪 Testing

We use `pytest` and Pixar's [`usdchecker`](https://github.com/PixarAnimationStudios/USD/tree/release/tools/usdchecker):

```bash
# Run Python unit tests
pytest tests/

# Golden-file validation
usdchecker --input tests/golden/sample.usda --check-only

# Linting
flake8 .
```

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Commit your changes (`git commit -m "feat: add XYZ"`)
4. Push to your branch (`git push origin feat/my-feature`)
5. Open a Pull Request

Please follow our [Code of Conduct](CODE_OF_CONDUCT.md) and include unit tests for new features.

---

## 📜 License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

* [Pixar USD](https://openusd.org) team for the USD core libraries
* NVIDIA Omniverse for the Kit SDK and Nucleus platform
* [ColinKennedy/USD-Cookbook](https://github.com/ColinKennedy/USD-Cookbook) for USD examples
* All contributors and community members

---

*Maintained by Jan Haluszka · [GitHub/jph2](https://github.com/jph2)*
