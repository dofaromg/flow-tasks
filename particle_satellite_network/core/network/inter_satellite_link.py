"""
Inter-Satellite Link Manager
衛星間鏈路管理器

管理衛星間的激光/無線鏈路
Manages laser/radio links between satellites
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from rich.console import Console

console = Console()


class LinkType(Enum):
    """鏈路類型"""
    LASER = "laser"  # 激光鏈路 - 高帶寬、低延遲
    RADIO = "radio"  # 無線鏈路 - 中帶寬、中延遲
    HYBRID = "hybrid"  # 混合鏈路


class LinkStatus(Enum):
    """鏈路狀態"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ESTABLISHING = "establishing"
    FAILED = "failed"
    MAINTENANCE = "maintenance"


@dataclass
class InterSatelliteLink:
    """衛星間鏈路"""
    link_id: str
    source_satellite: str
    target_satellite: str
    link_type: LinkType
    bandwidth_gbps: float
    latency_ms: float
    status: LinkStatus = LinkStatus.INACTIVE
    established_at: Optional[float] = None
    last_activity: float = field(default_factory=time.time)
    data_transferred_gb: float = 0.0
    error_count: int = 0
    
    def is_healthy(self) -> bool:
        """檢查鏈路是否健康"""
        return self.status == LinkStatus.ACTIVE and self.error_count < 10


@dataclass
class LinkMetrics:
    """鏈路指標"""
    throughput_gbps: float
    packet_loss_rate: float
    jitter_ms: float
    utilization: float  # 0.0 to 1.0


class InterSatelliteLinkManager:
    """
    衛星間鏈路管理器
    
    特性：
    - 激光鏈路建立與維護
    - 鏈路健康監控
    - 自動故障轉移
    - 帶寬管理
    - 鏈路預測與優化
    """
    
    def __init__(self):
        self.links: Dict[str, InterSatelliteLink] = {}
        self.link_metrics: Dict[str, LinkMetrics] = {}
        
        # Configuration
        self.max_links_per_satellite = 4
        self.link_timeout_seconds = 300  # 5 minutes
        self.health_check_interval = 10  # seconds
        
        # State
        self.is_running = False
        
        # Statistics
        self.total_links_established = 0
        self.total_links_failed = 0
        self.total_data_transferred_gb = 0.0
        
        console.print("[bold blue]Inter-Satellite Link Manager initialized[/bold blue]")
    
    async def establish_link(
        self,
        source: str,
        target: str,
        link_type: LinkType = LinkType.LASER,
        bandwidth_gbps: float = 100.0
    ) -> Optional[InterSatelliteLink]:
        """
        建立衛星間鏈路
        
        Args:
            source: 源衛星ID
            target: 目標衛星ID
            link_type: 鏈路類型
            bandwidth_gbps: 帶寬 (Gbps)
            
        Returns:
            建立的鏈路，如果失敗返回None
        """
        link_id = f"{source}->{target}"
        
        # Check if link already exists
        if link_id in self.links:
            console.print(f"[yellow]Link {link_id} already exists[/yellow]")
            return self.links[link_id]
        
        # Calculate latency based on link type
        latency_ms = 10.0 if link_type == LinkType.LASER else 50.0
        
        link = InterSatelliteLink(
            link_id=link_id,
            source_satellite=source,
            target_satellite=target,
            link_type=link_type,
            bandwidth_gbps=bandwidth_gbps,
            latency_ms=latency_ms,
            status=LinkStatus.ESTABLISHING
        )
        
        self.links[link_id] = link
        
        console.print(f"[cyan]🔗 Establishing {link_type.value} link: {source} → {target}...[/cyan]")
        
        # Simulate link establishment
        await asyncio.sleep(0.1)
        
        link.status = LinkStatus.ACTIVE
        link.established_at = time.time()
        self.total_links_established += 1
        
        console.print(f"[bold green]✅ Link established: {link_id} ({bandwidth_gbps} Gbps, {latency_ms}ms)[/bold green]")
        
        return link
    
    async def terminate_link(self, link_id: str) -> bool:
        """
        終止鏈路
        
        Args:
            link_id: 鏈路ID
            
        Returns:
            是否成功終止
        """
        if link_id not in self.links:
            return False
        
        link = self.links[link_id]
        link.status = LinkStatus.INACTIVE
        
        self.total_data_transferred_gb += link.data_transferred_gb
        
        console.print(f"[yellow]Terminated link: {link_id} (transferred {link.data_transferred_gb:.2f} GB)[/yellow]")
        
        del self.links[link_id]
        
        return True
    
    async def check_link_health(self, link_id: str) -> bool:
        """
        檢查鏈路健康狀態
        
        Args:
            link_id: 鏈路ID
            
        Returns:
            鏈路是否健康
        """
        if link_id not in self.links:
            return False
        
        link = self.links[link_id]
        
        # Check timeout
        time_since_activity = time.time() - link.last_activity
        if time_since_activity > self.link_timeout_seconds:
            link.status = LinkStatus.FAILED
            console.print(f"[red]Link {link_id} timed out[/red]")
            return False
        
        # Check error count
        if link.error_count >= 10:
            link.status = LinkStatus.FAILED
            console.print(f"[red]Link {link_id} failed due to errors[/red]")
            return False
        
        return link.is_healthy()
    
    async def monitor_links(self) -> None:
        """持續監控所有鏈路"""
        while self.is_running:
            for link_id in list(self.links.keys()):
                await self.check_link_health(link_id)
            
            await asyncio.sleep(self.health_check_interval)
    
    async def optimize_link_allocation(self, satellite_id: str) -> List[str]:
        """
        優化衛星的鏈路分配
        
        Args:
            satellite_id: 衛星ID
            
        Returns:
            推薦的目標衛星列表
        """
        # Find all links for this satellite
        satellite_links = [
            link for link in self.links.values()
            if link.source_satellite == satellite_id or link.target_satellite == satellite_id
        ]
        
        current_count = len(satellite_links)
        console.print(f"[cyan]Satellite {satellite_id} has {current_count}/{self.max_links_per_satellite} links[/cyan]")
        
        # Simple optimization: maintain max_links_per_satellite
        recommendations = []
        if current_count < self.max_links_per_satellite:
            needed = self.max_links_per_satellite - current_count
            console.print(f"[yellow]Recommend establishing {needed} more links[/yellow]")
        
        return recommendations
    
    def get_link_metrics(self, link_id: str) -> Optional[LinkMetrics]:
        """
        獲取鏈路指標
        
        Args:
            link_id: 鏈路ID
            
        Returns:
            鏈路指標
        """
        if link_id not in self.links:
            return None
        
        # Simulate metrics (in real implementation, these would be measured)
        if link_id not in self.link_metrics:
            link = self.links[link_id]
            self.link_metrics[link_id] = LinkMetrics(
                throughput_gbps=link.bandwidth_gbps * 0.8,  # 80% utilization
                packet_loss_rate=0.001,  # 0.1%
                jitter_ms=1.0,
                utilization=0.8
            )
        
        return self.link_metrics[link_id]
    
    def get_statistics(self) -> dict:
        """獲取統計信息"""
        active_links = [link for link in self.links.values() if link.status == LinkStatus.ACTIVE]
        
        return {
            "total_links": len(self.links),
            "active_links": len(active_links),
            "total_links_established": self.total_links_established,
            "total_links_failed": self.total_links_failed,
            "total_data_transferred_gb": self.total_data_transferred_gb,
            "avg_bandwidth_gbps": sum(link.bandwidth_gbps for link in active_links) / len(active_links) if active_links else 0,
            "laser_links": sum(1 for link in active_links if link.link_type == LinkType.LASER),
            "radio_links": sum(1 for link in active_links if link.link_type == LinkType.RADIO)
        }
    
    async def start(self) -> None:
        """啟動鏈路管理器"""
        self.is_running = True
        console.print("[bold green]🚀 Inter-Satellite Link Manager started[/bold green]")
        asyncio.create_task(self.monitor_links())
    
    async def stop(self) -> None:
        """停止鏈路管理器"""
        self.is_running = False
        console.print("[bold red]Inter-Satellite Link Manager stopped[/bold red]")


# 示例使用
if __name__ == "__main__":
    async def demo():
        # 創建鏈路管理器
        manager = InterSatelliteLinkManager()
        
        # 啟動
        await manager.start()
        
        # 建立鏈路
        link1 = await manager.establish_link("meo-001", "meo-002", LinkType.LASER, 100.0)
        link2 = await manager.establish_link("leo-001", "leo-002", LinkType.LASER, 25.0)
        link3 = await manager.establish_link("meo-001", "leo-001", LinkType.RADIO, 10.0)
        
        # 檢查鏈路健康
        await asyncio.sleep(1)
        health = await manager.check_link_health(link1.link_id)
        console.print(f"[bold blue]Link {link1.link_id} health:[/bold blue] {health}")
        
        # 獲取鏈路指標
        metrics = manager.get_link_metrics(link1.link_id)
        console.print(f"[bold blue]Link {link1.link_id} metrics:[/bold blue]", metrics)
        
        # 優化鏈路分配
        recommendations = await manager.optimize_link_allocation("meo-001")
        
        # 獲取統計
        stats = manager.get_statistics()
        console.print("[bold blue]Link Manager Statistics:[/bold blue]", stats)
        
        # 終止鏈路
        await manager.terminate_link(link1.link_id)
        
        await manager.stop()
    
    asyncio.run(demo())
