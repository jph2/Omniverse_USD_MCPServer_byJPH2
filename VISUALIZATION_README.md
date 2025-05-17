# USD Scene Graph Visualization Tools

This package provides powerful tools for visualizing and analyzing USD scene graphs with multiple formats, themes, and optimization options.

## Components

1. **Basic Visualizer** (`scene_graph_visualizer.py`):
   - Core visualization functionality
   - Multiple output formats (text, HTML, JSON, network)
   - Scene graph hierarchy representation
   - Property display options

2. **Optimized Visualizer** (`scene_graph_optimizer.py`):
   - Performance optimizations for large USD scenes
   - Smart filtering by prim types and path patterns
   - Multiple visual themes (light, dark, high-contrast)
   - Automatic optimizations based on scene complexity

3. **Example Scripts**:
   - `scene_graph_example.py`: Basic visualization demo
   - `optimized_visualization_example.py`: Advanced features demo
   - `benchmark_visualizers.py`: Performance comparison tool

## Usage

### Basic Visualization

Use the basic scene graph visualizer directly:

```python
from scene_graph_visualizer import UsdSceneGraphVisualizer

# Create a visualizer for a USD stage
visualizer = UsdSceneGraphVisualizer("my_stage.usda")

# Generate text visualization
text_output = visualizer.to_text(include_properties=True)
print(text_output)

# Generate HTML visualization
html_file = visualizer.to_html("scene_graph.html")
print(f"HTML visualization saved to {html_file}")

# Generate JSON or network data
json_data = visualizer.to_json("scene_data.json")
network_data = visualizer.to_network_data("network_data.json")
```

### Optimized Visualization

Use the scene graph optimizer for advanced options:

```python
from scene_graph_optimizer import UsdSceneGraphOptimizer

# Create optimizer for a USD stage
optimizer = UsdSceneGraphOptimizer("my_stage.usda")

# Generate filtered visualization with dark theme
result = optimizer.visualize(
    output_format="html",
    filter_types=["Material"],  # Show only materials
    theme="dark",               # Use dark theme
    open_browser=True           # Open in browser automatically
)
```

### Through Cursor Integration

Use the Cursor integration to visualize stages:

```python
from cursor_integration import CursorUsdTools

usd = CursorUsdTools()

# Generate visualization
result = usd.visualize_scene_graph(
    "my_stage.usda",
    output_format="html", 
    output_path="visualization.html",
    include_properties=True
)
```

## Command Line Usage

Run the tools directly from the command line:

```bash
# Basic visualizer
python scene_graph_visualizer.py my_stage.usda --format html --output viz.html --properties

# Optimized visualizer
python scene_graph_optimizer.py my_stage.usda --format html --filter-types Mesh Material --theme dark

# Create and visualize a demo scene
python scene_graph_example.py

# Create a complex demo scene with optimization options
python optimized_visualization_example.py

# Compare performance of different visualization approaches
python benchmark_visualizers.py --generate medium large
```

## Output Formats

### Text Format
Simple ASCII tree representation of the scene hierarchy:
```
USD Scene Graph: my_stage.usda
================================================================================
Up Axis: Y
Meters Per Unit: 0.01
Time Range: 1.0 to 240.0
Default Prim: /World
================================================================================
└── World (Xform)
    ├── Geometry (Xform)
    │   └── Cube (Cube)
    ├── Materials (Xform)
    │   └── RedMaterial (Material)
    └── Cameras (Xform)
        └── MainCamera (Camera)
```

### HTML Format
Interactive web-based visualization with:
- Collapsible/expandable tree nodes
- Search functionality
- Color-coded by prim type
- Property inspection for each prim
- Multiple visual themes

### JSON Format
Structured data for programmatic use:
```json
{
  "name": "my_stage.usda",
  "path": "/",
  "type": "stage",
  "properties": {
    "up_axis": "Y",
    "meters_per_unit": 0.01,
    "start_time_code": 1.0,
    "end_time_code": 240.0
  },
  "children": [
    {
      "name": "World",
      "path": "/World",
      "type": "Xform",
      "properties": {},
      "children": [...]
    }
  ]
}
```

### Network Format
Graph data for network visualization tools where:
- Nodes represent prims
- Edges represent parent-child relationships and material bindings

## Troubleshooting

### Common Issues

1. **USD Libraries Not Found**:
   - Ensure USD Python libraries are in your PYTHONPATH
   - Check that you're using the correct Python environment

2. **MCP Server Connection Issues**:
   - Verify the MCP server is running: `python usd_mcp_server.py --host 0.0.0.0 --port 5000`
   - Check connection settings in `cursor_integration.py`

3. **Memory Issues with Large Scenes**:
   - Use filtering options to focus on specific parts of the scene
   - Limit visualization depth with `max_depth` parameter
   - Use the optimized visualizer which applies automatic optimizations

4. **HTML Visualization Not Opening**:
   - Set `open_browser=True` to automatically open in default browser
   - Check that the file was created in the expected location
   - Try opening the HTML file manually in your browser

## Performance Tips

1. **For Large Scenes**:
   - Use type filtering to focus on specific prim types
   - Use path pattern filtering to limit the scope
   - Set a reasonable max_depth value
   - Consider using the text format for initial exploration

2. **Memory Optimization**:
   - The scene graph optimizer automatically applies optimizations based on scene complexity
   - For very large scenes, consider using the "network" format which is more memory-efficient

3. **Benchmark Different Approaches**:
   - Use `benchmark_visualizers.py` to compare performance across formats and approaches
   - Experiment with different optimization settings for your specific USD files 