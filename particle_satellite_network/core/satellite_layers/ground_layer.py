"""
Ground Layer - 地面層
功能：用戶接入、API 網關、地面站管理、觸發器
對應：End Users、Git Push Trigger

Ground Layer - Terrestrial Layer
Role: User access, API gateway, ground station management, triggers
Maps to: End Users, Git Push Trigger
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from rich.console import Console

console = Console()


@dataclass
class UserConnection:
    """用戶連接"""
    user_id: str
    connection_type: str  # satellite_link, fiber_backup
    connected_at: float = field(default_factory=time.time)
    data_transferred_mb: float = 0.0
    is_active: bool = True


@dataclass
class CICDEvent:
    """CI/CD 觸發事件"""
    event_id: str
    event_type: str  # git_push, pull_request, manual_deployment
    source: str
    payload: dict
    timestamp: float = field(default_factory=time.time)
    processed: bool = False


class GroundUserInterface:
    """
    地面層 - 用戶介面系統
    
    特性：
    - 用戶接入管理
    - 最近衛星連接
    - CI/CD 事件觸發
    - 部署訊號接收
    - 多種連接類型支持
    """
    
    def __init__(self, station_id: str = "gs-001", location: Tuple[float, float] = (0.0, 0.0)):
        self.station_id = station_id
        self.location = location  # (longitude, latitude)
        self.connection_type = "satellite_link"
        self.backup_connection_type = "fiber_backup"
        
        # Connected satellite
        self.connected_satellite: Optional[str] = None
        self.satellite_distance_km: float = 0.0
        self.connection_quality: float = 1.0  # 0.0 to 1.0
        
        # User management
        self.active_connections: Dict[str, UserConnection] = {}
        
        # CI/CD event queue
        self.cicd_event_queue = asyncio.Queue()
        self.processed_events: List[CICDEvent] = []
        
        # State
        self.is_running = False
        self.total_users_served = 0
        self.total_data_transferred_mb = 0.0
        
        # Performance metrics
        self.uplink_latency_ms = 0.0
        self.downlink_latency_ms = 0.0
        
        console.print(f"[bold white]Ground Station {station_id} initialized at {location}[/bold white]")
    
    async def connect_to_nearest_leo(self, available_satellites: List[Dict]) -> Optional[str]:
        """
        連接到最近的 LEO 衛星
        
        Args:
            available_satellites: 可用衛星列表，包含ID和位置
            
        Returns:
            連接的衛星ID，如果失敗返回None
        """
        if not available_satellites:
            console.print("[yellow]No available satellites[/yellow]")
            return None
        
        # 簡化的距離計算 - 實際應該使用更複雜的算法
        nearest_satellite = None
        min_distance = float('inf')
        
        for satellite in available_satellites:
            # 計算到衛星的距離（簡化版）
            sat_lon, sat_lat = satellite['position'][:2]
            distance = ((sat_lon - self.location[0])**2 + (sat_lat - self.location[1])**2)**0.5
            
            if distance < min_distance:
                min_distance = distance
                nearest_satellite = satellite['id']
        
        if nearest_satellite:
            self.connected_satellite = nearest_satellite
            self.satellite_distance_km = min_distance * 111  # Rough km conversion
            self.connection_quality = max(0.0, 1.0 - (min_distance / 10.0))
            
            console.print(f"[bold green]📡 Connected to {nearest_satellite} (distance: {self.satellite_distance_km:.2f} km)[/bold green]")
            console.print(f"   Connection quality: {self.connection_quality:.2%}")
            
            return nearest_satellite
        
        return None
    
    async def send_cicd_trigger(self, event: dict) -> dict:
        """
        發送 CI/CD 觸發事件
        類比訊號：Git Push → Ground Station → LEO → MEO → GEO
        
        Args:
            event: CI/CD 事件數據
            
        Returns:
            傳輸結果
        """
        if not self.connected_satellite:
            console.print("[red]No satellite connection available[/red]")
            return {
                "status": "error",
                "reason": "no_satellite_connection"
            }
        
        cicd_event = CICDEvent(
            event_id=f"cicd-{len(self.processed_events) + 1}",
            event_type=event.get("type", "git_push"),
            source=self.station_id,
            payload=event
        )
        
        await self.cicd_event_queue.put(cicd_event)
        
        console.print(f"[bold cyan]🚀 CI/CD Event Triggered: {cicd_event.event_type}[/bold cyan]")
        console.print(f"   Event ID: {cicd_event.event_id}")
        console.print(f"   Transmitting to: {self.connected_satellite}")
        
        # 模擬傳輸延遲
        await asyncio.sleep(0.003)  # 3ms uplink latency
        self.uplink_latency_ms = 3.0
        
        return {
            "status": "transmitted",
            "event_id": cicd_event.event_id,
            "target_satellite": self.connected_satellite,
            "uplink_latency_ms": self.uplink_latency_ms,
            "timestamp": time.time()
        }
    
    async def receive_deployment_signal(self, signal_data: dict) -> dict:
        """
        接收部署訊號
        類比訊號：GEO → MEO → LEO → Ground Station → Deploy
        
        Args:
            signal_data: 部署訊號數據
            
        Returns:
            接收結果
        """
        console.print(f"[bold magenta]📥 Deployment Signal Received[/bold magenta]")
        console.print(f"   From: {signal_data.get('source', 'unknown')}")
        console.print(f"   Type: {signal_data.get('deployment_type', 'unknown')}")
        
        # 模擬接收延遲
        await asyncio.sleep(0.003)  # 3ms downlink latency
        self.downlink_latency_ms = 3.0
        
        # 處理部署訊號
        deployment_result = await self._execute_deployment(signal_data)
        
        return {
            "status": "received_and_executed",
            "downlink_latency_ms": self.downlink_latency_ms,
            "deployment_result": deployment_result,
            "timestamp": time.time()
        }
    
    async def _execute_deployment(self, signal_data: dict) -> dict:
        """
        執行部署
        
        Args:
            signal_data: 部署訊號
            
        Returns:
            部署結果
        """
        deployment_type = signal_data.get('deployment_type', 'unknown')
        target_env = signal_data.get('target_environment', 'production')
        
        console.print(f"[green]Executing deployment: {deployment_type} to {target_env}[/green]")
        
        # 模擬部署過程
        await asyncio.sleep(0.1)
        
        return {
            "deployed": True,
            "deployment_type": deployment_type,
            "target_environment": target_env,
            "timestamp": time.time()
        }
    
    async def add_user_connection(self, user_id: str, connection_type: str = "satellite_link") -> bool:
        """
        添加用戶連接
        
        Args:
            user_id: 用戶ID
            connection_type: 連接類型
            
        Returns:
            是否成功
        """
        if user_id in self.active_connections:
            console.print(f"[yellow]User {user_id} already connected[/yellow]")
            return False
        
        connection = UserConnection(
            user_id=user_id,
            connection_type=connection_type
        )
        
        self.active_connections[user_id] = connection
        self.total_users_served += 1
        
        console.print(f"[green]User connected: {user_id} via {connection_type}[/green]")
        
        return True
    
    async def remove_user_connection(self, user_id: str) -> bool:
        """
        移除用戶連接
        
        Args:
            user_id: 用戶ID
            
        Returns:
            是否成功
        """
        if user_id not in self.active_connections:
            return False
        
        connection = self.active_connections[user_id]
        self.total_data_transferred_mb += connection.data_transferred_mb
        
        del self.active_connections[user_id]
        
        console.print(f"[yellow]User disconnected: {user_id}[/yellow]")
        
        return True
    
    async def switch_to_backup_connection(self) -> bool:
        """
        切換到備用連接（光纖）
        
        Returns:
            是否成功切換
        """
        if self.connection_type == "satellite_link":
            self.connection_type = self.backup_connection_type
            console.print(f"[bold yellow]⚠️  Switched to backup connection: {self.backup_connection_type}[/bold yellow]")
            return True
        
        return False
    
    async def process_cicd_events(self) -> None:
        """處理 CI/CD 事件隊列"""
        while self.is_running:
            try:
                if not self.cicd_event_queue.empty():
                    event = await self.cicd_event_queue.get()
                    # 這裡可以進一步處理事件
                    event.processed = True
                    self.processed_events.append(event)
                else:
                    await asyncio.sleep(0.1)
            except Exception as e:
                console.print(f"[red]Error processing CI/CD events: {e}[/red]")
                await asyncio.sleep(1)
    
    async def start(self) -> None:
        """啟動地面站"""
        self.is_running = True
        console.print(f"[bold green]🚀 Ground Station {self.station_id} started[/bold green]")
        
        # Start processing task
        asyncio.create_task(self.process_cicd_events())
    
    async def stop(self) -> None:
        """停止地面站"""
        self.is_running = False
        console.print(f"[bold red]Ground Station {self.station_id} stopped[/bold red]")
    
    def get_status(self) -> dict:
        """獲取狀態"""
        return {
            "station_id": self.station_id,
            "layer": "GROUND",
            "location": self.location,
            "is_running": self.is_running,
            "connected_satellite": self.connected_satellite,
            "satellite_distance_km": self.satellite_distance_km,
            "connection_type": self.connection_type,
            "connection_quality": self.connection_quality,
            "active_users": len(self.active_connections),
            "total_users_served": self.total_users_served,
            "total_data_transferred_mb": self.total_data_transferred_mb,
            "uplink_latency_ms": self.uplink_latency_ms,
            "downlink_latency_ms": self.downlink_latency_ms,
            "processed_events": len(self.processed_events),
            "pending_events": self.cicd_event_queue.qsize()
        }


# 示例使用
if __name__ == "__main__":
    async def demo():
        # 創建地面站
        ground_station = GroundUserInterface(
            station_id="gs-tokyo",
            location=(139.6917, 35.6895)
        )
        
        # 啟動
        await ground_station.start()
        
        # 連接到最近的 LEO 衛星
        available_satellites = [
            {"id": "leo-001", "position": (140.0, 36.0, 1000.0)},
            {"id": "leo-002", "position": (139.0, 35.0, 1000.0)}
        ]
        connected_sat = await ground_station.connect_to_nearest_leo(available_satellites)
        
        # 添加用戶連接
        await ground_station.add_user_connection("user-001", "satellite_link")
        await ground_station.add_user_connection("user-002", "satellite_link")
        
        # 發送 CI/CD 觸發事件
        cicd_event = {
            "type": "git_push",
            "repo": "dofaromg/flow-tasks",
            "branch": "main",
            "commit": "abc123"
        }
        trigger_result = await ground_station.send_cicd_trigger(cicd_event)
        console.print("[bold blue]Trigger Result:[/bold blue]", trigger_result)
        
        # 接收部署訊號
        deployment_signal = {
            "source": "geo-001",
            "deployment_type": "production",
            "target_environment": "production"
        }
        deployment_result = await ground_station.receive_deployment_signal(deployment_signal)
        console.print("[bold blue]Deployment Result:[/bold blue]", deployment_result)
        
        # 獲取狀態
        status = ground_station.get_status()
        console.print("[bold blue]Ground Station Status:[/bold blue]", status)
        
        await ground_station.stop()
    
    asyncio.run(demo())
