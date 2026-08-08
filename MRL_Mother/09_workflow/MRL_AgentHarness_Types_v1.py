#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_AgentHarness_Types_v1.py — Agent 執行骨架:共用型別（去重蒸餾唯一真實來源）
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=3 MrLiouAIRuntime

吸收來源（母體吸收記錄）
----------------------
蒸餾自 MRL-antigravity-sdk-python `google/antigravity/types.py`（1180 行），
去重後只保留母體缺少的核心型別。已在母體存在、不重複吸收的部分：
  - 會話/訊息模型   → 09_workflow/conversation.py, conversation_manager.py
  - 工具 schema 註冊 → 09_workflow/tool_registry.py
  - 多代理協作      → 09_workflow/MRL_multi_agent.py

本模組是 MRL_AgentHarness_* 系列共用型別的唯一真實來源；
其他 AgentHarness 模組一律 `from MRL_AgentHarness_Types_v1 import ...`。

依賴：Python stdlib only（dataclasses, enum）— 無 pydantic、無外部套件。
"""
from __future__ import annotations

import dataclasses
import enum
import time
from typing import Any, Callable, Dict, List, Optional

from MRL_utils import ORIGIN_SIGNATURE

__all__ = [
    "ORIGIN_SIGNATURE",
    "ToolCall",
    "ToolResult",
    "HookResult",
    "UsageMetadata",
    "StepType",
    "Step",
    "PythonTool",
    "Decision",
    "FileChangeKind",
    "FileChange",
]

# 工具即任意 Python callable（sync 或 async）。
PythonTool = Callable[..., Any]


class Decision(enum.Enum):
    """政策裁決結果。對齊 MRL_guardrail 語彙：ASK_USER ≈ REQUIRE_HUMAN。"""

    APPROVE = "APPROVE"
    DENY = "DENY"
    ASK_USER = "ASK_USER"


@dataclasses.dataclass
class ToolCall:
    """一次具名工具呼叫請求。

    Attributes:
        name: 工具名稱。
        args: 關鍵字引數 dict。
        canonical_path: 檔案類工具的正規化目標路徑（workspace 政策用）。
    """

    name: str
    args: Dict[str, Any] = dataclasses.field(default_factory=dict)
    canonical_path: Optional[str] = None


@dataclasses.dataclass
class ToolResult:
    """一次工具呼叫的結構化結果。result 與 error 互斥。"""

    name: str
    result: Any = None
    error: Optional[str] = None
    exception: Optional[BaseException] = None

    @property
    def ok(self) -> bool:
        return self.error is None


@dataclasses.dataclass
class HookResult:
    """Decide 型 hook 的裁決：allow=False 即阻斷，message 說明原因。"""

    allow: bool = True
    message: str = ""


@dataclasses.dataclass
class UsageMetadata:
    """token 用量累計（沙盒 gateway 以字元數估算；實機以 API 回報為準）。"""

    prompt_tokens: int = 0
    response_tokens: int = 0
    total_tokens: int = 0

    def add(self, other: "UsageMetadata") -> None:
        self.prompt_tokens += other.prompt_tokens
        self.response_tokens += other.response_tokens
        self.total_tokens += other.total_tokens


class StepType(str, enum.Enum):
    """對話歷史中一步的類型。"""

    USER = "user"
    MODEL = "model"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"


@dataclasses.dataclass
class Step:
    """對話歷史單步，含 LAW-0 簽章與時間戳。"""

    type: StepType
    content: Any
    origin_signature: str = ORIGIN_SIGNATURE
    ts: float = dataclasses.field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "content": self.content,
            "origin_signature": self.origin_signature,
            "ts": self.ts,
        }


class FileChangeKind(str, enum.Enum):
    """檔案系統變更類型（TriggerPulse 用）。"""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"


@dataclasses.dataclass(frozen=True)
class FileChange:
    """單一檔案變更事件。"""

    kind: FileChangeKind
    path: str


def _demo() -> None:
    tc = ToolCall(name="read_file", args={"path": "/tmp/x"})
    tr = ToolResult(name=tc.name, result="ok")
    step = Step(type=StepType.TOOL_RESULT, content={"name": tr.name, "ok": tr.ok})
    print("ToolCall:", tc)
    print("ToolResult.ok:", tr.ok)
    print("Step:", step.to_dict())
    print("Decision members:", [d.value for d in Decision])


if __name__ == "__main__":
    _demo()
