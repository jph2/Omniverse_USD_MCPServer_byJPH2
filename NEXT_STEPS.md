# Next Steps for USD MCP Server Refactoring

## Completed Tasks

We have successfully implemented a two-level architecture for the USD MCP Server:

### Level A: Basic USD Operations
- ✅ Created a `StageRegistry` class for centralized stage management
- ✅ Added thread-safe locking mechanisms
- ✅ Implemented LRU caching with automatic cleanup
- ✅ Added `open_stage` function that returns a stage ID
- ✅ Added `close_stage_by_id` function
- ✅ Added a registry maintenance thread
- ✅ Added `get_registry_status` function

### Level B: Advanced USD Operations
- ✅ Added `set_transform_by_id` function
- ✅ Added `visualize_scene_graph_by_id` function
- ✅ Added `analyze_stage_by_id` function
- ✅ Added `create_mesh_by_id` function
- ✅ Added `create_primitive_by_id` function
- ✅ Added `create_reference_by_id` function
- ✅ Added `create_material_by_id` function
- ✅ Added `bind_material_by_id` function

### Client Integration
- ✅ Updated `cursor_integration.py` to use the new stage ID-based API
- ✅ Updated `cursor_example.py` to use `create_if_missing` instead of `create_new`

### Documentation
- ✅ Updated README.md with two-level architecture details
- ✅ Created REFACTORING.md to document the changes
- ✅ Created LINTER_FIXES.md to document manual fixes needed
- ✅ Updated requirements.txt with MCP dependency
- ✅ Added notice to README.md about the refactoring

## Pending Tasks

### 1. Manual Linter Fixes
The most immediate next step is to manually fix the linter errors identified in LINTER_FIXES.md:
- [ ] Fix indentation in `create_stage` function (lines 192-212)
- [ ] Fix indentation in `analyze_stage` function (lines 327-331)
- [ ] Fix indentation of loops under `Sdf.ChangeBlock()` (multiple locations)
- [ ] Fix try-except structure in `get_usd_schema` (lines 1743-1768)

### 2. Complete Level B Refactoring
Convert the remaining USD operation functions to use stage IDs:
- [ ] All physics-related functions (add_rigid_body_by_id, setup_physics_scene_by_id, etc.)
- [ ] All animation-related functions (create_animation_by_id, etc.)

### 3. Update the Client Examples
- [ ] Update `claude_integration.py` and `chatgpt_integration.py` to use the new stage ID-based API

### 4. Add Integration Tests
- [ ] Create tests for Level A functions (stage registry)
- [ ] Create tests for Level B functions (stage ID operations)
- [ ] Test memory usage with large stages

### 5. Performance Optimization
- [ ] Profile the code to identify performance bottlenecks
- [ ] Optimize stage loading and unloading
- [ ] Add metrics for stage operations

### 6. Enhancement Ideas
- [ ] Add batch operations for multiple changes to a stage
- [ ] Implement save points / undo stack
- [ ] Add transaction support for atomic operations
- [ ] Add stage snapshot and restore functionality
- [ ] Implement more robust error handling

## Migration Strategy

To ensure a smooth transition to the new architecture, we recommend:

1. Fix all linter errors first to ensure code quality
2. Implement all Level B functions without removing the old ones
3. Update client examples to use the new API
4. Add clear deprecation warnings to the old functions
5. Create a comprehensive migration guide for users
6. Set a timeline for removing deprecated functions in the next major release

## Future Enhancements

Once the refactoring is complete, consider these advanced features:

1. **WebSocket Support**: Real-time updates for collaborative editing
2. **Schema Validation**: Validate all inputs and outputs against schema
3. **Pluggable Storage Backend**: Support different storage backends for stages
4. **Distributed Stage Registry**: For multi-server deployments
5. **Enhanced Visualization**: More interactive scene graph visualization options 