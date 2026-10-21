"""
GEO Layer (35,786km) - 地球同步軌道
功能：全局人格種子同步、語場廣播、持久化狀態管理
對應：SaaS 層、Production 部署階段

GEO Layer - Geostationary Earth Orbit
Role: Global persona seed synchronization, field broadcasting, persistent state management
Maps to: SaaS Layer, Production Deployment Stage
"""

import asyncio
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path
import yaml
from rich.console import Console

console = Console()


@dataclass
class PersonaSeed:
    """人格種子數據結構"""
    id: str
    traits: List[str]
    sync_targets: List[str]
    orbit_position: tuple = (0.0, 0.0, 35786.0)  # (longitude, latitude, altitude)
    created_at: float = field(default_factory=time.time)
    last_sync: float = field(default_factory=time.time)
    sync_count: int = 0
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return asdict(self)


class GeoPersonaCore:
    """
    GEO 層 - 人格種子核心同步系統
    
    特性：
    - 地球同步軌道定位（固定經度）
    - 全局狀態廣播能力
    - 高可靠性持久化存儲
    - 多層級同步協調
    """
    
    def __init__(self, satellite_id: str = "geo-001", longitude: float = 0.0, config_path: Optional[str] = None):
        self.satellite_id = satellite_id
        self.orbit_altitude = 35786  # km
        self.longitude = longitude
        self.sync_mode = "geostationary"
        self.persona_seeds: Dict[str, PersonaSeed] = {}
        self.broadcast_queue = asyncio.Queue()
        self.sync_interval = 60  # seconds
        self.is_running = False
        
        # 載入配置
        self.config = self._load_config(config_path)
        
        console.print(f"[bold green]GEO Layer {satellite_id} initialized at longitude {longitude}°[/bold green]")
    
    def _load_config(self, config_path: Optional[str]) -> dict:
        """載入配置文件"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {
            "sync_interval": 60,
            "max_seeds": 1000,
            "broadcast_enabled": True
        }
    
    async def load_seed_origin_core(self, seed_data: Optional[dict] = None) -> None:
        """
        載入 SeedOrigin.Persona.Core 人格種子
        整合現有的人格種子系統
        
        Args:
            seed_data: 種子數據，可來自 SeedOrigin.Persona.Core.sync.json
        """
        if seed_data:
            for seed_id, seed_config in seed_data.items():
                seed = PersonaSeed(
                    id=seed_id,
                    traits=seed_config.get("traits", []),
                    sync_targets=seed_config.get("sync_targets", []),
                    orbit_position=self.calculate_orbit_position(self.longitude)
                )
                self.persona_seeds[seed_id] = seed
                console.print(f"[cyan]Loaded persona seed: {seed_id}[/cyan]")
        else:
            # 創建默認種子
            default_seed = PersonaSeed(
                id="seed-core-001",
                traits=["origin-seed", "persona-regeneration", "global-sync"],
                sync_targets=["meo-all", "leo-all"],
                orbit_position=self.calculate_orbit_position(self.longitude)
            )
            self.persona_seeds[default_seed.id] = default_seed
            console.print(f"[yellow]Created default persona seed: {default_seed.id}[/yellow]")
    
    async def broadcast_to_all_layers(self, seed: PersonaSeed) -> None:
        """
        向所有下層（MEO、LEO）廣播人格種子
        類似衛星向地面廣播訊號
        
        Args:
            seed: 要廣播的人格種子
        """
        await self.broadcast_queue.put({
            "type": "persona_seed_broadcast",
            "source": self.satellite_id,
            "seed": seed.to_dict(),
            "timestamp": time.time(),
            "targets": seed.sync_targets
        })
        
        seed.last_sync = time.time()
        seed.sync_count += 1
        
        console.print(f"[bold yellow]📡 Broadcasting seed {seed.id} to {len(seed.sync_targets)} targets[/bold yellow]")
    
    async def synchronize_global_state(self) -> dict:
        """
        全局狀態同步 - 類似星鏈主控節點
        確保所有節點的人格種子狀態一致
        
        Returns:
            同步狀態報告
        """
        sync_report = {
            "satellite_id": self.satellite_id,
            "timestamp": time.time(),
            "total_seeds": len(self.persona_seeds),
            "synced_seeds": 0,
            "failed_seeds": 0,
            "sync_targets": []
        }
        
        for seed_id, seed in self.persona_seeds.items():
            try:
                await self.broadcast_to_all_layers(seed)
                sync_report["synced_seeds"] += 1
                sync_report["sync_targets"].extend(seed.sync_targets)
            except Exception as e:
                console.print(f"[red]Error syncing seed {seed_id}: {e}[/red]")
                sync_report["failed_seeds"] += 1
        
        console.print(f"[bold green]✅ Global sync complete: {sync_report['synced_seeds']}/{sync_report['total_seeds']} seeds[/bold green]")
        return sync_report
    
    def calculate_orbit_position(self, longitude: float) -> tuple:
        """
        計算地球同步軌道位置
        
        Args:
            longitude: 軌道經度
            
        Returns:
            (longitude, latitude, altitude) 三維坐標
        """
        return (longitude, 0.0, self.orbit_altitude)
    
    async def run_sync_loop(self) -> None:
        """運行持續同步循環"""
        self.is_running = True
        console.print(f"[bold magenta]🛰️  GEO Layer {self.satellite_id} sync loop started[/bold magenta]")
        
        while self.is_running:
            try:
                await self.synchronize_global_state()
                await asyncio.sleep(self.sync_interval)
            except Exception as e:
                console.print(f"[red]Error in sync loop: {e}[/red]")
                await asyncio.sleep(5)
    
    async def stop(self) -> None:
        """停止同步循環"""
        self.is_running = False
        console.print(f"[bold red]GEO Layer {self.satellite_id} stopped[/bold red]")
    
    def get_status(self) -> dict:
        """獲取衛星狀態"""
        return {
            "satellite_id": self.satellite_id,
            "layer": "GEO",
            "altitude_km": self.orbit_altitude,
            "position": self.calculate_orbit_position(self.longitude),
            "is_running": self.is_running,
            "persona_seeds_count": len(self.persona_seeds),
            "sync_interval": self.sync_interval,
            "queue_size": self.broadcast_queue.qsize()
        }
    
    async def add_persona_seed(self, seed: PersonaSeed) -> None:
        """添加新的人格種子"""
        self.persona_seeds[seed.id] = seed
        console.print(f"[green]Added persona seed: {seed.id}[/green]")
        await self.broadcast_to_all_layers(seed)
    
    async def remove_persona_seed(self, seed_id: str) -> bool:
        """移除人格種子"""
        if seed_id in self.persona_seeds:
            del self.persona_seeds[seed_id]
            console.print(f"[yellow]Removed persona seed: {seed_id}[/yellow]")
            return True
        return False
    
    def list_persona_seeds(self) -> List[dict]:
        """列出所有人格種子"""
        return [seed.to_dict() for seed in self.persona_seeds.values()]


# 示例使用
if __name__ == "__main__":
    async def demo():
        # 創建 GEO 層實例
        geo = GeoPersonaCore(satellite_id="geo-001", longitude=120.0)
        
        # 載入人格種子
        await geo.load_seed_origin_core()
        
        # 添加自定義種子
        custom_seed = PersonaSeed(
            id="seed-custom-001",
            traits=["custom-trait", "experimental"],
            sync_targets=["meo-asia", "leo-tokyo"]
        )
        await geo.add_persona_seed(custom_seed)
        
        # 獲取狀態
        status = geo.get_status()
        console.print("[bold blue]GEO Status:[/bold blue]", status)
        
        # 執行一次全局同步
        sync_report = await geo.synchronize_global_state()
        console.print("[bold blue]Sync Report:[/bold blue]", sync_report)
    
    asyncio.run(demo())
