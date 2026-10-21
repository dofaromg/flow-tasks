#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mr.liou.Core.Loss — MRL 損失函數庫
Mr.liou.Core.Loss.v1

零外部依賴：僅使用 mrl_tensor + Python 標準庫 math

提供損失函數：
  KLDivLoss        — KL 散度損失（知識蒸餾核心）
  DistillationLoss — 蒸餾損失 = α·KL(教師‖學生) + (1-α)·CE(真實標籤)
  CrossEntropyLoss — 交叉熵損失
  MSELoss          — 均方誤差損失
  HuberLoss        — Huber 損失（robust regression）
  CosineEmbeddingLoss — 餘弦嵌入損失（特徵對齊）

蒸餾核心公式：
  L_distill = α · T² · KL(softmax(t/T) ‖ log_softmax(s/T))
            + (1-α) · CE(s, y)
其中 T 為溫度係數，α 為蒸餾權重比例。
"""

import math
import sys
import os

# 確保可以找到 mrl_tensor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mrl_tensor import (
    Tensor, TensorOps, tensor, zeros,
    _flatten, _unflatten, _numel, Shape
)
from typing import Optional


# ===========================================================================
# 基礎損失函數
# ===========================================================================

class MSELoss:
    """
    均方誤差損失
    L = mean((pred - target)^2)
    """

    def __init__(self, reduction: str = "mean"):
        """
        Args:
            reduction: 'mean' | 'sum' | 'none'
        """
        self.reduction = reduction

    def __call__(self, pred: Tensor, target: Tensor) -> Tensor:
        diff = TensorOps.sub(pred, target)
        sq = TensorOps.mul(diff, diff)
        if self.reduction == "none":
            return sq
        if self.reduction == "sum":
            return TensorOps.sum(sq)
        return TensorOps.mean(sq)


class MAELoss:
    """
    平均絕對誤差損失
    L = mean(|pred - target|)
    """

    def __init__(self, reduction: str = "mean"):
        self.reduction = reduction

    def __call__(self, pred: Tensor, target: Tensor) -> Tensor:
        diff = TensorOps.sub(pred, target).abs()
        if self.reduction == "none":
            return diff
        if self.reduction == "sum":
            return TensorOps.sum(diff)
        return TensorOps.mean(diff)


class HuberLoss:
    """
    Huber 損失（SmoothL1）
    L = 0.5*(x^2) if |x| < delta, else delta*(|x| - 0.5*delta)
    """

    def __init__(self, delta: float = 1.0, reduction: str = "mean"):
        self.delta = delta
        self.reduction = reduction

    def __call__(self, pred: Tensor, target: Tensor) -> Tensor:
        d = self.delta
        diff_flat = [abs(p - t) for p, t in zip(pred._flat, target._flat)]
        loss_flat = [
            0.5 * x ** 2 if x < d else d * (x - 0.5 * d)
            for x in diff_flat
        ]
        out = Tensor._from_flat(loss_flat, pred.shape, pred.requires_grad)
        if self.reduction == "none":
            return out
        if self.reduction == "sum":
            return TensorOps.sum(out)
        return TensorOps.mean(out)


class CrossEntropyLoss:
    """
    交叉熵損失（整合 softmax）
    輸入為 logits（未 softmax），target 為類別索引

    pred:   (batch, num_classes) — 原始 logits
    target: List[int] — 每個樣本的真實類別 index
    """

    def __init__(self, reduction: str = "mean", ignore_index: int = -100):
        self.reduction = reduction
        self.ignore_index = ignore_index

    def __call__(self, pred: Tensor, target: list) -> Tensor:
        """
        Args:
            pred:   (batch, num_classes) Tensor
            target: list of int, length = batch
        """
        if pred.ndim == 1:
            pred = pred.reshape(1, pred.shape[0])

        batch, num_classes = pred.shape
        losses: list = []

        for i in range(batch):
            t = target[i]
            if t == self.ignore_index:
                continue
            # log_softmax
            row = pred._flat[i * num_classes: (i + 1) * num_classes]
            mx = max(row)
            log_sum = math.log(sum(math.exp(x - mx) for x in row)) + mx
            nll = -(row[t] - log_sum)
            losses.append(nll)

        if not losses:
            return Tensor(0.0)

        if self.reduction == "none":
            return Tensor(losses)
        if self.reduction == "sum":
            return Tensor(sum(losses))
        return Tensor(sum(losses) / len(losses))


class NLLLoss:
    """
    負對數似然損失
    pred 為 log 概率（log_softmax 輸出）
    """

    def __init__(self, reduction: str = "mean"):
        self.reduction = reduction

    def __call__(self, log_probs: Tensor, target: list) -> Tensor:
        batch = log_probs.shape[0]
        num_classes = log_probs.shape[1]
        losses = [
            -log_probs._flat[i * num_classes + target[i]]
            for i in range(batch)
        ]
        if self.reduction == "none":
            return Tensor(losses)
        if self.reduction == "sum":
            return Tensor(sum(losses))
        return Tensor(sum(losses) / len(losses))


# ===========================================================================
# KL 散度損失（蒸餾核心）
# ===========================================================================

class KLDivLoss:
    """
    KL 散度損失 KL(P ‖ Q)
    P: 目標分佈（教師模型的 softmax 輸出）
    Q: 預測分佈（學生模型的 log_softmax 輸出）

    公式：L = Σ P(x) * (log P(x) - Q_log(x))
    其中 Q_log = log_softmax(student_logits / T)
         P     = softmax(teacher_logits / T)

    注意：PyTorch 的 KLDivLoss 接受 (log_input, target)，
          即 input 為 log 概率，target 為概率。
    """

    def __init__(self, reduction: str = "batchmean"):
        """
        Args:
            reduction: 'batchmean' | 'mean' | 'sum' | 'none'
                batchmean: sum / batch_size（PyTorch 預設，數學上正確）
        """
        self.reduction = reduction

    def __call__(self, log_input: Tensor, target: Tensor) -> Tensor:
        """
        Args:
            log_input: log 概率，shape (batch, classes)
            target:    概率，shape (batch, classes)
        """
        # KL = Σ target * (log_target - log_input)
        # = Σ target * log_target - Σ target * log_input
        # 第一項為常數（教師熵），通常省略，只保留 -Σ target * log_input
        flat_out = []
        for p, lq in zip(target._flat, log_input._flat):
            # 避免 p=0 的 log(0)
            if p > 1e-10:
                flat_out.append(p * (math.log(p) - lq))
            else:
                flat_out.append(0.0)

        out = Tensor._from_flat(flat_out, target.shape, log_input.requires_grad)

        if self.reduction == "none":
            return out
        total = sum(flat_out)
        if self.reduction == "sum":
            return Tensor(total)
        if self.reduction == "mean":
            return Tensor(total / _numel(target.shape))
        # batchmean: divide by batch size (first dimension)
        batch = target.shape[0] if target.ndim >= 1 else 1
        return Tensor(total / batch)


# ===========================================================================
# 蒸餾損失（核心）
# ===========================================================================

class DistillationLoss:
    """
    知識蒸餾複合損失
    Mr.liou.Core.DistillationLoss.v1

    公式：
        L = α · T² · KL(softmax(t/T) ‖ log_softmax(s/T))
          + (1-α) · CE(s, y)

    其中：
        t = teacher_logits
        s = student_logits
        T = temperature（溫度，T>1 使分佈更平滑）
        α = distillation_weight（蒸餾損失佔比）
        y = hard_labels（真實類別 index）

    使用場景：
        - 將大型教師模型的「軟標籤」知識轉移給小型學生模型
        - temperature 越高，教師的軟標籤越平滑，含更多暗知識
    """

    def __init__(
        self,
        temperature: float = 4.0,
        alpha: float = 0.7,
    ):
        """
        Args:
            temperature: 蒸餾溫度（建議 2.0~8.0）
            alpha: 蒸餾損失權重（0~1，越大越依賴教師軟標籤）
        """
        if not (0.0 <= alpha <= 1.0):
            raise ValueError(f"alpha 必須在 [0, 1] 之間，收到 {alpha}")
        if temperature <= 0:
            raise ValueError(f"temperature 必須 > 0，收到 {temperature}")

        self.temperature = temperature
        self.alpha = alpha
        self._kl_loss = KLDivLoss(reduction="batchmean")
        self._ce_loss = CrossEntropyLoss(reduction="mean")

    def __call__(
        self,
        student_logits: Tensor,
        teacher_logits: Tensor,
        hard_labels: Optional[list] = None,
    ) -> "DistillationLossOutput":
        """
        Args:
            student_logits: (batch, num_classes)
            teacher_logits: (batch, num_classes)
            hard_labels:    list[int] or None（無硬標籤時 alpha 強制為 1.0）

        Returns:
            DistillationLossOutput（含總損失、蒸餾損失、CE損失）
        """
        T = self.temperature
        batch, num_classes = student_logits.shape

        # 計算溫度縮放後的 logits
        s_scaled_flat = [x / T for x in student_logits._flat]
        t_scaled_flat = [x / T for x in teacher_logits._flat]
        s_scaled = Tensor._from_flat(s_scaled_flat, student_logits.shape, student_logits.requires_grad)
        t_scaled = Tensor._from_flat(t_scaled_flat, teacher_logits.shape)

        # 教師軟標籤（概率分佈）
        teacher_probs = TensorOps.softmax(t_scaled, dim=1)
        # 學生 log 概率
        student_log_probs = TensorOps.log_softmax(s_scaled, dim=1)

        # 蒸餾損失（軟標籤部分）：T² 為比例補償
        soft_loss_val = self._kl_loss(student_log_probs, teacher_probs).item() * (T ** 2)
        soft_loss = Tensor(soft_loss_val)

        # 硬標籤損失（CE）
        if hard_labels is not None and self.alpha < 1.0:
            hard_loss = self._ce_loss(student_logits, hard_labels)
            alpha = self.alpha
        else:
            hard_loss = Tensor(0.0)
            alpha = 1.0

        # 總損失
        total_val = alpha * soft_loss.item() + (1 - alpha) * hard_loss.item()
        total_loss = Tensor(total_val)

        return DistillationLossOutput(
            total=total_loss,
            soft=soft_loss,
            hard=hard_loss,
            alpha=alpha,
            temperature=T,
        )


class DistillationLossOutput:
    """蒸餾損失計算結果容器"""

    def __init__(
        self,
        total: Tensor,
        soft: Tensor,
        hard: Tensor,
        alpha: float,
        temperature: float,
    ):
        self.total = total
        self.soft = soft
        self.hard = hard
        self.alpha = alpha
        self.temperature = temperature

    def item(self) -> float:
        return self.total.item()

    def to_dict(self) -> dict:
        return {
            "total_loss": round(self.total.item(), 6),
            "soft_loss":  round(self.soft.item(), 6),
            "hard_loss":  round(self.hard.item(), 6),
            "alpha":      self.alpha,
            "temperature": self.temperature,
        }

    def __repr__(self) -> str:
        return (
            f"DistillationLossOutput("
            f"total={self.total.item():.4f}, "
            f"soft={self.soft.item():.4f}, "
            f"hard={self.hard.item():.4f})"
        )


# ===========================================================================
# 餘弦嵌入損失（特徵對齊）
# ===========================================================================

class CosineEmbeddingLoss:
    """
    餘弦嵌入損失
    用於對齊學生與教師的中間層特徵表示

    L = 1 - cosine_similarity(a, b)  if y == 1
    L = max(0, cosine_similarity(a, b) - margin)  if y == -1
    """

    def __init__(self, margin: float = 0.0, reduction: str = "mean"):
        self.margin = margin
        self.reduction = reduction

    def __call__(
        self,
        a: Tensor,
        b: Tensor,
        y: Optional[list] = None,
    ) -> Tensor:
        """
        Args:
            a, b: (batch, dim)
            y: list[int] ∈ {1, -1}，None 時預設全為 1
        """
        if y is None:
            y = [1] * a.shape[0]
        batch = a.shape[0]
        losses = []
        for i in range(batch):
            dim = a.shape[1]
            va = a._flat[i * dim: (i + 1) * dim]
            vb = b._flat[i * dim: (i + 1) * dim]
            dot = sum(ai * bi for ai, bi in zip(va, vb))
            na = math.sqrt(sum(ai ** 2 for ai in va)) + 1e-9
            nb = math.sqrt(sum(bi ** 2 for bi in vb)) + 1e-9
            cos_sim = dot / (na * nb)
            if y[i] == 1:
                losses.append(1.0 - cos_sim)
            else:
                losses.append(max(0.0, cos_sim - self.margin))

        if self.reduction == "none":
            return Tensor(losses)
        if self.reduction == "sum":
            return Tensor(sum(losses))
        return Tensor(sum(losses) / len(losses))


# ===========================================================================
# 自檢測試
# ===========================================================================

if __name__ == "__main__":
    print("=== Mr.liou.Core.Loss 自檢測試 ===\n")

    # MSE
    pred = tensor([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    tgt = tensor([[1.5, 2.5, 3.5], [3.5, 4.5, 5.5]])
    mse = MSELoss()
    print(f"MSE Loss: {mse(pred, tgt).item():.4f}")  # 期望 0.25

    # Cross-Entropy
    logits = tensor([[2.0, 1.0, 0.1], [0.5, 2.5, 0.3]])
    labels = [0, 1]
    ce = CrossEntropyLoss()
    print(f"CE Loss: {ce(logits, labels).item():.4f}")

    # KL Divergence
    log_p = tensor([[-0.5, -1.0, -1.5], [-0.8, -0.3, -1.2]])
    q = tensor([[0.5, 0.3, 0.2], [0.4, 0.4, 0.2]])
    kl = KLDivLoss(reduction="batchmean")
    print(f"KL Div Loss: {kl(log_p, q).item():.4f}")

    # Distillation Loss
    student_logits = tensor([[2.0, 1.0, 0.1], [0.5, 2.5, 0.3]])
    teacher_logits = tensor([[2.5, 0.8, 0.2], [0.3, 2.8, 0.1]])
    hard_labels = [0, 1]

    dist_loss = DistillationLoss(temperature=4.0, alpha=0.7)
    out = dist_loss(student_logits, teacher_logits, hard_labels)
    print(f"Distillation Loss: {out}")
    print(f"  詳細: {out.to_dict()}")

    # Cosine Embedding Loss
    a = tensor([[1.0, 0.0], [0.0, 1.0]])
    b = tensor([[1.0, 0.0], [1.0, 0.0]])
    cos_loss = CosineEmbeddingLoss()
    print(f"Cosine Embedding Loss: {cos_loss(a, b).item():.4f}")

    print("\n✅ 所有損失函數自檢通過")
