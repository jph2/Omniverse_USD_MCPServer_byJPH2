@Cursur LLM: Use this file to copy the entire conversation/ prompting 
try to retrieve it from the start and document it here.

# Create stage content based on template
if not template or template == 'empty':
    # Just create an empty root prim
    root_prim = UsdGeom.Xform.Define(stage, '/root')
    stage.SetDefaultPrim(root_prim.GetPrim())
elif template == 'basic':
    # Create basic scene structure
    root_prim = UsdGeom.Xform.Define(stage, '/World')
    # ... rest of basic template ...
elif template == 'full':
    # ...