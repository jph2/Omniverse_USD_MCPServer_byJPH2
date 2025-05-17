"""
Omniverse_USD_MCPServer_byJPH2

This module provides a Model Context Protocol (MCP) server that offers tools and resources
for working with Universal Scene Description (USD) and NVIDIA Omniverse development.

The server provides the following capabilities:
- Tools for creating and manipulating USD stages and prims
- Resources containing documentation and guides for USD and Omniverse development
- Search functionality for the Omniverse Development Guide
"""

from mcp.server.fastmcp import FastMCP, Context
from pxr import Usd, UsdGeom, Sdf
import os
import json
import re
import argparse
import sys
from typing import Dict, List, Any, Optional, Union

# Create a named server
mcp = FastMCP("Omniverse_USD_MCPServer_byJPH2")

# =============================================================================
# USD Stage Tools
# =============================================================================

@mcp.tool()
def create_stage(file_path: str) -> str:
    """Create a new USD stage and save it to the specified file path
    
    Args:
        file_path: Path where the USD stage should be saved
        
    Returns:
        Confirmation message or error description
    """
    try:
        stage = Usd.Stage.CreateNew(file_path)
        # Create a root xform prim
        root_prim = UsdGeom.Xform.Define(stage, '/root')
        stage.SetDefaultPrim(root_prim.GetPrim())
        stage.GetRootLayer().Save()
        return f"Successfully created USD stage at {file_path}"
    except Exception as e:
        return f"Error creating stage: {str(e)}"

@mcp.tool()
def analyze_stage(file_path: str) -> str:
    """Analyze a USD stage and return information about its contents
    
    Args:
        file_path: Path to the USD file to analyze
        
    Returns:
        JSON string containing stage information or error description
    """
    try:
        if not os.path.exists(file_path):
            return f"File not found: {file_path}"
        
        stage = Usd.Stage.Open(file_path)
        if not stage:
            return f"Failed to open stage: {file_path}"
        
        # Get basic stage information
        result = {
            "root_layer_path": stage.GetRootLayer().realPath,
            "up_axis": UsdGeom.GetStageUpAxis(stage),
            "time_code_range": [stage.GetStartTimeCode(), stage.GetEndTimeCode()],
            "default_prim": str(stage.GetDefaultPrim().GetPath()) if stage.GetDefaultPrim() else None,
            "prims": []
        }
        
        # Traverse prim hierarchy
        for prim in Usd.PrimRange.Stage(stage):
            prim_data = {
                "path": str(prim.GetPath()),
                "type": prim.GetTypeName(),
                "active": prim.IsActive(),
                "attributes": []
            }
            
            # Gather attribute information for this prim
            if prim.GetTypeName():  # Only if prim has a type
                for attribute in prim.GetAttributes():
                    attr_data = {
                        "name": attribute.GetName(),
                        "type": str(attribute.GetTypeName())
                    }
                    
                    # Try to get the attribute value
                    try:
                        value = attribute.Get()
                        if value is not None:
                            attr_data["value"] = str(value)
                    except:
                        pass  # Skip if we can't get the value
                    
                    prim_data["attributes"].append(attr_data)
            
            result["prims"].append(prim_data)
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error analyzing stage: {str(e)}"

@mcp.tool()
def create_mesh(
    file_path: str, 
    prim_path: str, 
    points: List[tuple], 
    face_vertex_counts: List[int], 
    face_vertex_indices: List[int]
) -> str:
    """Create a mesh in a USD stage with specified geometry data
    
    Args:
        file_path: Path to the USD file
        prim_path: Path within the stage to create the mesh
        points: List of 3D points (vertices) as tuples
        face_vertex_counts: Number of vertices per face
        face_vertex_indices: Indices into the points array for each vertex of each face
        
    Returns:
        Confirmation message or error description
    """
    try:
        # Open existing stage or create a new one
        stage = Usd.Stage.Open(file_path) if os.path.exists(file_path) else Usd.Stage.CreateNew(file_path)
        
        # Create mesh
        mesh = UsdGeom.Mesh.Define(stage, prim_path)
        
        # Set mesh data
        mesh.GetPointsAttr().Set(points)
        mesh.GetFaceVertexCountsAttr().Set(face_vertex_counts)
        mesh.GetFaceVertexIndicesAttr().Set(face_vertex_indices)
        
        # Add display color attribute if it doesn't exist
        if not mesh.GetDisplayColorAttr():
            mesh.CreateDisplayColorAttr()
            mesh.GetDisplayColorAttr().Set([(0.8, 0.8, 0.8)])  # Default gray color
        
        # Save stage
        stage.GetRootLayer().Save()
        
        return f"Successfully created mesh at {prim_path}"
    except Exception as e:
        return f"Error creating mesh: {str(e)}"

# =============================================================================
# Documentation Resources
# =============================================================================

@mcp.resource("usd://schema")
def get_usd_schema() -> str:
    """Return information about common USD schema types
    
    Returns:
        JSON string containing schema information
    """
    schema_info = {
        "UsdGeom.Xform": "Transform node that can be used for grouping and hierarchical transformations",
        "UsdGeom.Mesh": "Polygonal mesh representation",
        "UsdGeom.Points": "Point cloud representation",
        "UsdGeom.Cube": "Parametric cube primitive",
        "UsdGeom.Sphere": "Parametric sphere primitive",
        "UsdGeom.Cylinder": "Parametric cylinder primitive",
        "UsdGeom.Cone": "Parametric cone primitive",
        "UsdLux.DistantLight": "Distant/directional light source",
        "UsdLux.DomeLight": "Dome/environment light source",
        "UsdLux.DiskLight": "Disk-shaped area light source",
        "UsdLux.SphereLight": "Spherical area light source",
        "UsdLux.RectLight": "Rectangular area light source",
        "UsdSkel.Skeleton": "Joints and rest pose for skeletal animation",
        "UsdSkel.SkelAnimation": "Joint animation data",
        "UsdShade.Material": "Material definition for surfaces",
        "UsdShade.Shader": "Shader implementation for materials",
        "UsdPhysics.RigidBody": "Rigid body for physics simulations",
        "UsdPhysics.CollisionAPI": "API for collision detection in physics",
        "UsdPhysics.JointAPI": "API for joint constraints in physics"
    }
    return json.dumps(schema_info, indent=2)

@mcp.resource("omniverse://help")
def get_omniverse_help() -> str:
    """Return help information about Omniverse Kit and USD integration
    
    Returns:
        Markdown formatted help text
    """
    help_info = """
    # Omniverse Kit and USD Integration
    
    ## Basic Concepts
    
    - **USD (Universal Scene Description)**: Pixar's open-source scene description format that provides a rich toolset for describing, composing, and editing 3D scenes.
    
    - **Omniverse Kit**: NVIDIA's extensible application development framework for building custom Omniverse applications and services.
    
    - **Extensions**: Plugins that add functionality to Omniverse applications, developed using Python and the Omniverse Kit SDK.
    
    ## Common Workflows
    
    1. **Scene Loading/Saving**: 
       - Use `Usd.Stage.Open()` to open existing stages
       - Use `Usd.Stage.CreateNew()` to create new stages
       - Use `stage.GetRootLayer().Save()` to save changes
    
    2. **Prim Manipulation**: 
       - Use `stage.GetPrimAtPath()` to access prims
       - Use `UsdGeom.*` classes to create and manipulate geometry
       - Use `prim.GetAttributes()` to access attributes
    
    3. **Material Assignment**: 
       - Use `UsdShade` and MaterialX for surface appearances
       - Use `UsdShade.Material.Define()` to create materials
       - Use `UsdShade.MaterialBindingAPI().Bind()` to assign materials
    
    4. **Physics Setup**: 
       - Use `UsdPhysics` for physical simulations
       - Apply `UsdPhysics.RigidBodyAPI` for dynamic objects
       - Create colliders with `UsdPhysics.CollisionAPI`
    
    5. **Collaborative Workflows**: 
       - Use Nucleus server for multi-user editing
       - Use layer stacks for non-destructive editing
       - Use references and payloads for instancing
    
    ## Performance Tips
    
    - Use instancing for repeated geometry via `.SetInstanceable(True)`
    - Defer operations using change blocks with `with Sdf.ChangeBlock():`
    - Organize complex scenes with references and payloads
    - Optimize mesh topology for real-time viewing
    - Use purpose attributes to selectively load content
    """
    return help_info

@mcp.resource("omniverse://development-guide")
def get_omniverse_development_guide() -> str:
    """Return comprehensive development guide for Omniverse Kit and USD development
    
    Returns:
        Markdown formatted development guide
    """
    guide = """
    # Comprehensive Omniverse Development Guide
    
    ## Omniverse Kit Architecture
    
    ### Core Components
    
    - **Kit SDK**: The foundation of Omniverse applications built on a service-oriented architecture. Kit provides a plugin-based system allowing developers to extend functionality in modular ways.
    
    - **Carbonite**: Performance optimization SDK for real-time 3D workflows, handling memory management, threading, and resource allocation.
    
    - **Nucleus**: Collaborative database and asset management system, enabling real-time multi-user workflows and asset versioning.
    
    - **RTX Renderer**: Real-time ray tracing rendering engine leveraging NVIDIA RTX technology for physically accurate rendering.
    
    - **Physics**: PhysX integration for simulation of physical interactions, providing high-performance physics calculations.
    
    ### Extension System
    
    Omniverse Kit uses a modular plugin architecture where functionality is added through extensions.
    
    #### Extension Structure
    ```
    my_extension/
    ├── config/
    │   └── extension.toml       # Extension metadata
    ├── data/                    # Static assets
    ├── icons/                   # UI icons
    ├── omni/                    # Python module namespace
    │   └── my_extension/        # Extension code
    │       ├── __init__.py      # Entry point
    │       └── scripts/         # Additional scripts
    └── docs/                    # Documentation
    ```
    
    #### Extension Registration
    ```python
    import omni.ext
    
    class MyExtension(omni.ext.IExt):
        def on_startup(self, ext_id):
            # Initialize extension
            self._window = None
            self._menu_path = "Window/My Extension"
            
            # Create a menu item
            editor_menu = omni.kit.ui.get_editor_menu()
            if editor_menu:
                self._menu = editor_menu.add_item(
                    self._menu_path, self._on_menu_click, toggle=True, value=False
                )
        
        def on_shutdown(self):
            # Clean up resources
            if self._menu:
                editor_menu = omni.kit.ui.get_editor_menu()
                if editor_menu:
                    editor_menu.remove_item(self._menu)
            
            if self._window:
                self._window.destroy()
                self._window = None
    ```
    
    ## USD Python Development
    
    ### Stage Management
    
    #### Creating Stages
    ```python
    from pxr import Usd, UsdGeom
    
    # Create a new stage
    stage = Usd.Stage.CreateNew("my_stage.usda")
    
    # Define a default prim
    root_prim = UsdGeom.Xform.Define(stage, "/Root")
    stage.SetDefaultPrim(root_prim.GetPrim())
    
    # Save the stage
    stage.GetRootLayer().Save()
    ```
    
    #### Loading Stages
    ```python
    from pxr import Usd
    
    # Open an existing stage
    stage = Usd.Stage.Open("existing_stage.usda")
    
    # Open with specific load set
    stage = Usd.Stage.Open("heavy_stage.usda", Usd.Stage.LoadNone)
    
    # Load specific prims
    root = stage.GetPrimAtPath("/Root")
    stage.LoadAndUnload([root], [])  # Load root, unload nothing
    ```
    
    ### Prim Operations
    
    #### Creating and Modifying Prims
    ```python
    from pxr import Usd, UsdGeom, Gf
    
    # Create a sphere
    sphere = UsdGeom.Sphere.Define(stage, "/Root/Sphere")
    sphere.CreateRadiusAttr(2.0)
    
    # Create a transform
    xform = UsdGeom.Xform.Define(stage, "/Root/Group")
    
    # Set transform matrix
    op = xform.AddTranslateOp()
    op.Set(Gf.Vec3d(1.0, 2.0, 3.0))
    
    # Set visibility
    UsdGeom.Imageable(sphere.GetPrim()).CreateVisibilityAttr("invisible")
    ```
    
    #### Working with Attributes
    ```python
    # Create custom attributes
    prim = stage.GetPrimAtPath("/Root")
    attr = prim.CreateAttribute("customAttr", Sdf.ValueTypeNames.Float)
    attr.Set(1.0)
    
    # Time samples
    attr.Set(1.0, 0.0)  # value 1.0 at time 0
    attr.Set(2.0, 1.0)  # value 2.0 at time 1
    
    # Metadata
    attr.SetMetadata("documentation", "This is a custom attribute")
    ```
    
    ### USD Composition
    
    #### References and Payloads
    ```python
    # Add a reference
    prim = stage.GetPrimAtPath("/Root/ReferencedObject")
    prim.GetReferences().AddReference("external_asset.usd", "/SourcePrim")
    
    # Add a payload
    prim = stage.GetPrimAtPath("/Root/HeavyObject")
    prim.GetPayloads().AddPayload("heavy_asset.usd", "/SourcePrim")
    ```
    
    #### Layer Management
    ```python
    from pxr import Sdf
    
    # Create a new layer
    layer = Sdf.Layer.CreateNew("sublayer.usda")
    
    # Add a sublayer
    rootLayer = stage.GetRootLayer()
    rootLayer.subLayerPaths.append("sublayer.usda")
    
    # Edit in a specific layer
    with Usd.EditContext(stage, layer):
        UsdGeom.Sphere.Define(stage, "/Root/LayerSpecificSphere")
    ```
    
    ## Omniverse Kit UI Development
    
    ### UI Elements with omni.ui
    
    ```python
    import omni.ui as ui
    
    # Create a window
    self._window = ui.Window("My Extension", width=300, height=300)
    with self._window.frame:
        with ui.VStack(spacing=5):
            ui.Label("Hello Omniverse")
            
            def on_click():
                print("Button clicked!")
            
            ui.Button("Click Me", clicked_fn=on_click)
            
            with ui.HStack():
                self._slider = ui.FloatSlider(min=0, max=10)
                self._value_label = ui.Label("0.0")
            
                def on_slider_change(val):
                    self._value_label.text = f"{val:.1f}"
                
                self._slider.model.add_value_changed_fn(on_slider_change)
    ```
    
    ### Viewport Integration
    
    ```python
    import omni.kit.viewport.utility as vp_utils
    
    # Get active viewport
    viewport_api = vp_utils.get_active_viewport_window()
    
    # Register for selection changes
    self._selection_subscription = omni.usd.get_context().get_selection().create_subscription_to_pop(
        self._on_selection_changed
    )
    
    # Manipulator example
    self._manipulator = omni.kit.manipulator.create_manipulator("xform")
    self._manipulator.set_transform(position, rotation, scale)
    ```
    
    ## Performance Optimization
    
    ### USD Performance Tips
    
    1. **Use SdfChangeBlock for batched changes**
    ```python
    with Sdf.ChangeBlock():
        # Multiple USD operations here
        for i in range(1000):
            UsdGeom.Sphere.Define(stage, f"/Root/Sphere_{i}")
    ```
    
    2. **Leverage instanceable prims for repeated geometry**
    ```python
    prototype = UsdGeom.Scope.Define(stage, "/Prototypes/Cube")
    # ... add geometry to prototype
    
    instance = stage.OverridePrim("/Instances/Cube_1")
    instance.SetInstanceable(True)
    instance.GetReferences().AddReference("", "/Prototypes/Cube")
    ```
    
    3. **Use purpose attributes for optimization**
    ```python
    geom = UsdGeom.Mesh.Define(stage, "/Root/DetailMesh")
    UsdGeom.Imageable(geom).CreatePurposeAttr("proxy")
    ```
    
    ### Carbonite SDK for Optimization
    
    Carbonite provides optimized memory management and threading for high-performance applications:
    
    ```python
    import omni.carbonite as carbonite
    
    # Create a thread pool
    thread_pool = carbonite.ThreadPool(num_threads=4)
    
    # Submit task to thread pool
    future = thread_pool.submit(heavy_computation_function, arg1, arg2)
    
    # Wait for result
    result = future.get()
    ```
    
    ## Networking and Collaboration
    
    ### Omniverse Client Library
    
    ```python
    import omni.client
    
    # Connect to Nucleus server
    result = omni.client.connect("omniverse://localhost/Users")
    
    # List folder contents
    list_result, entries = omni.client.list("omniverse://localhost/Projects")
    for entry in entries:
        print(f"Found: {entry.relative_path}")
    
    # Live editing
    omni.client.live_process_status(
        "omniverse://localhost/Projects/MyProject.usd",
        True,  # Start live session
        cb_fn=self._on_live_update
    )
    
    def _on_live_update(self, update_info):
        # Handle real-time updates
        if update_info.status == omni.client.LiveUpdateStatus.LIVE_UPDATE:
            print(f"Updated: {update_info.path}")
    ```
    
    ## Physics and Simulation
    
    ### PhysX Integration
    
    ```python
    from pxr import PhysxSchema, UsdPhysics
    
    # Add physics scene
    physics_scene = UsdPhysics.Scene.Define(stage, "/World/physics")
    
    # Add rigid body
    rigid_body = UsdPhysics.RigidBody.Define(stage, "/World/Cube")
    
    # Add collider
    collider = UsdPhysics.SphereCollider.Define(stage, "/World/Cube/Collider")
    collider.CreateRadiusAttr(1.0)
    
    # Set mass properties
    mass_api = UsdPhysics.MassAPI.Apply(rigid_body.GetPrim())
    mass_api.CreateMassAttr(10.0)
    
    # Add force
    force = UsdPhysics.ForceAPI.Apply(rigid_body.GetPrim())
    force.CreateMagnitudeAttr(100.0)
    force.CreateDirectionAttr(Gf.Vec3f(0, 1, 0))
    ```
    
    ## Material and Rendering
    
    ### MDL Materials
    
    ```python
    from pxr import UsdShade, Sdf
    
    # Create material
    material = UsdShade.Material.Define(stage, "/Root/Materials/MyMaterial")
    
    # Create MDL shader
    mdl_shader = UsdShade.Shader.Define(stage, "/Root/Materials/MyMaterial/Shader")
    mdl_shader.CreateIdAttr("nvidia.mdl.OmniPBR")
    
    # Set inputs
    mdl_shader.CreateInput("diffuse_color", Sdf.ValueTypeNames.Color3f).Set((1.0, 0.0, 0.0))
    mdl_shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.8)
    mdl_shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.2)
    
    # Connect shader to material outputs
    material.CreateSurfaceOutput().ConnectToSource(mdl_shader.ConnectableAPI(), "surface")
    
    # Bind material to geometry
    UsdShade.MaterialBindingAPI(stage.GetPrimAtPath("/Root/Mesh")).Bind(material)
    ```
    
    ## Best Practices
    
    1. **Extension Organization**
       - Keep extension code modular and focused
       - Implement clear lifecycle management in on_startup/on_shutdown
       - Use namespaces to avoid conflicts
    
    2. **USD Data Management**
       - Use layers to organize scene data logically
       - Implement proper error handling for USD operations
       - Create utility functions for common operations
    
    3. **Performance**
       - Profile your code to identify bottlenecks
       - Batch USD operations when possible
       - Implement threading for heavy computations
       - Use instanceable prims for repeated elements
    
    4. **UI Design**
       - Follow Omniverse UI guidelines for consistency
       - Implement responsive layouts
       - Connect UI elements to data models properly
    
    5. **Versioning and Compatibility**
       - Document Omniverse Kit version requirements
       - Test against multiple versions
       - Use feature detection rather than version checks
    """
    return guide

# =============================================================================
# Search and Utility Tools
# =============================================================================

@mcp.tool()
def search_omniverse_guide(topic: str) -> str:
    """Search the Comprehensive Omniverse Development Guide for specific topics
    
    Args:
        topic: The topic to search for (e.g., 'materials', 'physics', 'extension', etc.)
    
    Returns:
        Relevant sections from the development guide matching the topic
    """
    guide = get_omniverse_development_guide()
    
    # Split the guide into sections by headers
    sections = re.split(r'(?=#+\s)', guide)
    
    # Filter sections that match the topic
    matching_sections = []
    for section in sections:
        if topic.lower() in section.lower():
            # Clean up the section
            clean_section = section.strip()
            if clean_section:
                matching_sections.append(clean_section)
    
    if not matching_sections:
        return (f"No information found for topic: '{topic}'. Try different keywords like "
                f"'materials', 'extensions', 'physics', 'UI', 'performance', etc.")
    
    # Join the matching sections and return
    return "\n\n".join(matching_sections)

# =============================================================================
# Main Entry Point
# =============================================================================

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description='Omniverse_USD_MCPServer_byJPH2')
    parser.add_argument('--transport', type=str, default='stdio',
                        choices=['stdio', 'sse'],
                        help='Transport protocol (stdio or sse)')
    parser.add_argument('--port', type=int, default=8000,
                        help='Port number for SSE transport')
    return parser.parse_args()

if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_arguments()
    
    try:
        if args.transport == "stdio":
            print("Starting Omniverse_USD_MCPServer_byJPH2 (stdio transport)")
            mcp.start_stdio()
        elif args.transport == "sse":
            print(f"Starting Omniverse_USD_MCPServer_byJPH2 (SSE transport on port {args.port})")
            mcp.start_sse(port=args.port)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)