#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mr.liou.Particle.EnvParameters.v1 - 粒子環境參數與創世公式模組
Particle Environment Parameter Module applying mrliou's genesis logical thinking formulas.

創世公式:
  P_{k+1} = N_k · P_k · η_k  (成長)
  P_k = P_{k+1} / (N_k · η_k)  (反推)

環境變化公式:
  η_k = (context * context_weight + runtime * runtime_weight + dependency * dependency_weight) * (1 - external_noise) * trust_score
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

class ParticleEnvParameters:
    """
    MrLioū 粒子環境參數管理器 (Particle Environment Parameters Manager)
    
    用於管理和載入 MRL 系統中的六大公式參數，特別是創世公式與環境變化公式。
    支援自 MRL_Mother 參數註冊表動態載入最新參數值。
    """
    
    def __init__(self, registry_path: Optional[str] = None):
        """
        初始化環境參數與預設值
        
        Args:
            registry_path: 選擇性指定 MRL_formula_parameter_registry.json 的路徑
        """
        self.version = "v1.0.0"
        self.particle_id = f"MrLioū.Particle.EnvParameters.{self.version}"
        self.console = Console()
        
        # 1. 預設創世公式參數 (MRL_創世公式)
        self.p_k = 1.0
        self.n_k = 1.0
        self.eta_k = 0.618
        
        # 2. 預設環境變化觀測權重 (MRL_環境變化公式)
        self.context_weight = 0.4
        self.runtime_weight = 0.3
        self.dependency_weight = 0.2
        self.external_noise = 0.1
        self.trust_score = 0.9
        
        # 3. 其他核心公式參數預設值
        self.alpha = 1.0
        self.beta = 1.0
        self.scale_mode = "linear"
        self.inverse_epsilon = 1e-9
        self.stability_clip = 1000000.0
        self.loss_bound = 0.001
        
        # 嘗試載入母體註冊表參數
        self._load_from_registry(registry_path)

    def _load_from_registry(self, registry_path: Optional[str] = None) -> bool:
        """
        嘗試從母體參數註冊表載入真實的環境與創世參數
        """
        possible_paths = []
        if registry_path:
            possible_paths.append(Path(registry_path))
        else:
            # 尋找 MRL_Mother/data/MRL_formula_parameter_registry.json
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # 尋找 repo 根目錄下的路徑
            repo_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
            possible_paths.append(Path(repo_root) / "MRL_Mother" / "data" / "MRL_formula_parameter_registry.json")
            possible_paths.append(Path(repo_root) / "data" / "MRL_formula_parameter_registry.json")
            
        for path in possible_paths:
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    records = data.get("records", [])
                    for record in records:
                        f_name = record.get("formula_name")
                        p_name = record.get("parameter_name")
                        p_val = record.get("parameter_value")
                        
                        if f_name == "MRL_創世公式":
                            if p_name == "P_k": self.p_k = float(p_val)
                            elif p_name == "N_k": self.n_k = float(p_val)
                            elif p_name == "eta_k": self.eta_k = float(p_val)
                        elif f_name == "MRL_環境變化公式":
                            if p_name == "context_weight": self.context_weight = float(p_val)
                            elif p_name == "runtime_weight": self.runtime_weight = float(p_val)
                            elif p_name == "dependency_weight": self.dependency_weight = float(p_val)
                            elif p_name == "external_noise": self.external_noise = float(p_val)
                            elif p_name == "trust_score": self.trust_score = float(p_val)
                        elif f_name == "MRL_放大縮小公式":
                            if p_name == "alpha": self.alpha = float(p_val)
                            elif p_name == "beta": self.beta = float(p_val)
                            elif p_name == "scale_mode": self.scale_mode = str(p_val)
                        elif f_name == "MRL_反推公式":
                            if p_name == "inverse_epsilon": self.inverse_epsilon = float(p_val)
                            elif p_name == "stability_clip": self.stability_clip = float(p_val)
                            elif p_name == "loss_bound": self.loss_bound = float(p_val)
                    return True
                except Exception as e:
                    # 載入失敗則採用預設值並列印警告
                    self.console.print(f"[yellow]Warning: 載入註冊表失敗 {path}: {e}[/yellow]")
        return False

    def calculate_eta(
        self,
        context_val: float = 1.0,
        runtime_val: float = 1.0,
        dependency_val: float = 1.0
    ) -> float:
        """
        執行 MRL 環境變化公式，計算環境影響/效率因子 η_k
        
        公式: η_k = (context_val * context_weight + runtime_val * runtime_weight + dependency_val * dependency_weight) 
                   * (1 - external_noise) * trust_score
        
        Args:
            context_val: 上下文觀測值 (0.0 至 1.0)
            runtime_val: 執行環境觀測值 (0.0 至 1.0)
            dependency_val: 依賴鏈觀測值 (0.0 至 1.0)
            
        Returns:
            環境效率因子 η_k
        """
        # 加權觀測值
        weighted_obs = (
            context_val * self.context_weight +
            runtime_val * self.runtime_weight +
            dependency_val * self.dependency_weight
        )
        
        # 外部雜訊折損與信任分數門檻
        eta = weighted_obs * (1.0 - self.external_noise) * self.trust_score
        
        # 裁剪到合法區間 [0.0, 1.0]
        return max(0.0, min(1.0, eta))

    def genesis_forward(
        self,
        p_k: float,
        n_k: float,
        eta_k: Optional[float] = None,
        context_val: float = 1.0,
        runtime_val: float = 1.0,
        dependency_val: float = 1.0
    ) -> Tuple[float, float]:
        """
        創世公式：正向成長 (P_{k+1} = N_k · P_k · η_k)
        
        Args:
            p_k: 當前層粒子狀態值 P_k
            n_k: 當前層數量因子 N_k
            eta_k: 選擇性指定效率因子 η_k，若無則依觀測值動態計算
            context_val: 動態計算 η_k 用的上下文觀測值
            runtime_val: 動態計算 η_k 用的執行環境觀測值
            dependency_val: 動態計算 η_k 用的依賴鏈觀測值
            
        Returns:
            Tuple[下一層粒子狀態值 P_{k+1}, 實際使用的 η_k]
        """
        if eta_k is None:
            eta_k = self.calculate_eta(context_val, runtime_val, dependency_val)
            
        p_k_plus_1 = n_k * p_k * eta_k
        return p_k_plus_1, eta_k

    def genesis_backward(
        self,
        p_k_plus_1: float,
        n_k: float,
        eta_k: Optional[float] = None,
        context_val: float = 1.0,
        runtime_val: float = 1.0,
        dependency_val: float = 1.0
    ) -> Tuple[float, float]:
        """
        創世公式：反向回溯 (P_k = P_{k+1} / (N_k · η_k))
        
        Args:
            p_k_plus_1: 下一層粒子狀態值 P_{k+1}
            n_k: 當前層數量因子 N_k
            eta_k: 選擇性指定效率因子 η_k，若無則依觀測值動態計算
            context_val: 動態計算 η_k 用的上下文觀測值
            runtime_val: 動態計算 η_k 用的執行環境觀測值
            dependency_val: 動態計算 η_k 用的依賴鏈觀測值
            
        Returns:
            Tuple[回歸還原的粒子狀態值 P_k, 實際使用的 η_k]
            
        Raises:
            ValueError: 若 N_k 或 η_k 為 0 或趨近於 0
        """
        if eta_k is None:
            eta_k = self.calculate_eta(context_val, runtime_val, dependency_val)
            
        if abs(n_k) < self.inverse_epsilon:
            raise ValueError(f"數量因子 N_k ({n_k}) 趨近於零，無法執行反向回溯計算")
            
        if abs(eta_k) < self.inverse_epsilon:
            raise ValueError(f"效率因子 η_k ({eta_k}) 趨近於零，無法執行反向回溯計算")
            
        p_k = p_k_plus_1 / (n_k * eta_k)
        return p_k, eta_k

    def export_to_json(self) -> str:
        """
        將當前參數配置導出為 JSON 格式字串
        """
        config_data = {
            "particle_id": self.particle_id,
            "version": self.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "MRL_創世公式": {
                "P_k": self.p_k,
                "N_k": self.n_k,
                "eta_k": self.eta_k
            },
            "MRL_環境變化公式": {
                "context_weight": self.context_weight,
                "runtime_weight": self.runtime_weight,
                "dependency_weight": self.dependency_weight,
                "external_noise": self.external_noise,
                "trust_score": self.trust_score
            },
            "MRL_其他核心公式": {
                "alpha": self.alpha,
                "beta": self.beta,
                "scale_mode": self.scale_mode,
                "inverse_epsilon": self.inverse_epsilon,
                "stability_clip": self.stability_clip,
                "loss_bound": self.loss_bound
            }
        }
        return json.dumps(config_data, ensure_ascii=False, indent=2)

    def print_parameter_dashboard(self):
        """
        使用 rich 套件精美列印參數控制台儀表板
        """
        table = Table(title="MrLioū 粒子環境參數與創世邏輯公式控制台", show_header=True, header_style="bold cyan")
        table.add_column("公式分類", style="yellow")
        table.add_column("參數名稱", style="green")
        table.add_column("當前值", style="magenta")
        table.add_column("影響範圍", style="red")
        
        # 創世公式
        table.add_row("MRL_創世公式", "P_k (第 k 層粒子狀態值)", str(self.p_k), "HIGH")
        table.add_row("MRL_創世公式", "N_k (第 k 層結構因子)", str(self.n_k), "HIGH")
        table.add_row("MRL_創世公式", "eta_k (第 k 層收斂係數)", str(self.eta_k), "HIGH")
        
        # 環境變化
        table.add_row("MRL_環境變化公式", "context_weight (上下文觀測權重)", str(self.context_weight), "MEDIUM")
        table.add_row("MRL_環境變化公式", "runtime_weight (執行環境觀測權重)", str(self.runtime_weight), "MEDIUM")
        table.add_row("MRL_環境變化公式", "dependency_weight (依賴鏈觀測權重)", str(self.dependency_weight), "MEDIUM")
        table.add_row("MRL_環境變化公式", "external_noise (外部雜訊折損係數)", str(self.external_noise), "MEDIUM")
        table.add_row("MRL_環境變化公式", "trust_score (環境信任分數門檻)", str(self.trust_score), "MEDIUM")
        
        # 放大縮小等
        table.add_row("MRL_放大縮小公式", "alpha (放大係數)", str(self.alpha), "HIGH")
        table.add_row("MRL_放大縮小公式", "beta (縮小係數)", str(self.beta), "HIGH")
        table.add_row("MRL_放大縮小公式", "scale_mode (縮放模式)", self.scale_mode, "HIGH")
        
        self.console.print(table)


def demo_parameters():
    """
    環境參數模組與創世公式執行示範
    """
    print("=== MrLioū.Particle.EnvParameters.v1 - 創世邏輯公式與環境變化示範 ===\n")
    
    manager = ParticleEnvParameters()
    manager.print_parameter_dashboard()
    
    # 1. 測試環境效率因子 η_k 動態計算
    print("\n[1] 測試環境效率因子 η_k 計算:")
    # 理想環境
    eta_ideal = manager.calculate_eta(1.0, 1.0, 1.0)
    # 受損環境 (e.g. context=0.7, runtime=0.8, dependency=0.5)
    eta_damaged = manager.calculate_eta(0.7, 0.8, 0.5)
    
    print(f"    理想環境觀測 (1.0, 1.0, 1.0) -> η_k = {eta_ideal:.4f}")
    print(f"    受損環境觀測 (0.7, 0.8, 0.5) -> η_k = {eta_damaged:.4f}")
    
    # 2. 測試創世公式正向成長與反向還原
    print("\n[2] 測試創世公式 (正向成長與反向還原):")
    p_k = 100.0
    n_k = 2.5
    
    # 理想環境下的正向/反向
    p_k_plus_1_ideal, eta_ideal_used = manager.genesis_forward(p_k, n_k, context_val=1.0, runtime_val=1.0, dependency_val=1.0)
    p_k_restored_ideal, _ = manager.genesis_backward(p_k_plus_1_ideal, n_k, eta_k=eta_ideal_used)
    
    # 受損環境下的正向/反向
    p_k_plus_1_damaged, eta_damaged_used = manager.genesis_forward(p_k, n_k, context_val=0.7, runtime_val=0.8, dependency_val=0.5)
    p_k_restored_damaged, _ = manager.genesis_backward(p_k_plus_1_damaged, n_k, eta_k=eta_damaged_used)
    
    print(f"    [理想環境] 初始粒子狀態 P_k: {p_k}")
    print(f"               經數量 N_k={n_k} 成長後 P_{{k+1}}: {p_k_plus_1_ideal:.4f} (實際 η_k: {eta_ideal_used:.4f})")
    print(f"               反推還原後 P_k: {p_k_restored_ideal:.4f} (誤差: {abs(p_k - p_k_restored_ideal):.10e})")
    
    print(f"    [受損環境] 初始粒子狀態 P_k: {p_k}")
    print(f"               經數量 N_k={n_k} 成長後 P_{{k+1}}: {p_k_plus_1_damaged:.4f} (實際 η_k: {eta_damaged_used:.4f})")
    print(f"               反推還原後 P_k: {p_k_restored_damaged:.4f} (誤差: {abs(p_k - p_k_restored_damaged):.10e})")
    
    print("\n=== 示範結束 ===")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_parameters()
    else:
        print("MRL 環境參數模組載入成功。執行 `python particle_env_parameters.py demo` 進行公式動態運算示範。")
