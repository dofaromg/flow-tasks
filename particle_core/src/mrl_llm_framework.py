"""
MRL LLM Framework - 知識蒸餾與粒子融合核心架構
Mr.liou.LLM.Core.Framework.v1

核心概念：
1. 教師模型（External APIs）→ 知識蒸餾 → 學生模型（Local Qwen）
2. 粒子化專業能力 → 動態融合 → 超級模型
3. 零邊際成本推理 → 無限規模部署
"""

import torch
import torch.nn as nn
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime
import hashlib


# ============================================================================
# 1. 能力粒子定義
# ============================================================================

class MRL_Capability_Type(Enum):
    """MRL 能力粒子類型"""
    REASONING = "reasoning"              # 深度推理
    CODING = "coding"                   # 代碼生成
    LANGUAGE = "language"               # 多語言
    ANALYSIS = "analysis"               # 數據分析
    CREATIVE = "creative"               # 創意寫作
    INSTRUCTION_FOLLOWING = "instruction_following"  # 指令遵循
    LONG_CONTEXT = "long_context"       # 長上下文
    SAFETY = "safety"                   # 安全性


@dataclass
class MRL_Particle:
    """
    MRL 粒子 - 最小能力單元
    
    Name Format: Mr.liou.Particle.{Type}.{Spec}.v{Version}
    Example: Mr.liou.Particle.Reasoning.P19.v1
    """
    name: str                           # 粒子名稱
    capability_type: MRL_Capability_Type  # 能力類型
    version: str                        # 版本
    base_model: str                     # 基礎模型
    teacher_model: str                  # 教師模型
    lora_rank: int = 16                 # LoRA 秩
    lora_alpha: int = 32                # LoRA Alpha
    distillation_temperature: float = 4.0  # 蒸餾溫度
    
    # 性能指標
    accuracy: float = 0.0
    inference_time_ms: float = 0.0
    memory_mb: float = 0.0
    
    # 追蹤信息
    created_at: str = None
    training_samples: int = 0
    training_epochs: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
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
            "accuracy": self.accuracy,
            "inference_time_ms": self.inference_time_ms,
            "memory_mb": self.memory_mb,
            "created_at": self.created_at,
            "training_samples": self.training_samples,
            "training_epochs": self.training_epochs
        }
    
    def compute_hash(self) -> str:
        """計算粒子的內容哈希值（用於版本控制）"""
        content = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ============================================================================
# 2. 知識蒸餾損失函數
# ============================================================================

class MRL_DistillationLoss(nn.Module):
    """
    MRL 知識蒸餾損失 - 軟標籤傳遞
    
    L_total = α·L_hard + (1-α)·L_soft
    
    其中：
    - L_hard: 標準交叉熵（學生 vs 真實標籤）
    - L_soft: KL 散度（學生 logits vs 教師 logits，溫度縮放）
    """
    
    def __init__(
        self,
        temperature: float = 4.0,
        alpha: float = 0.7,
        use_teacher_features: bool = True
    ):
        super().__init__()
        self.temperature = temperature
        self.alpha = alpha
        self.use_teacher_features = use_teacher_features
        self.kl_div = nn.KLDivLoss(reduction='batchmean')
        self.ce_loss = nn.CrossEntropyLoss()
    
    def forward(
        self,
        student_logits: torch.Tensor,
        teacher_logits: torch.Tensor,
        true_labels: torch.Tensor,
        student_features: Optional[torch.Tensor] = None,
        teacher_features: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        計算蒸餾損失
        
        Args:
            student_logits: [batch_size, num_classes] - 學生模型輸出
            teacher_logits: [batch_size, num_classes] - 教師模型輸出
            true_labels: [batch_size] - 真實標籤
            student_features: [batch_size, hidden_size] - 學生中間層特徵
            teacher_features: [batch_size, hidden_size] - 教師中間層特徵
        
        Returns:
            Total loss
        """
        # 軟標籤蒸餾損失
        soft_student = torch.nn.functional.log_softmax(
            student_logits / self.temperature, dim=-1
        )
        soft_teacher = torch.nn.functional.softmax(
            teacher_logits / self.temperature, dim=-1
        )
        
        loss_soft = self.kl_div(soft_student, soft_teacher) * (self.temperature ** 2)
        
        # 硬標籤損失（真實標籤）
        loss_hard = self.ce_loss(student_logits, true_labels)
        
        # 特徵蒸餾損失（可選）
        loss_features = 0
        if self.use_teacher_features and student_features is not None and teacher_features is not None:
            loss_features = torch.nn.functional.mse_loss(student_features, teacher_features)
        
        # 總損失
        total_loss = self.alpha * loss_hard + (1 - self.alpha) * loss_soft + 0.1 * loss_features
        
        return total_loss


# ============================================================================
# 3. LoRA 適配器（粒子化能力）
# ============================================================================

class MRL_LoRA_Adapter(nn.Module):
    """
    MRL LoRA 適配器 - 高效微調粒子
    
    原理：
    W_new = W_base + α * (B @ A)
    
    其中：
    - W_base: 基礎模型權重（凍結）
    - A: [d_in, r] - 下投影
    - B: [r, d_out] - 上投影
    - r: LoRA 秩（遠小於 d_out）
    """
    
    def __init__(
        self,
        in_features: int,
        out_features: int,
        rank: int = 16,
        alpha: float = 32.0,
        dropout: float = 0.05
    ):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank
        
        # LoRA 矩陣
        self.lora_a = nn.Linear(in_features, rank, bias=False)
        self.lora_b = nn.Linear(rank, out_features, bias=False)
        self.dropout = nn.Dropout(dropout)
        
        # 初始化
        nn.init.kaiming_uniform_(self.lora_a.weight, a=5 ** 0.5)
        nn.init.zeros_(self.lora_b.weight)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """應用 LoRA 調整"""
        lora_out = self.lora_b(self.dropout(self.lora_a(x)))
        return lora_out * self.scaling


# ============================================================================
# 4. 粒子融合引擎
# ============================================================================

class MRL_Particle_Fusion_Engine:
    """
    MRL 粒子融合引擎 - 動態組合多個能力粒子
    
    融合方式：
    M_fused = M_base + w_1·ΔW_1 + w_2·ΔW_2 + ... + w_n·ΔW_n
    
    其中：
    - M_base: 基礎模型
    - ΔW_i: 第 i 個粒子的 LoRA 增量
    - w_i: 動態融合權重（可根據任務調整）
    """
    
    def __init__(self, base_model_name: str = "Qwen2.5-32B-Instruct"):
        self.base_model_name = base_model_name
        self.particles: Dict[str, MRL_Particle] = {}
        self.lora_adapters: Dict[str, MRL_LoRA_Adapter] = {}
        self.fusion_weights: Dict[str, float] = {}
        self.fusion_history = []
    
    def register_particle(
        self,
        particle: MRL_Particle,
        lora_adapter: MRL_LoRA_Adapter
    ):
        """註冊一個能力粒子"""
        self.particles[particle.name] = particle
        self.lora_adapters[particle.name] = lora_adapter
        self.fusion_weights[particle.name] = 1.0 / max(len(self.particles), 1)
        
        print(f"✓ 粒子已註冊: {particle.name}")
        print(f"  - 能力: {particle.capability_type.value}")
        print(f"  - 教師: {particle.teacher_model}")
        print(f"  - 準確率: {particle.accuracy:.2%}")
    
    def set_fusion_weights(self, weights: Dict[str, float]):
        """設置粒子融合權重"""
        total = sum(weights.values())
        self.fusion_weights = {k: v / total for k, v in weights.items()}
        
        print("\n📊 粒子融合權重更新:")
        for particle_name, weight in self.fusion_weights.items():
            print(f"  {particle_name}: {weight:.2%}")
    
    def fuse_for_task(
        self,
        task_type: str,
        task_requirements: Dict[str, float]
    ) -> Dict[str, float]:
        """
        根據任務需求動態融合粒子
        
        Args:
            task_type: 任務類型（e.g., "code_generation", "mathematical_reasoning"）
            task_requirements: 需求權重 {"coding": 0.7, "reasoning": 0.3}
        
        Returns:
            optimized_fusion_weights
        """
        optimized_weights = {}
        
        for particle_name, particle in self.particles.items():
            capability = particle.capability_type.value
            base_weight = task_requirements.get(capability, 0.0)
            
            # 根據粒子性能調整權重
            performance_factor = particle.accuracy  # 準確率作為因子
            optimized_weights[particle_name] = base_weight * performance_factor
        
        # 正規化
        total = sum(optimized_weights.values())
        if total > 0:
            optimized_weights = {k: v / total for k, v in optimized_weights.items()}
        
        self.fusion_weights = optimized_weights
        
        # 記錄融合歷史
        self.fusion_history.append({
            "timestamp": datetime.now().isoformat(),
            "task_type": task_type,
            "requirements": task_requirements,
            "weights": optimized_weights
        })
        
        return optimized_weights
    
    def get_fusion_report(self) -> Dict:
        """獲取融合引擎的詳細報告"""
        return {
            "base_model": self.base_model_name,
            "registered_particles": {
                name: particle.to_dict()
                for name, particle in self.particles.items()
            },
            "current_fusion_weights": self.fusion_weights,
            "fusion_history_count": len(self.fusion_history),
            "total_particle_accuracy": sum(
                p.accuracy for p in self.particles.values()
            ) / max(len(self.particles), 1)
        }


# ============================================================================
# 5. 知識蒸餾訓練器
# ============================================================================

class MRL_Distillation_Trainer:
    """
    MRL 知識蒸餾訓練器 - 從教師模型學習
    
    流程：
    1. 從教師模型收集軟標籤
    2. 用學生模型進行訓練
    3. 監測性能保留率
    4. 保存為粒子
    """
    
    def __init__(
        self,
        student_model,
        teacher_model_api,
        distillation_loss: MRL_DistillationLoss,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.student_model = student_model
        self.teacher_model_api = teacher_model_api
        self.distillation_loss = distillation_loss
        self.device = device
        self.training_log = []
    
    def train_epoch(
        self,
        train_loader,
        optimizer,
        epoch: int
    ) -> Dict[str, float]:
        """訓練一個 epoch"""
        self.student_model.train()
        total_loss = 0
        
        for batch_idx, (inputs, true_labels) in enumerate(train_loader):
            inputs = inputs.to(self.device)
            true_labels = true_labels.to(self.device)
            
            # 從教師模型獲取軟標籤
            with torch.no_grad():
                teacher_outputs = self.teacher_model_api.get_logits(inputs)
                teacher_logits = torch.tensor(
                    teacher_outputs, device=self.device, dtype=torch.float32
                )
            
            # 學生模型前向傳播
            optimizer.zero_grad()
            student_outputs = self.student_model(inputs)
            
            # 計算蒸餾損失
            loss = self.distillation_loss(
                student_logits=student_outputs,
                teacher_logits=teacher_logits,
                true_labels=true_labels
            )
            
            # 反向傳播
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
            if (batch_idx + 1) % 10 == 0:
                print(f"Epoch {epoch}, Batch {batch_idx + 1}: Loss = {loss.item():.4f}")
        
        avg_loss = total_loss / len(train_loader)
        self.training_log.append({
            "epoch": epoch,
            "loss": avg_loss,
            "timestamp": datetime.now().isoformat()
        })
        
        return {"epoch": epoch, "avg_loss": avg_loss}
    
    def evaluate(self, eval_loader) -> Dict[str, float]:
        """評估學生模型性能"""
        self.student_model.eval()
        correct = 0
        total = 0
        
        with torch.no_grad():
            for inputs, labels in eval_loader:
                inputs = inputs.to(self.device)
                labels = labels.to(self.device)
                
                outputs = self.student_model(inputs)
                _, predicted = torch.max(outputs, 1)
                
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        
        accuracy = correct / total
        return {"accuracy": accuracy, "correct": correct, "total": total}


# ============================================================================
# 6. 粒子管理系統
# ============================================================================

class MRL_Particle_Manager:
    """
    MRL 粒子管理系統 - 生命週期管理
    
    功能：
    - 粒子註冊、版本控制
    - 粒子性能追蹤
    - 粒子依賴管理
    - 粒子更新與回滾
    """
    
    def __init__(self, storage_path: str = "./mrl_particles"):
        self.storage_path = storage_path
        self.particles_registry = {}
        self.particle_versions = {}
        self.performance_metrics = {}
    
    def save_particle(self, particle: MRL_Particle, path: str = None):
        """保存粒子定義"""
        if path is None:
            path = f"{self.storage_path}/{particle.name}.json"
        
        with open(path, 'w') as f:
            json.dump(particle.to_dict(), f, indent=2)
        
        # 記錄版本
        if particle.name not in self.particle_versions:
            self.particle_versions[particle.name] = []
        
        self.particle_versions[particle.name].append({
            "version": particle.version,
            "hash": particle.compute_hash(),
            "saved_at": datetime.now().isoformat()
        })
        
        print(f"✓ 粒子已保存: {particle.name} v{particle.version}")
    
    def load_particle(self, name: str, version: str = None) -> MRL_Particle:
        """載入粒子定義"""
        path = f"{self.storage_path}/{name}.json"
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        return MRL_Particle(
            name=data['name'],
            capability_type=MRL_Capability_Type(data['capability_type']),
            version=data['version'],
            base_model=data['base_model'],
            teacher_model=data['teacher_model'],
            lora_rank=data.get('lora_rank', 16),
            lora_alpha=data.get('lora_alpha', 32),
            distillation_temperature=data.get('distillation_temperature', 4.0),
            accuracy=data.get('accuracy', 0.0),
            inference_time_ms=data.get('inference_time_ms', 0.0),
            memory_mb=data.get('memory_mb', 0.0),
            created_at=data.get('created_at'),
            training_samples=data.get('training_samples', 0),
            training_epochs=data.get('training_epochs', 0)
        )
    
    def get_particle_status(self, particle_name: str) -> Dict:
        """獲取粒子狀態"""
        if particle_name not in self.particle_versions:
            return {"status": "not_found"}
        
        return {
            "name": particle_name,
            "versions": self.particle_versions[particle_name],
            "performance_metrics": self.performance_metrics.get(particle_name, {}),
            "total_versions": len(self.particle_versions[particle_name])
        }
    
    def list_all_particles(self) -> List[Dict]:
        """列出所有粒子"""
        return [
            {
                "name": name,
                "versions": self.particle_versions[name]
            }
            for name in self.particle_versions.keys()
        ]


# ============================================================================
# 7. 測試與演示
# ============================================================================

def demo_mrl_llm_framework():
    """MRL LLM 框架演示"""
    
    print("=" * 80)
    print("MRL LLM 框架演示 - 知識蒸餾與粒子融合")
    print("=" * 80)
    
    # 1. 創建粒子
    print("\n[1] 創建能力粒子...")
    
    reasoning_particle = MRL_Particle(
        name="Mr.liou.Particle.Reasoning.P19.v1",
        capability_type=MRL_Capability_Type.REASONING,
        version="1.0",
        base_model="Qwen2.5-32B-Instruct",
        teacher_model="Claude-3.5-Opus",
        lora_rank=16,
        lora_alpha=32,
        distillation_temperature=4.0,
        accuracy=0.85,
        inference_time_ms=250,
        memory_mb=12400,
        training_samples=10000,
        training_epochs=5
    )
    
    coding_particle = MRL_Particle(
        name="Mr.liou.Particle.Coding.P22.v1",
        capability_type=MRL_Capability_Type.CODING,
        version="1.0",
        base_model="Qwen2.5-32B-Instruct",
        teacher_model="GPT-4-Turbo",
        lora_rank=32,
        lora_alpha=64,
        distillation_temperature=3.0,
        accuracy=0.92,
        inference_time_ms=300,
        memory_mb=12800,
        training_samples=15000,
        training_epochs=8
    )
    
    print(f"✓ 推理粒子: {reasoning_particle.name}")
    print(f"  - 精度: {reasoning_particle.accuracy:.2%}")
    print(f"  - 延遲: {reasoning_particle.inference_time_ms}ms")
    
    print(f"✓ 編碼粒子: {coding_particle.name}")
    print(f"  - 精度: {coding_particle.accuracy:.2%}")
    print(f"  - 延遲: {coding_particle.inference_time_ms}ms")
    
    # 2. 初始化融合引擎
    print("\n[2] 初始化粒子融合引擎...")
    fusion_engine = MRL_Particle_Fusion_Engine(
        base_model_name="Qwen2.5-32B-Instruct"
    )
    
    # 註冊粒子
    fusion_engine.register_particle(reasoning_particle, MRL_LoRA_Adapter(4096, 4096, rank=16))
    fusion_engine.register_particle(coding_particle, MRL_LoRA_Adapter(4096, 4096, rank=32))
    
    # 3. 動態融合示例
    print("\n[3] 任務1: 數學問題求解（需要推理）")
    weights_math = fusion_engine.fuse_for_task(
        task_type="mathematical_reasoning",
        task_requirements={"reasoning": 0.8, "coding": 0.2}
    )
    
    print("\n[4] 任務2: 代碼生成（需要編碼）")
    weights_code = fusion_engine.fuse_for_task(
        task_type="code_generation",
        task_requirements={"reasoning": 0.2, "coding": 0.8}
    )
    
    # 4. 生成報告
    print("\n[5] 融合引擎報告:")
    report = fusion_engine.get_fusion_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    
    # 5. 知識蒸餾損失演示
    print("\n[6] 知識蒸餾損失函數:")
    distillation_loss = MRL_DistillationLoss(
        temperature=4.0,
        alpha=0.7,
        use_teacher_features=True
    )
    
    # 模擬數據
    batch_size, num_classes = 32, 10
    student_logits = torch.randn(batch_size, num_classes)
    teacher_logits = torch.randn(batch_size, num_classes)
    true_labels = torch.randint(0, num_classes, (batch_size,))
    
    loss = distillation_loss(
        student_logits=student_logits,
        teacher_logits=teacher_logits,
        true_labels=true_labels
    )
    
    print(f"✓ 蒸餾損失: {loss.item():.4f}")
    print(f"  - 溫度: 4.0（軟化標籤分佈）")
    print(f"  - Alpha: 0.7（70% 軟標籤, 30% 硬標籤）")
    
    print("\n" + "=" * 80)
    print("演示完成！")
    print("=" * 80)


if __name__ == "__main__":
    demo_mrl_llm_framework()
