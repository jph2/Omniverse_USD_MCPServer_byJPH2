"""
Basic tests for the USD MCP server.

These tests verify that the core functionality of the server is working properly.
"""

import unittest
import os
import tempfile
import json
import sys
import logging

# Add the parent directory to the path so we can import the server module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Disable excessive logging during tests
logging.basicConfig(level=logging.ERROR)

# Import server functionality
from usd_mcp_server.core.stage_operations import (
    create_stage,
    open_stage,
    save_stage,
    list_prims,
    define_prim,
    create_reference,
    create_mesh
)

from usd_mcp_server.core.registry import stage_registry

class TestBasicUsdOperations(unittest.TestCase):
    """Test basic USD operations."""
    
    def setUp(self):
        """Set up test fixtures. Create a temporary directory for test files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_filepath = os.path.join(self.temp_dir.name, "test_stage.usda")
    
    def tearDown(self):
        """Tear down test fixtures. Clean up temporary files."""
        self.temp_dir.cleanup()
    
    def test_create_stage(self):
        """Test creating a new stage."""
        # Create a new stage
        result = create_stage(self.test_filepath, "empty", "Y")
        result_dict = json.loads(result)
        
        # Check success status
        self.assertTrue(result_dict["ok"])
        self.assertIn("stage_id", result_dict["data"])
        
        # Check that the file exists
        self.assertTrue(os.path.exists(self.test_filepath))
    
    def test_open_stage(self):
        """Test opening an existing stage."""
        # First create a stage
        create_result = create_stage(self.test_filepath, "basic", "Y")
        create_result_dict = json.loads(create_result)
        
        # Now open it
        open_result = open_stage(self.test_filepath)
        open_result_dict = json.loads(open_result)
        
        # Check success status
        self.assertTrue(open_result_dict["ok"])
        self.assertIn("stage_id", open_result_dict["data"])
    
    def test_list_prims(self):
        """Test listing prims on a stage."""
        # Create a stage with a basic template (has some default prims)
        create_result = create_stage(self.test_filepath, "basic", "Y")
        create_result_dict = json.loads(create_result)
        stage_id = create_result_dict["data"]["stage_id"]
        
        # List prims
        list_result = list_prims(stage_id)
        list_result_dict = json.loads(list_result)
        
        # Check success status
        self.assertTrue(list_result_dict["ok"])
        self.assertIn("prims", list_result_dict["data"])
        
        # Should have some prims since we used the basic template
        self.assertGreater(len(list_result_dict["data"]["prims"]), 0)
    
    def test_define_prim(self):
        """Test defining a new prim on a stage."""
        # Create a stage
        create_result = create_stage(self.test_filepath, "empty", "Y")
        create_result_dict = json.loads(create_result)
        stage_id = create_result_dict["data"]["stage_id"]
        
        # Define a new prim
        prim_path = "/root/new_prim"
        define_result = define_prim(stage_id, prim_path, "Xform")
        define_result_dict = json.loads(define_result)
        
        # Check success status
        self.assertTrue(define_result_dict["ok"])
        
        # Verify the prim exists by listing prims
        list_result = list_prims(stage_id, "/root")
        list_result_dict = json.loads(list_result)
        
        # Find our new prim in the results
        found = False
        for prim in list_result_dict["data"]["prims"]:
            if prim["path"] == prim_path:
                found = True
                break
        
        self.assertTrue(found, f"Could not find newly created prim at {prim_path}")
    
    def test_create_mesh(self):
        """Test creating a mesh on a stage."""
        # Create a stage
        create_result = create_stage(self.test_filepath, "empty", "Y")
        create_result_dict = json.loads(create_result)
        stage_id = create_result_dict["data"]["stage_id"]
        
        # Define a simple cube mesh
        prim_path = "/root/cube"
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
        
        mesh_result = create_mesh(stage_id, prim_path, points, face_vertex_counts, face_vertex_indices)
        mesh_result_dict = json.loads(mesh_result)
        
        # Check success status
        self.assertTrue(mesh_result_dict["ok"])
        
        # Verify the mesh exists by listing prims
        list_result = list_prims(stage_id, "/root")
        list_result_dict = json.loads(list_result)
        
        # Find our new mesh in the results
        found = False
        for prim in list_result_dict["data"]["prims"]:
            if prim["path"] == prim_path:
                found = True
                break
        
        self.assertTrue(found, f"Could not find newly created mesh at {prim_path}")
    
    def test_save_stage(self):
        """Test saving a stage after modifications."""
        # Create a stage
        create_result = create_stage(self.test_filepath, "empty", "Y")
        create_result_dict = json.loads(create_result)
        stage_id = create_result_dict["data"]["stage_id"]
        
        # Define a new prim to modify the stage
        define_prim(stage_id, "/root/test_save", "Xform")
        
        # Save the stage
        save_result = save_stage(stage_id)
        save_result_dict = json.loads(save_result)
        
        # Check success status
        self.assertTrue(save_result_dict["ok"])
        
        # Check file modification time to ensure it was updated
        self.assertTrue(os.path.exists(self.test_filepath))
        
        # Open the stage again to ensure modifications were saved
        open_result = open_stage(self.test_filepath)
        open_result_dict = json.loads(open_result)
        new_stage_id = open_result_dict["data"]["stage_id"]
        
        # Check if the prim exists
        list_result = list_prims(new_stage_id)
        list_result_dict = json.loads(list_result)
        
        # Find our test prim in the results
        found = False
        for prim in list_result_dict["data"]["prims"]:
            if prim["path"] == "/root/test_save":
                found = True
                break
        
        self.assertTrue(found, "Saved prim not found when reopening stage")
    
    def test_stage_registry(self):
        """Test the stage registry functionality."""
        # Create several stages
        stages = []
        for i in range(3):
            filepath = os.path.join(self.temp_dir.name, f"stage_{i}.usda")
            result = create_stage(filepath, "empty", "Y")
            result_dict = json.loads(result)
            stages.append(result_dict["data"]["stage_id"])
        
        # Check registry stats
        stats = stage_registry.get_stats()
        self.assertEqual(stats["total_stages"], 3)
        self.assertEqual(len(stats["stage_ids"]), 3)
        
        # Verify all our stage IDs are in the registry
        for stage_id in stages:
            self.assertIn(stage_id, stats["stage_ids"])
        
        # Test unregistering a stage
        stage_registry.unregister_stage(stages[0])
        stats = stage_registry.get_stats()
        self.assertEqual(stats["total_stages"], 2)
        self.assertNotIn(stages[0], stats["stage_ids"])

if __name__ == "__main__":
    unittest.main() 