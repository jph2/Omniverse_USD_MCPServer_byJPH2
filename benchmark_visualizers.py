#!/usr/bin/env python3
"""
Omniverse USD MCP Server - Scene Graph Visualizer Benchmark

This script benchmarks different scene graph visualization approaches
to compare performance and memory usage.

Prerequisites:
1. Run the USD MCP Server: python usd_mcp_server.py --host 0.0.0.0 --port 5000
2. Create test USD files of various sizes or use the built-in generator
"""

from scene_graph_visualizer import UsdSceneGraphVisualizer
from scene_graph_optimizer import UsdSceneGraphOptimizer
from cursor_integration import CursorUsdTools
import time
import os
import sys
import argparse
import json
import tracemalloc
from typing import Dict, Any, List, Optional, Tuple

class BenchmarkResult:
    """Stores benchmark results for a visualization approach"""
    
    def __init__(self, name: str):
        """Initialize benchmark result
        
        Args:
            name: Name of the approach being benchmarked
        """
        self.name = name
        self.elapsed_time = 0.0
        self.memory_peak = 0
        self.file_size = 0
        self.success = False
        self.error = None
        self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary for serialization
        
        Returns:
            Dictionary with benchmark results
        """
        return {
            "name": self.name,
            "elapsed_time_seconds": self.elapsed_time,
            "memory_peak_kb": self.memory_peak / 1024,  # Convert bytes to KB
            "file_size_kb": self.file_size / 1024 if self.file_size else 0,
            "success": self.success,
            "error": str(self.error) if self.error else None,
            "metadata": self.metadata
        }

def generate_test_stage(file_path: str, complexity: str = "medium") -> Dict[str, Any]:
    """Generate a test USD stage with controlled complexity
    
    Args:
        file_path: Path to save the stage
        complexity: Complexity level ("small", "medium", "large", "huge")
        
    Returns:
        Dictionary with stage information
    """
    usd_tools = CursorUsdTools()
    
    # Define complexity parameters
    complexity_params = {
        "small": {
            "grid_size": 3,
            "levels": 1,
            "variations": 2
        },
        "medium": {
            "grid_size": 5,
            "levels": 2,
            "variations": 3
        },
        "large": {
            "grid_size": 10,
            "levels": 3,
            "variations": 4
        },
        "huge": {
            "grid_size": 15,
            "levels": 4,
            "variations": 5
        }
    }
    
    params = complexity_params.get(complexity, complexity_params["medium"])
    grid_size = params["grid_size"]
    levels = params["levels"]
    variations = params["variations"]
    
    # Create stage
    result = usd_tools.create_stage(file_path, template="full")
    if not result.get("ok", False):
        return result
    
    # Create a grid of objects
    for x in range(-grid_size // 2, grid_size // 2 + 1):
        for z in range(-grid_size // 2, grid_size // 2 + 1):
            # Base path for this grid position
            base_path = f"/World/Grid/{x}_{z}"
            
            # Create hierarchy with specified levels
            for level in range(levels):
                for variant in range(variations):
                    # Create object path
                    obj_path = f"{base_path}/Level_{level}/Variant_{variant}"
                    
                    # Alternate between different primitive types
                    prim_types = ["cube", "sphere", "cylinder", "cone"]
                    prim_type = prim_types[(x + z + level + variant) % len(prim_types)]
                    
                    # Position offset based on level and variant
                    pos_x = x * 3.0 + variant * 0.2
                    pos_y = level * 1.0 + 0.5
                    pos_z = z * 3.0 + variant * 0.2
                    
                    # Create primitive
                    usd_tools.create_primitive(
                        file_path,
                        prim_type,
                        obj_path,
                        size=0.5,
                        position=(pos_x, pos_y, pos_z)
                    )
                    
                    # Add material for some objects
                    if (x + z + level + variant) % 3 == 0:
                        mat_path = f"/World/Materials/Material_{x}_{z}_{level}_{variant}"
                        r = ((x + grid_size//2) / grid_size)
                        g = ((z + grid_size//2) / grid_size)
                        b = ((level + 1) / levels)
                        
                        usd_tools.create_material(
                            file_path,
                            mat_path,
                            diffuse_color=(r, g, b),
                            metallic=(variant / variations) * 0.8,
                            roughness=0.5
                        )
                        
                        usd_tools.bind_material(
                            file_path,
                            obj_path,
                            mat_path
                        )
    
    # Add ground plane
    usd_tools.create_primitive(
        file_path,
        "cube",
        "/World/Environment/Ground",
        size=grid_size * 3.0,
        position=(0, -0.25, 0)
    )
    usd_tools.set_transform(
        file_path,
        "/World/Environment/Ground",
        scale=(1.0, 0.1, 1.0)
    )
    
    # Add ground material
    usd_tools.create_material(
        file_path,
        "/World/Materials/GroundMaterial",
        diffuse_color=(0.3, 0.3, 0.3),
        metallic=0.0,
        roughness=0.9
    )
    
    usd_tools.bind_material(
        file_path,
        "/World/Environment/Ground",
        "/World/Materials/GroundMaterial"
    )
    
    # Get stage analysis
    analysis = usd_tools.analyze_stage(file_path)
    prim_count = len(analysis.get("data", {}).get("prims", [])) if analysis.get("ok", False) else 0
    
    return {
        "ok": True,
        "stage_path": file_path,
        "prim_count": prim_count,
        "complexity": complexity,
        "parameters": params
    }

def benchmark_approach(approach: str, stage_path: str, output_format: str = "html", 
                      output_dir: str = "benchmark_results") -> BenchmarkResult:
    """Benchmark a specific visualization approach
    
    Args:
        approach: Visualization approach to benchmark
        stage_path: Path to the USD stage file
        output_format: Output format for visualization
        output_dir: Directory to store output files
        
    Returns:
        BenchmarkResult with performance metrics
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Prepare output path
    stage_name = os.path.splitext(os.path.basename(stage_path))[0]
    output_file = f"{output_dir}/{stage_name}_{approach}_{output_format}"
    if output_format == "html":
        output_file += ".html"
    elif output_format in ["json", "network"]:
        output_file += ".json"
    
    # Initialize result
    result = BenchmarkResult(approach)
    
    try:
        # Start memory tracking
        tracemalloc.start()
        
        # Start timing
        start_time = time.time()
        
        # Run the appropriate approach
        if approach == "basic_visualizer":
            # Use the basic visualizer directly
            visualizer = UsdSceneGraphVisualizer(stage_path)
            
            if output_format == "text":
                text_output = visualizer.to_text()
                with open(output_file + ".txt", 'w') as f:
                    f.write(text_output)
            elif output_format == "html":
                visualizer.to_html(output_file)
            elif output_format == "json":
                visualizer.to_json(output_file)
            elif output_format == "network":
                visualizer.to_network_data(output_file)
        
        elif approach == "optimizer":
            # Use the scene graph optimizer
            optimizer = UsdSceneGraphOptimizer(stage_path)
            
            viz_result = optimizer.visualize(
                output_format=output_format,
                output_path=output_file,
                open_browser=False  # Don't open browser during benchmarking
            )
            
            # Add metadata from the optimizer result
            if viz_result.get("ok", False):
                result.metadata = viz_result.get("performance", {})
        
        elif approach == "direct_mcp_call":
            # Use the MCP server directly through cursor integration
            usd_tools = CursorUsdTools()
            
            viz_result = usd_tools.visualize_scene_graph(
                file_path=stage_path,
                output_format=output_format,
                output_path=output_file
            )
            
            if viz_result.get("ok", False):
                result.metadata["server_response"] = viz_result.get("message", "")
        
        # End timing
        end_time = time.time()
        result.elapsed_time = end_time - start_time
        
        # Get memory usage
        current, peak = tracemalloc.get_traced_memory()
        result.memory_peak = peak
        
        # Get output file size if it exists
        if os.path.exists(output_file):
            result.file_size = os.path.getsize(output_file)
        
        result.success = True
        
    except Exception as e:
        result.success = False
        result.error = e
        traceback.print_exc()
    
    finally:
        # Stop memory tracking
        tracemalloc.stop()
    
    return result

def run_benchmarks(stage_paths: List[str], approaches: List[str], 
                  output_formats: List[str], output_dir: str = "benchmark_results") -> Dict[str, List[BenchmarkResult]]:
    """Run benchmarks across multiple stages, approaches, and formats
    
    Args:
        stage_paths: Paths to USD stage files
        approaches: Visualization approaches to benchmark
        output_formats: Output formats to test
        output_dir: Directory to store output files
        
    Returns:
        Dictionary mapping stage names to lists of benchmark results
    """
    results = {}
    
    for stage_path in stage_paths:
        stage_name = os.path.splitext(os.path.basename(stage_path))[0]
        results[stage_name] = []
        
        print(f"\nBenchmarking stage: {stage_name}")
        
        for approach in approaches:
            for output_format in output_formats:
                print(f"  Testing {approach} with {output_format} format...")
                benchmark = benchmark_approach(
                    approach=approach,
                    stage_path=stage_path,
                    output_format=output_format,
                    output_dir=output_dir
                )
                
                results[stage_name].append(benchmark)
                
                # Print result
                status = "SUCCESS" if benchmark.success else "FAILED"
                print(f"    {status} - Time: {benchmark.elapsed_time:.2f}s, Memory: {benchmark.memory_peak/1024/1024:.2f}MB")
    
    return results

def generate_report(results: Dict[str, List[BenchmarkResult]], output_file: str = "benchmark_report.html") -> None:
    """Generate an HTML report from benchmark results
    
    Args:
        results: Dictionary mapping stage names to lists of benchmark results
        output_file: Path to save the HTML report
    """
    # Create output directory if needed
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Collect data for charts
    stages = list(results.keys())
    approaches = set()
    formats = set()
    
    for stage_results in results.values():
        for result in stage_results:
            approaches.add(result.name)
            if "format" in result.metadata:
                formats.add(result.metadata["format"])
    
    approaches = list(approaches)
    formats = list(formats)
    
    # Prepare HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>USD Scene Graph Visualizer Benchmark Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        .summary {{
            margin: 20px 0;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .success {{
            color: #27ae60;
        }}
        .failure {{
            color: #e74c3c;
        }}
        .chart-container {{
            height: 400px;
            margin: 30px 0;
        }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            font-size: 0.9em;
            color: #7f8c8d;
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <h1>USD Scene Graph Visualizer Benchmark Report</h1>
        <p>Generated on {time.strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <div class="summary">
            <h2>Summary</h2>
            <p>Benchmarked {len(stages)} stages with {len(approaches)} different visualization approaches.</p>
        </div>
        
        <h2>Performance Comparison</h2>
        
        <div class="chart-container">
            <canvas id="timeChart"></canvas>
        </div>
        
        <div class="chart-container">
            <canvas id="memoryChart"></canvas>
        </div>
        
        <h2>Detailed Results</h2>
"""

    # Add detailed results tables for each stage
    for stage_name, stage_results in results.items():
        html_content += f"""
        <h3>Stage: {stage_name}</h3>
        <table>
            <tr>
                <th>Approach</th>
                <th>Format</th>
                <th>Time (s)</th>
                <th>Memory (MB)</th>
                <th>Output Size (KB)</th>
                <th>Status</th>
            </tr>
"""

        for result in stage_results:
            format_name = result.metadata.get("format", "unknown")
            status_class = "success" if result.success else "failure"
            status_text = "Success" if result.success else f"Failed: {result.error}"
            
            html_content += f"""
            <tr>
                <td>{result.name}</td>
                <td>{format_name}</td>
                <td>{result.elapsed_time:.2f}</td>
                <td>{result.memory_peak/1024/1024:.2f}</td>
                <td>{result.file_size/1024:.2f}</td>
                <td class="{status_class}">{status_text}</td>
            </tr>
"""
        
        html_content += """
        </table>
"""

    # Prepare data for charts
    time_chart_data = {}
    memory_chart_data = {}
    
    for stage_name, stage_results in results.items():
        for result in stage_results:
            approach_key = result.name
            
            if approach_key not in time_chart_data:
                time_chart_data[approach_key] = []
                memory_chart_data[approach_key] = []
            
            if result.success:
                time_chart_data[approach_key].append(result.elapsed_time)
                memory_chart_data[approach_key].append(result.memory_peak / 1024 / 1024)  # Convert to MB
    
    # Add JavaScript for charts
    html_content += f"""
        <script>
            // Time performance chart
            const timeCtx = document.getElementById('timeChart').getContext('2d');
            new Chart(timeCtx, {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(stages)},
                    datasets: [
"""

    colors = ['rgba(54, 162, 235, 0.7)', 'rgba(255, 99, 132, 0.7)', 'rgba(75, 192, 192, 0.7)', 
             'rgba(255, 159, 64, 0.7)', 'rgba(153, 102, 255, 0.7)']
    
    for i, (approach, times) in enumerate(time_chart_data.items()):
        color = colors[i % len(colors)]
        html_content += f"""
                        {{
                            label: '{approach}',
                            data: {json.dumps(times)},
                            backgroundColor: '{color}',
                            borderColor: '{color.replace("0.7", "1")}',
                            borderWidth: 1
                        }},
"""
    
    html_content += """
                    ]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Time Performance Comparison (seconds)',
                            font: { size: 16 }
                        },
                        legend: {
                            position: 'top',
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Time (seconds)'
                            }
                        }
                    }
                }
            });
            
            // Memory performance chart
            const memoryCtx = document.getElementById('memoryChart').getContext('2d');
            new Chart(memoryCtx, {
                type: 'bar',
                data: {
                    labels: """ + json.dumps(stages) + """,
                    datasets: [
"""

    for i, (approach, memory_values) in enumerate(memory_chart_data.items()):
        color = colors[(i+2) % len(colors)]  # Offset for different colors
        html_content += f"""
                        {{
                            label: '{approach}',
                            data: {json.dumps(memory_values)},
                            backgroundColor: '{color}',
                            borderColor: '{color.replace("0.7", "1")}',
                            borderWidth: 1
                        }},
"""
    
    html_content += """
                    ]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Memory Usage Comparison (MB)',
                            font: { size: 16 }
                        },
                        legend: {
                            position: 'top',
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Memory (MB)'
                            }
                        }
                    }
                }
            });
        </script>
        
        <div class="footer">
            <p>USD Scene Graph Visualizer Benchmark</p>
        </div>
    </div>
</body>
</html>
"""

    # Write the HTML report
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"\nBenchmark report generated: {output_file}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="USD Scene Graph Visualizer Benchmark")
    parser.add_argument("--stages", "-s", nargs="+", help="Paths to USD stage files for benchmarking")
    parser.add_argument("--generate", "-g", choices=["small", "medium", "large", "huge"], 
                      nargs="+", default=["medium"], 
                      help="Generate test stages with specified complexities")
    parser.add_argument("--approaches", "-a", nargs="+", 
                      choices=["basic_visualizer", "optimizer", "direct_mcp_call"],
                      default=["basic_visualizer", "optimizer", "direct_mcp_call"],
                      help="Visualization approaches to benchmark")
    parser.add_argument("--formats", "-f", nargs="+", 
                      choices=["text", "html", "json", "network"],
                      default=["html", "text"],
                      help="Output formats to test")
    parser.add_argument("--output-dir", "-o", default="benchmark_results",
                      help="Directory to store benchmark outputs")
    parser.add_argument("--report", "-r", default="benchmark_report.html",
                      help="Path for the benchmark report")
    
    args = parser.parse_args()
    
    # Ensure we have stages to benchmark
    stage_paths = []
    
    # Generate test stages if requested
    if args.generate:
        print("Generating test stages...")
        for complexity in args.generate:
            file_path = f"test_stage_{complexity}.usda"
            result = generate_test_stage(file_path, complexity)
            if result.get("ok", False):
                print(f"  Generated {complexity} stage with {result.get('prim_count', 0)} prims: {file_path}")
                stage_paths.append(file_path)
            else:
                print(f"  Failed to generate {complexity} stage: {result.get('message', '')}")
    
    # Add user-specified stages
    if args.stages:
        for stage_path in args.stages:
            if os.path.exists(stage_path):
                stage_paths.append(stage_path)
            else:
                print(f"Warning: Stage file not found: {stage_path}")
    
    if not stage_paths:
        print("Error: No stages to benchmark. Please specify stages with --stages or generate them with --generate.")
        return 1
    
    # Run benchmarks
    print(f"\nRunning benchmarks on {len(stage_paths)} stages...")
    benchmark_results = run_benchmarks(
        stage_paths=stage_paths,
        approaches=args.approaches,
        output_formats=args.formats,
        output_dir=args.output_dir
    )
    
    # Generate report
    generate_report(benchmark_results, args.report)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 