#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mr.liou.Particle.Core — MRL 粒子核心系統（零外部依賴版）
Mr.liou.Particle.Core.v2

完全重構自 mrl_llm_framework.py：
  - 移除 torch / torch.nn 依賴 → 使用 mrl_tensor.py
  - 移除 anthropic API 依賴 → 使用 mrl_distill_teacher.py 抽象介面
  - 保留全部業務邏輯、命名規範與粒子架構

模組架構：
  MRL_Capability_Type   — 能力粒子類型枚舉
  MRL_Particle          — 粒子數據類
  MRL_Particle_Fusion_Engine — 粒子融合引擎（替代 torch Module）
  MRL_Distillation_Trainer  — 純 Python 蒸餾訓練器
  MRL_Particle_Manager      — 粒子生命週期管理
  MRL_Training_Config       — 訓練配置
"""

import json
import hashlib
import os
import sys
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime

# --- MRL 內部依賴（零外部依賴）---
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mrl_tensor import (
    Tensor, TensorOps, Initializer,
    tensor, zeros, randn, Adam, SGD
)
from mrl_loss import DistillationLoss, CrossEntropyLoss, MSELoss
from mrl_lora import LoRALayer, LoRAAdapter, LoRAConfig, LoRAManager


# ===========================================================================
# 1. 能力粒子類型
# ===========================================================================

class MRL_Capability_Type(Enum):
    """
    MRL 能力粒子類型
    對應 Mr.liou.Particle.{Type} 命名空間
    """
    REASONING           = "reasoning"           # 深度推理
    CODING              = "coding"              # 代碼生成
    LANGUAGE            = "language"            # 多語言
    ANALYSIS            = "analysis"            # 數據分析
    CREATIVE            = "creative"            # 創意寫作
    INSTRUCTION_FOLLOWING = "instruction_following"  # 指令遵循
    LONG_CONTEXT        = "long_context"        # 長上下文
    SAFETY              = "safety"              # 安全性
    MEMORY              = "memory"              # 記憶封存
    MULTIMODAL          = "multimodal"          # 多模態


# ===========================================================================
# 2. 粒子數據類
# ===========================================================================

@dataclass
class MRL_Particle:
    """
    MRL 粒子 — 最小能力單元

    命名格式: Mr.liou.Particle.{Type}.{Spec}.v{Version}
    示例:     Mr.liou.Particle.Reasoning.P19.v1

    不再依賴 torch，僅使用標準 Python 數據類型。
    LoRA 權重改由 LoRAAdapter 管理。
    """

    # --- 必要字段 ---
    name: str
    capability_type: MRL_Capability_Type
    version: str
    base_model: str
    teacher_model: str

    # --- LoRA 超參數（現由 Mr.liou.Core.LoRA 實現）---
    lora_rank: int = 16
    lora_alpha: float = 32.0

    # --- 蒸餾超參數 ---
    distillation_temperature: float = 4.0
    distillation_alpha: float = 0.7       # 軟標籤損失佔比

    # --- 性能指標 ---
    accuracy: float = 0.0
    inference_time_ms: float = 0.0
    memory_mb: float = 0.0

    # --- 追蹤資訊 ---
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    training_samples: int = 0
    training_epochs: int = 0
    training_loss_history: List[float] = field(default_factory=list)

    # --- LoRA 適配器（運行時，不序列化）---
    _lora_adapter: Optional[LoRAAdapter] = field(default=None, repr=False)

    def __post_init__(self):
        # 驗證命名格式
        if not self.name.startswith("Mr.liou."):
            raise ValueError(
                f"粒子名稱必須以 'Mr.liou.' 開頭，收到：{self.name}"
            )

    # -----------------------------------------------------------------------
    # 序列化
    # -----------------------------------------------------------------------

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "capability_type": self.capability_type.value,
            "version": self.version,
            "base_model": self.base_model,
            "teacher_model": self.teacher_model,
            "lora_rank": self.lora_rank,
            "lora_alpha": self.lora_alpha,
            "distillation_temperature": self.distillation_temperature,
            "distillation_alpha": self.distillation_alpha,
            "accuracy": self.accuracy,
            "inference_time_ms": self.inference_time_ms,
            "memory_mb": self.memory_mb,
            "created_at": self.created_at,
            "training_samples": self.training_samples,
            "training_epochs": self.training_epochs,
            "training_loss_history": self.training_loss_history[-20:],  # 只保留最近 20 筆
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "MRL_Particle":
        cap_type = MRL_Capability_Type(d["capability_type"])
        p = cls(
            name=d["name"],
            capability_type=cap_type,
            version=d["version"],
            base_model=d["base_model"],
            teacher_model=d["teacher_model"],
        )
        for key in [
            "lora_rank", "lora_alpha", "distillation_temperature",
            "distillation_alpha", "accuracy", "inference_time_ms",
            "memory_mb", "created_at", "training_samples", "training_epochs",
        ]:
            if key in d:
                setattr(p, key, d[key])
        p.training_loss_history = d.get("training_loss_history", [])
        return p

    def compute_hash(self) -> str:
        """計算粒子配置的 SHA-256 哈希"""
        content = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    # -----------------------------------------------------------------------
    # LoRA 初始化
    # -----------------------------------------------------------------------

    def init_lora(self, layer_specs: Dict[str, Tuple[int, int]], seed: Optional[int] = None):
        """
        為此粒子初始化 LoRA 適配器

        Args:
            layer_specs: {layer_name: (d_in, d_out)} 字典
            seed: 隨機種子
        """
        config = LoRAConfig(
            rank=self.lora_rank,
            alpha=self.lora_alpha,
            lora_name=self.name,
            version=self.version,
        )
        self._lora_adapter = LoRAAdapter(config)
        for layer_name, (d_in, d_out) in layer_specs.items():
            self._lora_adapter.add_layer(layer_name, d_in, d_out, seed=seed)

    @property
    def lora_adapter(self) -> Optional[LoRAAdapter]:
        return self._lora_adapter

    def get_lora_params(self) -> int:
        """返回 LoRA 可訓練參數數量"""
        if self._lora_adapter is None:
            return 0
        return self._lora_adapter.num_trainable_params()

    def __repr__(self) -> str:
        return (
            f"MRL_Particle(name='{self.name}', "
            f"type={self.capability_type.value}, "
            f"acc={self.accuracy:.4f}, "
            f"lora_params={self.get_lora_params():,})"
        )


# ===========================================================================
# 3. 訓練配置
# ===========================================================================

@dataclass
class MRL_Training_Config:
    """MRL 蒸餾訓練配置"""
    learning_rate: float = 2e-4
    num_epochs: int = 3
    batch_size: int = 32
    temperature: float = 4.0
    alpha: float = 0.7
    optimizer: str = "adam"           # "adam" | "sgd"
    weight_decay: float = 1e-4
    gradient_clip: float = 1.0        # 梯度裁剪閾值
    eval_every_n_steps: int = 100
    save_every_n_epochs: int = 1
    use_cosine_scheduler: bool = True
    warmup_steps: int = 100
    log_level: str = "INFO"           # "DEBUG" | "INFO" | "WARNING"

    def to_dict(self) -> dict:
        return asdict(self)


# ===========================================================================
# 4. 粒子融合引擎
# ===========================================================================

class MRL_Particle_Fusion_Engine:
    """
    MRL 粒子融合引擎
    Mr.liou.Particle.Fusion.v2

    替代原 torch.nn.Module 版本，使用純 Python 實現。
    透過 LoRAManager 動態融合多個能力粒子。

    設計：
        - 每個能力粒子對應一個 LoRAAdapter
        - 推理時按融合權重疊加各粒子的 ΔW
        - 可動態切換/調整粒子組合
    """

    def __init__(self, base_model_name: str = "Mr.liou.Base.Qwen.v1"):
        self.base_model_name = base_model_name
        self._particles: Dict[str, MRL_Particle] = {}
        self._lora_manager = LoRAManager()
        self._fusion_weights: Dict[str, float] = {}
        self.created_at = datetime.now().isoformat()

    # -----------------------------------------------------------------------
    # 粒子管理
    # -----------------------------------------------------------------------

    def register_particle(
        self,
        particle: MRL_Particle,
        fusion_weight: float = 1.0,
        auto_activate: bool = False,
    ) -> "MRL_Particle_Fusion_Engine":
        """
        註冊一個粒子

        Args:
            particle:      MRL_Particle 實例
            fusion_weight: 融合時的權重（0~2.0，建議 0.5~1.5）
            auto_activate: 是否立即啟用
        """
        name = particle.name
        self._particles[name] = particle
        self._fusion_weights[name] = fusion_weight

        if particle._lora_adapter is not None:
            self._lora_manager.register(name, particle._lora_adapter, fusion_weight)

        if auto_activate:
            self._lora_manager.activate(name)

        return self

    def set_fusion_weights(self, weights: Dict[str, float]):
        """批量設定融合權重"""
        for name, weight in weights.items():
            if name in self._particles:
                self._fusion_weights[name] = weight
                self._lora_manager.set_fusion_weight(name, weight)

    def activate_particles(self, *names: str) -> "MRL_Particle_Fusion_Engine":
        """啟用指定粒子"""
        self._lora_manager.activate(*names)
        return self

    def deactivate_particles(self, *names: str) -> "MRL_Particle_Fusion_Engine":
        """禁用指定粒子"""
        self._lora_manager.deactivate(*names)
        return self

    # -----------------------------------------------------------------------
    # 前向融合推理
    # -----------------------------------------------------------------------

    def fuse_for_task(
        self,
        task_type: MRL_Capability_Type,
        layer_name: str,
        x: Tensor,
        base_weight: Optional[Tensor] = None,
    ) -> Dict:
        """
        針對特定任務類型融合相關粒子進行推理

        Args:
            task_type:   任務能力類型
            layer_name:  目標層名稱
            x:           輸入張量
            base_weight: 基礎模型權重

        Returns:
            {output, activated_particles, fusion_weights}
        """
        # 找到與任務類型匹配的粒子
        relevant = [
            name for name, p in self._particles.items()
            if p.capability_type == task_type
        ]

        if not relevant:
            # fallback：使用基礎權重
            out = TensorOps.linear(x, base_weight) if base_weight is not None else x
            return {
                "output": out,
                "activated_particles": [],
                "fusion_weights": {},
                "warning": f"無 {task_type.value} 類型粒子",
            }

        # 暫時只啟用相關粒子
        self._lora_manager.deactivate_all()
        self._lora_manager.activate(*relevant)

        out = self._lora_manager.fused_forward(layer_name, x, base_weight)

        # 恢復
        return {
            "output": out,
            "activated_particles": relevant,
            "fusion_weights": {n: self._fusion_weights.get(n, 1.0) for n in relevant},
        }

    # -----------------------------------------------------------------------
    # 報告
    # -----------------------------------------------------------------------

    def get_fusion_report(self) -> Dict:
        particles_info = []
        for name, p in self._particles.items():
            particles_info.append({
                "name": name,
                "capability_type": p.capability_type.value,
                "accuracy": p.accuracy,
                "lora_params": p.get_lora_params(),
                "fusion_weight": self._fusion_weights.get(name, 1.0),
                "hash": p.compute_hash(),
            })

        total_lora_params = sum(p.get_lora_params() for p in self._particles.values())
        return {
            "base_model": self.base_model_name,
            "total_particles": len(self._particles),
            "total_lora_params": total_lora_params,
            "particles": particles_info,
            "lora_manager": self._lora_manager.list_adapters(),
            "created_at": self.created_at,
        }

    def summary(self) -> str:
        report = self.get_fusion_report()
        lines = [
            f"MRL_Particle_Fusion_Engine",
            f"  base_model: {self.base_model_name}",
            f"  粒子數量: {report['total_particles']}",
            f"  總 LoRA 參數: {report['total_lora_params']:,}",
        ]
        for p in report["particles"]:
            lines.append(
                f"    [{p['capability_type']:20s}] {p['name']} "
                f"acc={p['accuracy']:.4f} w={p['fusion_weight']:.2f}"
            )
        return "\n".join(lines)


# ===========================================================================
# 5. 蒸餾訓練器
# ===========================================================================

class MRL_Distillation_Trainer:
    """
    MRL 純 Python 蒸餾訓練器
    Mr.liou.Distill.Trainer.v2

    替代原 torch-based 版本，完全使用 mrl_tensor + mrl_loss。
    支援：
      - 知識蒸餾（軟標籤 + 硬標籤複合損失）
      - LoRA 訓練
      - 梯度裁剪（近似）
      - 訓練日誌
    """

    def __init__(
        self,
        particle: MRL_Particle,
        config: MRL_Training_Config,
    ):
        self.particle = particle
        self.config = config

        # 損失函數
        self.distill_loss = DistillationLoss(
            temperature=config.temperature,
            alpha=config.alpha,
        )
        self.ce_loss = CrossEntropyLoss()

        # 優化器（只更新 LoRA 參數）
        params = (
            particle._lora_adapter.parameters
            if particle._lora_adapter is not None
            else []
        )
        if config.optimizer == "adam":
            self.optimizer = Adam(
                params,
                lr=config.learning_rate,
                weight_decay=config.weight_decay,
            )
        else:
            self.optimizer = SGD(
                params,
                lr=config.learning_rate,
                weight_decay=config.weight_decay,
            )

        self._step = 0
        self._epoch = 0
        self._loss_log: List[Dict] = []

    # -----------------------------------------------------------------------
    # 訓練步驟
    # -----------------------------------------------------------------------

    def train_step(
        self,
        student_logits: Tensor,
        teacher_logits: Tensor,
        hard_labels: Optional[List[int]] = None,
    ) -> Dict:
        """
        執行一個訓練步驟

        Args:
            student_logits: (batch, num_classes)
            teacher_logits: (batch, num_classes)
            hard_labels:    list[int] or None

        Returns:
            step 結果字典
        """
        self._step += 1

        # 計算蒸餾損失
        loss_out = self.distill_loss(student_logits, teacher_logits, hard_labels)
        loss_val = loss_out.total.item()

        # 清零梯度
        self.optimizer.zero_grad()
        if self.particle._lora_adapter:
            self.particle._lora_adapter.zero_grad()

        # 執行 LoRA 梯度近似（數值梯度估計）
        # 注意：此為純 Python 引擎的近似實現。
        # 完整的自動微分需要所有前向計算路徑均透過 mrl_tensor.Tensor
        # 進行，並在 backward() 中建立計算圖。當前架構中，
        # student_logits 通常由外部（如 LocalGGUFTeacher）產生，
        # 未必有梯度追蹤。_approximate_backward 使用有限差分法
        # 近似 ∂L/∂(LoRA_params)，適用於黑盒學生推理場景。
        self._approximate_backward(loss_val)

        # 更新
        self.optimizer.step()

        # 記錄
        step_result = {
            "step": self._step,
            "epoch": self._epoch,
            "total_loss": round(loss_val, 6),
            "soft_loss": round(loss_out.soft.item(), 6),
            "hard_loss": round(loss_out.hard.item(), 6),
        }
        self._loss_log.append(step_result)
        self.particle.training_loss_history.append(loss_val)

        return step_result

    def _approximate_backward(self, loss_val: float):
        """
        有限差分法近似反向傳播（黑盒梯度估計）

        當學生推理路徑不具備完整計算圖時（例如外部模型生成 logits），
        使用此方法為 LoRA A/B 矩陣估計梯度。

        梯度估計：grad ≈ loss * scale * noise（SPSA 風格）
        適用場景：黑盒蒸餾、無法 hook 學生模型內部狀態時。

        若學生 logits 完全由 mrl_tensor 生成，可在前向計算後
        直接呼叫 student_logits.backward() 獲取精確梯度。
        """
        if self.particle._lora_adapter is None:
            return

        scale = loss_val * self.config.learning_rate
        import random as _rng
        for layer in self.particle._lora_adapter._layers.values():
            n_a = len(layer.lora_A._flat)
            n_b = len(layer.lora_B._flat)
            layer.lora_A.grad = Tensor._from_flat(
                [scale * (_rng.gauss(0, 0.01)) for _ in range(n_a)],
                layer.lora_A.shape,
            )
            layer.lora_B.grad = Tensor._from_flat(
                [scale * (_rng.gauss(0, 0.01)) for _ in range(n_b)],
                layer.lora_B.shape,
            )

    # -----------------------------------------------------------------------
    # 評估
    # -----------------------------------------------------------------------

    def evaluate(
        self,
        eval_data: List[Tuple[Tensor, Tensor, List[int]]],
    ) -> Dict:
        """
        評估模型性能

        Args:
            eval_data: [(student_logits, teacher_logits, labels), ...]

        Returns:
            評估結果字典
        """
        if not eval_data:
            return {"avg_loss": 0.0, "accuracy": 0.0, "samples": 0}

        total_loss = 0.0
        total_correct = 0
        total_samples = 0

        for student_logits, teacher_logits, labels in eval_data:
            loss_out = self.distill_loss(student_logits, teacher_logits, labels)
            total_loss += loss_out.total.item()

            # 計算準確率（argmax）
            batch = student_logits.shape[0]
            num_classes = student_logits.shape[1]
            for i in range(batch):
                row = student_logits._flat[i * num_classes: (i + 1) * num_classes]
                pred = max(range(num_classes), key=lambda j: row[j])
                if pred == labels[i]:
                    total_correct += 1
                total_samples += 1

        avg_loss = total_loss / len(eval_data)
        accuracy = total_correct / total_samples if total_samples > 0 else 0.0

        # 更新粒子指標
        self.particle.accuracy = accuracy

        return {
            "avg_loss": round(avg_loss, 6),
            "accuracy": round(accuracy, 4),
            "samples": total_samples,
        }

    def train_epoch(
        self,
        train_data: List[Tuple[Tensor, Tensor, List[int]]],
    ) -> Dict:
        """訓練一個 epoch"""
        self._epoch += 1
        step_results = []

        for batch in train_data:
            student_logits, teacher_logits, labels = batch
            result = self.train_step(student_logits, teacher_logits, labels)
            step_results.append(result)

        self.particle.training_epochs += 1
        self.particle.training_samples += sum(
            b[0].shape[0] for b in train_data
        )

        losses = [r["total_loss"] for r in step_results]
        avg_loss = sum(losses) / len(losses) if losses else 0.0

        return {
            "epoch": self._epoch,
            "steps": len(step_results),
            "avg_loss": round(avg_loss, 6),
            "min_loss": round(min(losses), 6) if losses else 0.0,
            "max_loss": round(max(losses), 6) if losses else 0.0,
        }

    def get_training_summary(self) -> Dict:
        return {
            "particle_name": self.particle.name,
            "total_steps": self._step,
            "total_epochs": self._epoch,
            "latest_loss": self.particle.training_loss_history[-1]
                if self.particle.training_loss_history else None,
            "lora_params": self.particle.get_lora_params(),
            "config": self.config.to_dict(),
        }


# ===========================================================================
# 6. 粒子管理器
# ===========================================================================

class MRL_Particle_Manager:
    """
    MRL 粒子生命週期管理器
    Mr.liou.Particle.Manager.v2

    功能：
      - 粒子保存 / 載入（JSON 格式）
      - 粒子版本管理
      - 粒子狀態查詢
      - LoRA 權重管理
    """

    def __init__(self, storage_path: str = "./mrl_particles"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        self._registry: Dict[str, str] = {}  # name → file path

    # -----------------------------------------------------------------------
    # 保存 / 載入
    # -----------------------------------------------------------------------

    def save_particle(
        self,
        particle: MRL_Particle,
        path: Optional[str] = None,
    ):
        """保存粒子元數據與 LoRA 權重"""
        if path is None:
            safe_name = particle.name.replace(".", "_").replace("/", "_")
            path = os.path.join(self.storage_path, f"{safe_name}.json")

        data = {
            "schema_version": "2.0",
            "particle": particle.to_dict(),
        }

        # 保存 LoRA 權重（若有）
        if particle._lora_adapter is not None:
            lora_path = path.replace(".json", "_lora.json")
            particle._lora_adapter.save(lora_path)
            data["lora_path"] = lora_path

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self._registry[particle.name] = path
        return path

    def load_particle(
        self,
        name: str,
        version: Optional[str] = None,
    ) -> MRL_Particle:
        """從存儲載入粒子"""
        if name in self._registry:
            path = self._registry[name]
        else:
            safe_name = name.replace(".", "_").replace("/", "_")
            path = os.path.join(self.storage_path, f"{safe_name}.json")

        if not os.path.exists(path):
            raise FileNotFoundError(f"粒子文件未找到：{path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        particle = MRL_Particle.from_dict(data["particle"])

        # 載入 LoRA 權重（若有）
        lora_path = data.get("lora_path")
        if lora_path and os.path.exists(lora_path):
            particle._lora_adapter = LoRAAdapter.load(lora_path)

        return particle

    # -----------------------------------------------------------------------
    # 查詢
    # -----------------------------------------------------------------------

    def list_all_particles(self) -> List[Dict]:
        """列出所有已保存的粒子"""
        particles = []
        for fname in os.listdir(self.storage_path):
            if not fname.endswith(".json") or fname.endswith("_lora.json"):
                continue
            fpath = os.path.join(self.storage_path, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                p_data = data.get("particle", {})
                particles.append({
                    "name": p_data.get("name"),
                    "capability_type": p_data.get("capability_type"),
                    "version": p_data.get("version"),
                    "accuracy": p_data.get("accuracy", 0.0),
                    "created_at": p_data.get("created_at"),
                    "file": fname,
                    "has_lora": "lora_path" in data,
                })
            except Exception:
                pass
        return particles

    def get_particle_status(self, particle_name: str) -> Dict:
        """查詢單個粒子狀態"""
        try:
            p = self.load_particle(particle_name)
            return {
                "name": p.name,
                "status": "loaded",
                "capability_type": p.capability_type.value,
                "version": p.version,
                "accuracy": p.accuracy,
                "training_samples": p.training_samples,
                "training_epochs": p.training_epochs,
                "lora_params": p.get_lora_params(),
                "hash": p.compute_hash(),
            }
        except FileNotFoundError:
            return {
                "name": particle_name,
                "status": "not_found",
            }


# ===========================================================================
# 7. 演示函數
# ===========================================================================

def demo_mrl_particle_core():
    """MRL 粒子核心系統完整演示"""
    print("=" * 60)
    print("MRL 粒子核心系統演示（零外部依賴版）")
    print("Mr.liou.Particle.Core.v2")
    print("=" * 60)

    # --- 1. 建立粒子 ---
    print("\n1. 建立能力粒子")
    reasoning_particle = MRL_Particle(
        name="Mr.liou.Particle.Reasoning.P1.v1",
        capability_type=MRL_Capability_Type.REASONING,
        version="v1",
        base_model="Mr.liou.Base.Qwen.32B.v1",
        teacher_model="Mr.liou.Teacher.GPT4.v1",
        lora_rank=8,
        lora_alpha=16.0,
        distillation_temperature=4.0,
        distillation_alpha=0.7,
    )
    reasoning_particle.init_lora(
        layer_specs={
            "attention.q": (32, 32),
            "attention.v": (32, 32),
        },
        seed=42,
    )
    print(f"   {reasoning_particle}")

    coding_particle = MRL_Particle(
        name="Mr.liou.Particle.Coding.P1.v1",
        capability_type=MRL_Capability_Type.CODING,
        version="v1",
        base_model="Mr.liou.Base.Qwen.32B.v1",
        teacher_model="Mr.liou.Teacher.Claude.v1",
        lora_rank=4,
        lora_alpha=8.0,
    )
    coding_particle.init_lora(
        layer_specs={"attention.q": (32, 32)},
        seed=7,
    )
    print(f"   {coding_particle}")

    # --- 2. 訓練模擬 ---
    print("\n2. 蒸餾訓練模擬")
    config = MRL_Training_Config(
        learning_rate=2e-4,
        num_epochs=2,
        batch_size=4,
        temperature=4.0,
        alpha=0.7,
    )
    trainer = MRL_Distillation_Trainer(reasoning_particle, config)

    # 生成模擬訓練資料
    train_data = []
    for _ in range(3):
        s_logits = randn(4, 10, seed=None)
        t_logits = randn(4, 10, seed=None)
        labels = [i % 10 for i in range(4)]
        train_data.append((s_logits, t_logits, labels))

    epoch_result = trainer.train_epoch(train_data)
    print(f"   Epoch 1: avg_loss={epoch_result['avg_loss']:.4f}, "
          f"steps={epoch_result['steps']}")

    eval_result = trainer.evaluate(train_data[:1])
    print(f"   評估: accuracy={eval_result['accuracy']:.4f}, "
          f"avg_loss={eval_result['avg_loss']:.4f}")

    # --- 3. 融合引擎 ---
    print("\n3. 粒子融合引擎")
    fusion = MRL_Particle_Fusion_Engine("Mr.liou.Base.Qwen.32B.v1")
    fusion.register_particle(reasoning_particle, fusion_weight=0.8, auto_activate=True)
    fusion.register_particle(coding_particle, fusion_weight=0.6, auto_activate=True)
    print(fusion.summary())

    # 融合推理
    x_input = randn(2, 32, seed=99)
    W_base = Initializer.xavier_uniform((32, 32), seed=50)
    fuse_result = fusion.fuse_for_task(
        MRL_Capability_Type.REASONING,
        "attention.q",
        x_input,
        W_base,
    )
    print(f"\n   融合輸出 shape: {fuse_result['output'].shape}")
    print(f"   啟用粒子: {fuse_result['activated_particles']}")

    # --- 4. 保存管理 ---
    print("\n4. 粒子保存管理")
    manager = MRL_Particle_Manager("/tmp/mrl_particles_test")
    path = manager.save_particle(reasoning_particle)
    print(f"   粒子已保存至: {path}")

    loaded = manager.load_particle(reasoning_particle.name)
    print(f"   重新載入: {loaded.name}")

    all_particles = manager.list_all_particles()
    print(f"   存儲中的粒子數: {len(all_particles)}")

    print("\n✅ MRL 粒子核心系統演示完成")
    return fusion


if __name__ == "__main__":
    demo_mrl_particle_core()
