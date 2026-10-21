"""
CI/CD Signal Processor
CI/CD 訊號處理器

將 CI/CD 流程映射為衛星通訊訊號傳輸
Maps CI/CD workflows to satellite communication signal transmission
"""

import asyncio
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from rich.console import Console

console = Console()


class SignalType(Enum):
    """訊號類型"""
    GIT_PUSH = "git_push"
    PULL_REQUEST = "pull_request"
    MANUAL_DEPLOYMENT = "manual_deployment"
    BUILD_COMPLETE = "build_complete"
    TEST_COMPLETE = "test_complete"
    DEPLOYMENT_COMPLETE = "deployment_complete"


class ProcessingLayer(Enum):
    """處理層級"""
    GROUND = "ground"
    LEO = "leo"
    MEO = "meo"
    GEO = "geo"


@dataclass
class CICDSignal:
    """CI/CD 訊號"""
    signal_id: str
    signal_type: SignalType
    layer: ProcessingLayer
    data: dict
    timestamp: float = field(default_factory=time.time)
    hops: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0
    
    def add_hop(self, layer: ProcessingLayer) -> None:
        """添加跳轉記錄"""
        self.hops.append(f"{layer.value}@{time.time()}")


class CICDSignalProcessor:
    """
    CI/CD 訊號處理器
    
    訊號流向：
    1. Git Push (Ground) → 2. Source Processing (LEO) → 
    3. Build/Test (MEO) → 4. Deploy (GEO) → 5. Production (Ground)
    """
    
    def __init__(self):
        self.signal_chain: List[CICDSignal] = []
        self.processing_stats: Dict[SignalType, int] = {}
        
        # Queues for each layer
        self.ground_queue = asyncio.Queue()
        self.leo_queue = asyncio.Queue()
        self.meo_queue = asyncio.Queue()
        self.geo_queue = asyncio.Queue()
        
        console.print("[bold blue]CI/CD Signal Processor initialized[/bold blue]")
    
    async def process_git_push_signal(self, commit_data: dict) -> dict:
        """
        處理 Git Push 訊號
        階段1: 地面站接收源碼變更
        
        Args:
            commit_data: 提交數據
            
        Returns:
            處理結果
        """
        signal = CICDSignal(
            signal_id=f"signal-{len(self.signal_chain) + 1}",
            signal_type=SignalType.GIT_PUSH,
            layer=ProcessingLayer.GROUND,
            data=commit_data
        )
        
        console.print(f"[bold cyan]🚀 Git Push Signal Received[/bold cyan]")
        console.print(f"   Repo: {commit_data.get('repo', 'unknown')}")
        console.print(f"   Branch: {commit_data.get('branch', 'unknown')}")
        console.print(f"   Commit: {commit_data.get('commit', 'unknown')}")
        
        # Transmit to LEO layer
        await self._transmit_to_leo(signal)
        
        self.signal_chain.append(signal)
        self._update_stats(SignalType.GIT_PUSH)
        
        return {
            "status": "transmitted",
            "signal_id": signal.signal_id,
            "next_layer": "LEO",
            "timestamp": time.time()
        }
    
    async def _transmit_to_leo(self, signal: CICDSignal) -> None:
        """
        傳輸訊號到 LEO 層
        
        Args:
            signal: CI/CD 訊號
        """
        signal.add_hop(ProcessingLayer.LEO)
        await self.leo_queue.put(signal)
        
        console.print(f"[yellow]📡 Signal {signal.signal_id} transmitted: GROUND → LEO[/yellow]")
        
        # Simulate transmission delay
        await asyncio.sleep(0.003)  # 3ms
    
    async def process_build_signal(self, build_config: dict) -> dict:
        """
        處理構建訊號
        階段2-3: LEO 處理源碼 → MEO 執行構建
        
        Args:
            build_config: 構建配置
            
        Returns:
            處理結果
        """
        signal = CICDSignal(
            signal_id=f"signal-{len(self.signal_chain) + 1}",
            signal_type=SignalType.BUILD_COMPLETE,
            layer=ProcessingLayer.MEO,
            data=build_config
        )
        
        console.print(f"[bold cyan]🔨 Build Signal Processing[/bold cyan]")
        console.print(f"   Environment: {build_config.get('environment', 'unknown')}")
        
        # Simulate build process
        await asyncio.sleep(0.1)  # 100ms build time
        
        signal.add_hop(ProcessingLayer.MEO)
        await self.meo_queue.put(signal)
        
        self.signal_chain.append(signal)
        self._update_stats(SignalType.BUILD_COMPLETE)
        
        return {
            "status": "build_complete",
            "signal_id": signal.signal_id,
            "next_layer": "GEO",
            "timestamp": time.time()
        }
    
    async def process_deployment_signal(self, deployment_config: dict) -> dict:
        """
        處理部署訊號
        階段4: MEO 完成測試 → GEO 協調部署
        
        Args:
            deployment_config: 部署配置
            
        Returns:
            處理結果
        """
        signal = CICDSignal(
            signal_id=f"signal-{len(self.signal_chain) + 1}",
            signal_type=SignalType.DEPLOYMENT_COMPLETE,
            layer=ProcessingLayer.GEO,
            data=deployment_config
        )
        
        console.print(f"[bold magenta]🚀 Deployment Signal Processing[/bold magenta]")
        console.print(f"   Target: {deployment_config.get('target', 'unknown')}")
        
        signal.add_hop(ProcessingLayer.GEO)
        await self.geo_queue.put(signal)
        
        self.signal_chain.append(signal)
        self._update_stats(SignalType.DEPLOYMENT_COMPLETE)
        
        return {
            "status": "deployment_initiated",
            "signal_id": signal.signal_id,
            "timestamp": time.time()
        }
    
    def _update_stats(self, signal_type: SignalType) -> None:
        """更新統計"""
        if signal_type not in self.processing_stats:
            self.processing_stats[signal_type] = 0
        self.processing_stats[signal_type] += 1
    
    def get_signal_trace(self, signal_id: str) -> Optional[CICDSignal]:
        """
        獲取訊號追踪
        
        Args:
            signal_id: 訊號ID
            
        Returns:
            訊號對象
        """
        for signal in self.signal_chain:
            if signal.signal_id == signal_id:
                return signal
        return None
    
    def get_statistics(self) -> dict:
        """獲取統計信息"""
        return {
            "total_signals": len(self.signal_chain),
            "processing_stats": {k.value: v for k, v in self.processing_stats.items()},
            "queue_sizes": {
                "ground": self.ground_queue.qsize(),
                "leo": self.leo_queue.qsize(),
                "meo": self.meo_queue.qsize(),
                "geo": self.geo_queue.qsize()
            }
        }


# 示例使用
if __name__ == "__main__":
    async def demo():
        # 創建訊號處理器
        processor = CICDSignalProcessor()
        
        # 模擬 Git Push
        commit_data = {
            "repo": "dofaromg/flow-tasks",
            "branch": "main",
            "commit": "abc123def456",
            "author": "dofaromg"
        }
        result1 = await processor.process_git_push_signal(commit_data)
        console.print("[bold blue]Git Push Result:[/bold blue]", result1)
        
        # 模擬構建
        build_config = {
            "environment": "production",
            "build_type": "release"
        }
        result2 = await processor.process_build_signal(build_config)
        console.print("[bold blue]Build Result:[/bold blue]", result2)
        
        # 模擬部署
        deployment_config = {
            "target": "production",
            "region": "asia-east1"
        }
        result3 = await processor.process_deployment_signal(deployment_config)
        console.print("[bold blue]Deployment Result:[/bold blue]", result3)
        
        # 獲取統計
        stats = processor.get_statistics()
        console.print("[bold blue]Processor Statistics:[/bold blue]", stats)
    
    asyncio.run(demo())
