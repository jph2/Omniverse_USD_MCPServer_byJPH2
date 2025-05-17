# Comprehensive Omniverse Development Guide

Created by: Jan Haluszka
Created time: May 14, 2025 7:13 PM
Last edited time: May 17, 2025 1:40 PM
Multi-select: OV Script
Status: In progress

## Comprehensive Omniverse Development Guide

This guide combines high-level architectural considerations with specific technical implementation details for developing robust Omniverse extensions and scripts.

---

## Core USD Concepts

### USD Stage Management

- **Proper Initialization & Cleanup**
    
    ```python
    context = omni.usd.get_context()
    stage   = context.get_stage()
    
    ```
    
- **Default Prim**
    
    ```python
    world = stage.DefinePrim("/World", "Xform")
    stage.SetDefaultPrim(world)
    
    ```
    
- **Standard Metadata**
    
    ```python
    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(100)
    stage.SetTimeCodesPerSecond(60)
    stage.SetMetadata("upAxis", "Y")
    stage.SetMetadata("metersPerUnit", 0.01)
    
    ```
    
- **Proper Stage Release**
    
    ```python
    # For large in-memory stages:
    stage.Unload()
    # For explicit layers:
    layer.Close()
    stage = None
    
    ```
    

### Layer Stack Introspection

```python
# Inspect and log each layer in the stage's layer stack
layer_stack = stage.GetPrimAtPath("/").GetLayerStack()
for layer in layer_stack:
    print(f"{layer.GetIdentifier()}  (offset={layer.GetLayerOffset()})")

```

Use this to diagnose ordering or unexpected overrides.

### Composition Arcs & Performance

- **Arc Strength** affects eval cost: fewer, weaker arcs (e.g. payloads) can be cheaper than heavy references.
- Minimize deep reference chains when you only need lightweight overrides (consider payload + variant as a lighter alternative).

---

### Change Blocks & Batching

- **Usd.EditContext**:
    
    ```python
    with Usd.EditContext(stage, stage.GetRootLayer()):
        define_materials()
        create_bindings()
        set_variants()
    
    ```
    
- **Sdf.ChangeBlock**:
    
    ```python
    with Sdf.ChangeBlock():
        layer.SetInfo("comment", "Batch edit")
        for i in range(100):
            create_prim(i)
    
    ```
    

---

### Prim Operations

- **Absolute SdfPath**: always begin with `/`.
- **Path Composition**:
    
    ```python
    child = parent_path.AppendChild("ChildName")
    
    ```
    
- **API Schemas**:
    
    ```python
    from pxr import Sdf
    prim.SetMetadata("apiSchemas",
                     Sdf.TokenListOp.CreateExplicit(["ShapingAPI"]))
    
    ```
    
- **Defensive Guards**:
    
    ```python
    if not prim.IsValid():
        log_error(f"Invalid prim: {path}")
        return False
    
    ```
    

---

### Material & Shader Handling

- **Use UsdShade API** for networks, bindings, inheritance.
- **GetBaseName()** vs `GetPath()` on properties to avoid fingerprint quirks.
- **Shader Connection Fallback**:
    
    ```python
    try:
        target.ConnectToSource(src, name)
    except TypeError:
        target.ConnectToSource(src.GetPrim().GetPath(), name)
    
    ```
    
- **Fingerprint Strategies**:
    1. Property-only
    2. Type + Property
    3. Full network hash
    
    ```python
    def fingerprint(mat):
        shader = mat.GetSurfaceShader()
        data = {
            "type": str(shader.GetTypeName()),
            "inputs": {i.GetBaseName(): i.Get()
                       for i in shader.GetInputs()}
        }
        return hash_dict(data)
    
    ```
    

---

### Variant Sets

```python
vs = prim.GetVariantSets().AddVariantSet("LOD")
vs.AddVariant("High")
vs.SetVariantSelection("High")

```

Capture and propagate selections via `.GetVariantSelection()`.

---

### References, Payloads & Time Warping

- **References vs Payloads**:
    - Use payloads for lazy load; references for always-on content.
- **Layer Offsets**:
    
    ```python
    ref = prim.GetReferences().AddReference("anim.usda")
    ref.SetLayerOffset(Sdf.LayerOffset(offset=10.0, scale=2.0))
    
    ```
    
- **Time Sampling**:
    
    ```python
    t = stage_time * offset.GetScale() + offset.GetOffset()
    
    ```
    

---

### Coordinate System

- USD is Y-up.
- Ground plane on XZ at Y=0:
    
    ```python
    UsdGeom.Xform.Define(stage, "/Ground").AddTranslateOp().Set((0,0,0))
    
    ```
    

---

## Script Structure & Organization

### Header & Metadata

```python
#!/usr/bin/env python3
"""
Material Harmonizer v1.0.1
© 2025 – MIT License
Consolidate duplicate materials non‐destructively.
"""

```

Use semantic versioning and include author/license info.

### Imports

```python
# Standard
import os, sys, json
# USD
from pxr import Usd, UsdShade, Sdf
# Omniverse
import omni.usd

```

Group and alphabetize; avoid `*` imports.

### Config Block

```python
# --- SETTINGS ---
OUTPUT_DIR       = "./out"
MATERIAL_LIB_USDA= "mat_lib.usda"
VERBOSE          = True
# --- END SETTINGS ---

```

Allow override via external config for complex scripts.

### Execution Pattern

```python
def main():
    # ... your logic ...
    return {"status": "success"}

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    try:
        res = main()
        sys.exit(0 if res["status"]=="success" else 1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

```

---

## Omniverse Kit–Specific Considerations

### Extension Structure

- `extension.toml` with correct `id`, `version`, `dependencies`.
- Support both:
    - Standalone via Kit console
    - `IExt`–based plugin

### Service Architecture

- Register services with `omni.services.register_service()`
- Teardown on shutdown to avoid leaks.

### UI Integration

- Use `omni.ui` patterns; keep main-thread only.
- Consistent margins via `ui.Spacer()`.

### Command System & Undo/Redo

```python
import omni.kit.commands

class MyCommand(omni.kit.commands.Command):
    def _execute(self, prim_path: Sdf.Path):
        prim = stage.GetPrimAtPath(str(prim_path))
        prim.GetAttribute("visibility").Set(False)
        return True

omni.kit.commands.register("ToggleVisibility", MyCommand)

```

### Subscription Model

- Use weak refs:
    
    ```python
    from weakref import ref
    sub = stage.GetOnEditTargetLayerChanged() \\
         .Add(lambda p: on_change(p))
    
    ```
    
- Remove in `on_shutdown()`.

---

## Performance Considerations

### USD Scene Optimization

- Cache `GetPrimAtPath` results.
- Avoid repeated `UsdPrimRange` if unnecessary.

### Carbonite SDK Usage

- Leverage Carbonite allocators:
    
    ```python
    from carb.mem import new_allocator
    alloc = new_allocator("FastPool", {"size":1<<20})
    
    ```
    
- Use Carbonite threads for bulk tasks:
    
    ```python
    from carb.threading import ThreadPool
    pool = ThreadPool(num_threads=4)
    pool.submit(batch_process)
    
    ```
    

### Asynchronous Patterns

- Use `async def` for I/O; avoid blocking UI.

### Batching

- Batch USD layer edits (see Change Blocks).

---

## Threading & Concurrency

- UI on main thread
- Use stage locks for worker threads:
    
    ```python
    from pxr import Usd
    with Usd.StageCache.Get().LockStage(stage):
        do_work()
    
    ```
    

---

## Robustness & Error Handling

### Custom Exception Hierarchy

```python
class OmniExtError(Exception): pass
class LayerLoadError(OmniExtError): pass
class MaterialError(OmniExtError): pass

```

Classify recoverable vs fatal in your `except` clauses.

### Validation & Logging

- Validate paths, prims, schemas.
- Use `carb.logging` at levels INFO/WARN/ERROR.

---

## Cross-Platform Compatibility

- Use `os.path` or `ArResolver` for paths.
- Handle permissions gracefully.

---

## Extension Distribution

- **Packaging**: correct `package.json`, include all assets.
- **Versioning**: semantic, indicate supported Kit versions.
- **Documentation**: README, API docs, examples.

---

## Live Collaboration

### Omniverse Client Streaming

```python
import omni.client

def stream_changes(url):
    session = omni.client.get_live_session(url)
    session.set_update_callback(lambda p: on_remote_change(p))
    session.start()

```

Handle incoming change events to refresh your UI or stage.

### Wallet & Auth

```python
import omni.client

ok, info = omni.client.get_user_info()
if ok != omni.client.Result.OK:
    raise OmniExtError("Nucleus auth failed")

```

Manage tokens securely and respect permission scopes.

---

## Omnigraph Integration

- Define custom nodes in Python/C++, register via `.schema.usda`.
- Ensure clear docs and UI metadata for each node.

---

## Testing & Quality Assurance

### Automated Testing

```python
def test_material():
    stage = Usd.Stage.CreateInMemory()
    create_material(stage)
    expected = Usd.Stage.Open("golden.mat.usda")
    assert stage.ExportToString() == expected.ExportToString()

```

- **CI**: run `usdchecker`, `PXR-Lint`, tests on GitHub Actions.

### Localization & RTL

- Extract strings to `.po` files (GNU gettext).
- Custom RTL layouts in `omni.ui` if needed.

---

## Performance Profiling

- Hook into `Tf.PerfLog` to time operations.
- Use CLI tools (`usdstats`, `usdrecord`) wrapped in helper scripts:
    
    ```bash
    # scripts/usd_stat.sh
    usdstats --input $1 | grep "composition"
    
    ```
    

---

## Pro Tips

- **Physics & Simulation**
    
    ```python
    from omni.physx import get_physics_interface
    phys = get_physics_interface()
    phys.create_scene()
    
    ```
    
- **CLI Helpers**
    
    ```bash
    #!/usr/bin/env bash
    alias myusdcat="usdcat --flatten"
    
    ```
    
- **Env & Dependencies**
Use `conda` or `venv` with Omniverse's Python interpreter to isolate third-party packages.
- **USD Instrumentation**
    
    ```python
    import Tf
    Tf.PerfLog.Get().LogBlock("StageOpen"):
        stage = Usd.Stage.Open(path)
    
    ```
    

---

## Example Repositories for USD and Omniverse Kit

To enhance your guide, here are curated GitHub repositories featuring practical examples for USD (Universal Scene Description) and Omniverse Kit development, along with the most important links to official documentation.

---

**USD Example Projects**

- **USD Cookbook**
A comprehensive collection of simple, focused USD projects. Each project demonstrates a single feature or a group of USD features, organized into categories like Features, Concepts, Tricks, Plugins, Tools, and References.
    - *Languages*: Python, C++, USDA
    - *Highlights*:
        - Clear separation of concepts and features
        - Real-world and isolated code examples
        - Explanatory comments and README summaries
    - **Repository**: [ColinKennedy/USD-Cookbook](https://github.com/ColinKennedy/USD-Cookbook)

---

**Omniverse Kit Example Projects**

- **Omniverse Kit App Template**
    
    A foundational toolkit for building custom Omniverse applications using the Kit SDK. Includes templates for applications and extensions, supporting both Python and C++.
    
    - *Features*:
        - Pre-configured templates for editors, viewers, and services
        - Boilerplate for extension and app development
        - GPU-accelerated, OpenUSD-based workflows
    - **Repository**: [NVIDIA-Omniverse/kit-app-template](https://github.com/NVIDIA-Omniverse/kit-app-template)
- **Omniverse Kit Extension Template**
    
    A template repository for developing and hot-reloading Omniverse Kit extensions.
    
    - *Features*:
        - Step-by-step instructions for extension setup
        - Example extension (`omni.hello.world`)
        - Hot-reload support and extension manager integration
    - **Repository**: [NVIDIA-Omniverse/kit-extension-template](https://github.com/NVIDIA-Omniverse/kit-extension-template)
- **Omniverse Kit Automation Sample**
    
    Demonstrates automating Omniverse Kit applications via a REST API interface.
    
    - *Features*:
        - UI and non-UI interaction automation
        - Example scenarios for widget manipulation and live session creation
    - **Repository**: [NVIDIA-Omniverse/kit-automation-sample](https://github.com/NVIDIA-Omniverse/kit-automation-sample)
- **Omniverse Connect Samples**
    
    Examples for writing Omniverse Connectors and Converters using the OpenUSD and Omniverse Connect SDK.
    
    - *Features*:
        - Asset import/export
        - Scene synchronization
        - Integration with Omniverse services
    - **Repository**: [NVIDIA-Omniverse/connect-samples](https://github.com/NVIDIA-Omniverse/connect-samples)

---

## Most Important Documentation Links

**OpenUSD Documentation**

- [OpenUSD Home](https://openusd.org/)
- [OpenUSD Tutorials](https://openusd.org/docs/USD-Tutorials.html)
- [OpenUSD API Reference](https://openusd.org/docs/api/index.html)
- [USD Geometry API (UsdGeom)](https://openusd.org/docs/api/usd_geom_page_front.html)
- [Pixar USD API Overview](https://graphics.pixar.com/usd/release/api/index.html)
- [USD Survival Guide](https://lucascheller.github.io/VFX-UsdSurvivalGuide/index.html)

**NVIDIA Omniverse Documentation**

- [Omniverse Kit App Template Docs](https://docs.omniverse.nvidia.com/kit/docs/kit-app-template/latest/docs/intro.html)
- [Omniverse Kit SDK Overview](https://docs.omniverse.nvidia.com/kit/docs/kit-app-template/latest/docs/kit_sdk_overview.html)
- [Omniverse Kit SDK Manual](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/latest/guide/kit_overview.html)
- [Omniverse Carbonite SDK](https://docs.omniverse.nvidia.com/kit/docs/carbonite/latest/index.html)
- [Omniverse Client Library](https://docs.omniverse.nvidia.com/kit/docs/client_library/latest/index.html)
- [Omniverse Naming and Configuration](https://docs.omniverse.nvidia.com/kit/docs/kit-app-template/latest/docs/naming_and_configuration.html)
- [Omniverse Extending Services](https://docs.omniverse.nvidia.com/kit/docs/kit-app-template/latest/docs/extending_services.html)
- [Omniverse Extending Editor Applications](https://docs.omniverse.nvidia.com/kit/docs/kit-app-template/latest/docs/extending_editors.html)
- [Omniverse Packaging App](https://docs.omniverse.nvidia.com/kit/docs/kit-app-template/latest/docs/packaging_app.html)

---

### Example Projects and Templates

- [USD Cookbook: Practical USD Examples (Python & C++)](https://github.com/ColinKennedy/USD-Cookbook)
- [Omniverse Kit App Template: Custom App Starter](https://github.com/NVIDIA-Omniverse/kit-app-template)
- [Omniverse Kit Extension Template: Extension Development](https://github.com/NVIDIA-Omniverse/kit-extension-template)
- [Omniverse Kit Automation Sample: REST API Control](https://github.com/NVIDIA-Omniverse/kit-automation-sample)
- [Omniverse Connect Samples: Connector Development](https://github.com/NVIDIA-Omniverse/connect-samples)

### Key Documentation

- [OpenUSD Tutorials](https://openusd.org/docs/USD-Tutorials.html)
- [USD API Reference](https://openusd.org/docs/api/index.html)
- [Omniverse Kit App Template Docs](https://docs.omniverse.nvidia.com/kit/docs/kit-app-template/latest/docs/intro.html)
- [Omniverse Kit SDK Manual](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/latest/guide/kit_overview.html)
- [Omniverse Carbonite SDK](https://docs.omniverse.nvidia.com/kit/docs/carbonite/latest/index.html)