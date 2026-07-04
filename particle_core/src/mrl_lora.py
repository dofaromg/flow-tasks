#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mr.liou.Core.LoRA — 低秩適配器（Low-Rank Adaptation）
Mr.liou.Core.LoRA.v1

零外部依賴：僅使用 mrl_tensor + Python 標準庫

LoRA 核心公式：
    h = W₀x + ΔWx = W₀x + BA x
    ΔW = B · A
    B ∈ R^(d_out × r)，初始化為 0
    A ∈ R^(r × d_in)，初始化為正態分佈
    r 為秩（rank），r << min(d_in, d_out)

訓練時：W₀ 凍結，只更新 A、B
推理時：可將 W₀ + BA 合併成新的 W（merge_weights）

架構：
  LoRALayer     — 單個 LoRA 層（替代線性層）
  LoRAAdapter   — 適配器包裝器（套在現有權重矩陣上）
  LoRAManager   — 多粒子 LoRA 管理器（啟用/禁用/切換）
  LoRAConfig    — LoRA 配置數據類
"""

import math
import json
import os
import sys
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mrl_tensor import (
    Tensor, TensorOps, Initializer,
    tensor, zeros, randn, Adam, SGD,
    _numel, Shape
)


# ===========================================================================
# LoRA 配置
# ===========================================================================

@dataclass
class LoRAConfig:
    """
    LoRA 配置數據類

    Attributes:
        rank:         LoRA 秩 r（建議 4~64）
        alpha:        縮放因子（scaling = alpha / rank）
        dropout:      Dropout 概率（目前為 0.0，預留）
        target_layers: 要套用 LoRA 的層名稱列表
        lora_name:    LoRA 名稱標識
        version:      版本號
    """
    rank: int = 16
    alpha: float = 32.0
    dropout: float = 0.0
    target_layers: List[str] = field(default_factory=list)
    lora_name: str = "default"
    version: str = "v1"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def scaling(self) -> float:
        """LoRA 縮放係數 = alpha / rank"""
        return self.alpha / self.rank

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "LoRAConfig":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str) -> "LoRAConfig":
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))


# ===========================================================================
# LoRALayer — 核心計算層
# ===========================================================================

class LoRALayer:
    """
    Mr.liou.Core.LoRALayer

    單個 LoRA 層，替代標準線性層的增量部分。

    計算：out = W₀ @ x^T + scaling * B @ A @ x^T
    其中 W₀ 為原始凍結權重（外部提供或 None）
    """

    def __init__(
        self,
        d_in: int,
        d_out: int,
        rank: int = 16,
        alpha: float = 32.0,
        seed: Optional[int] = None,
    ):
        """
        Args:
            d_in:  輸入維度
            d_out: 輸出維度
            rank:  LoRA 秩 r
            alpha: 縮放因子
            seed:  隨機種子
        """
        self.d_in = d_in
        self.d_out = d_out
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank

        # A: (r, d_in) — 正態分佈初始化
        self.lora_A = Initializer.kaiming_normal(
            (rank, d_in), seed=seed, requires_grad=True
        )
        # B: (d_out, r) — 零初始化（使 ΔW = BA = 0 at start）
        self.lora_B = Initializer.zeros(
            (d_out, rank), requires_grad=True
        )

        self.enabled = True
        self._merged = False

    @property
    def parameters(self) -> List[Tensor]:
        """返回可訓練參數列表"""
        return [self.lora_A, self.lora_B]

    def forward(self, x: Tensor, base_weight: Optional[Tensor] = None) -> Tensor:
        """
        前向傳播

        Args:
            x:           (batch, d_in)
            base_weight: (d_out, d_in) 原始權重（可選）

        Returns:
            (batch, d_out)
        """
        if not self.enabled:
            if base_weight is not None:
                return TensorOps.linear(x, base_weight)
            return zeros((x.shape[0], self.d_out))

        # LoRA 增量：x @ A^T @ B^T * scaling
        # A: (r, d_in) → A^T: (d_in, r)
        # x @ A^T: (batch, r)
        xa = TensorOps.matmul(x, self.lora_A.T())  # (batch, r)
        # xa @ B^T: (batch, d_out)
        lora_out = TensorOps.matmul(xa, self.lora_B.T())  # (batch, d_out)
        # scaling
        scale_tensor = tensor(self.scaling)
        lora_out = TensorOps.mul(lora_out, scale_tensor)

        if base_weight is not None:
            base_out = TensorOps.linear(x, base_weight)
            return TensorOps.add(base_out, lora_out)
        return lora_out

    def get_delta_weight(self) -> Tensor:
        """
        計算 ΔW = scaling * B @ A
        shape: (d_out, d_in)
        """
        # B: (d_out, r), A: (r, d_in)
        delta = TensorOps.matmul(self.lora_B, self.lora_A)  # (d_out, d_in)
        scale = tensor(self.scaling)
        return TensorOps.mul(delta, scale)

    def merge_into(self, base_weight: Tensor) -> Tensor:
        """
        將 LoRA 增量合併進基礎權重
        返回新的合併後權重 W = W₀ + ΔW
        """
        if self._merged:
            raise RuntimeError("LoRA 已被合併，不能再次合併")
        delta = self.get_delta_weight()
        merged = TensorOps.add(base_weight, delta)
        self._merged = True
        return merged

    def zero_grad(self):
        self.lora_A.grad = None
        self.lora_B.grad = None

    def state_dict(self) -> dict:
        return {
            "d_in": self.d_in,
            "d_out": self.d_out,
            "rank": self.rank,
            "alpha": self.alpha,
            "lora_A": self.lora_A._flat,
            "lora_B": self.lora_B._flat,
            "enabled": self.enabled,
            "merged": self._merged,
        }

    def load_state_dict(self, sd: dict):
        self.lora_A._flat = list(sd["lora_A"])
        self.lora_B._flat = list(sd["lora_B"])
        self.enabled = sd.get("enabled", True)
        self._merged = sd.get("merged", False)


# ===========================================================================
# LoRAAdapter — 適配器包裝器
# ===========================================================================

class LoRAAdapter:
    """
    Mr.liou.Core.LoRAAdapter

    對現有「層」套用 LoRA 的包裝器。
    支援多個命名 LoRA 層（對應不同能力粒子）。

    使用方式：
        adapter = LoRAAdapter(config)
        adapter.add_layer("attention.q", d_in=512, d_out=512)
        adapter.add_layer("attention.k", d_in=512, d_out=512)

        # 前向計算
        out = adapter.forward("attention.q", x, base_weight_q)

        # 保存/載入
        adapter.save("./lora_weights.json")
    """

    def __init__(self, config: LoRAConfig):
        self.config = config
        self._layers: Dict[str, LoRALayer] = {}

    def add_layer(
        self,
        name: str,
        d_in: int,
        d_out: int,
        seed: Optional[int] = None,
    ) -> "LoRAAdapter":
        """新增一個 LoRA 層"""
        self._layers[name] = LoRALayer(
            d_in=d_in,
            d_out=d_out,
            rank=self.config.rank,
            alpha=self.config.alpha,
            seed=seed,
        )
        return self

    def forward(
        self,
        layer_name: str,
        x: Tensor,
        base_weight: Optional[Tensor] = None,
    ) -> Tensor:
        """對指定層執行 LoRA 前向計算"""
        if layer_name not in self._layers:
            raise KeyError(f"LoRA 層 '{layer_name}' 未找到")
        return self._layers[layer_name].forward(x, base_weight)

    @property
    def parameters(self) -> List[Tensor]:
        """返回所有層的可訓練參數"""
        params = []
        for layer in self._layers.values():
            params.extend(layer.parameters)
        return params

    def enable(self, layer_name: Optional[str] = None):
        """啟用指定層或所有層"""
        if layer_name:
            self._layers[layer_name].enabled = True
        else:
            for layer in self._layers.values():
                layer.enabled = True

    def disable(self, layer_name: Optional[str] = None):
        """禁用指定層或所有層"""
        if layer_name:
            self._layers[layer_name].enabled = False
        else:
            for layer in self._layers.values():
                layer.enabled = False

    def zero_grad(self):
        for layer in self._layers.values():
            layer.zero_grad()

    def num_trainable_params(self) -> int:
        """計算可訓練參數總數"""
        total = 0
        for layer in self._layers.values():
            total += layer.d_in * layer.rank  # A
            total += layer.d_out * layer.rank  # B
        return total

    def compression_ratio(self, base_params: int) -> float:
        """計算相對基礎模型的參數壓縮比"""
        lora_params = self.num_trainable_params()
        if base_params == 0:
            return 0.0
        return lora_params / base_params

    def save(self, path: str):
        """保存 LoRA 權重"""
        data = {
            "config": self.config.to_dict(),
            "layers": {
                name: layer.state_dict()
                for name, layer in self._layers.items()
            }
        }
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str) -> "LoRAAdapter":
        """從文件載入 LoRA 適配器"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        config = LoRAConfig.from_dict(data["config"])
        adapter = cls(config)
        for name, sd in data["layers"].items():
            adapter._layers[name] = LoRALayer(
                d_in=sd["d_in"],
                d_out=sd["d_out"],
                rank=sd["rank"],
                alpha=sd["alpha"],
            )
            adapter._layers[name].load_state_dict(sd)
        return adapter

    def summary(self) -> str:
        lines = [
            f"LoRAAdapter: {self.config.lora_name} ({self.config.version})",
            f"  rank={self.config.rank}, alpha={self.config.alpha}, "
            f"scaling={self.config.scaling:.4f}",
            f"  layers: {len(self._layers)}",
            f"  trainable params: {self.num_trainable_params():,}",
        ]
        for name, layer in self._layers.items():
            lines.append(
                f"    [{name}]: ({layer.d_out}, {layer.d_in}), "
                f"ΔW=({layer.d_out}, {layer.d_in}), enabled={layer.enabled}"
            )
        return "\n".join(lines)


# ===========================================================================
# LoRAManager — 多粒子 LoRA 管理器
# ===========================================================================

class LoRAManager:
    """
    Mr.liou.Core.LoRAManager

    管理多個 LoRA 適配器（對應不同能力粒子），
    支援動態切換、疊加、權重融合。

    典型場景：
        - reasoning_lora: 深度推理能力粒子
        - coding_lora: 代碼生成能力粒子
        - 同時啟用多個粒子 → 能力融合
    """

    def __init__(self):
        self._adapters: Dict[str, LoRAAdapter] = {}
        self._active: List[str] = []
        self._fusion_weights: Dict[str, float] = {}

    def register(
        self,
        name: str,
        adapter: LoRAAdapter,
        fusion_weight: float = 1.0,
    ) -> "LoRAManager":
        """註冊一個 LoRA 適配器"""
        self._adapters[name] = adapter
        self._fusion_weights[name] = fusion_weight
        return self

    def activate(self, *names: str) -> "LoRAManager":
        """啟用指定的 LoRA 適配器（可多個）"""
        for name in names:
            if name not in self._adapters:
                raise KeyError(f"LoRA 適配器 '{name}' 未找到")
            if name not in self._active:
                self._active.append(name)
        return self

    def deactivate(self, *names: str) -> "LoRAManager":
        """禁用指定的 LoRA 適配器"""
        for name in names:
            if name in self._active:
                self._active.remove(name)
        return self

    def deactivate_all(self) -> "LoRAManager":
        self._active.clear()
        return self

    def set_fusion_weight(self, name: str, weight: float):
        """設定適配器融合權重"""
        if name not in self._adapters:
            raise KeyError(f"LoRA 適配器 '{name}' 未找到")
        self._fusion_weights[name] = weight

    def fused_forward(
        self,
        layer_name: str,
        x: Tensor,
        base_weight: Optional[Tensor] = None,
    ) -> Tensor:
        """
        執行多粒子融合前向計算
        out = base_out + Σ(w_i * lora_i_delta)
        """
        if not self._active:
            if base_weight is not None:
                return TensorOps.linear(x, base_weight)
            raise RuntimeError("無啟用的 LoRA 且無基礎權重")

        # 計算基礎輸出
        if base_weight is not None:
            result = TensorOps.linear(x, base_weight)
        else:
            result = None

        # 疊加各個啟用的 LoRA 增量
        for adapter_name in self._active:
            adapter = self._adapters[adapter_name]
            if layer_name not in adapter._layers:
                continue
            layer = adapter._layers[layer_name]
            if not layer.enabled:
                continue
            weight = self._fusion_weights.get(adapter_name, 1.0)
            delta = layer.get_delta_weight()
            # 縮放融合權重
            w_tensor = tensor(weight)
            delta_scaled = TensorOps.mul(delta, w_tensor)
            # 增量貢獻
            delta_out = TensorOps.matmul(x, delta_scaled.T())
            if result is None:
                result = delta_out
            else:
                result = TensorOps.add(result, delta_out)

        if result is None:
            batch = x.shape[0] if x.ndim > 1 else 1
            d_out = list(self._adapters.values())[0]._layers.get(layer_name, None)
            if d_out:
                return zeros((batch, d_out.d_out))
        return result

    def get_adapter(self, name: str) -> LoRAAdapter:
        return self._adapters[name]

    def list_adapters(self) -> List[Dict]:
        return [
            {
                "name": name,
                "active": name in self._active,
                "fusion_weight": self._fusion_weights.get(name, 1.0),
                "trainable_params": adapter.num_trainable_params(),
                "layers": list(adapter._layers.keys()),
            }
            for name, adapter in self._adapters.items()
        ]

    def summary(self) -> str:
        lines = ["LoRAManager 摘要", f"  已註冊適配器: {len(self._adapters)}"]
        for name, adapter in self._adapters.items():
            active_marker = "✓" if name in self._active else "○"
            w = self._fusion_weights.get(name, 1.0)
            lines.append(
                f"  [{active_marker}] {name} (w={w:.2f}) — "
                f"{adapter.config.lora_name} r={adapter.config.rank} "
                f"params={adapter.num_trainable_params():,}"
            )
        return "\n".join(lines)


# ===========================================================================
# 簡易訓練循環輔助
# ===========================================================================

class LoRATrainer:
    """
    Mr.liou.Core.LoRATrainer

    針對 LoRA 適配器的輕量訓練器。
    凍結基礎權重，只更新 LoRA 的 A、B 矩陣。
    """

    def __init__(
        self,
        adapter: LoRAAdapter,
        lr: float = 1e-4,
        optimizer: str = "adam",
    ):
        self.adapter = adapter
        params = adapter.parameters
        if optimizer == "adam":
            self.opt: Union[Adam, SGD] = Adam(params, lr=lr)
        else:
            self.opt = SGD(params, lr=lr)

    def train_step(
        self,
        loss_val: float,
        loss_grad_flat: Optional[List[float]] = None,
    ) -> float:
        """
        執行一步訓練更新（模擬梯度）

        Args:
            loss_val:       損失值（標量）
            loss_grad_flat: 對應輸出的梯度向量（可選）

        Returns:
            損失值
        """
        # 清零梯度
        self.opt.zero_grad()
        self.adapter.zero_grad()

        # 若有梯度資訊，分配到各層
        if loss_grad_flat is not None:
            params = self.adapter.parameters
            idx = 0
            for p in params:
                n = p.numel()
                g_slice = loss_grad_flat[idx: idx + n]
                if len(g_slice) == n:
                    from mrl_tensor import Tensor as T, TensorOps as TO
                    p.grad = T._from_flat(list(g_slice), p.shape)
                idx += n

        self.opt.step()
        return loss_val

    def get_param_stats(self) -> Dict[str, float]:
        """返回參數統計信息"""
        all_vals = []
        for layer in self.adapter._layers.values():
            all_vals.extend(layer.lora_A._flat)
            all_vals.extend(layer.lora_B._flat)
        if not all_vals:
            return {}
        mean_v = sum(all_vals) / len(all_vals)
        std_v = math.sqrt(sum((x - mean_v) ** 2 for x in all_vals) / max(len(all_vals) - 1, 1))
        return {
            "count": len(all_vals),
            "mean": round(mean_v, 6),
            "std": round(std_v, 6),
            "min": round(min(all_vals), 6),
            "max": round(max(all_vals), 6),
            "norm": round(math.sqrt(sum(x ** 2 for x in all_vals)), 6),
        }


# ===========================================================================
# 自檢測試
# ===========================================================================

if __name__ == "__main__":
    print("=== Mr.liou.Core.LoRA 自檢測試 ===\n")

    # --- 1. 基礎 LoRALayer 測試 ---
    print("1. LoRALayer 前向計算")
    layer = LoRALayer(d_in=8, d_out=4, rank=2, alpha=4.0, seed=42)
    x = Initializer.normal((3, 8), seed=1)  # batch=3, d_in=8
    W0 = Initializer.xavier_uniform((4, 8), seed=2)  # base weight

    out_with_base = layer.forward(x, W0)
    out_delta_only = layer.forward(x)
    print(f"   output with base weight: {out_with_base.shape}")
    print(f"   output delta only: {out_delta_only.shape}")

    # --- 2. LoRAAdapter ---
    print("\n2. LoRAAdapter 多層管理")
    config = LoRAConfig(rank=4, alpha=8.0, lora_name="Mr.liou.Particle.Reasoning.v1")
    adapter = LoRAAdapter(config)
    adapter.add_layer("attn.q", d_in=16, d_out=16, seed=10)
    adapter.add_layer("attn.v", d_in=16, d_out=16, seed=11)
    print(adapter.summary())
    print(f"   可訓練參數: {adapter.num_trainable_params():,}")

    # --- 3. LoRAManager 融合 ---
    print("\n3. LoRAManager 多粒子融合")
    mgr = LoRAManager()

    config_r = LoRAConfig(rank=4, alpha=8.0, lora_name="reasoning")
    adapter_r = LoRAAdapter(config_r)
    adapter_r.add_layer("proj", d_in=8, d_out=4, seed=20)

    config_c = LoRAConfig(rank=2, alpha=4.0, lora_name="coding")
    adapter_c = LoRAAdapter(config_c)
    adapter_c.add_layer("proj", d_in=8, d_out=4, seed=21)

    mgr.register("reasoning", adapter_r, fusion_weight=0.7)
    mgr.register("coding", adapter_c, fusion_weight=0.5)
    mgr.activate("reasoning", "coding")
    print(mgr.summary())

    x2 = Initializer.normal((2, 8), seed=5)
    W_proj = Initializer.xavier_uniform((4, 8), seed=6)
    fused_out = mgr.fused_forward("proj", x2, W_proj)
    print(f"   融合輸出 shape: {fused_out.shape}")

    # --- 4. 保存 / 載入 ---
    print("\n4. LoRA 權重保存與載入")
    save_path = "/tmp/mrl_lora_test.json"
    adapter.save(save_path)
    loaded = LoRAAdapter.load(save_path)
    print(f"   保存至: {save_path}")
    print(f"   載入後層數: {len(loaded._layers)}")
    assert loaded.config.lora_name == adapter.config.lora_name

    print("\n✅ 所有 LoRA 自檢通過")
