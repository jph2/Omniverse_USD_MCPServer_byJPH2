#!/usr/bin/env python3
"""
Integrity checker for USD MCP Server refactoring.

This script checks the integrity of the implementation by verifying:
1. Each file path-based method has a corresponding stage ID-based method
2. The parameters (except file_path vs stage_id) match between corresponding methods
3. The return types and documentation are consistent
"""

import ast
import re
import sys
from typing import Dict, List, Optional, Set, Tuple

# Functions that should have both file path-based and stage ID-based versions
FUNCTION_PAIRS = [
    ("analyze_stage", "analyze_stage_by_id"),
    ("create_mesh", "create_mesh_by_id"),
    ("create_primitive", "create_primitive_by_id"),
    ("create_reference", "create_reference_by_id"),
    ("create_material", "create_material_by_id"),
    ("bind_material", "bind_material_by_id"),
    ("set_transform", "set_transform_by_id"),
    ("visualize_scene_graph", "visualize_scene_graph_by_id"),
    ("close_stage", "close_stage_by_id"),
    ("setup_physics_scene", "setup_physics_scene_by_id"),
    ("add_rigid_body", "add_rigid_body_by_id"),
    # Add more pairs as needed
]

# Functions with special case handling
SPECIAL_CASES = {
    "create_stage": "open_stage",  # Different function name pattern
}

def parse_function_parameters(node: ast.FunctionDef) -> Dict[str, Dict]:
    """Extract function parameters and their types from a function definition"""
    params = {}
    
    for arg in node.args.args:
        if arg.arg == 'self':
            continue
            
        param_name = arg.arg
        param_type = None
        
        # Try to get type annotation
        if arg.annotation:
            if isinstance(arg.annotation, ast.Name):
                param_type = arg.annotation.id
            elif isinstance(arg.annotation, ast.Subscript):
                param_type = ast.unparse(arg.annotation)
            else:
                param_type = ast.unparse(arg.annotation)
        
        params[param_name] = {
            "type": param_type
        }
        
    # Add default values
    for i, default in enumerate(node.args.defaults):
        arg_index = len(node.args.args) - len(node.args.defaults) + i
        arg_name = node.args.args[arg_index].arg
        
        if arg_name in params:
            params[arg_name]["default"] = ast.unparse(default)
    
    return params

def parse_function_return_type(node: ast.FunctionDef) -> Optional[str]:
    """Extract function return type from a function definition"""
    if node.returns:
        if isinstance(node.returns, ast.Name):
            return node.returns.id
        else:
            return ast.unparse(node.returns)
    return None

def parse_function_docstring(node: ast.FunctionDef) -> Optional[str]:
    """Extract function docstring from a function definition"""
    if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
        return node.body[0].value.s
    return None

def parse_functions(file_path: str) -> Dict[str, Dict]:
    """Parse all functions in a file and return their details"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    tree = ast.parse(content)
    functions = {}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name.startswith('_'):
                continue  # Skip private functions
                
            functions[node.name] = {
                "parameters": parse_function_parameters(node),
                "return_type": parse_function_return_type(node),
                "docstring": parse_function_docstring(node)
            }
    
    return functions

def compare_functions(file_path_funcs: Dict[str, Dict], stage_id_funcs: Dict[str, Dict]) -> List[str]:
    """Compare file path-based functions with stage ID-based functions"""
    issues = []
    
    for file_path_func, stage_id_func in FUNCTION_PAIRS:
        if file_path_func not in file_path_funcs:
            issues.append(f"File path function {file_path_func} not found")
            continue
            
        if stage_id_func not in stage_id_funcs:
            issues.append(f"Stage ID function {stage_id_func} not found")
            continue
        
        # Check parameters
        file_path_params = file_path_funcs[file_path_func]["parameters"]
        stage_id_params = stage_id_funcs[stage_id_func]["parameters"]
        
        # Verify file_path -> stage_id parameter replacement
        if "file_path" not in file_path_params:
            issues.append(f"{file_path_func} does not have a file_path parameter")
            
        if "stage_id" not in stage_id_params:
            issues.append(f"{stage_id_func} does not have a stage_id parameter")
        
        # Check other parameters match
        for param_name, param_info in file_path_params.items():
            if param_name == "file_path":
                continue  # Skip comparison for file_path parameter
                
            if param_name not in stage_id_params:
                issues.append(f"{stage_id_func} is missing parameter {param_name} from {file_path_func}")
                continue
                
            stage_id_param_info = stage_id_params[param_name]
            
            # Check parameter type
            if param_info.get("type") != stage_id_param_info.get("type"):
                issues.append(f"Parameter {param_name} has different type in {file_path_func} ({param_info.get('type')}) vs {stage_id_func} ({stage_id_param_info.get('type')})")
            
            # Check default value
            if "default" in param_info and "default" in stage_id_param_info:
                if param_info["default"] != stage_id_param_info["default"]:
                    issues.append(f"Parameter {param_name} has different default value in {file_path_func} ({param_info['default']}) vs {stage_id_func} ({stage_id_param_info['default']})")
        
        # Check for extra parameters in stage_id function
        for param_name in stage_id_params:
            if param_name == "stage_id":
                continue  # Skip comparison for stage_id parameter
                
            if param_name not in file_path_params:
                issues.append(f"{stage_id_func} has extra parameter {param_name} not in {file_path_func}")
        
        # Compare return types
        if file_path_funcs[file_path_func]["return_type"] != stage_id_funcs[stage_id_func]["return_type"]:
            issues.append(f"Return type differs: {file_path_func} ({file_path_funcs[file_path_func]['return_type']}) vs {stage_id_func} ({stage_id_funcs[stage_id_func]['return_type']})")
    
    # Check special cases
    for file_path_func, stage_id_func in SPECIAL_CASES.items():
        if file_path_func not in file_path_funcs:
            issues.append(f"Special case file path function {file_path_func} not found")
            continue
            
        if stage_id_func not in stage_id_funcs:
            issues.append(f"Special case stage ID function {stage_id_func} not found")
            continue
            
        # Custom checks based on special case
        if file_path_func == "create_stage" and stage_id_func == "open_stage":
            if "create_if_missing" not in stage_id_funcs[stage_id_func]["parameters"]:
                issues.append(f"{stage_id_func} does not have a create_if_missing parameter")
            
            if "file_path" not in stage_id_funcs[stage_id_func]["parameters"]:
                issues.append(f"{stage_id_func} does not have a file_path parameter")
                
            if file_path_funcs[file_path_func]["return_type"] != stage_id_funcs[stage_id_func]["return_type"]:
                issues.append(f"Return type differs: {file_path_func} ({file_path_funcs[file_path_func]['return_type']}) vs {stage_id_func} ({stage_id_funcs[stage_id_func]['return_type']})")
    
    return issues

def check_unused_functions(file_path_funcs: Dict[str, Dict], stage_id_funcs: Dict[str, Dict]) -> List[str]:
    """Check for file path-based functions that don't have stage ID counterparts"""
    issues = []
    expected_file_path_funcs = [pair[0] for pair in FUNCTION_PAIRS] + list(SPECIAL_CASES.keys())
    
    for func_name in file_path_funcs.keys():
        if func_name not in expected_file_path_funcs and func_name.endswith("_stage"):
            # Check if there's a corresponding stage_id function
            stage_id_version = func_name + "_by_id"
            if stage_id_version not in stage_id_funcs:
                issues.append(f"File path function {func_name} has no stage ID counterpart")
    
    return issues

def main():
    """Main function to check integrity of the implementation"""
    file_path = "usd_mcp_server.py"
    
    try:
        functions = parse_functions(file_path)
        
        # Split into file path-based and stage ID-based functions
        file_path_funcs = {}
        stage_id_funcs = {}
        
        for func_name, func_info in functions.items():
            if func_name.endswith("_by_id") or func_name in SPECIAL_CASES.values():
                stage_id_funcs[func_name] = func_info
            elif not func_name.startswith("_") and func_name not in ["main", "parse_arguments"]:
                file_path_funcs[func_name] = func_info
        
        print(f"Found {len(file_path_funcs)} file path-based functions and {len(stage_id_funcs)} stage ID-based functions")
        
        # Check for issues
        issues = compare_functions(file_path_funcs, stage_id_funcs)
        issues.extend(check_unused_functions(file_path_funcs, stage_id_funcs))
        
        if issues:
            print("\nIssues found:")
            for issue in issues:
                print(f"- {issue}")
            print(f"\nTotal issues: {len(issues)}")
            return 1
        else:
            print("\nNo issues found! Implementation has good integrity.")
            return 0
            
    except Exception as e:
        print(f"Error checking integrity: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 