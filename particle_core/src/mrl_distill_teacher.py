#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mr.liou.Distill.Teacher — 教師模型抽象介面
Mr.liou.Distill.Teacher.v1

零外部依賴設計：
  - 定義純抽象的「教師介面」，與任何外部 API 解耦
  - 提供多種實現：本地 GGUF、subprocess、Mock、Ensemble
  - 支援異步/批次推理
  - 完全移除對 anthropic / openai / requests 的依賴

架構：
  TeacherInterface      — 抽象基類（協議介面）
  LocalGGUFTeacher      — 本地 llama.cpp GGUF 模型教師
  SubprocessTeacher     — 透過 subprocess 調用外部命令
  MockTeacher           — 測試用 Mock 教師（零依賴，完全本地）
  EnsembleTeacher       — 多教師模型集成
  TeacherFactory        — 教師模型工廠

蒸餾協議：
  教師模型輸出 logits（或 token 概率分佈）
  學生模型學習此軟標籤分佈（而非硬標籤）
"""

import os
import sys
import json
import math
import random
import subprocess
import threading
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mrl_tensor import Tensor, TensorOps, Initializer, tensor, randn


# ===========================================================================
# 抽象教師介面
# ===========================================================================

class TeacherInterface(ABC):
    """
    Mr.liou.Distill.TeacherInterface

    所有教師模型的抽象基類。
    子類只需實現 _generate_logits() 方法。
    """

    def __init__(self, model_name: str, num_classes: int = 32000):
        self.model_name = model_name
        self.num_classes = num_classes
        self._call_count = 0
        self._total_time_ms = 0.0
        self._is_ready = False

    @abstractmethod
    def _generate_logits(self, inputs: List[str]) -> List[List[float]]:
        """
        核心推理方法（子類必須實現）

        Args:
            inputs: 文本輸入列表（batch）

        Returns:
            每個輸入對應的 logits 列表，shape: (batch, num_classes)
        """
        ...

    def get_logits(self, inputs: List[str]) -> Tensor:
        """
        獲取教師模型的 logits（Tensor 格式）

        Args:
            inputs: 輸入文本列表

        Returns:
            logits Tensor, shape: (batch, num_classes)
        """
        import time
        t0 = time.perf_counter()

        raw = self._generate_logits(inputs)

        elapsed_ms = (time.perf_counter() - t0) * 1000
        self._call_count += 1
        self._total_time_ms += elapsed_ms

        # 轉換為 Tensor
        flat = []
        for row in raw:
            flat.extend(row)
        return Tensor._from_flat(flat, (len(raw), self.num_classes))

    def get_soft_labels(
        self,
        inputs: List[str],
        temperature: float = 4.0,
    ) -> Tensor:
        """
        獲取溫度縮放後的軟標籤（softmax 概率分佈）

        Args:
            inputs:      輸入文本列表
            temperature: 蒸餾溫度

        Returns:
            概率分佈 Tensor, shape: (batch, num_classes)
        """
        logits = self.get_logits(inputs)
        # 溫度縮放
        scaled_flat = [x / temperature for x in logits._flat]
        scaled = Tensor._from_flat(scaled_flat, logits.shape)
        # Softmax
        return TensorOps.softmax(scaled, dim=1)

    def get_stats(self) -> Dict:
        """返回調用統計"""
        return {
            "model_name": self.model_name,
            "call_count": self._call_count,
            "avg_time_ms": round(
                self._total_time_ms / max(self._call_count, 1), 2
            ),
            "total_time_ms": round(self._total_time_ms, 2),
            "is_ready": self._is_ready,
        }

    def is_available(self) -> bool:
        """檢查教師模型是否可用"""
        return self._is_ready

    def warmup(self, n_calls: int = 1):
        """預熱教師模型"""
        dummy = ["warmup"] * n_calls
        self._generate_logits(dummy)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model='{self.model_name}', classes={self.num_classes})"


# ===========================================================================
# MockTeacher — 完全本地、零依賴（測試 / 開發用）
# ===========================================================================

class MockTeacher(TeacherInterface):
    """
    Mr.liou.Distill.MockTeacher

    完全本地的 Mock 教師模型，不依賴任何外部資源。
    用途：
      - 單元測試
      - 沒有 GPU 的開發環境
      - CI/CD 流水線中的快速驗證

    可配置：
      - 固定輸出（deterministic）
      - 隨機輸出（模擬真實分佈）
      - 基於 hash 的確定性輸出（輸入相同 → 輸出相同）
    """

    def __init__(
        self,
        model_name: str = "Mr.liou.Teacher.Mock.v1",
        num_classes: int = 32000,
        mode: str = "hash",       # "hash" | "random" | "fixed"
        fixed_class: Optional[int] = None,
        seed: Optional[int] = None,
        noise_std: float = 1.0,
    ):
        """
        Args:
            mode:        "hash"（確定性）| "random"（隨機）| "fixed"（固定類別）
            fixed_class: mode="fixed" 時高亮的類別 index
            seed:        隨機種子
            noise_std:   logits 雜訊標準差
        """
        super().__init__(model_name, num_classes)
        self.mode = mode
        self.fixed_class = fixed_class
        self.noise_std = noise_std
        self._rng = random.Random(seed)
        self._is_ready = True

    def _generate_logits(self, inputs: List[str]) -> List[List[float]]:
        results = []
        for text in inputs:
            if self.mode == "fixed":
                target = self.fixed_class or 0
                logits = [self._rng.gauss(0, self.noise_std) for _ in range(self.num_classes)]
                logits[target] += 5.0  # 讓目標類別突出
            elif self.mode == "hash":
                # 基於輸入 hash 生成確定性 logits
                import hashlib
                seed_val = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
                rng = random.Random(seed_val)
                logits = [rng.gauss(0, self.noise_std) for _ in range(self.num_classes)]
                # 讓 hash 的前幾個字節對應的類別稍微突出
                dominant = seed_val % self.num_classes
                logits[dominant] += 3.0
            else:  # random
                logits = [self._rng.gauss(0, self.noise_std) for _ in range(self.num_classes)]
            results.append(logits)
        return results


# ===========================================================================
# LocalGGUFTeacher — 本地 GGUF 模型（llama.cpp 後端）
# ===========================================================================

class LocalGGUFTeacher(TeacherInterface):
    """
    Mr.liou.Distill.LocalGGUFTeacher

    透過 llama.cpp 運行本地 GGUF 模型作為教師。
    依賴：llama-cpp-python（可選，若未安裝則降級至 subprocess 模式）

    GGUF 格式支援的模型：
      - Qwen2.5（推薦，與 MRL 架構對齊）
      - LLaMA 3.x
      - Mistral / Mixtral
      - 任何 llama.cpp 支援的格式
    """

    def __init__(
        self,
        model_path: str,
        num_classes: int = 32000,
        n_ctx: int = 2048,
        n_gpu_layers: int = 0,       # 0=CPU only
        n_threads: Optional[int] = None,
        verbose: bool = False,
    ):
        """
        Args:
            model_path:   GGUF 模型文件路徑
            n_ctx:        上下文窗口大小
            n_gpu_layers: GPU 層數（0 = 純 CPU）
            n_threads:    CPU 線程數（None = 自動）
        """
        model_name = os.path.basename(model_path)
        super().__init__(model_name, num_classes)
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.n_threads = n_threads or max(1, os.cpu_count() - 1)
        self.verbose = verbose
        self._llm = None
        self._load_lock = threading.Lock()

    def _load_model(self):
        """延遲載入模型"""
        if self._llm is not None:
            return

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"GGUF 模型未找到: {self.model_path}")

        with self._load_lock:
            if self._llm is not None:
                return
            try:
                from llama_cpp import Llama  # type: ignore[import-untyped]  # llama_cpp 無官方 stub
                self._llm = Llama(
                    model_path=self.model_path,
                    n_ctx=self.n_ctx,
                    n_gpu_layers=self.n_gpu_layers,
                    n_threads=self.n_threads,
                    verbose=self.verbose,
                    logits_all=True,
                )
                self._is_ready = True
            except ImportError:
                raise RuntimeError(
                    "llama-cpp-python 未安裝。\n"
                    "安裝方式: pip install llama-cpp-python\n"
                    "或使用 MockTeacher 進行無依賴測試"
                )

    def _generate_logits(self, inputs: List[str]) -> List[List[float]]:
        self._load_model()
        results = []
        for text in inputs:
            # 獲取最後 token 的 logits
            tokens = self._llm.tokenize(text.encode())
            self._llm.reset()
            self._llm.eval(tokens)
            logits_raw = list(self._llm.eval_logits[-1])
            # 裁剪或填充到 num_classes
            if len(logits_raw) >= self.num_classes:
                logits = logits_raw[:self.num_classes]
            else:
                logits = logits_raw + [0.0] * (self.num_classes - len(logits_raw))
            results.append(logits)
        return results

    def is_available(self) -> bool:
        if not os.path.exists(self.model_path):
            return False
        try:
            import llama_cpp  # type: ignore  # noqa: F401
            return True
        except ImportError:
            return False


# ===========================================================================
# SubprocessTeacher — 透過 subprocess 調用外部推理命令
# ===========================================================================

class SubprocessTeacher(TeacherInterface):
    """
    Mr.liou.Distill.SubprocessTeacher

    透過 subprocess 調用任意外部命令獲取 logits。
    適合：
      - 呼叫 Python 以外的推理引擎（C++, Rust 等）
      - 呼叫本地部署的 ollama / vllm CLI
      - 自定義推理腳本

    協議：
      stdin:  JSON 行格式 {"inputs": ["text1", "text2"]}
      stdout: JSON 行格式 {"logits": [[...], [...]]}
    """

    def __init__(
        self,
        command: List[str],
        model_name: str = "subprocess-teacher",
        num_classes: int = 32000,
        timeout: float = 30.0,
        env: Optional[Dict[str, str]] = None,
    ):
        """
        Args:
            command: 子進程命令列表，例如 ["python", "my_teacher.py"]
            timeout: 超時時間（秒）
        """
        super().__init__(model_name, num_classes)
        self.command = command
        self.timeout = timeout
        self.env = {**os.environ, **(env or {})}
        self._is_ready = True

    def _generate_logits(self, inputs: List[str]) -> List[List[float]]:
        request = json.dumps({"inputs": inputs}, ensure_ascii=False)
        try:
            result = subprocess.run(
                self.command,
                input=request,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=self.env,
            )
            if result.returncode != 0:
                raise RuntimeError(f"子進程錯誤: {result.stderr}")
            response = json.loads(result.stdout.strip())
            logits = response.get("logits", [])
            if not logits:
                raise ValueError("子進程未返回 logits")
            return logits
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"子進程超時 ({self.timeout}s)")


# ===========================================================================
# EnsembleTeacher — 多教師集成
# ===========================================================================

class EnsembleTeacher(TeacherInterface):
    """
    Mr.liou.Distill.EnsembleTeacher

    集成多個教師模型，透過加權平均合併 logits。
    「多教師蒸餾」可提升學生模型品質。
    """

    def __init__(
        self,
        teachers: List[Tuple[TeacherInterface, float]],
        model_name: str = "Mr.liou.Teacher.Ensemble.v1",
        aggregate: str = "weighted_mean",  # "weighted_mean" | "max"
    ):
        """
        Args:
            teachers:  [(teacher, weight), ...]
            aggregate: 合併方式
        """
        # 確定 num_classes（取所有教師的最小值）
        num_classes = min(t.num_classes for t, _ in teachers)
        super().__init__(model_name, num_classes)
        self.teachers = teachers
        self.aggregate = aggregate
        # 正規化權重
        total_w = sum(w for _, w in teachers)
        self._normalized_weights = [w / total_w for _, w in teachers]
        self._is_ready = all(t.is_available() for t, _ in teachers)

    def _generate_logits(self, inputs: List[str]) -> List[List[float]]:
        all_logits = []
        for teacher, _ in self.teachers:
            raw = teacher._generate_logits(inputs)
            all_logits.append(raw)

        batch = len(inputs)
        results = []
        for i in range(batch):
            if self.aggregate == "max":
                combined = [0.0] * self.num_classes
                for teacher_logits in all_logits:
                    for j in range(self.num_classes):
                        combined[j] = max(combined[j], teacher_logits[i][j])
            else:  # weighted_mean
                combined = [0.0] * self.num_classes
                for k, (teacher_logits, w) in enumerate(zip(all_logits, self._normalized_weights)):
                    row = teacher_logits[i]
                    for j in range(self.num_classes):
                        combined[j] += w * row[j]
            results.append(combined)
        return results

    def get_stats(self) -> Dict:
        stats = super().get_stats()
        stats["ensemble_teachers"] = [
            {"name": t.model_name, "weight": w, **t.get_stats()}
            for t, w in self.teachers
        ]
        return stats


# ===========================================================================
# TeacherFactory — 工廠函數
# ===========================================================================

class TeacherFactory:
    """
    Mr.liou.Distill.TeacherFactory

    根據配置自動選擇最佳可用的教師模型。
    選擇順序：LocalGGUF → Subprocess → Mock（最終 fallback）
    """

    @staticmethod
    def create(
        model_name: str = "auto",
        gguf_path: Optional[str] = None,
        subprocess_cmd: Optional[List[str]] = None,
        num_classes: int = 32000,
        force_mock: bool = False,
        mock_mode: str = "hash",
        mock_seed: Optional[int] = None,
    ) -> TeacherInterface:
        """
        自動選擇並建立教師模型

        Args:
            model_name:      模型名稱（用於標識）
            gguf_path:       本地 GGUF 模型路徑（若有）
            subprocess_cmd:  子進程命令（若有）
            num_classes:     分類數量
            force_mock:      強制使用 Mock 教師
            mock_mode:       Mock 模式
            mock_seed:       Mock 隨機種子

        Returns:
            最佳可用的 TeacherInterface 實例
        """
        if force_mock:
            return MockTeacher(
                model_name=model_name,
                num_classes=num_classes,
                mode=mock_mode,
                seed=mock_seed,
            )

        # 嘗試本地 GGUF
        if gguf_path:
            teacher = LocalGGUFTeacher(
                model_path=gguf_path,
                num_classes=num_classes,
            )
            if teacher.is_available():
                return teacher

        # 嘗試 subprocess
        if subprocess_cmd:
            return SubprocessTeacher(
                command=subprocess_cmd,
                model_name=model_name,
                num_classes=num_classes,
            )

        # Fallback: Mock（開發/測試模式）
        return MockTeacher(
            model_name=f"Mock({model_name})",
            num_classes=num_classes,
            mode=mock_mode,
            seed=mock_seed,
        )

    @staticmethod
    def create_ensemble(
        configs: List[Dict],
        num_classes: int = 32000,
    ) -> EnsembleTeacher:
        """
        建立集成教師模型

        Args:
            configs: [{"gguf_path": ..., "weight": 1.0, ...}, ...]
        """
        teachers = []
        for cfg in configs:
            weight = cfg.pop("weight", 1.0)
            t = TeacherFactory.create(num_classes=num_classes, **cfg)
            teachers.append((t, weight))
        return EnsembleTeacher(teachers, num_classes=num_classes)


# ===========================================================================
# 蒸餾資料集輔助工具
# ===========================================================================

class DistillationDataset:
    """
    蒸餾訓練資料集輔助器

    自動批次調用教師模型獲取軟標籤，
    並整合至訓練管線。
    """

    def __init__(
        self,
        teacher: TeacherInterface,
        temperature: float = 4.0,
        batch_size: int = 16,
    ):
        self.teacher = teacher
        self.temperature = temperature
        self.batch_size = batch_size
        self._cache: Dict[str, List[float]] = {}  # 軟標籤快取

    def get_soft_labels_batch(
        self,
        texts: List[str],
        use_cache: bool = True,
    ) -> Tensor:
        """
        批次獲取軟標籤

        Args:
            texts:     輸入文本列表
            use_cache: 是否快取結果

        Returns:
            softmax 概率分佈 Tensor, shape (batch, num_classes)
        """
        uncached = []
        uncached_idx = []
        results: List[Optional[List[float]]] = [None] * len(texts)

        # 查快取
        for i, text in enumerate(texts):
            if use_cache and text in self._cache:
                results[i] = self._cache[text]
            else:
                uncached.append(text)
                uncached_idx.append(i)

        # 批次推理未快取的
        if uncached:
            for start in range(0, len(uncached), self.batch_size):
                batch = uncached[start: start + self.batch_size]
                soft = self.teacher.get_soft_labels(batch, self.temperature)
                n = len(batch)
                nc = self.teacher.num_classes
                for j in range(n):
                    idx = uncached_idx[start + j]
                    row = soft._flat[j * nc: (j + 1) * nc]
                    results[idx] = row
                    if use_cache:
                        self._cache[uncached[start + j]] = row

        # 組合結果
        flat = []
        for r in results:
            flat.extend(r)
        return Tensor._from_flat(flat, (len(texts), self.teacher.num_classes))

    def clear_cache(self):
        self._cache.clear()

    def cache_size(self) -> int:
        return len(self._cache)


# ===========================================================================
# 自檢測試
# ===========================================================================

if __name__ == "__main__":
    print("=== Mr.liou.Distill.Teacher 自檢測試 ===\n")

    # --- 1. MockTeacher ---
    print("1. MockTeacher（hash 模式）")
    mock = MockTeacher(num_classes=10, mode="hash", seed=42)
    inputs = ["推理任務：A > B, B > C，則 A 和 C 的關係？", "寫一個 Python 排序函數"]
    logits = mock.get_logits(inputs)
    print(f"   logits shape: {logits.shape}")
    soft = mock.get_soft_labels(inputs, temperature=4.0)
    print(f"   soft labels shape: {soft.shape}")
    # 驗證概率總和 ≈ 1
    for i in range(2):
        row_sum = sum(soft._flat[i * 10: (i + 1) * 10])
        print(f"   行 {i} 概率總和: {row_sum:.6f}")

    # --- 2. MockTeacher（固定類別模式）---
    print("\n2. MockTeacher（fixed 模式）")
    fixed = MockTeacher(num_classes=5, mode="fixed", fixed_class=2)
    logits2 = fixed.get_logits(["test"])
    print(f"   logits: {[round(x, 2) for x in logits2._flat[:5]]}")

    # --- 3. EnsembleTeacher ---
    print("\n3. EnsembleTeacher（2 個 Mock 集成）")
    t1 = MockTeacher(num_classes=10, mode="hash", seed=1)
    t2 = MockTeacher(num_classes=10, mode="random", seed=2)
    ensemble = EnsembleTeacher([(t1, 0.7), (t2, 0.3)])
    ens_logits = ensemble.get_logits(["集成測試"])
    print(f"   集成輸出 shape: {ens_logits.shape}")

    # --- 4. TeacherFactory ---
    print("\n4. TeacherFactory（auto 選擇）")
    teacher = TeacherFactory.create(
        model_name="Mr.liou.Teacher.Demo.v1",
        num_classes=10,
        force_mock=True,
        mock_mode="hash",
    )
    print(f"   選擇的教師: {teacher}")
    print(f"   可用: {teacher.is_available()}")

    # --- 5. DistillationDataset ---
    print("\n5. DistillationDataset（快取軟標籤）")
    dataset = DistillationDataset(teacher, temperature=4.0, batch_size=4)
    texts = ["文本A", "文本B", "文本C"]
    soft_batch = dataset.get_soft_labels_batch(texts)
    print(f"   批次軟標籤 shape: {soft_batch.shape}")

    # 二次調用（使用快取）
    soft_cached = dataset.get_soft_labels_batch(texts)
    print(f"   快取大小: {dataset.cache_size()}")
    assert soft_batch._flat == soft_cached._flat, "快取結果不一致"

    # --- 6. 統計 ---
    print("\n6. 調用統計")
    stats = teacher.get_stats()
    print(f"   調用次數: {stats['call_count']}")
    print(f"   平均時間: {stats['avg_time_ms']} ms")

    print("\n✅ 所有教師模型自檢通過")
