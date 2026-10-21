# MRL_MetaIR_Compiler — COMPATIBILITY ALIAS（歷史名稱，非 canonical）
# origin_signature: MrLiouWord
# canonical 已遷移至 MRL_MrLiouIR_Compiler；本檔僅為向後兼容 alias，請勿新增主體邏輯。
"""[DEPRECATED] MetaIR 為歷史名稱 / Adapter / alias。

正式 canonical = MrLiouIR（見 MRL_MrLiouIR_Compiler）。本模組原樣轉出，供舊引用兼容。
"""
from __future__ import annotations

from .MRL_MrLiouIR_Compiler import (  # noqa: F401
    ORIGIN_SIGNATURE,
    compile_metair,
    compile_mrliouir,
)

__all__ = ["compile_mrliouir", "compile_metair", "ORIGIN_SIGNATURE"]
