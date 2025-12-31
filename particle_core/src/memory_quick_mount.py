#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRLiou Memory Quick Mount (MQM) 模組
Memory Quick Mount Module - 記憶體快速掛載和狀態快照功能

提供記憶種子的快速掛載、狀態快照記錄和重新載入功能。
Provides quick mount for memory seeds, state snapshot recording, and rehydration.
"""

import json
import yaml
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint


class ParticleCompressor:
    """
    基礎粒子壓縮器 (Basic Particle Compressor)
    
    支援時間、主體、夥伴、行動、項目編碼
    Supports time, subject, partner, action, item encoding
    """
    
    # 粒子編碼映射 (Particle encoding mapping)
    ENCODINGS = {
        'time': '⏰',
        'subject': '👤',
        'partner': '🤝',
        'action': '⚡',
        'item': '📦',
        'location': '📍',
        'state': '🔄',
        'result': '✅'
    }
    
    def __init__(self):
        self.console = Console()
    
    def compress(self, data: Dict[str, Any]) -> str:
        """
        壓縮資料為粒子表示法
        Compress data into particle notation
        
        Args:
            data: 要壓縮的資料 (data to compress)
            
        Returns:
            粒子壓縮字串 (particle compressed string)
        """
        compressed_parts = []
        
        for key, value in data.items():
            if key in self.ENCODINGS:
                symbol = self.ENCODINGS[key]
                compressed_parts.append(f"{symbol}[{value}]")
            else:
                compressed_parts.append(f"⊕{key}:{value}")
        
        return "→".join(compressed_parts)
    
    def decompress(self, compressed: str) -> Dict[str, Any]:
        """
        解壓縮粒子表示法為原始資料
        Decompress particle notation to original data
        
        Args:
            compressed: 粒子壓縮字串 (particle compressed string)
            
        Returns:
            解壓縮後的資料 (decompressed data)
        """
        data = {}
        parts = compressed.split("→")
        
        # 反向映射 (Reverse mapping)
        reverse_encodings = {v: k for k, v in self.ENCODINGS.items()}
        
        for part in parts:
            part = part.strip()
            
            # 處理標準編碼 (Handle standard encodings)
            for symbol, key in reverse_encodings.items():
                if part.startswith(symbol):
                    value = part[len(symbol):].strip('[]')
                    data[key] = value
                    break
            else:
                # 處理自訂編碼 (Handle custom encodings)
                if part.startswith('⊕'):
                    part = part[1:]  # Remove ⊕
                    if ':' in part:
                        key, value = part.split(':', 1)
                        data[key] = value
        
        return data


class AdvancedParticleCompressor(ParticleCompressor):
    """
    進階粒子壓縮器 (Advanced Particle Compressor)
    
    支援巢狀結構壓縮
    Supports nested structure compression
    """
    
    def compress_nested(self, data: Any, level: int = 0) -> str:
        """
        壓縮巢狀結構
        Compress nested structures
        
        Args:
            data: 要壓縮的資料 (data to compress)
            level: 巢狀層級 (nesting level)
            
        Returns:
            巢狀粒子壓縮字串 (nested particle compressed string)
        """
        indent = "  " * level
        
        if isinstance(data, dict):
            parts = []
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    nested = self.compress_nested(value, level + 1)
                    parts.append(f"{indent}⊕{key}⟨\n{nested}\n{indent}⟩")
                else:
                    symbol = self.ENCODINGS.get(key, '⊕')
                    if symbol != '⊕':
                        parts.append(f"{indent}{symbol}[{key}={value}]")
                    else:
                        parts.append(f"{indent}⊕{key}:{value}")
            return "\n".join(parts)
        
        elif isinstance(data, list):
            parts = []
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    nested = self.compress_nested(item, level + 1)
                    parts.append(f"{indent}⊕[{i}]⟨\n{nested}\n{indent}⟩")
                else:
                    parts.append(f"{indent}⊕[{i}]:{item}")
            return "\n".join(parts)
        
        else:
            return f"{indent}{data}"


class MemoryQuickMounter:
    """
    核心記憶掛載類別 (Core Memory Mounting Class)
    
    提供記憶種子載入、掛載、快照和重新載入功能
    Provides memory seed loading, mounting, snapshot, and rehydration features
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化記憶快速掛載器
        Initialize Memory Quick Mounter
        
        Args:
            config_path: 配置檔案路徑 (configuration file path)
        """
        self.console = Console()
        self.compressor = AdvancedParticleCompressor()
        self.config = self._load_config(config_path)
        
        # 創建必要目錄 (Create necessary directories)
        self.context_dir = Path(self.config.get('context_dir', 'context'))
        self.snapshot_dir = Path(self.config.get('snapshot_dir', 'snapshots'))
        self.context_dir.mkdir(exist_ok=True)
        self.snapshot_dir.mkdir(exist_ok=True)
        
        # 記憶種子儲存 (Memory seed storage)
        self.loaded_seeds = []
        self.mounted_context = {}
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        載入配置檔案
        Load configuration file
        
        Args:
            config_path: 配置檔案路徑 (configuration file path)
            
        Returns:
            配置字典 (configuration dictionary)
        """
        if not config_path:
            return {
                'context_dir': 'context',
                'snapshot_dir': 'snapshots',
                'seeds': []
            }
        
        config_file = Path(config_path)
        if not config_file.exists():
            self.console.print(f"[yellow]⚠ 配置檔案不存在: {config_path}[/yellow]")
            self.console.print(f"[yellow]⚠ Config file not found: {config_path}[/yellow]")
            return {
                'context_dir': 'context',
                'snapshot_dir': 'snapshots',
                'seeds': []
            }
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    return yaml.safe_load(f) or {}
                else:
                    return json.load(f)
        except Exception as e:
            self.console.print(f"[red]✗ 載入配置失敗: {e}[/red]")
            self.console.print(f"[red]✗ Failed to load config: {e}[/red]")
            return {
                'context_dir': 'context',
                'snapshot_dir': 'snapshots',
                'seeds': []
            }
    
    def load_seed(self, seed_path: str) -> Optional[Dict[str, Any]]:
        """
        載入記憶種子 (支援 JSON/YAML)
        Load memory seed (supports JSON/YAML)
        
        Args:
            seed_path: 種子檔案路徑 (seed file path)
            
        Returns:
            種子資料或 None (seed data or None)
        """
        seed_file = Path(seed_path)
        
        if not seed_file.exists():
            self.console.print(f"[red]✗ 種子檔案不存在: {seed_path}[/red]")
            self.console.print(f"[red]✗ Seed file not found: {seed_path}[/red]")
            return None
        
        try:
            with open(seed_file, 'r', encoding='utf-8') as f:
                if seed_path.endswith('.yaml') or seed_path.endswith('.yml'):
                    seed_data = yaml.safe_load(f)
                else:
                    seed_data = json.load(f)
            
            self.console.print(f"[green]✓ 成功載入種子: {seed_path}[/green]")
            self.console.print(f"[green]✓ Successfully loaded seed: {seed_path}[/green]")
            
            return seed_data
        
        except json.JSONDecodeError as e:
            self.console.print(f"[red]✗ JSON 解析失敗: {e}[/red]")
            self.console.print(f"[red]✗ JSON parsing failed: {e}[/red]")
            return None
        except yaml.YAMLError as e:
            self.console.print(f"[red]✗ YAML 解析失敗: {e}[/red]")
            self.console.print(f"[red]✗ YAML parsing failed: {e}[/red]")
            return None
        except Exception as e:
            self.console.print(f"[red]✗ 載入種子失敗: {e}[/red]")
            self.console.print(f"[red]✗ Failed to load seed: {e}[/red]")
            return None
    
    def mount(self) -> bool:
        """
        掛載種子到整合上下文
        Mount seeds to integration context
        
        Returns:
            掛載是否成功 (whether mount was successful)
        """
        self.console.print("\n[bold cyan]🔧 開始掛載記憶種子...[/bold cyan]")
        self.console.print("[bold cyan]🔧 Starting memory seed mount...[/bold cyan]\n")
        
        seed_paths = self.config.get('seeds', [])
        
        if not seed_paths:
            self.console.print("[yellow]⚠ 配置中沒有指定種子檔案[/yellow]")
            self.console.print("[yellow]⚠ No seed files specified in config[/yellow]")
            return False
        
        success_count = 0
        for seed_path in seed_paths:
            seed_data = self.load_seed(seed_path)
            if seed_data:
                self.loaded_seeds.append({
                    'path': seed_path,
                    'data': seed_data,
                    'loaded_at': datetime.now().isoformat()
                })
                
                # 整合到上下文 (Integrate into context)
                if 'structure' in seed_data:
                    self.mounted_context.update(seed_data['structure'])
                
                success_count += 1
        
        # 儲存上下文到檔案 (Save context to file)
        if success_count > 0:
            context_file = self.context_dir / 'mounted_context.json'
            with open(context_file, 'w', encoding='utf-8') as f:
                json.dump(self.mounted_context, f, ensure_ascii=False, indent=2)
            
            self.console.print(f"\n[green]✓ 成功掛載 {success_count} 個種子[/green]")
            self.console.print(f"[green]✓ Successfully mounted {success_count} seed(s)[/green]")
            self.console.print(f"[dim]上下文已儲存至: {context_file}[/dim]")
            self.console.print(f"[dim]Context saved to: {context_file}[/dim]\n")
            
            # 顯示掛載摘要 (Display mount summary)
            self._display_mount_summary()
            
            return True
        
        return False
    
    def _display_mount_summary(self):
        """顯示掛載摘要 (Display mount summary)"""
        table = Table(title="掛載摘要 / Mount Summary", show_header=True, header_style="bold magenta")
        table.add_column("項目 / Item", style="cyan", no_wrap=True)
        table.add_column("值 / Value", style="green")
        
        table.add_row("已載入種子數 / Loaded Seeds", str(len(self.loaded_seeds)))
        table.add_row("上下文鍵數 / Context Keys", str(len(self.mounted_context)))
        table.add_row("上下文目錄 / Context Dir", str(self.context_dir))
        table.add_row("快照目錄 / Snapshot Dir", str(self.snapshot_dir))
        
        self.console.print(table)
    
    def snapshot(self, agent_name: str, state: Dict[str, Any]) -> bool:
        """
        記錄代理狀態快照
        Record agent state snapshot
        
        Args:
            agent_name: 代理名稱 (agent name)
            state: 狀態資料 (state data)
            
        Returns:
            快照是否成功 (whether snapshot was successful)
        """
        self.console.print(f"\n[bold cyan]📸 為代理 '{agent_name}' 建立快照...[/bold cyan]")
        self.console.print(f"[bold cyan]📸 Creating snapshot for agent '{agent_name}'...[/bold cyan]\n")
        
        timestamp = datetime.now()
        snapshot_data = {
            'agent': agent_name,
            'state': state,
            'timestamp': timestamp.isoformat(),
            'context': self.mounted_context.copy()
        }
        
        # 壓縮狀態 (Compress state)
        compressed = self.compressor.compress_nested(state)
        snapshot_data['compressed'] = compressed
        
        # 儲存快照 (Save snapshot)
        snapshot_filename = f"snapshot_{agent_name}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        snapshot_file = self.snapshot_dir / snapshot_filename
        
        try:
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot_data, f, ensure_ascii=False, indent=2)
            
            # 更新最新快照指標 (Update latest snapshot pointer)
            latest_file = self.snapshot_dir / f"latest_{agent_name}.json"
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump({'latest_snapshot': str(snapshot_file)}, f, ensure_ascii=False, indent=2)
            
            self.console.print(f"[green]✓ 快照已儲存: {snapshot_file}[/green]")
            self.console.print(f"[green]✓ Snapshot saved: {snapshot_file}[/green]")
            
            # 顯示壓縮結果 (Display compressed result)
            panel = Panel(
                compressed,
                title=f"粒子壓縮表示 / Particle Compressed Representation",
                style="blue"
            )
            self.console.print(panel)
            
            return True
        
        except Exception as e:
            self.console.print(f"[red]✗ 建立快照失敗: {e}[/red]")
            self.console.print(f"[red]✗ Failed to create snapshot: {e}[/red]")
            return False
    
    def rehydrate(self, agent_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        重新載入最後已知狀態
        Rehydrate last known state
        
        Args:
            agent_name: 代理名稱 (可選) (agent name, optional)
            
        Returns:
            重新載入的狀態或 None (rehydrated state or None)
        """
        self.console.print("\n[bold cyan]💧 重新載入狀態...[/bold cyan]")
        self.console.print("[bold cyan]💧 Rehydrating state...[/bold cyan]\n")
        
        if agent_name:
            # 載入特定代理的最新快照 (Load specific agent's latest snapshot)
            latest_file = self.snapshot_dir / f"latest_{agent_name}.json"
            
            if not latest_file.exists():
                self.console.print(f"[yellow]⚠ 找不到代理 '{agent_name}' 的快照[/yellow]")
                self.console.print(f"[yellow]⚠ No snapshot found for agent '{agent_name}'[/yellow]")
                return None
            
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    latest_info = json.load(f)
                
                snapshot_path = Path(latest_info['latest_snapshot'])
                
                with open(snapshot_path, 'r', encoding='utf-8') as f:
                    snapshot_data = json.load(f)
                
                self.console.print(f"[green]✓ 成功重新載入代理 '{agent_name}' 的狀態[/green]")
                self.console.print(f"[green]✓ Successfully rehydrated state for agent '{agent_name}'[/green]")
                self.console.print(f"[dim]時間戳記: {snapshot_data['timestamp']}[/dim]")
                self.console.print(f"[dim]Timestamp: {snapshot_data['timestamp']}[/dim]\n")
                
                # 顯示狀態資訊 (Display state info)
                self._display_state_info(snapshot_data)
                
                return snapshot_data
            
            except Exception as e:
                self.console.print(f"[red]✗ 重新載入失敗: {e}[/red]")
                self.console.print(f"[red]✗ Rehydration failed: {e}[/red]")
                return None
        
        else:
            # 列出所有可用快照 (List all available snapshots)
            snapshots = list(self.snapshot_dir.glob("latest_*.json"))
            
            if not snapshots:
                self.console.print("[yellow]⚠ 找不到任何快照[/yellow]")
                self.console.print("[yellow]⚠ No snapshots found[/yellow]")
                return None
            
            self.console.print(f"[green]找到 {len(snapshots)} 個代理快照:[/green]")
            self.console.print(f"[green]Found {len(snapshots)} agent snapshot(s):[/green]")
            
            for snapshot in snapshots:
                agent = snapshot.stem.replace('latest_', '')
                self.console.print(f"  • {agent}")
            
            return None
    
    def _display_state_info(self, snapshot_data: Dict[str, Any]):
        """顯示狀態資訊 (Display state information)"""
        table = Table(title="狀態資訊 / State Information", show_header=True, header_style="bold magenta")
        table.add_column("項目 / Item", style="cyan", no_wrap=True)
        table.add_column("值 / Value", style="green")
        
        table.add_row("代理 / Agent", snapshot_data.get('agent', 'N/A'))
        table.add_row("時間 / Timestamp", snapshot_data.get('timestamp', 'N/A'))
        
        state = snapshot_data.get('state', {})
        for key, value in state.items():
            table.add_row(f"狀態.{key} / State.{key}", str(value))
        
        self.console.print(table)
        
        # 顯示壓縮表示 (Display compressed representation)
        if 'compressed' in snapshot_data:
            panel = Panel(
                snapshot_data['compressed'],
                title="粒子壓縮表示 / Particle Compressed Representation",
                style="blue"
            )
            self.console.print("\n", panel)


def main():
    """
    CLI 主程式入口
    CLI main entry point
    """
    parser = argparse.ArgumentParser(
        description='MRLiou Memory Quick Mount (MQM) - 記憶體快速掛載工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='配置檔案路徑 (Configuration file path)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令 (Available commands)')
    
    # mount 命令 (mount command)
    subparsers.add_parser(
        'mount',
        help='掛載記憶種子 (Mount memory seeds)'
    )
    
    # snapshot 命令 (snapshot command)
    snapshot_parser = subparsers.add_parser(
        'snapshot',
        help='記錄快照 (Record snapshot)'
    )
    snapshot_parser.add_argument(
        '--agent',
        type=str,
        required=True,
        help='代理名稱 (Agent name)'
    )
    snapshot_parser.add_argument(
        '--state',
        type=str,
        required=True,
        help='狀態資料 (JSON 格式) (State data in JSON format)'
    )
    
    # rehydrate 命令 (rehydrate command)
    rehydrate_parser = subparsers.add_parser(
        'rehydrate',
        help='重新載入狀態 (Rehydrate state)'
    )
    rehydrate_parser.add_argument(
        '--agent',
        type=str,
        help='代理名稱 (可選) (Agent name, optional)'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 初始化掛載器 (Initialize mounter)
    mounter = MemoryQuickMounter(config_path=args.config)
    
    # 執行命令 (Execute command)
    if args.command == 'mount':
        success = mounter.mount()
        sys.exit(0 if success else 1)
    
    elif args.command == 'snapshot':
        try:
            state_data = json.loads(args.state)
            success = mounter.snapshot(args.agent, state_data)
            sys.exit(0 if success else 1)
        except json.JSONDecodeError as e:
            console = Console()
            console.print(f"[red]✗ 狀態資料 JSON 格式錯誤: {e}[/red]")
            console.print(f"[red]✗ Invalid JSON format for state data: {e}[/red]")
            sys.exit(1)
    
    elif args.command == 'rehydrate':
        result = mounter.rehydrate(agent_name=args.agent)
        sys.exit(0 if result or not args.agent else 1)


if __name__ == '__main__':
    main()
