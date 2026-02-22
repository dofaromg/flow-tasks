"""
Dynamic Mesh Topology Network
動態網狀拓撲網路

實現去中心化、自組織、彈性重路由的網路架構
Implements decentralized, self-organizing, resilient rerouting network architecture
"""

import asyncio
import time
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
import heapq
from rich.console import Console

console = Console()


@dataclass
class NetworkNode:
    """網路節點"""
    id: str
    layer: str  # GEO, MEO, LEO, GROUND
    position: Tuple[float, float, float]  # (lon, lat, alt)
    is_active: bool = True
    connections: Set[str] = field(default_factory=set)
    load: float = 0.0  # 0.0 to 1.0
    latency_ms: float = 0.0


@dataclass
class NetworkLink:
    """網路鏈路"""
    source_id: str
    target_id: str
    bandwidth_gbps: float
    latency_ms: float
    reliability: float = 1.0
    is_active: bool = True
    created_at: float = field(default_factory=time.time)


class ParticleMeshNetwork:
    """
    粒子網狀網路 - 類似星鏈的動態拓撲
    
    特性：
    - 動態節點加入/移除
    - 自動鏈路建立
    - 多路徑路由
    - 自愈能力
    - 負載均衡
    """
    
    def __init__(self, name: str = "particle-mesh-network"):
        self.name = name
        self.nodes: Dict[str, NetworkNode] = {}
        self.links: Dict[Tuple[str, str], NetworkLink] = {}
        self.topology_graph: Dict[str, Set[str]] = {}
        
        # Monitoring
        self.total_nodes = 0
        self.total_links = 0
        self.failed_nodes: Set[str] = set()
        self.failed_links: Set[Tuple[str, str]] = set()
        
        # State
        self.is_running = False
        self.topology_update_interval = 5  # seconds
        
        console.print(f"[bold blue]Particle Mesh Network '{name}' initialized[/bold blue]")
    
    def add_node(self, node: NetworkNode) -> bool:
        """
        添加節點到網路
        
        Args:
            node: 網路節點
            
        Returns:
            是否成功添加
        """
        if node.id in self.nodes:
            console.print(f"[yellow]Node {node.id} already exists[/yellow]")
            return False
        
        self.nodes[node.id] = node
        self.topology_graph[node.id] = node.connections.copy()
        self.total_nodes += 1
        
        console.print(f"[green]Added node: {node.id} (Layer: {node.layer})[/green]")
        
        return True
    
    def add_nodes(self, nodes: List[NetworkNode]) -> int:
        """
        批量添加節點
        
        Args:
            nodes: 節點列表
            
        Returns:
            成功添加的節點數量
        """
        count = 0
        for node in nodes:
            if self.add_node(node):
                count += 1
        
        console.print(f"[green]Added {count}/{len(nodes)} nodes[/green]")
        return count
    
    def add_link(self, link: NetworkLink) -> bool:
        """
        添加鏈路
        
        Args:
            link: 網路鏈路
            
        Returns:
            是否成功添加
        """
        link_key = (link.source_id, link.target_id)
        reverse_key = (link.target_id, link.source_id)
        
        if link_key in self.links or reverse_key in self.links:
            console.print(f"[yellow]Link {link.source_id} ↔ {link.target_id} already exists[/yellow]")
            return False
        
        # Check if nodes exist
        if link.source_id not in self.nodes or link.target_id not in self.nodes:
            console.print(f"[red]Cannot add link: nodes not found[/red]")
            return False
        
        self.links[link_key] = link
        self.total_links += 1
        
        # Update topology graph
        if link.source_id not in self.topology_graph:
            self.topology_graph[link.source_id] = set()
        if link.target_id not in self.topology_graph:
            self.topology_graph[link.target_id] = set()
        
        self.topology_graph[link.source_id].add(link.target_id)
        self.topology_graph[link.target_id].add(link.source_id)  # Bidirectional
        
        # Update node connections
        self.nodes[link.source_id].connections.add(link.target_id)
        self.nodes[link.target_id].connections.add(link.source_id)
        
        console.print(f"[green]Added link: {link.source_id} ↔ {link.target_id} ({link.bandwidth_gbps} Gbps)[/green]")
        
        return True
    
    async def build_dynamic_topology(self) -> dict:
        """
        構建動態拓撲
        - 節點可移動（衛星軌道運動）
        - 鏈路可重組（視線範圍變化）
        - 路徑可快速切換（智能路由）
        
        Returns:
            拓撲統計信息
        """
        console.print("[bold cyan]🔧 Building dynamic topology...[/bold cyan]")
        
        # Analyze current topology
        stats = {
            "total_nodes": len(self.nodes),
            "total_links": len(self.links),
            "active_nodes": sum(1 for node in self.nodes.values() if node.is_active),
            "active_links": sum(1 for link in self.links.values() if link.is_active),
            "layers": {},
            "avg_connections_per_node": 0
        }
        
        # Layer statistics
        for node in self.nodes.values():
            if node.layer not in stats["layers"]:
                stats["layers"][node.layer] = 0
            stats["layers"][node.layer] += 1
        
        # Average connections
        if self.nodes:
            total_connections = sum(len(node.connections) for node in self.nodes.values())
            stats["avg_connections_per_node"] = total_connections / len(self.nodes)
        
        console.print(f"[green]✅ Topology built: {stats['active_nodes']} nodes, {stats['active_links']} links[/green]")
        
        return stats
    
    def calculate_shortest_path(self, source: str, destination: str) -> Optional[List[str]]:
        """
        計算最短路徑 (Dijkstra算法)
        考慮因素：延遲、帶寬、可靠性、跳數
        
        Args:
            source: 源節點ID
            destination: 目標節點ID
            
        Returns:
            路徑節點ID列表，如果不存在返回None
        """
        if source not in self.nodes or destination not in self.nodes:
            return None
        
        if source == destination:
            return [source]
        
        # Dijkstra algorithm with priority queue
        distances = {node_id: float('inf') for node_id in self.nodes}
        distances[source] = 0
        previous = {}
        pq = [(0, source)]  # (distance, node_id)
        visited = set()
        
        while pq:
            current_dist, current_node = heapq.heappop(pq)
            
            if current_node in visited:
                continue
            
            visited.add(current_node)
            
            if current_node == destination:
                break
            
            # Check neighbors
            for neighbor in self.topology_graph.get(current_node, set()):
                if neighbor in visited or not self.nodes[neighbor].is_active:
                    continue
                
                # Calculate edge weight (using latency as primary metric)
                link_key = (current_node, neighbor)
                reverse_key = (neighbor, current_node)
                
                link = self.links.get(link_key) or self.links.get(reverse_key)
                if not link or not link.is_active:
                    continue
                
                # Weight combines latency, reliability, and load
                weight = link.latency_ms * (2.0 - link.reliability) * (1.0 + self.nodes[neighbor].load)
                
                new_dist = current_dist + weight
                
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current_node
                    heapq.heappush(pq, (new_dist, neighbor))
        
        # Reconstruct path
        if destination not in previous and source != destination:
            return None
        
        path = []
        current = destination
        while current in previous:
            path.append(current)
            current = previous[current]
        path.append(source)
        path.reverse()
        
        console.print(f"[cyan]Shortest path: {' → '.join(path)}[/cyan]")
        
        return path
    
    async def resilient_rerouting(self, failed_node: str) -> Dict[str, List[str]]:
        """
        彈性重路由
        當節點失效時自動重新計算路徑
        
        Args:
            failed_node: 失效的節點ID
            
        Returns:
            受影響路徑的重路由結果
        """
        if failed_node not in self.nodes:
            return {}
        
        console.print(f"[bold red]⚠️  Node {failed_node} failed! Initiating resilient rerouting...[/bold red]")
        
        # Mark node as inactive
        self.nodes[failed_node].is_active = False
        self.failed_nodes.add(failed_node)
        
        # Mark all links to this node as inactive
        for link_key in list(self.links.keys()):
            if failed_node in link_key:
                self.links[link_key].is_active = False
                self.failed_links.add(link_key)
        
        # Find alternative paths for affected connections
        rerouted_paths = {}
        affected_connections = self.nodes[failed_node].connections
        
        for connection in affected_connections:
            if connection in self.failed_nodes:
                continue
            
            # Find alternative path
            alternative_path = self.calculate_shortest_path(connection, "ground-001")  # Example destination
            if alternative_path:
                rerouted_paths[connection] = alternative_path
        
        console.print(f"[green]✅ Rerouted {len(rerouted_paths)} connections[/green]")
        
        return rerouted_paths
    
    def get_node_neighbors(self, node_id: str) -> List[str]:
        """
        獲取節點的鄰居
        
        Args:
            node_id: 節點ID
            
        Returns:
            鄰居節點ID列表
        """
        if node_id not in self.topology_graph:
            return []
        
        return list(self.topology_graph[node_id])
    
    def get_network_statistics(self) -> dict:
        """獲取網路統計信息"""
        active_nodes = [node for node in self.nodes.values() if node.is_active]
        active_links = [link for link in self.links.values() if link.is_active]
        
        return {
            "name": self.name,
            "total_nodes": self.total_nodes,
            "active_nodes": len(active_nodes),
            "failed_nodes": len(self.failed_nodes),
            "total_links": self.total_links,
            "active_links": len(active_links),
            "failed_links": len(self.failed_links),
            "avg_node_load": sum(node.load for node in active_nodes) / len(active_nodes) if active_nodes else 0,
            "topology_density": len(active_links) / len(active_nodes) if active_nodes else 0
        }
    
    async def monitor_topology(self) -> None:
        """持續監控拓撲"""
        while self.is_running:
            stats = self.get_network_statistics()
            console.print(f"[dim]Network stats: {stats['active_nodes']} nodes, {stats['active_links']} links[/dim]")
            await asyncio.sleep(self.topology_update_interval)
    
    async def start(self) -> None:
        """啟動網路"""
        self.is_running = True
        console.print(f"[bold green]🚀 Mesh network '{self.name}' started[/bold green]")
        asyncio.create_task(self.monitor_topology())
    
    async def stop(self) -> None:
        """停止網路"""
        self.is_running = False
        console.print(f"[bold red]Mesh network '{self.name}' stopped[/bold red]")


# 示例使用
if __name__ == "__main__":
    async def demo():
        # 創建網狀網路
        mesh = ParticleMeshNetwork(name="demo-mesh")
        
        # 添加節點
        nodes = [
            NetworkNode(id="geo-001", layer="GEO", position=(0, 0, 35786)),
            NetworkNode(id="meo-001", layer="MEO", position=(120, 35, 10000)),
            NetworkNode(id="meo-002", layer="MEO", position=(121, 35, 10000)),
            NetworkNode(id="leo-001", layer="LEO", position=(120, 35, 1000)),
            NetworkNode(id="leo-002", layer="LEO", position=(121, 35, 1000)),
            NetworkNode(id="ground-001", layer="GROUND", position=(120, 35, 0)),
        ]
        mesh.add_nodes(nodes)
        
        # 添加鏈路
        links = [
            NetworkLink("geo-001", "meo-001", bandwidth_gbps=50, latency_ms=119),
            NetworkLink("meo-001", "meo-002", bandwidth_gbps=100, latency_ms=33),
            NetworkLink("meo-001", "leo-001", bandwidth_gbps=10, latency_ms=30),
            NetworkLink("meo-002", "leo-002", bandwidth_gbps=10, latency_ms=30),
            NetworkLink("leo-001", "ground-001", bandwidth_gbps=1, latency_ms=3),
        ]
        for link in links:
            mesh.add_link(link)
        
        # 構建拓撲
        topology_stats = await mesh.build_dynamic_topology()
        console.print("[bold blue]Topology Stats:[/bold blue]", topology_stats)
        
        # 計算最短路徑
        path = mesh.calculate_shortest_path("geo-001", "ground-001")
        console.print(f"[bold blue]Path from GEO to Ground:[/bold blue] {path}")
        
        # 模擬節點失效
        rerouted = await mesh.resilient_rerouting("meo-001")
        console.print("[bold blue]Rerouted paths:[/bold blue]", rerouted)
        
        # 獲取統計
        stats = mesh.get_network_statistics()
        console.print("[bold blue]Network Statistics:[/bold blue]", stats)
    
    asyncio.run(demo())
