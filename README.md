# Omniverse USD MCP Server

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-compatible-green)](https://docs.modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Model Context Protocol (MCP) server for working with Universal Scene Description (USD) and NVIDIA Omniverse. This server provides a standardized API for basic USD operations.

## Core Features

The server currently provides these core USD operations:

- Create, open, and save USD stages
- List and analyze stage contents
- Create prims and define basic geometry
- Add references to external USD files
- Proper resource management with stage cleanup

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
        
        # Save the stage
        await client.call_tool("save_usd_stage", {
            "stage_id": stage_id
        })
        
        # Close and cleanup the stage when done
        await client.call_tool("close_stage", {
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

The server provides these tools for USD operations:

### Core USD Tools

- `create_new_stage`: Create a new USD stage
- `open_usd_stage`: Open an existing USD stage
- `save_usd_stage`: Save changes to a stage
- `close_stage`: Close and unload a stage, freeing resources
- `list_stage_prims`: List all prims in a stage
- `analyze_usd_stage`: Analyze stage content
- `define_stage_prim`: Create a new prim
- `create_stage_reference`: Create a reference to another USD file
- `create_stage_mesh`: Create a mesh with geometry data

## Example Scripts

In the `examples/` directory, you'll find example scripts demonstrating how to use the server:

- `basic_example.py`: Shows basic stage creation and manipulation


## Production Readiness: 
Requires ~20 hours of polish (tests, CI, error handling) to meet enterprise standards.

This implementation has a strong foundation but needs hardening for mission-critical workflows. If you’re willing to contribute missing tests/maintenance tools, it’s a viable starting point for USD automation.



## Future Roadmap

Future releases will expand functionality to include:

- Physics simulation tools
- Material creation and management
- Animation keyframing
- Scene graph visualization
- Advanced geometry operations

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
