# Scene Graph Visualization Documentation

This guide covers the scene graph visualization capabilities of the Omniverse USD MCP Server, which provide powerful tools for understanding and navigating USD scene hierarchies.

## Overview

The scene graph visualizer offers multiple output formats and visualization options to help you understand complex USD scene structures. Key features include:

- Multiple output formats (text, HTML, JSON, network)
- Visual themes for better readability
- Filtering by prim types and path patterns
- Performance optimizations for large scenes
- Integration with AI assistants through the MCP server

## Visualization Formats

### Text Format

The simplest visualization is the text format, which displays the scene hierarchy as an ASCII tree.

```
/
├── World
│   ├── Ground
│   ├── RedSphere
│   │   └── Looks
│   │       └── RedMaterial
│   ├── BlueCube
│   │   └── Looks
│   │       └── BlueMaterial
│   └── Materials
│       ├── RedMaterial
│       └── BlueMaterial
```

**Usage:**
```python
from cursor_integration import CursorUsdTools

tools = CursorUsdTools()
result = tools.visualize_scene_graph(
    stage_id="stage_123",
    format="text"
)

print(result["data"]["visualization"])
```

### HTML Format

The HTML format provides an interactive tree view with collapsible nodes, search functionality, and color-coded prim types. This is ideal for complex scenes where you need to navigate the hierarchy dynamically.

**Features:**
- Collapsible/expandable tree nodes
- Search functionality
- Prim type color coding
- Property inspection
- Multiple themes (light, dark, high-contrast)

**Usage:**
```python
result = tools.visualize_scene_graph(
    stage_id="stage_123",
    format="html",
    output_path="scene_visualization.html",
    theme="dark"
)
```

### JSON Format

The JSON format provides a structured representation of the scene graph that can be easily processed by other tools or used for custom visualizations.

**Usage:**
```python
result = tools.visualize_scene_graph(
    stage_id="stage_123",
    format="json",
    output_path="scene_data.json"
)
```

**Example output structure:**
```json
{
  "name": "Root",
  "path": "/",
  "type": "Stage",
  "children": [
    {
      "name": "World",
      "path": "/World",
      "type": "Xform",
      "children": [
        {
          "name": "Sphere",
          "path": "/World/Sphere",
          "type": "Sphere",
          "properties": {
            "size": 1.0,
            "visibility": "inherited"
          }
        }
      ]
    }
  ]
}
```

### Network Format

The network format generates data suitable for network visualization libraries like D3.js. It represents prims as nodes and relationships as edges.

**Usage:**
```python
result = tools.visualize_scene_graph(
    stage_id="stage_123",
    format="network",
    output_path="network_data.json"
)
```

## Filtering Options

### Type Filtering

You can filter the visualization to show only specific prim types:

```python
result = tools.visualize_scene_graph(
    stage_id="stage_123",
    format="html",
    output_path="materials.html",
    filter_types=["Material"],
    theme="light"
)
```

Common prim types to filter for:
- `Xform`
- `Mesh`
- `Material`
- `Sphere`, `Cube`, `Cylinder`, `Cone`
- `PhysicsRigidBodyAPI`
- `PhysicsCollisionAPI`

### Path Filtering

You can filter by path patterns using regular expressions:

```python
result = tools.visualize_scene_graph(
    stage_id="stage_123",
    format="html",
    output_path="character.html",
    filter_pattern="Character",
    theme="dark"
)
```

### Depth Limiting

You can limit the depth of the hierarchy to focus on high-level structure:

```python
result = tools.visualize_scene_graph(
    stage_id="stage_123",
    format="text",
    max_depth=3
)
```

## Themes

The HTML visualization supports multiple themes for different preferences and environments:

- **Light**: Clean, bright theme for standard usage
- **Dark**: Reduced eye strain for darker environments
- **High Contrast**: Accessibility-focused theme with strong contrast

```python
result = tools.visualize_scene_graph(
    stage_id="stage_123",
    format="html",
    output_path="visualization.html",
    theme="dark"  # or "light" or "contrast"
)
```

## Performance Optimizations

The scene graph visualizer includes optimizations for handling large USD scenes:

- **Automatic Complexity Detection**: Analyzes scene size and applies appropriate optimizations
- **Lazy Loading**: Defers loading of deep hierarchies until needed
- **Property Filtering**: Only loads the most relevant properties for visualization

For large scenes (1000+ prims), the visualizer automatically:
1. Limits property display to essential attributes
2. Sets reasonable depth limits (but allows expanding)
3. Uses more efficient traversal methods

## Advanced Usage: Scene Graph Optimizer

For more advanced visualization needs, you can use the `UsdSceneGraphOptimizer` class directly:

```python
from scene_graph_optimizer import UsdSceneGraphOptimizer

# Create optimizer for a USD stage
optimizer = UsdSceneGraphOptimizer("/path/to/stage.usda")

# Generate visualization with specific options
result = optimizer.visualize(
    output_format="html",
    output_path="visualization.html",
    filter_types=["Material"],  # Only show materials
    filter_pattern="Character",  # Only show paths containing "Character"
    theme="dark",               # Use dark theme
    max_depth=3,                # Limit display depth 
    open_browser=True           # Open in browser automatically
)
```

## Integration with Cursor

Cursor's natural language interface can be used to generate visualizations through the MCP server:

```
Visualize the scene graph of my current stage in HTML format with a dark theme, filtering for only material prims
```

Cursor will translate this into the appropriate API calls to the MCP server.

## Using with ChatGPT or Claude

When using with ChatGPT or Claude, you can request visualizations through natural language:

```
Show me the structure of the USD scene, focusing only on the geometry elements
```

The AI assistant will call the appropriate endpoints to generate the visualization.

## Example Workflow

1. Create a new USD stage with some content
2. Visualize the scene graph to understand its structure
3. Make targeted changes based on the visualization
4. Generate a new visualization to confirm changes
5. Export the visualization for documentation or sharing

```python
from cursor_integration import CursorUsdTools

tools = CursorUsdTools()

# 1. Create a stage with content
stage_result = tools.open_stage("example.usda", create_new=True)
stage_id = stage_result["data"]["stage_id"]

tools.create_primitive(stage_id, "sphere", "/World/Sphere", size=1.0)
tools.create_primitive(stage_id, "cube", "/World/Cube", position=[2, 0, 0])

# 2. Visualize the initial scene
tools.visualize_scene_graph(
    stage_id=stage_id,
    format="html",
    output_path="initial_scene.html"
)

# 3. Make changes based on the visualization
tools.create_material(
    stage_id=stage_id,
    material_path="/World/Materials/RedMaterial",
    diffuse_color=[1, 0, 0]
)

tools.bind_material(
    stage_id=stage_id,
    material_path="/World/Materials/RedMaterial",
    prim_path="/World/Sphere"
)

# 4. Generate a new visualization to confirm changes
tools.visualize_scene_graph(
    stage_id=stage_id,
    format="html",
    output_path="updated_scene.html"
)

# 5. Save the stage
tools.save_stage(stage_id)
```

## Troubleshooting

- **Visualization too large**: Use `max_depth` to limit the hierarchy depth
- **Too many properties**: Use `filter_types` to focus on specific prim types
- **Performance issues**: Consider using the text format for very large scenes
- **Empty visualization**: Check that the stage is properly loaded and contains data

## Related Documentation

- [Main README](README.md)
- [Integration Guide](INTEGRATION_GUIDE.md)
- [USD MCP Server API Reference](MCP_README.md)
- [Autopoietic Development Story](SCENE_GRAPH_GENESIS.md) 