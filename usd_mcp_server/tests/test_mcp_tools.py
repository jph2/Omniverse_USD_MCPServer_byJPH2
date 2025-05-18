"""
Tests for core MCP tools to ensure API contracts are maintained.

These tests validate that the core USD operations work correctly.
"""

import os
import json
import tempfile
import pytest
import sys

# Import the main module to access the MCP tools
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from usd_mcp_server.__main__ import (
    create_new_stage,
    open_usd_stage,
    save_usd_stage,
    close_stage,
    list_stage_prims,
    analyze_usd_stage,
    define_stage_prim,
    create_stage_reference,
    create_stage_mesh,
    get_health
)

def parse_response(response):
    """Parse JSON response from MCP tools"""
    if isinstance(response, str):
        return json.loads(response)
    return response

def test_create_and_list_stage():
    """Test creating a new stage, listing prims, and closing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        stage_path = os.path.join(temp_dir, "test.usda")
        
        # Create a new stage
        create_response = parse_response(create_new_stage(stage_path))
        assert create_response["ok"]
        stage_id = create_response["data"]["stage_id"]
        
        # List prims
        list_response = parse_response(list_stage_prims(stage_id))
        assert list_response["ok"]
        assert "prims" in list_response["data"]
        
        # Close the stage
        close_response = parse_response(close_stage(stage_id))
        assert close_response["ok"]

def test_stage_save_and_reload():
    """Test saving a stage and reopening it"""
    with tempfile.TemporaryDirectory() as temp_dir:
        stage_path = os.path.join(temp_dir, "test_save.usda")
        
        # Create and get stage_id
        create_response = parse_response(create_new_stage(stage_path))
        stage_id = create_response["data"]["stage_id"]
        
        # Define a test prim
        define_response = parse_response(define_stage_prim(
            stage_id, "/TestPrim", "Xform"
        ))
        assert define_response["ok"]
        
        # Save the stage
        save_response = parse_response(save_usd_stage(stage_id))
        assert save_response["ok"]
        
        # Close the stage
        parse_response(close_stage(stage_id))
        
        # Reopen and verify prim exists
        open_response = parse_response(open_usd_stage(stage_path))
        assert open_response["ok"]
        reopened_stage_id = open_response["data"]["stage_id"]
        
        list_response = parse_response(list_stage_prims(reopened_stage_id))
        assert list_response["ok"]
        
        # Find our test prim
        found = False
        for prim in list_response["data"]["prims"]:
            if prim["path"] == "/TestPrim":
                found = True
                break
        
        assert found, "TestPrim not found after reload"
        
        # Clean up
        parse_response(close_stage(reopened_stage_id))

def test_create_mesh():
    """Test creating a mesh with geometry data"""
    with tempfile.TemporaryDirectory() as temp_dir:
        stage_path = os.path.join(temp_dir, "test_mesh.usda")
        
        # Create stage
        create_response = parse_response(create_new_stage(stage_path))
        stage_id = create_response["data"]["stage_id"]
        
        # Create a simple cube mesh
        points = [
            [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
            [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]
        ]
        face_vertex_counts = [4, 4, 4, 4, 4, 4]  # 6 faces, 4 vertices each
        face_vertex_indices = [
            0, 1, 2, 3,  # bottom face
            4, 5, 6, 7,  # top face
            0, 1, 5, 4,  # front face
            1, 2, 6, 5,  # right face
            2, 3, 7, 6,  # back face
            3, 0, 4, 7   # left face
        ]
        
        mesh_response = parse_response(create_stage_mesh(
            stage_id, "/Cube", points, face_vertex_counts, face_vertex_indices
        ))
        assert mesh_response["ok"]
        
        # Verify the mesh was created
        list_response = parse_response(list_stage_prims(stage_id))
        
        found = False
        for prim in list_response["data"]["prims"]:
            if prim["path"] == "/Cube":
                found = True
                break
        
        assert found, "Mesh not found after creation"
        
        # Clean up
        parse_response(close_stage(stage_id))

def test_create_reference():
    """Test creating a reference from one stage to another"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create source stage with an object to reference
        source_path = os.path.join(temp_dir, "source.usda")
        source_response = parse_response(create_new_stage(source_path))
        source_id = source_response["data"]["stage_id"]
        
        # Add a cube to the source stage
        parse_response(define_stage_prim(source_id, "/SourceCube", "Cube"))
        parse_response(save_usd_stage(source_id))
        parse_response(close_stage(source_id))
        
        # Create target stage with a reference to the source
        target_path = os.path.join(temp_dir, "target.usda")
        target_response = parse_response(create_new_stage(target_path))
        target_id = target_response["data"]["stage_id"]
        
        # Create a reference to the source stage
        ref_response = parse_response(create_stage_reference(
            target_id, "/RefCube", source_path, "/SourceCube"
        ))
        assert ref_response["ok"]
        
        # Save and close
        parse_response(save_usd_stage(target_id))
        parse_response(close_stage(target_id))

def test_analyze_stage():
    """Test analyzing a stage's content"""
    with tempfile.TemporaryDirectory() as temp_dir:
        stage_path = os.path.join(temp_dir, "analyze_test.usda")
        
        # Create a stage with some content
        create_response = parse_response(create_new_stage(stage_path, "basic"))
        stage_id = create_response["data"]["stage_id"]
        
        # Add some prims
        parse_response(define_stage_prim(stage_id, "/World/TestSphere", "Sphere"))
        parse_response(define_stage_prim(stage_id, "/World/TestCube", "Cube"))
        
        # Save the stage
        parse_response(save_usd_stage(stage_id))
        parse_response(close_stage(stage_id))
        
        # Analyze the stage
        analyze_response = parse_response(analyze_usd_stage(stage_path))
        assert analyze_response["ok"]
        
        # Check for expected analysis data
        analysis = analyze_response["data"]
        assert "file_path" in analysis
        assert "total_prims" in analysis
        assert analysis["total_prims"] > 0

def test_health_endpoint():
    """Test the health endpoint"""
    health_response = parse_response(get_health())
    assert health_response["ok"]
    assert "status" in health_response["data"]
    assert health_response["data"]["status"] == "healthy" 