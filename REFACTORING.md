# USD MCP Server Refactoring

## Two-Level Architecture Implementation

This repository has been refactored to implement a more modular and maintainable architecture for the USD MCP Server. The refactoring focused on creating a clear separation between basic USD operations and higher-level functionality, resulting in a two-level architecture:

### Level A: Basic USD Operations

The foundation of the server, providing core USD stage management:

- **StageRegistry Class**: A central, thread-safe registry that tracks all open USD stages
- **Stage ID System**: Unique identifiers for each open stage, reducing dependency on file paths
- **Memory Management**: Efficient LRU caching and explicit cleanup to manage memory usage
- **Thread Safety**: All operations use locking to ensure thread-safe access to stages
- **Explicit Stage Lifecycle**: Clear ownership model with explicit open/close operations

Key components added:
- `StageRegistry` class
- `open_stage` function (returns a stage_id)
- `close_stage_by_id` function
- `maintain_stage_registry` background thread
- `get_registry_status` diagnostic function

### Level B: Advanced USD Operations

Higher-level functionality that builds on the foundation of Level A:

- **Stage ID-based Operations**: All tools retrieve stages through the registry using stage IDs
- **Scene Graph Visualization**: Advanced tools for analyzing and visualizing USD scene graphs
- **Complex Manipulations**: Tools for physics, materials, animation and other USD features
- **Performance Optimizations**: Batched operations and specialized handling for large scenes

Key components added:
- `visualize_scene_graph_by_id` function
- `set_transform_by_id` function

## Benefits of the New Architecture

1. **Improved Memory Management**
   - Explicit control over stage lifecycle with open/close operations
   - LRU caching with automatic cleanup for memory efficiency
   - Reduced redundant stage loading by reusing stages through their IDs

2. **Better Code Organization**
   - Clear separation between basic USD operations and complex manipulations
   - More modular and maintainable code structure
   - Easier to extend with new functionality

3. **Enhanced Thread Safety**
   - All operations on stages use proper locking
   - Reduced risk of race conditions when multiple operations access stages

4. **Consistent API Design**
   - Uniform pattern for stage-based operations
   - Explicit error handling and status reporting
   - Better diagnostics through registry status reporting

5. **Performance Improvements**
   - Reduced file I/O by reusing open stages
   - More efficient caching strategy
   - Better memory usage patterns

## Future Improvements

The refactoring lays the groundwork for several future improvements:

1. **Complete Migration**: Convert all existing USD operation functions to use stage IDs
2. **Transaction Support**: Add support for batched operations and undo/redo
3. **Advanced Caching**: Implement more sophisticated caching strategies for large stages
4. **Performance Optimization**: Further optimize operations for large USD scenes
5. **Extension Points**: Define clear extension mechanisms for custom functionality

## Requirements Update

The refactoring added a dependency on the `mcp` library, which has been added to the `requirements.txt` file.

## Documentation

The `README.md` has been updated to document the new architecture and its benefits, including examples of how to use the new APIs. 