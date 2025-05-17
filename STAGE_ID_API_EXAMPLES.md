# Stage ID-based API Examples

This document provides examples of how to use the new stage ID-based API for common USD operations.

## Basic Stage Operations

### Opening a Stage

```python
from cursor_integration import CursorUsdTools

tools = CursorUsdTools()

# Open an existing stage
result = tools.open_stage("my_scene.usda")
if result["ok"]:
    stage_id = result["data"]["stage_id"]
    print(f"Stage opened with ID: {stage_id}")
else:
    print(f"Error: {result['message']}")

# Create a new stage if it doesn't exist
result = tools.open_stage("new_scene.usda", create_if_missing=True)
if result["ok"]:
    stage_id = result["data"]["stage_id"]
    print(f"Stage created with ID: {stage_id}")
```

### Closing a Stage

```python
# Close a stage, saving if modified
result = tools.close_stage(stage_id, save_if_modified=True)
if result["ok"]:
    print("Stage closed successfully")
```

## Creating Geometric Primitives

```python
# Create a sphere
sphere_result = tools.create_primitive(
    stage_id=stage_id,
    primitive_type="sphere",
    prim_path="/World/Sphere",
    size=1.0,
    position=[0, 1, 0]
)

# Create a cube
cube_result = tools.create_primitive(
    stage_id=stage_id,
    primitive_type="cube",
    prim_path="/World/Cube",
    size=1.0,
    position=[2, 0, 0]
)

# Create a cylinder
cylinder_result = tools.create_primitive(
    stage_id=stage_id,
    primitive_type="cylinder",
    prim_path="/World/Cylinder",
    size=1.0,
    position=[-2, 0, 0]
)
```

## Working with Materials

```python
# Create a material
material_result = tools.create_material(
    stage_id=stage_id,
    material_path="/World/Materials/RedMaterial",
    diffuse_color=[1, 0, 0],  # Red
    metallic=0.1,
    roughness=0.3
)

# Bind the material to a prim
bind_result = tools.bind_material(
    stage_id=stage_id,
    material_path="/World/Materials/RedMaterial",
    prim_path="/World/Sphere"
)
```

## Transforming Objects

```python
# Set transform of a prim
transform_result = tools.set_transform(
    stage_id=stage_id,
    prim_path="/World/Cube",
    position=[3, 0, 0],
    rotation=[0, 45, 0],  # 45 degrees around Y axis
    scale=[1, 2, 1]  # Stretched in Y dimension
)
```

## Visualizing the Scene Graph

```python
# Generate a text visualization
text_result = tools.visualize_scene_graph(
    stage_id=stage_id,
    format="text"
)
if text_result["ok"]:
    print(text_result["data"]["visualization"])

# Create an HTML visualization
html_result = tools.visualize_scene_graph(
    stage_id=stage_id,
    format="html",
    output_path="scene_graph.html",
    theme="dark"
)
if html_result["ok"]:
    print(f"HTML visualization saved to: {html_result['data']['output_path']}")
```

## Creating a Complete Scene

```python
# Example of creating a complete scene with multiple objects and materials
def create_complete_scene(file_path):
    tools = CursorUsdTools()
    
    # Open a new stage
    result = tools.open_stage(file_path, create_if_missing=True)
    if not result["ok"]:
        return result
    
    stage_id = result["data"]["stage_id"]
    
    # Create a ground plane
    tools.create_primitive(
        stage_id=stage_id,
        primitive_type="cube",
        prim_path="/World/Ground",
        size=10.0,
        position=[0, -0.5, 0]
    )
    
    tools.set_transform(
        stage_id=stage_id,
        prim_path="/World/Ground",
        scale=[1.0, 0.1, 1.0]
    )
    
    # Create some objects
    primitives = [
        {"type": "sphere", "path": "/World/Sphere", "pos": [0, 1, 0], "color": [1, 0, 0]},
        {"type": "cube", "path": "/World/Cube", "pos": [2, 0.5, 0], "color": [0, 0, 1]},
        {"type": "cylinder", "path": "/World/Cylinder", "pos": [-2, 0.5, 0], "color": [0, 1, 0]}
    ]
    
    # Create materials folder
    tools.define_prim(
        stage_id=stage_id,
        prim_path="/World/Materials",
        prim_type="Scope"
    )
    
    # Create primitives and their materials
    for i, prim in enumerate(primitives):
        tools.create_primitive(
            stage_id=stage_id,
            primitive_type=prim["type"],
            prim_path=prim["path"],
            size=1.0,
            position=prim["pos"]
        )
        
        material_path = f"/World/Materials/Material_{i}"
        tools.create_material(
            stage_id=stage_id,
            material_path=material_path,
            diffuse_color=prim["color"]
        )
        
        tools.bind_material(
            stage_id=stage_id,
            material_path=material_path,
            prim_path=prim["path"]
        )
    
    # Save the stage
    tools.save_stage(stage_id)
    
    return {
        "ok": True,
        "message": "Scene created successfully",
        "data": {"stage_id": stage_id}
    }
```

## Benefits of the Stage ID-based API

1. **Memory Management**: Stages remain in memory until explicitly closed, avoiding redundant loading
2. **Thread Safety**: All operations are thread-safe, protected by the stage registry's locking mechanisms
3. **Consistent API**: All functions follow the same pattern of accepting a stage_id parameter
4. **Explicit Lifecycle**: Clear lifecycle management for stages with explicit open/close operations
5. **Performance**: Reduced file I/O by reusing open stages through their IDs 