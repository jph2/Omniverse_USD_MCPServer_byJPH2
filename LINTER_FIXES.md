# Manual Linter Fixes for USD MCP Server

During the refactoring process, several linter errors were identified in the `usd_mcp_server.py` file that could not be automatically fixed. These errors need to be addressed manually.

## Identified Linter Issues

### 1. Indentation Errors in `create_stage` (lines 192-212)

The template handling logic in the `create_stage` function has inconsistent indentation. The indentation should be fixed as follows:

```python
# Create stage content based on template
if not template or template == 'empty':
    # Just create an empty root prim
    root_prim = UsdGeom.Xform.Define(stage, '/root')
    stage.SetDefaultPrim(root_prim.GetPrim())
elif template == 'basic':
    # Create basic scene structure
    root_prim = UsdGeom.Xform.Define(stage, '/World')
    stage.SetDefaultPrim(root_prim.GetPrim())
    
    # Add a camera
    camera = UsdGeom.Camera.Define(stage, '/World/Camera')
    camera.CreateFocalLengthAttr(24.0)
    camera.CreateClippingRangeAttr((0.01, 10000.0))
    camera.CreateFocusDistanceAttr(5.0)
    
    # Add a light
    light = UsdGeom.Xform.Define(stage, '/World/Light')
elif template == 'full':
    # Create comprehensive scene structure
    world = UsdGeom.Xform.Define(stage, '/World')
    stage.SetDefaultPrim(world.GetPrim())
    # ...
```

### 2. Indentation Issues in `analyze_stage` (lines 327-331)

The `else` block in the `analyze_stage` function has incorrect indentation:

```python
# Try to use cached stage or open a new one
if abs_path in stage_cache:
    stage = stage_cache[abs_path]
else:
    stage = Usd.Stage.Open(file_path)
    if not stage:
        return error_response(f"Failed to open stage: {file_path}")
    stage_cache[abs_path] = stage
```

### 3. Indentation of Loops Under `Sdf.ChangeBlock()` (multiple locations)

In multiple functions (e.g., `analyze_stage` around line 344, `create_mesh` around line 429), code under `with Sdf.ChangeBlock():` is not correctly indented:

```python
# Traverse prim hierarchy with SdfChangeBlock for better performance
with Sdf.ChangeBlock():
    for prim in Usd.PrimRange.Stage(stage):
        # ...

# In create_mesh:
with Sdf.ChangeBlock():
    # Create mesh
    mesh = UsdGeom.Mesh.Define(stage, prim_path)
    # ...
```

### 4. Try-Except Structure in `get_usd_schema` (lines 1743-1768)

The try-except block in `get_usd_schema` has incorrect indentation:

```python
@mcp.resource("usd://schema")
def get_usd_schema() -> str:
    """Return information about common USD schema types
    
    Returns:
        JSON string containing schema information
    """
    try:
        schema_info = {
            "UsdGeom.Xform": "Transform node that can be used for grouping and hierarchical transformations",
            # ...
        }
        return json.dumps(schema_info, indent=2)
    except Exception as e:
        logger.exception(f"Error retrieving USD schema information: {str(e)}")
        return error_response(f"Error retrieving USD schema information: {str(e)}")
```

## Recommendation

These indentation errors should be fixed manually to ensure proper code structure and prevent potential runtime errors. In each case, ensure that:

1. The indentation is consistent (4 spaces per level)
2. Code blocks are properly nested under their parent statements
3. All lines in a block have the same indentation level
4. Try-except blocks have proper structure

After manually fixing these issues, run a linter tool (e.g., `flake8`) to verify that the fixes have resolved the problems. 