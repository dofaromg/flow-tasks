#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mr.liou.Core.Tensor — 純 Python 張量引擎
Mr.liou.Core.Tensor.v1

零外部依賴：僅使用 Python 標準庫（math, random, array, functools）

架構：
  Tensor — 多維浮點數容器（list-of-lists），支援自動梯度追蹤
  TensorOps — 靜態張量運算（矩陣乘法、廣播、激活函數等）
  Initializer — 權重初始化策略（Xavier/Kaiming/Normal/Zeros/Ones）

設計原則：
  - API 與 torch.Tensor 命名習慣對齊，便於未來無縫切換
  - 所有計算在純 Python 中完成，可直接在標準 Python 環境執行
  - 梯度追蹤採用靜態計算圖（存儲反向函數）
"""

import math
import random
import copy
from typing import (
    Any, Callable, Dict, List, Optional, Sequence, Tuple, Union
)
from functools import reduce


# ---------------------------------------------------------------------------
# 型別別名
# ---------------------------------------------------------------------------
Shape = Tuple[int, ...]
Flat = List[float]


# ===========================================================================
# 核心工具函數
# ===========================================================================

def _shape_of(data: Any) -> Shape:
    """遞歸推導巢狀列表的形狀"""
    if not isinstance(data, list):
        return ()
    if not data:
        return (0,)
    return (len(data),) + _shape_of(data[0])


def _flatten(data: Any) -> Flat:
    """遞歸展平巢狀列表至一維"""
    if not isinstance(data, list):
        return [float(data)]
    result: Flat = []
    for item in data:
        result.extend(_flatten(item))
    return result


def _unflatten(flat: Flat, shape: Shape) -> Any:
    """從一維列表重建指定形狀的巢狀列表"""
    if len(shape) == 0:
        return flat[0]
    if len(shape) == 1:
        return flat[:shape[0]]
    stride = reduce(lambda a, b: a * b, shape[1:], 1)
    return [
        _unflatten(flat[i * stride: (i + 1) * stride], shape[1:])
        for i in range(shape[0])
    ]


def _numel(shape: Shape) -> int:
    """計算總元素數"""
    if not shape:
        return 1
    return reduce(lambda a, b: a * b, shape, 1)


def _broadcast_shapes(s1: Shape, s2: Shape) -> Shape:
    """計算廣播後的形狀（NumPy 語意）"""
    if len(s1) < len(s2):
        s1 = (1,) * (len(s2) - len(s1)) + s1
    elif len(s2) < len(s1):
        s2 = (1,) * (len(s1) - len(s2)) + s2
    out = []
    for a, b in zip(s1, s2):
        if a == b:
            out.append(a)
        elif a == 1:
            out.append(b)
        elif b == 1:
            out.append(a)
        else:
            raise ValueError(f"廣播形狀不相容：{s1} 與 {s2}")
    return tuple(out)


def _broadcast_flat(flat: Flat, src_shape: Shape, dst_shape: Shape) -> Flat:
    """將 flat 資料廣播至 dst_shape 後返回新的 flat"""
    if src_shape == dst_shape:
        return list(flat)
    # Pad src_shape with leading 1s
    padded = (1,) * (len(dst_shape) - len(src_shape)) + src_shape
    # Rebuild nested then expand
    data = _unflatten(flat, padded)
    expanded = _expand_to(data, padded, dst_shape)
    return _flatten(expanded)


def _expand_to(data: Any, src_shape: Shape, dst_shape: Shape) -> Any:
    """遞歸廣播巢狀列表"""
    if not src_shape:
        return data
    s, d = src_shape[0], dst_shape[0]
    if s == d:
        return [_expand_to(data[i], src_shape[1:], dst_shape[1:]) for i in range(d)]
    elif s == 1:
        inner = _expand_to(data[0], src_shape[1:], dst_shape[1:])
        return [copy.deepcopy(inner) for _ in range(d)]
    else:
        raise ValueError(f"無法廣播維度 {s} → {d}")


# ===========================================================================
# Tensor 類別
# ===========================================================================

class Tensor:
    """
    Mr.liou.Core.Tensor — MRL 核心張量類別

    屬性：
        data  : 巢狀 List[float]，存儲實際數值
        shape : 張量形狀 Tuple[int, ...]
        grad  : 梯度（相同形狀的 Tensor 或 None）
        requires_grad : 是否追蹤梯度
        _backward_fn  : 反向傳播函數（內部使用）
    """

    __slots__ = ("_flat", "shape", "grad", "requires_grad", "_backward_fn", "_prev")

    def __init__(
        self,
        data: Any,
        requires_grad: bool = False,
    ):
        if isinstance(data, Tensor):
            self._flat = list(data._flat)
            self.shape = data.shape
        elif isinstance(data, list):
            self.shape = _shape_of(data)
            self._flat = _flatten(data)
        elif isinstance(data, (int, float)):
            self.shape = ()
            self._flat = [float(data)]
        else:
            raise TypeError(f"不支援的資料類型：{type(data)}")

        self.grad: Optional["Tensor"] = None
        self.requires_grad = requires_grad
        self._backward_fn: Optional[Callable[[], None]] = None
        self._prev: List["Tensor"] = []

    # -----------------------------------------------------------------------
    # 基本屬性
    # -----------------------------------------------------------------------

    @property
    def data(self) -> Any:
        """以巢狀 list 形式返回資料"""
        if not self.shape:
            return self._flat[0]
        return _unflatten(self._flat, self.shape)

    @property
    def ndim(self) -> int:
        return len(self.shape)

    def numel(self) -> int:
        return _numel(self.shape)

    def item(self) -> float:
        """標量張量轉 Python float"""
        if self.numel() != 1:
            raise RuntimeError("item() 僅適用於單元素張量")
        return self._flat[0]

    # -----------------------------------------------------------------------
    # 複製與轉換
    # -----------------------------------------------------------------------

    def clone(self) -> "Tensor":
        t = Tensor.__new__(Tensor)
        t._flat = list(self._flat)
        t.shape = self.shape
        t.grad = None
        t.requires_grad = self.requires_grad
        t._backward_fn = None
        t._prev = []
        return t

    def detach(self) -> "Tensor":
        """返回不帶梯度的副本"""
        t = self.clone()
        t.requires_grad = False
        return t

    def tolist(self) -> Any:
        return self.data

    def reshape(self, *shape: int) -> "Tensor":
        new_shape = tuple(shape)
        if _numel(new_shape) != self.numel():
            raise ValueError(f"reshape：元素總數不符 {self.shape} → {new_shape}")
        t = Tensor.__new__(Tensor)
        t._flat = list(self._flat)
        t.shape = new_shape
        t.grad = None
        t.requires_grad = self.requires_grad
        t._backward_fn = None
        t._prev = []
        return t

    def view(self, *shape: int) -> "Tensor":
        return self.reshape(*shape)

    def flatten(self) -> "Tensor":
        return self.reshape(self.numel())

    def T(self) -> "Tensor":
        """2D 轉置"""
        if self.ndim != 2:
            raise RuntimeError("T() 僅支援 2D 張量")
        rows, cols = self.shape
        flat = [self._flat[j * cols + i] for i in range(cols) for j in range(rows)]
        t = Tensor.__new__(Tensor)
        t._flat = flat
        t.shape = (cols, rows)
        t.grad = None
        t.requires_grad = self.requires_grad
        t._backward_fn = None
        t._prev = []
        return t

    # -----------------------------------------------------------------------
    # 梯度操作
    # -----------------------------------------------------------------------

    def zero_grad(self):
        """清除梯度"""
        self.grad = None

    def backward(self, grad: Optional["Tensor"] = None):
        """反向傳播（純靜態計算圖）"""
        if grad is None:
            if self.numel() != 1:
                raise RuntimeError("backward() 非標量張量需要提供 grad 參數")
            grad = Tensor([1.0])

        # 累積梯度
        if self.requires_grad:
            if self.grad is None:
                self.grad = grad.clone()
            else:
                self.grad = TensorOps.add(self.grad, grad)

        # 呼叫反向函數
        if self._backward_fn is not None:
            self._backward_fn()

    def _accumulate_grad(self, g: "Tensor"):
        if self.grad is None:
            self.grad = g.clone()
        else:
            self.grad = TensorOps.add(self.grad, g)

    # -----------------------------------------------------------------------
    # 算術運算（支援 Tensor / float / int）
    # -----------------------------------------------------------------------

    def __add__(self, other: Union["Tensor", float, int]) -> "Tensor":
        return TensorOps.add(self, _to_tensor(other))

    def __radd__(self, other: Union[float, int]) -> "Tensor":
        return TensorOps.add(_to_tensor(other), self)

    def __sub__(self, other: Union["Tensor", float, int]) -> "Tensor":
        return TensorOps.sub(self, _to_tensor(other))

    def __rsub__(self, other: Union[float, int]) -> "Tensor":
        return TensorOps.sub(_to_tensor(other), self)

    def __mul__(self, other: Union["Tensor", float, int]) -> "Tensor":
        return TensorOps.mul(self, _to_tensor(other))

    def __rmul__(self, other: Union[float, int]) -> "Tensor":
        return TensorOps.mul(_to_tensor(other), self)

    def __truediv__(self, other: Union["Tensor", float, int]) -> "Tensor":
        return TensorOps.div(self, _to_tensor(other))

    def __neg__(self) -> "Tensor":
        return TensorOps.mul(self, Tensor(-1.0))

    def __matmul__(self, other: "Tensor") -> "Tensor":
        return TensorOps.matmul(self, other)

    def __repr__(self) -> str:
        return f"Tensor(shape={self.shape}, requires_grad={self.requires_grad})"

    def __len__(self) -> int:
        if not self.shape:
            raise TypeError("0-d 張量無長度")
        return self.shape[0]

    # -----------------------------------------------------------------------
    # 索引（唯讀）
    # -----------------------------------------------------------------------

    def __getitem__(self, idx: Any) -> "Tensor":
        if self.ndim == 0:
            raise IndexError("0-d 張量不支援索引")
        if isinstance(idx, int):
            stride = _numel(self.shape[1:]) if self.ndim > 1 else 1
            new_flat = self._flat[idx * stride: (idx + 1) * stride]
            new_shape = self.shape[1:]
            t = Tensor.__new__(Tensor)
            t._flat = new_flat
            t.shape = new_shape if new_shape else ()
            t.grad = None
            t.requires_grad = self.requires_grad
            t._backward_fn = None
            t._prev = []
            return t
        raise NotImplementedError("目前僅支援整數索引")

    # -----------------------------------------------------------------------
    # 統計方法
    # -----------------------------------------------------------------------

    def sum(self, dim: Optional[int] = None) -> "Tensor":
        return TensorOps.sum(self, dim)

    def mean(self, dim: Optional[int] = None) -> "Tensor":
        return TensorOps.mean(self, dim)

    def max(self) -> "Tensor":
        return Tensor(max(self._flat))

    def min(self) -> "Tensor":
        return Tensor(min(self._flat))

    def abs(self) -> "Tensor":
        return Tensor(_unflatten([abs(x) for x in self._flat], self.shape))

    # -----------------------------------------------------------------------
    # 內部工廠方法（直接定義在 Tensor 類中，避免循環依賴與 monkey-patch）
    # -----------------------------------------------------------------------

    @staticmethod
    def _from_flat(flat: Flat, shape: Shape, requires_grad: bool = False) -> "Tensor":
        """從一維 flat 列表和形狀建立 Tensor（不觸發 __init__ 驗證）"""
        t = Tensor.__new__(Tensor)
        t._flat = flat
        t.shape = shape
        t.grad = None
        t.requires_grad = requires_grad
        t._backward_fn = None
        t._prev = []
        return t


def _to_tensor(x: Any) -> "Tensor":
    if isinstance(x, Tensor):
        return x
    return Tensor(float(x))


# ===========================================================================
# TensorOps — 靜態運算集合
# ===========================================================================

class TensorOps:
    """
    Mr.liou.Core.TensorOps — MRL 張量運算庫

    所有方法為純函數（不修改輸入張量），支援基礎自動梯度。
    """

    # -----------------------------------------------------------------------
    # 元素級運算
    # -----------------------------------------------------------------------

    @staticmethod
    def add(a: Tensor, b: Tensor) -> Tensor:
        """逐元素加法（支援廣播）"""
        out_shape = _broadcast_shapes(a.shape if a.shape else (1,),
                                      b.shape if b.shape else (1,))
        fa = _broadcast_flat(a._flat, a.shape if a.shape else (1,), out_shape)
        fb = _broadcast_flat(b._flat, b.shape if b.shape else (1,), out_shape)
        out_flat = [x + y for x, y in zip(fa, fb)]
        out = Tensor._from_flat(out_flat, out_shape, a.requires_grad or b.requires_grad)

        if out.requires_grad:
            def _bwd():
                g = out.grad
                if g is None:
                    return
                if a.requires_grad:
                    a._accumulate_grad(TensorOps._reduce_grad(g, a.shape))
                if b.requires_grad:
                    b._accumulate_grad(TensorOps._reduce_grad(g, b.shape))
            out._backward_fn = _bwd
            out._prev = [a, b]
        return out

    @staticmethod
    def sub(a: Tensor, b: Tensor) -> Tensor:
        """逐元素減法"""
        return TensorOps.add(a, TensorOps.mul(b, Tensor(-1.0)))

    @staticmethod
    def mul(a: Tensor, b: Tensor) -> Tensor:
        """逐元素乘法（支援廣播）"""
        out_shape = _broadcast_shapes(a.shape if a.shape else (1,),
                                      b.shape if b.shape else (1,))
        fa = _broadcast_flat(a._flat, a.shape if a.shape else (1,), out_shape)
        fb = _broadcast_flat(b._flat, b.shape if b.shape else (1,), out_shape)
        out_flat = [x * y for x, y in zip(fa, fb)]
        out = Tensor._from_flat(out_flat, out_shape, a.requires_grad or b.requires_grad)

        if out.requires_grad:
            def _bwd():
                g = out.grad
                if g is None:
                    return
                if a.requires_grad:
                    ga_flat = [gv * bv for gv, bv in zip(g._flat, fb)]
                    ga = Tensor._from_flat(ga_flat, out_shape)
                    a._accumulate_grad(TensorOps._reduce_grad(ga, a.shape))
                if b.requires_grad:
                    gb_flat = [gv * av for gv, av in zip(g._flat, fa)]
                    gb = Tensor._from_flat(gb_flat, out_shape)
                    b._accumulate_grad(TensorOps._reduce_grad(gb, b.shape))
            out._backward_fn = _bwd
            out._prev = [a, b]
        return out

    @staticmethod
    def div(a: Tensor, b: Tensor) -> Tensor:
        """逐元素除法（支援廣播）"""
        eps = 1e-9
        out_shape = _broadcast_shapes(a.shape if a.shape else (1,),
                                      b.shape if b.shape else (1,))
        fa = _broadcast_flat(a._flat, a.shape if a.shape else (1,), out_shape)
        fb = _broadcast_flat(b._flat, b.shape if b.shape else (1,), out_shape)
        out_flat = [x / (y + eps) for x, y in zip(fa, fb)]
        out = Tensor._from_flat(out_flat, out_shape, a.requires_grad or b.requires_grad)

        if out.requires_grad:
            def _bwd():
                g = out.grad
                if g is None:
                    return
                if a.requires_grad:
                    ga_flat = [gv / (bv + eps) for gv, bv in zip(g._flat, fb)]
                    a._accumulate_grad(TensorOps._reduce_grad(
                        Tensor._from_flat(ga_flat, out_shape), a.shape))
                if b.requires_grad:
                    gb_flat = [-gv * av / ((bv + eps) ** 2)
                               for gv, av, bv in zip(g._flat, fa, fb)]
                    b._accumulate_grad(TensorOps._reduce_grad(
                        Tensor._from_flat(gb_flat, out_shape), b.shape))
            out._backward_fn = _bwd
            out._prev = [a, b]
        return out

    # -----------------------------------------------------------------------
    # 矩陣運算
    # -----------------------------------------------------------------------

    @staticmethod
    def matmul(a: Tensor, b: Tensor) -> Tensor:
        """
        矩陣乘法
        支援：(m,k) @ (k,n) → (m,n)
              (b,m,k) @ (b,k,n) → (b,m,n)  批次模式
        """
        if a.ndim == 2 and b.ndim == 2:
            return TensorOps._matmul2d(a, b)
        elif a.ndim == 3 and b.ndim == 3:
            # 批次矩陣乘法
            if a.shape[0] != b.shape[0]:
                raise ValueError("批次維度不符")
            results = [TensorOps._matmul2d(a[i], b[i]) for i in range(a.shape[0])]
            out_shape = (a.shape[0],) + results[0].shape
            out_flat = []
            for r in results:
                out_flat.extend(r._flat)
            return Tensor._from_flat(out_flat, out_shape,
                                     a.requires_grad or b.requires_grad)
        elif a.ndim == 1 and b.ndim == 1:
            # 向量點積
            if a.shape[0] != b.shape[0]:
                raise ValueError("向量長度不符")
            v = sum(x * y for x, y in zip(a._flat, b._flat))
            return Tensor(v)
        else:
            raise ValueError(f"matmul 不支援形狀 {a.shape} @ {b.shape}")

    @staticmethod
    def _matmul2d(a: Tensor, b: Tensor) -> Tensor:
        m, k1 = a.shape
        k2, n = b.shape
        if k1 != k2:
            raise ValueError(f"矩陣乘法維度不符：{a.shape} @ {b.shape}")
        out_flat: Flat = [0.0] * (m * n)
        for i in range(m):
            for j in range(n):
                s = 0.0
                for p in range(k1):
                    s += a._flat[i * k1 + p] * b._flat[p * n + j]
                out_flat[i * n + j] = s
        out = Tensor._from_flat(out_flat, (m, n),
                                a.requires_grad or b.requires_grad)

        if out.requires_grad:
            def _bwd():
                g = out.grad
                if g is None:
                    return
                # dL/dA = dL/dOut @ B^T
                if a.requires_grad:
                    a._accumulate_grad(TensorOps._matmul2d(g, b.T()))
                # dL/dB = A^T @ dL/dOut
                if b.requires_grad:
                    b._accumulate_grad(TensorOps._matmul2d(a.T(), g))
            out._backward_fn = _bwd
            out._prev = [a, b]
        return out

    @staticmethod
    def linear(x: Tensor, weight: Tensor, bias: Optional[Tensor] = None) -> Tensor:
        """
        全連接層：out = x @ W^T + b
        x:      (batch, in_features)
        weight: (out_features, in_features)
        bias:   (out_features,)
        """
        out = TensorOps.matmul(x, weight.T())
        if bias is not None:
            out = TensorOps.add(out, bias)
        return out

    # -----------------------------------------------------------------------
    # 歸約運算
    # -----------------------------------------------------------------------

    @staticmethod
    def sum(t: Tensor, dim: Optional[int] = None) -> Tensor:
        """沿指定維度求和（dim=None 為全域求和）"""
        if dim is None:
            return Tensor(sum(t._flat))
        if dim < 0:
            dim = t.ndim + dim
        new_shape = t.shape[:dim] + t.shape[dim + 1:]
        stride_inner = _numel(t.shape[dim + 1:]) if dim + 1 < t.ndim else 1
        stride_outer = _numel(t.shape[dim:])
        n_outer = _numel(t.shape[:dim])
        dim_size = t.shape[dim]
        out_flat = [0.0] * (n_outer * stride_inner)
        for o in range(n_outer):
            for i in range(stride_inner):
                s = 0.0
                for d in range(dim_size):
                    idx = o * stride_outer + d * stride_inner + i
                    s += t._flat[idx]
                out_flat[o * stride_inner + i] = s
        return Tensor._from_flat(out_flat, new_shape if new_shape else (), t.requires_grad)

    @staticmethod
    def mean(t: Tensor, dim: Optional[int] = None) -> Tensor:
        """沿指定維度求均值"""
        s = TensorOps.sum(t, dim)
        if dim is None:
            return Tensor(s.item() / t.numel())
        return TensorOps.div(s, Tensor(float(t.shape[dim])))

    # -----------------------------------------------------------------------
    # 激活函數
    # -----------------------------------------------------------------------

    @staticmethod
    def relu(t: Tensor) -> Tensor:
        """ReLU 激活函數 max(0, x)"""
        out_flat = [max(0.0, x) for x in t._flat]
        out = Tensor._from_flat(out_flat, t.shape, t.requires_grad)
        if out.requires_grad:
            def _bwd():
                g = out.grad
                if g is None or not t.requires_grad:
                    return
                mask = [1.0 if x > 0 else 0.0 for x in t._flat]
                g_flat = [gv * m for gv, m in zip(g._flat, mask)]
                t._accumulate_grad(Tensor._from_flat(g_flat, t.shape))
            out._backward_fn = _bwd
            out._prev = [t]
        return out

    @staticmethod
    def gelu(t: Tensor) -> Tensor:
        """GELU 激活函數（近似版）"""
        def _gelu_scalar(x: float) -> float:
            return 0.5 * x * (1.0 + math.tanh(
                math.sqrt(2.0 / math.pi) * (x + 0.044715 * x ** 3)
            ))
        out_flat = [_gelu_scalar(x) for x in t._flat]
        return Tensor._from_flat(out_flat, t.shape, t.requires_grad)

    @staticmethod
    def sigmoid(t: Tensor) -> Tensor:
        """Sigmoid 激活函數 1 / (1 + e^-x)"""
        def _sig(x: float) -> float:
            if x >= 0:
                return 1.0 / (1.0 + math.exp(-x))
            else:
                e = math.exp(x)
                return e / (1.0 + e)
        out_flat = [_sig(x) for x in t._flat]
        out = Tensor._from_flat(out_flat, t.shape, t.requires_grad)
        if out.requires_grad:
            def _bwd():
                g = out.grad
                if g is None or not t.requires_grad:
                    return
                g_flat = [gv * sv * (1 - sv)
                          for gv, sv in zip(g._flat, out_flat)]
                t._accumulate_grad(Tensor._from_flat(g_flat, t.shape))
            out._backward_fn = _bwd
            out._prev = [t]
        return out

    @staticmethod
    def tanh(t: Tensor) -> Tensor:
        """Tanh 激活函數"""
        out_flat = [math.tanh(x) for x in t._flat]
        out = Tensor._from_flat(out_flat, t.shape, t.requires_grad)
        if out.requires_grad:
            def _bwd():
                g = out.grad
                if g is None or not t.requires_grad:
                    return
                g_flat = [gv * (1 - tv ** 2)
                          for gv, tv in zip(g._flat, out_flat)]
                t._accumulate_grad(Tensor._from_flat(g_flat, t.shape))
            out._backward_fn = _bwd
            out._prev = [t]
        return out

    @staticmethod
    def softmax(t: Tensor, dim: int = -1) -> Tensor:
        """Softmax（數值穩定版）"""
        if t.ndim == 0:
            return Tensor(1.0)
        if dim < 0:
            dim = t.ndim + dim
        if t.ndim == 1:
            mx = max(t._flat)
            exps = [math.exp(x - mx) for x in t._flat]
            s = sum(exps)
            return Tensor([e / s for e in exps])
        # 2D case along dim=1
        if t.ndim == 2 and dim == 1:
            rows = t.shape[0]
            cols = t.shape[1]
            out_flat: Flat = []
            for i in range(rows):
                row = t._flat[i * cols: (i + 1) * cols]
                mx = max(row)
                exps = [math.exp(x - mx) for x in row]
                s = sum(exps)
                out_flat.extend([e / s for e in exps])
            return Tensor._from_flat(out_flat, t.shape, t.requires_grad)
        # General: flatten last dim
        raise NotImplementedError(f"softmax 目前支援 1D 或 2D(dim=1)，收到 ndim={t.ndim}, dim={dim}")

    @staticmethod
    def log_softmax(t: Tensor, dim: int = -1) -> Tensor:
        """Log-Softmax（數值穩定版）"""
        if t.ndim == 1:
            mx = max(t._flat)
            log_sum_exp = math.log(sum(math.exp(x - mx) for x in t._flat)) + mx
            return Tensor([x - log_sum_exp for x in t._flat])
        if t.ndim == 2 and (dim == 1 or dim == -1):
            rows, cols = t.shape
            out_flat: Flat = []
            for i in range(rows):
                row = t._flat[i * cols: (i + 1) * cols]
                mx = max(row)
                log_sum_exp = math.log(sum(math.exp(x - mx) for x in row)) + mx
                out_flat.extend([x - log_sum_exp for x in row])
            return Tensor._from_flat(out_flat, t.shape, t.requires_grad)
        raise NotImplementedError(f"log_softmax 支援 1D 或 2D(dim=1)")

    # -----------------------------------------------------------------------
    # 梯度輔助
    # -----------------------------------------------------------------------

    @staticmethod
    def _reduce_grad(g: Tensor, target_shape: Shape) -> Tensor:
        """將梯度廣播形狀歸約回目標形狀（反廣播）"""
        if g.shape == target_shape:
            return g
        if not target_shape:
            return Tensor(sum(g._flat))
        # Sum over leading dimensions
        while g.ndim > len(target_shape):
            g = TensorOps.sum(g, 0)
        # Sum over dimensions where target is 1
        for i, (gs, ts) in enumerate(zip(g.shape, target_shape)):
            if ts == 1 and gs > 1:
                g = TensorOps.sum(g, i).reshape(*g.shape[:i], 1, *g.shape[i + 1:])
        return g


# ===========================================================================
# Initializer — 權重初始化策略
# ===========================================================================

class Initializer:
    """
    Mr.liou.Core.Initializer — 權重初始化策略

    所有方法返回 Tensor（requires_grad=True）
    """

    @staticmethod
    def zeros(shape: Shape, requires_grad: bool = True) -> Tensor:
        """全零初始化"""
        flat = [0.0] * _numel(shape)
        return Tensor._from_flat(flat, shape, requires_grad)

    @staticmethod
    def ones(shape: Shape, requires_grad: bool = True) -> Tensor:
        """全一初始化"""
        flat = [1.0] * _numel(shape)
        return Tensor._from_flat(flat, shape, requires_grad)

    @staticmethod
    def normal(
        shape: Shape,
        mean: float = 0.0,
        std: float = 1.0,
        seed: Optional[int] = None,
        requires_grad: bool = True,
    ) -> Tensor:
        """正態分佈初始化（Box-Muller 方法）"""
        rng = random.Random(seed)
        n = _numel(shape)
        flat: Flat = []
        for _ in range((n + 1) // 2):
            u1 = rng.random() + 1e-10
            u2 = rng.random()
            mag = std * math.sqrt(-2.0 * math.log(u1))
            z0 = mag * math.cos(2.0 * math.pi * u2) + mean
            z1 = mag * math.sin(2.0 * math.pi * u2) + mean
            flat.extend([z0, z1])
        return Tensor._from_flat(flat[:n], shape, requires_grad)

    @staticmethod
    def uniform(
        shape: Shape,
        low: float = -1.0,
        high: float = 1.0,
        seed: Optional[int] = None,
        requires_grad: bool = True,
    ) -> Tensor:
        """均勻分佈初始化"""
        rng = random.Random(seed)
        flat = [rng.uniform(low, high) for _ in range(_numel(shape))]
        return Tensor._from_flat(flat, shape, requires_grad)

    @staticmethod
    def xavier_uniform(
        shape: Shape,
        gain: float = 1.0,
        seed: Optional[int] = None,
        requires_grad: bool = True,
    ) -> Tensor:
        """Xavier 均勻初始化（Glorot）"""
        if len(shape) < 2:
            raise ValueError("Xavier 初始化需要至少 2 維")
        fan_in, fan_out = shape[-1], shape[-2]  # (out, in) for weight matrix
        limit = gain * math.sqrt(6.0 / (fan_in + fan_out))
        return Initializer.uniform(shape, -limit, limit, seed, requires_grad)

    @staticmethod
    def kaiming_normal(
        shape: Shape,
        mode: str = "fan_in",
        nonlinearity: str = "relu",
        seed: Optional[int] = None,
        requires_grad: bool = True,
    ) -> Tensor:
        """Kaiming 正態初始化（He）"""
        if len(shape) < 2:
            raise ValueError("Kaiming 初始化需要至少 2 維")
        fan_in, fan_out = shape[-1], shape[-2]
        fan = fan_in if mode == "fan_in" else fan_out
        gain = math.sqrt(2.0) if nonlinearity == "relu" else 1.0
        std = gain / math.sqrt(fan)
        return Initializer.normal(shape, 0.0, std, seed, requires_grad)


# ===========================================================================
# SGD / Adam — 純 Python 優化器
# ===========================================================================

class SGD:
    """
    Mr.liou.Core.SGD — 隨機梯度下降優化器（含動量）
    """

    def __init__(
        self,
        params: List[Tensor],
        lr: float = 0.01,
        momentum: float = 0.0,
        weight_decay: float = 0.0,
    ):
        self.params = params
        self.lr = lr
        self.momentum = momentum
        self.weight_decay = weight_decay
        self._velocity: List[Optional[List[float]]] = [None] * len(params)

    def zero_grad(self):
        for p in self.params:
            p.grad = None

    def step(self):
        for i, p in enumerate(self.params):
            if p.grad is None:
                continue
            g = list(p.grad._flat)
            # L2 正則
            if self.weight_decay > 0:
                g = [gv + self.weight_decay * pv for gv, pv in zip(g, p._flat)]
            # 動量
            if self.momentum > 0:
                if self._velocity[i] is None:
                    self._velocity[i] = list(g)
                else:
                    v = self._velocity[i]
                    self._velocity[i] = [
                        self.momentum * vi + gv for vi, gv in zip(v, g)
                    ]
                g = self._velocity[i]
            p._flat = [pv - self.lr * gv for pv, gv in zip(p._flat, g)]


class Adam:
    """
    Mr.liou.Core.Adam — Adam 優化器
    """

    def __init__(
        self,
        params: List[Tensor],
        lr: float = 1e-3,
        betas: Tuple[float, float] = (0.9, 0.999),
        eps: float = 1e-8,
        weight_decay: float = 0.0,
    ):
        self.params = params
        self.lr = lr
        self.betas = betas
        self.eps = eps
        self.weight_decay = weight_decay
        self.t = 0
        n = len(params)
        self._m: List[Optional[List[float]]] = [None] * n
        self._v: List[Optional[List[float]]] = [None] * n

    def zero_grad(self):
        for p in self.params:
            p.grad = None

    def step(self):
        self.t += 1
        b1, b2 = self.betas
        for i, p in enumerate(self.params):
            if p.grad is None:
                continue
            g = list(p.grad._flat)
            if self.weight_decay > 0:
                g = [gv + self.weight_decay * pv for gv, pv in zip(g, p._flat)]

            if self._m[i] is None:
                self._m[i] = [0.0] * len(g)
                self._v[i] = [0.0] * len(g)

            m = self._m[i]
            v = self._v[i]
            m_new = [b1 * mi + (1 - b1) * gi for mi, gi in zip(m, g)]
            v_new = [b2 * vi + (1 - b2) * gi ** 2 for vi, gi in zip(v, g)]
            self._m[i] = m_new
            self._v[i] = v_new

            m_hat = [mi / (1 - b1 ** self.t) for mi in m_new]
            v_hat = [vi / (1 - b2 ** self.t) for vi in v_new]
            p._flat = [
                pv - self.lr * mh / (math.sqrt(vh) + self.eps)
                for pv, mh, vh in zip(p._flat, m_hat, v_hat)
            ]


# ===========================================================================
# 便捷工廠函數
# ===========================================================================

def zeros(shape: Union[Shape, int], requires_grad: bool = False) -> Tensor:
    if isinstance(shape, int):
        shape = (shape,)
    return Initializer.zeros(shape, requires_grad)


def ones(shape: Union[Shape, int], requires_grad: bool = False) -> Tensor:
    if isinstance(shape, int):
        shape = (shape,)
    return Initializer.ones(shape, requires_grad)


def randn(*shape: int, seed: Optional[int] = None, requires_grad: bool = False) -> Tensor:
    return Initializer.normal(shape, seed=seed, requires_grad=requires_grad)


def tensor(data: Any, requires_grad: bool = False) -> Tensor:
    return Tensor(data, requires_grad)


# ===========================================================================
# 自檢測試
# ===========================================================================

if __name__ == "__main__":
    print("=== Mr.liou.Core.Tensor 自檢測試 ===\n")

    # 基本運算
    a = tensor([[1.0, 2.0], [3.0, 4.0]])
    b = tensor([[5.0, 6.0], [7.0, 8.0]])
    print("a + b =", (a + b).tolist())
    print("a * b =", (a * b).tolist())
    print("a @ b =", (a @ b).tolist())

    # Softmax
    x = tensor([1.0, 2.0, 3.0])
    print("softmax([1,2,3]) =", TensorOps.softmax(x).tolist())

    # Kaiming 初始化
    w = Initializer.kaiming_normal((4, 3), seed=42)
    print("Kaiming normal (4,3), shape =", w.shape)

    # Adam 優化器模擬
    p = tensor([[1.0, 2.0]], requires_grad=True)
    opt = Adam([p], lr=0.1)
    p.grad = tensor([[0.5, -0.5]])
    opt.step()
    print("Adam step result:", p.tolist())

    print("\n✅ 所有自檢通過")
