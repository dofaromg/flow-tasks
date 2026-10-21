"""
LEO Layer (~1,000km) - 低軌道
功能：實時粒子計算、低延遲響應、邊緣計算、動態負載均衡
對應：IaaS 層、Development/Source Code 階段

LEO Layer - Low Earth Orbit
Role: Real-time particle computation, low latency response, edge computing, dynamic load balancing
Maps to: IaaS Layer, Development/Source Code Stage
"""

import asyncio
import time
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from rich.console import Console

console = Console()


@dataclass
class ParticleTask:
    """粒子計算任務"""
    id: str
    particle_data: dict
    priority: int = 5
    created_at: float = field(default_factory=time.time)
    executed_at: Optional[float] = None
    execution_time_ms: float = 0.0
    result: Optional[dict] = None


@dataclass
class SatellitePosition:
    """衛星位置"""
    longitude: float
    latitude: float
    altitude: float  # km
    timestamp: float = field(default_factory=time.time)
    
    def distance_to(self, other: 'SatellitePosition') -> float:
        """計算到另一個位置的距離 (km)"""
        # 簡化的距離計算
        R = 6371  # Earth radius in km
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        horizontal_distance = R * c
        altitude_diff = abs(self.altitude - other.altitude)
        
        return math.sqrt(horizontal_distance**2 + altitude_diff**2)


class LeoParticleRuntime:
    """
    LEO 層 - 粒子實時執行系統
    
    特性：
    - 超低延遲（~1ms）
    - 邊緣計算能力
    - 就近接入原則
    - 衛星切換（handover）
    - 動態負載均衡
    """
    
    def __init__(self, satellite_id: str = "leo-001", position: Tuple[float, float, float] = (0.0, 0.0, 1000.0)):
        self.satellite_id = satellite_id
        self.orbit_altitude = 1000  # km
        self.position = SatellitePosition(
            longitude=position[0],
            latitude=position[1],
            altitude=position[2]
        )
        self.latency_target_ms = 1.0  # 1ms 超低延遲目標
        self.actual_latency_ms = 0.0
        
        # Particle computation
        self.particle_pool: List[ParticleTask] = []
        self.task_queue = asyncio.Queue()
        self.completed_tasks: List[ParticleTask] = []
        
        # State
        self.is_running = False
        self.processed_count = 0
        self.total_processing_time = 0.0
        
        # Connected ground stations
        self.connected_ground_stations: List[str] = []
        
        # Neighboring satellites for handover
        self.neighbor_satellites: Dict[str, SatellitePosition] = {}
        
        # Load metrics
        self.current_load = 0.0  # 0.0 to 1.0
        self.max_concurrent_tasks = 100
        
        console.print(f"[bold gold1]LEO Layer {satellite_id} initialized at position {position}[/bold gold1]")
    
    async def execute_particle(self, particle: dict) -> dict:
        """
        執行粒子計算 - 邊緣計算模式
        類似 Cloudflare Workers 的邊緣運算
        
        Args:
            particle: 粒子數據
            
        Returns:
            執行結果
        """
        task = ParticleTask(
            id=f"task-{self.processed_count + 1}",
            particle_data=particle,
            priority=particle.get("priority", 5)
        )
        
        start_time = time.time()
        
        try:
            # 執行粒子邏輯
            result = await self._run_particle_logic(particle)
            
            execution_time = (time.time() - start_time) * 1000  # ms
            
            task.executed_at = time.time()
            task.execution_time_ms = execution_time
            task.result = result
            
            self.completed_tasks.append(task)
            self.processed_count += 1
            self.total_processing_time += execution_time
            self.actual_latency_ms = self.total_processing_time / self.processed_count
            
            # Update load
            self._update_load()
            
            console.print(f"[green]✨ Executed particle {task.id} in {execution_time:.2f}ms[/green]")
            
            return {
                "status": "success",
                "task_id": task.id,
                "execution_time_ms": execution_time,
                "result": result,
                "satellite_id": self.satellite_id
            }
        except Exception as e:
            console.print(f"[red]Error executing particle: {e}[/red]")
            return {
                "status": "error",
                "error": str(e),
                "satellite_id": self.satellite_id
            }
    
    async def _run_particle_logic(self, particle: dict) -> dict:
        """
        執行粒子邏輯代碼
        整合 particle_core 的執行引擎
        
        Args:
            particle: 粒子數據
            
        Returns:
            執行結果
        """
        # 模擬粒子計算
        await asyncio.sleep(0.001)  # 1ms 模擬計算時間
        
        # 這裡可以整合 particle_core 的執行引擎
        # 實際實現需要根據 particle_core 的 API
        
        return {
            "computed": True,
            "input": particle,
            "output": {
                "value": particle.get("value", 0) * 2,
                "timestamp": time.time()
            }
        }
    
    async def find_nearest_ground_station(self, ground_stations: List[Dict]) -> Optional[str]:
        """
        尋找最近的地面站
        實現就近接入原則（最低延遲）
        
        Args:
            ground_stations: 地面站列表，包含位置信息
            
        Returns:
            最近地面站的ID，如果沒有返回None
        """
        if not ground_stations:
            return None
        
        nearest_station = None
        min_distance = float('inf')
        
        for station in ground_stations:
            station_pos = SatellitePosition(
                longitude=station['coordinates'][0],
                latitude=station['coordinates'][1],
                altitude=0.0  # Ground level
            )
            
            distance = self.position.distance_to(station_pos)
            
            if distance < min_distance:
                min_distance = distance
                nearest_station = station['id']
        
        if nearest_station:
            console.print(f"[cyan]📍 Nearest ground station: {nearest_station} ({min_distance:.2f} km)[/cyan]")
            self.connected_ground_stations.append(nearest_station)
        
        return nearest_station
    
    async def handover_to_next_satellite(self, next_satellite_id: str) -> dict:
        """
        切換到下一顆衛星
        當衛星移出覆蓋範圍時無縫切換
        
        Args:
            next_satellite_id: 下一顆衛星的ID
            
        Returns:
            切換結果
        """
        if next_satellite_id not in self.neighbor_satellites:
            console.print(f"[yellow]Warning: {next_satellite_id} not in neighbor list[/yellow]")
            return {
                "status": "failed",
                "reason": "satellite_not_found"
            }
        
        # 傳輸當前任務隊列
        handover_data = {
            "source_satellite": self.satellite_id,
            "target_satellite": next_satellite_id,
            "pending_tasks": self.task_queue.qsize(),
            "active_connections": len(self.connected_ground_stations),
            "timestamp": time.time()
        }
        
        console.print(f"[bold yellow]🔄 Handover: {self.satellite_id} → {next_satellite_id}[/bold yellow]")
        console.print(f"   Transferring {handover_data['pending_tasks']} pending tasks")
        
        return {
            "status": "success",
            "handover_data": handover_data
        }
    
    def add_neighbor_satellite(self, satellite_id: str, position: Tuple[float, float, float]) -> None:
        """
        添加鄰近衛星
        
        Args:
            satellite_id: 衛星ID
            position: 位置 (lon, lat, alt)
        """
        self.neighbor_satellites[satellite_id] = SatellitePosition(
            longitude=position[0],
            latitude=position[1],
            altitude=position[2]
        )
        console.print(f"[cyan]Added neighbor satellite: {satellite_id}[/cyan]")
    
    def _update_load(self) -> None:
        """更新當前負載"""
        active_tasks = self.task_queue.qsize()
        self.current_load = min(1.0, active_tasks / self.max_concurrent_tasks)
    
    def is_overloaded(self, threshold: float = 0.8) -> bool:
        """
        檢查是否過載
        
        Args:
            threshold: 負載閾值 (0.0-1.0)
            
        Returns:
            是否過載
        """
        return self.current_load >= threshold
    
    async def process_task_queue(self) -> None:
        """處理任務隊列"""
        while self.is_running:
            try:
                if not self.task_queue.empty():
                    particle_data = await self.task_queue.get()
                    await self.execute_particle(particle_data)
                else:
                    await asyncio.sleep(0.01)  # 10ms
            except Exception as e:
                console.print(f"[red]Error processing task queue: {e}[/red]")
                await asyncio.sleep(0.1)
    
    async def start(self) -> None:
        """啟動 LEO 處理系統"""
        self.is_running = True
        console.print(f"[bold green]🚀 LEO Layer {self.satellite_id} started[/bold green]")
        
        # Start processing task
        asyncio.create_task(self.process_task_queue())
    
    async def stop(self) -> None:
        """停止 LEO 處理系統"""
        self.is_running = False
        console.print(f"[bold red]LEO Layer {self.satellite_id} stopped[/bold red]")
    
    def get_status(self) -> dict:
        """獲取狀態"""
        return {
            "satellite_id": self.satellite_id,
            "layer": "LEO",
            "altitude_km": self.orbit_altitude,
            "position": (self.position.longitude, self.position.latitude, self.position.altitude),
            "is_running": self.is_running,
            "processed_count": self.processed_count,
            "current_load": self.current_load,
            "is_overloaded": self.is_overloaded(),
            "avg_latency_ms": self.actual_latency_ms,
            "latency_target_ms": self.latency_target_ms,
            "connected_ground_stations": len(self.connected_ground_stations),
            "neighbor_satellites": len(self.neighbor_satellites),
            "queue_size": self.task_queue.qsize(),
            "completed_tasks": len(self.completed_tasks)
        }


# 示例使用
if __name__ == "__main__":
    async def demo():
        # 創建 LEO 層實例
        leo1 = LeoParticleRuntime(satellite_id="leo-001", position=(120.0, 35.0, 1000.0))
        leo2 = LeoParticleRuntime(satellite_id="leo-002", position=(121.0, 35.0, 1000.0))
        
        # 添加鄰近衛星
        leo1.add_neighbor_satellite("leo-002", (121.0, 35.0, 1000.0))
        
        # 啟動
        await leo1.start()
        
        # 執行粒子計算
        particle = {
            "type": "compute",
            "value": 42,
            "priority": 8
        }
        result = await leo1.execute_particle(particle)
        console.print("[bold blue]Execution Result:[/bold blue]", result)
        
        # 尋找最近的地面站
        ground_stations = [
            {"id": "gs-tokyo", "coordinates": [139.6917, 35.6895]},
            {"id": "gs-osaka", "coordinates": [135.5023, 34.6937]}
        ]
        nearest = await leo1.find_nearest_ground_station(ground_stations)
        console.print(f"[bold blue]Nearest Station:[/bold blue] {nearest}")
        
        # 測試切換
        handover_result = await leo1.handover_to_next_satellite("leo-002")
        console.print("[bold blue]Handover Result:[/bold blue]", handover_result)
        
        # 獲取狀態
        status = leo1.get_status()
        console.print("[bold blue]LEO Status:[/bold blue]", status)
        
        await leo1.stop()
    
    asyncio.run(demo())
