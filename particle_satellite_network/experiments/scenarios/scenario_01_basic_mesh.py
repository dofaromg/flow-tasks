"""
實驗場景1: 基礎網狀網路測試
Experiment Scenario 1: Basic Mesh Network Test

目標: 驗證動態網狀拓撲的建立與路由功能
Goal: Verify dynamic mesh topology construction and routing
"""

import asyncio
import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from particle_satellite_network.core.satellite_layers import (
    GeoPersonaCore, MeoLogicPipeline, LeoParticleRuntime, GroundUserInterface, PersonaSeed
)
from particle_satellite_network.core.network import (
    ParticleMeshNetwork, NetworkNode, NetworkLink
)
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


async def setup_satellite_layers():
    """設置所有衛星層"""
    console.print(Panel.fit(
        "[bold cyan]🛰️  Setting up Satellite Layers[/bold cyan]",
        border_style="cyan"
    ))
    
    # Create GEO layer
    geo = GeoPersonaCore(satellite_id="geo-001", longitude=0.0)
    await geo.load_seed_origin_core()
    
    # Create MEO layers
    meo_nodes = []
    for i in range(3):
        meo = MeoLogicPipeline(
            satellite_id=f"meo-00{i+1}",
            region="asia-pacific"
        )
        meo_nodes.append(meo)
    
    # Create LEO layers
    leo_nodes = []
    for i in range(5):
        leo = LeoParticleRuntime(
            satellite_id=f"leo-00{i+1}",
            position=(120.0 + i * 2, 35.0, 1000.0)
        )
        leo_nodes.append(leo)
    
    # Create ground station
    ground = GroundUserInterface(
        station_id="gs-tokyo",
        location=(139.6917, 35.6895)
    )
    
    return geo, meo_nodes, leo_nodes, ground


async def build_mesh_network(geo, meo_nodes, leo_nodes, ground):
    """構建網狀網路"""
    console.print(Panel.fit(
        "[bold yellow]🔧 Building Mesh Network Topology[/bold yellow]",
        border_style="yellow"
    ))
    
    mesh = ParticleMeshNetwork(name="scenario-01-mesh")
    
    # Add GEO node
    geo_node = NetworkNode(
        id="geo-001",
        layer="GEO",
        position=(0.0, 0.0, 35786.0)
    )
    mesh.add_node(geo_node)
    
    # Add MEO nodes
    for i, meo in enumerate(meo_nodes):
        meo_node = NetworkNode(
            id=f"meo-00{i+1}",
            layer="MEO",
            position=(120.0 + i * 40, 35.0, 10000.0)
        )
        mesh.add_node(meo_node)
    
    # Add LEO nodes
    for i, leo in enumerate(leo_nodes):
        leo_node = NetworkNode(
            id=f"leo-00{i+1}",
            layer="LEO",
            position=(120.0 + i * 2, 35.0, 1000.0)
        )
        mesh.add_node(leo_node)
    
    # Add ground node
    ground_node = NetworkNode(
        id="gs-tokyo",
        layer="GROUND",
        position=(139.6917, 35.6895, 0.0)
    )
    mesh.add_node(ground_node)
    
    # Add links
    # GEO to MEO links
    for i in range(len(meo_nodes)):
        link = NetworkLink(
            source_id="geo-001",
            target_id=f"meo-00{i+1}",
            bandwidth_gbps=50.0,
            latency_ms=119.0
        )
        mesh.add_link(link)
    
    # MEO to MEO links (inter-satellite)
    for i in range(len(meo_nodes) - 1):
        link = NetworkLink(
            source_id=f"meo-00{i+1}",
            target_id=f"meo-00{i+2}",
            bandwidth_gbps=100.0,
            latency_ms=33.0
        )
        mesh.add_link(link)
    
    # MEO to LEO links
    for i in range(len(meo_nodes)):
        for j in range(2):  # Each MEO connects to 2 LEOs
            leo_idx = i * 2 + j
            if leo_idx < len(leo_nodes):
                link = NetworkLink(
                    source_id=f"meo-00{i+1}",
                    target_id=f"leo-00{leo_idx+1}",
                    bandwidth_gbps=10.0,
                    latency_ms=30.0
                )
                mesh.add_link(link)
    
    # LEO to Ground link
    link = NetworkLink(
        source_id="leo-001",
        target_id="gs-tokyo",
        bandwidth_gbps=1.0,
        latency_ms=3.0
    )
    mesh.add_link(link)
    
    # Build topology
    topology_stats = await mesh.build_dynamic_topology()
    
    return mesh, topology_stats


async def test_routing(mesh):
    """測試路由功能"""
    console.print(Panel.fit(
        "[bold green]🔍 Testing Routing Functions[/bold green]",
        border_style="green"
    ))
    
    test_pairs = [
        ("geo-001", "gs-tokyo"),
        ("meo-001", "leo-003"),
        ("leo-001", "gs-tokyo"),
    ]
    
    results = []
    for source, dest in test_pairs:
        start_time = time.time()
        path = mesh.calculate_shortest_path(source, dest)
        elapsed_ms = (time.time() - start_time) * 1000
        
        if path:
            results.append({
                "source": source,
                "destination": dest,
                "path": " → ".join(path),
                "hops": len(path) - 1,
                "time_ms": elapsed_ms
            })
    
    return results


async def test_resilience(mesh):
    """測試彈性重路由"""
    console.print(Panel.fit(
        "[bold red]⚠️  Testing Resilient Rerouting[/bold red]",
        border_style="red"
    ))
    
    # Simulate node failure
    failed_node = "meo-002"
    rerouted_paths = await mesh.resilient_rerouting(failed_node)
    
    return {
        "failed_node": failed_node,
        "rerouted_connections": len(rerouted_paths),
        "details": rerouted_paths
    }


async def run_basic_mesh_experiment():
    """運行基礎網狀網路實驗"""
    console.print(Panel.fit(
        "[bold magenta]🔬 Experiment Scenario 1: Basic Mesh Network Test[/bold magenta]\n"
        "[dim]Testing dynamic topology, routing, and resilience[/dim]",
        border_style="magenta",
        title="Start"
    ))
    
    # Setup
    geo, meo_nodes, leo_nodes, ground = await setup_satellite_layers()
    
    # Build mesh
    mesh, topology_stats = await build_mesh_network(geo, meo_nodes, leo_nodes, ground)
    
    # Display topology stats
    table = Table(title="🌐 Network Topology Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Nodes", str(topology_stats["total_nodes"]))
    table.add_row("Active Nodes", str(topology_stats["active_nodes"]))
    table.add_row("Total Links", str(topology_stats["total_links"]))
    table.add_row("Active Links", str(topology_stats["active_links"]))
    table.add_row("Avg Connections/Node", f"{topology_stats['avg_connections_per_node']:.2f}")
    
    console.print(table)
    
    # Test routing
    routing_results = await test_routing(mesh)
    
    # Display routing results
    table = Table(title="📊 Routing Test Results")
    table.add_column("Source", style="cyan")
    table.add_column("Destination", style="yellow")
    table.add_column("Path", style="green")
    table.add_column("Hops", style="blue")
    table.add_column("Time (ms)", style="magenta")
    
    for result in routing_results:
        table.add_row(
            result["source"],
            result["destination"],
            result["path"],
            str(result["hops"]),
            f"{result['time_ms']:.3f}"
        )
    
    console.print(table)
    
    # Test resilience
    resilience_result = await test_resilience(mesh)
    
    # Display resilience results
    console.print(f"\n[bold red]Failed Node:[/bold red] {resilience_result['failed_node']}")
    console.print(f"[bold green]Rerouted Connections:[/bold green] {resilience_result['rerouted_connections']}")
    
    # Get final network statistics
    final_stats = mesh.get_network_statistics()
    
    # Summary
    console.print(Panel.fit(
        f"[bold green]✅ Experiment Complete![/bold green]\n\n"
        f"[cyan]Active Nodes:[/cyan] {final_stats['active_nodes']}/{final_stats['total_nodes']}\n"
        f"[cyan]Active Links:[/cyan] {final_stats['active_links']}/{final_stats['total_links']}\n"
        f"[cyan]Failed Nodes:[/cyan] {final_stats['failed_nodes']}\n"
        f"[cyan]Topology Density:[/cyan] {final_stats['topology_density']:.2f}",
        border_style="green",
        title="Summary"
    ))
    
    return {
        "topology_stats": topology_stats,
        "routing_results": routing_results,
        "resilience_result": resilience_result,
        "final_stats": final_stats
    }


if __name__ == "__main__":
    result = asyncio.run(run_basic_mesh_experiment())
    console.print(f"\n[bold]Experiment completed successfully! ✨[/bold]")
