"""
MEO Layer (~10,000km) - 中軌道
功能：邏輯流處理、動態路由、區域協調、中繼轉發
對應：PaaS 層、Build/Test 階段

MEO Layer - Medium Earth Orbit
Role: Logic flow processing, dynamic routing, regional coordination, relay forwarding
Maps to: PaaS Layer, Build/Test Stage
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import sys

# Add particle_core to path for integration
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "particle_core"))

try:
    from particle_core.src.logic_pipeline import LogicPipeline
except ImportError:
    # Fallback if particle_core not available
    class LogicPipeline:
        def __init__(self):
            pass
        
        async def process(self, data):
            return {"status": "processed", "data": data}

from rich.console import Console

console = Console()


@dataclass
class LogicFlow:
    """邏輯流數據結構"""
    id: str
    source: str
    destination: str
    data: dict
    priority: int = 5  # 1-10, 10 is highest
    created_at: float = field(default_factory=time.time)
    hops: List[str] = field(default_factory=list)
    
    def add_hop(self, satellite_id: str) -> None:
        """添加跳轉記錄"""
        self.hops.append(f"{satellite_id}@{time.time()}")


@dataclass
class InterSatelliteLink:
    """衛星間鏈路"""
    target_id: str
    link_type: str = "laser"  # laser, radio
    bandwidth_gbps: float = 100.0
    latency_ms: float = 33.0
    is_active: bool = True
    established_at: float = field(default_factory=time.time)


class MeoLogicPipeline:
    """
    MEO 層 - 邏輯管道處理系統
    
    特性：
    - 區域性邏輯處理能力
    - 智能路由選擇
    - 衛星間激光鏈路通訊
    - 中繼轉發功能
    - 負載均衡
    """
    
    def __init__(self, satellite_id: str = "meo-001", region: str = "asia-pacific"):
        self.satellite_id = satellite_id
        self.region = region
        self.orbit_altitude = 10000  # km
        self.coverage_area = "regional"
        
        # Logic pipeline integration
        self.logic_pipeline = LogicPipeline()
        
        # Inter-satellite links
        self.inter_satellite_links: Dict[str, InterSatelliteLink] = {}
        
        # Processing queues
        self.logic_flow_queue = asyncio.Queue()
        self.relay_queue = asyncio.Queue()
        
        # State
        self.is_running = False
        self.processed_count = 0
        self.relayed_count = 0
        
        # Performance metrics
        self.avg_processing_time = 0.0
        self.total_processing_time = 0.0
        
        console.print(f"[bold blue]MEO Layer {satellite_id} initialized in {region}[/bold blue]")
    
    async def route_logic_flow(self, flow: LogicFlow) -> dict:
        """
        動態路由邏輯流
        類似星鏈的智能路由選擇最佳路徑
        
        Args:
            flow: 邏輯流數據
            
        Returns:
            路由結果
        """
        flow.add_hop(self.satellite_id)
        
        # 計算最優路徑
        optimal_path = self._calculate_optimal_path(flow)
        
        # 執行管道處理
        result = await self._execute_pipeline(flow, optimal_path)
        
        console.print(f"[cyan]📊 Routed flow {flow.id} via path: {' → '.join(optimal_path)}[/cyan]")
        
        return result
    
    def _calculate_optimal_path(self, flow: LogicFlow) -> List[str]:
        """
        計算最優路徑
        考慮因素：延遲、負載、可用性、帶寬
        
        Args:
            flow: 邏輯流數據
            
        Returns:
            最優路徑的衛星ID列表
        """
        # 簡化版路由算法
        path = [self.satellite_id]
        
        # 如果有激光鏈路可用，選擇延遲最低的
        if self.inter_satellite_links:
            best_link = min(
                self.inter_satellite_links.values(),
                key=lambda link: link.latency_ms if link.is_active else float('inf')
            )
            if best_link.is_active:
                path.append(best_link.target_id)
        
        # 添加目標
        path.append(flow.destination)
        
        return path
    
    async def _execute_pipeline(self, flow: LogicFlow, path: List[str]) -> dict:
        """
        執行邏輯管道
        
        Args:
            flow: 邏輯流數據
            path: 執行路徑
            
        Returns:
            執行結果
        """
        start_time = time.time()
        
        try:
            # 使用 particle_core 的邏輯管道
            result = await self._process_with_particle_core(flow.data)
            
            processing_time = time.time() - start_time
            self.total_processing_time += processing_time
            self.processed_count += 1
            self.avg_processing_time = self.total_processing_time / self.processed_count
            
            return {
                "status": "success",
                "flow_id": flow.id,
                "path": path,
                "processing_time_ms": processing_time * 1000,
                "result": result,
                "satellite_id": self.satellite_id
            }
        except Exception as e:
            console.print(f"[red]Error executing pipeline for flow {flow.id}: {e}[/red]")
            return {
                "status": "error",
                "flow_id": flow.id,
                "error": str(e),
                "satellite_id": self.satellite_id
            }
    
    async def _process_with_particle_core(self, data: dict) -> dict:
        """
        使用 particle_core 處理邏輯
        
        Args:
            data: 輸入數據
            
        Returns:
            處理結果
        """
        # 這裡整合 particle_core 的邏輯處理功能
        # 實際實現需要根據 particle_core 的 API
        try:
            if hasattr(self.logic_pipeline, 'process'):
                result = await self.logic_pipeline.process(data)
            else:
                # Fallback to simple processing
                result = {"processed": True, "data": data}
            return result
        except Exception as e:
            console.print(f"[yellow]Particle core processing fallback: {e}[/yellow]")
            return {"processed": True, "data": data, "note": "fallback mode"}
    
    async def establish_laser_link(self, target_satellite: str, bandwidth_gbps: float = 100.0) -> bool:
        """
        建立衛星間激光鏈路（Inter-Satellite Link）
        實現衛星間高速數據傳輸
        
        Args:
            target_satellite: 目標衛星ID
            bandwidth_gbps: 鏈路帶寬 (Gbps)
            
        Returns:
            是否成功建立
        """
        link = InterSatelliteLink(
            target_id=target_satellite,
            link_type="laser",
            bandwidth_gbps=bandwidth_gbps,
            latency_ms=33.0  # Theoretical latency for MEO-MEO
        )
        
        self.inter_satellite_links[target_satellite] = link
        console.print(f"[bold green]🔗 Established laser link: {self.satellite_id} ↔ {target_satellite} ({bandwidth_gbps} Gbps)[/bold green]")
        
        return True
    
    async def relay_to_leo(self, data: dict, leo_target: str) -> dict:
        """
        中繼數據到 LEO 層
        
        Args:
            data: 要中繼的數據
            leo_target: LEO 層目標ID
            
        Returns:
            中繼結果
        """
        relay_package = {
            "type": "meo_to_leo_relay",
            "source": self.satellite_id,
            "destination": leo_target,
            "data": data,
            "timestamp": time.time()
        }
        
        await self.relay_queue.put(relay_package)
        self.relayed_count += 1
        
        console.print(f"[yellow]📡 Relaying to LEO: {self.satellite_id} → {leo_target}[/yellow]")
        
        return {
            "status": "relayed",
            "target": leo_target,
            "relay_count": self.relayed_count
        }
    
    async def relay_to_geo(self, data: dict, geo_target: str) -> dict:
        """
        中繼數據到 GEO 層
        
        Args:
            data: 要中繼的數據
            geo_target: GEO 層目標ID
            
        Returns:
            中繼結果
        """
        relay_package = {
            "type": "meo_to_geo_relay",
            "source": self.satellite_id,
            "destination": geo_target,
            "data": data,
            "timestamp": time.time()
        }
        
        await self.relay_queue.put(relay_package)
        self.relayed_count += 1
        
        console.print(f"[magenta]📡 Relaying to GEO: {self.satellite_id} → {geo_target}[/magenta]")
        
        return {
            "status": "relayed",
            "target": geo_target,
            "relay_count": self.relayed_count
        }
    
    async def process_logic_flows(self) -> None:
        """處理邏輯流隊列"""
        while self.is_running:
            try:
                if not self.logic_flow_queue.empty():
                    flow = await self.logic_flow_queue.get()
                    await self.route_logic_flow(flow)
                else:
                    await asyncio.sleep(0.1)
            except Exception as e:
                console.print(f"[red]Error processing logic flows: {e}[/red]")
                await asyncio.sleep(1)
    
    async def start(self) -> None:
        """啟動 MEO 處理系統"""
        self.is_running = True
        console.print(f"[bold green]🚀 MEO Layer {self.satellite_id} started[/bold green]")
        
        # Start processing task
        asyncio.create_task(self.process_logic_flows())
    
    async def stop(self) -> None:
        """停止 MEO 處理系統"""
        self.is_running = False
        console.print(f"[bold red]MEO Layer {self.satellite_id} stopped[/bold red]")
    
    def get_status(self) -> dict:
        """獲取狀態"""
        return {
            "satellite_id": self.satellite_id,
            "layer": "MEO",
            "region": self.region,
            "altitude_km": self.orbit_altitude,
            "is_running": self.is_running,
            "processed_count": self.processed_count,
            "relayed_count": self.relayed_count,
            "avg_processing_time_ms": self.avg_processing_time * 1000,
            "inter_satellite_links": len(self.inter_satellite_links),
            "active_links": sum(1 for link in self.inter_satellite_links.values() if link.is_active),
            "queue_size": self.logic_flow_queue.qsize()
        }


# 示例使用
if __name__ == "__main__":
    async def demo():
        # 創建 MEO 層實例
        meo1 = MeoLogicPipeline(satellite_id="meo-001", region="asia-pacific")
        meo2 = MeoLogicPipeline(satellite_id="meo-002", region="asia-pacific")
        
        # 建立衛星間鏈路
        await meo1.establish_laser_link("meo-002", bandwidth_gbps=100.0)
        
        # 創建邏輯流
        flow = LogicFlow(
            id="flow-001",
            source="ground-001",
            destination="leo-001",
            data={"action": "process", "payload": {"value": 42}}
        )
        
        # 路由邏輯流
        result = await meo1.route_logic_flow(flow)
        console.print("[bold blue]Flow Result:[/bold blue]", result)
        
        # 中繼到 LEO
        relay_result = await meo1.relay_to_leo({"test": "data"}, "leo-001")
        console.print("[bold blue]Relay Result:[/bold blue]", relay_result)
        
        # 獲取狀態
        status = meo1.get_status()
        console.print("[bold blue]MEO Status:[/bold blue]", status)
    
    asyncio.run(demo())
