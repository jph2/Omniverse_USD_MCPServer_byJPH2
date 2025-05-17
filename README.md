# Omniverse_USD_MCPServer_byJPH2

A Model Context Protocol (MCP) server for NVIDIA Omniverse and Universal Scene Description (USD).

## Overview

This project provides an MCP server that offers tools and resources for working with Universal Scene Description (USD) and NVIDIA Omniverse development. It serves as a bridge between AI assistants and USD/Omniverse functionality, allowing for natural language interactions with USD operations.

## Features

- **USD Stage Operations**: Create, analyze, and manipulate USD stages and prims
- **Documentation Resources**: Comprehensive guides and references for USD schema types and Omniverse development
- **AI Integration**: Example implementation showing how to integrate with AI assistants

## Components

- `usd_mcp_server.py`: Main MCP server implementation providing USD tools and resources
- `usd_mcp_client.py`: Client to connect to the server and use its capabilities
- `ai_integration_example.py`: Demonstration of integrating with an AI assistant
- `mcp_tester.py`: Simple CLI tool to test and debug the server

## Installation

1. Ensure you have Python 3.7+ installed
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Starting the Server

```bash
python usd_mcp_server.py
```

### Using the Client

```bash
python usd_mcp_client.py
```

### Testing the Server

```bash
python mcp_tester.py
```

### Example AI Integration

```bash
python ai_integration_example.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.
