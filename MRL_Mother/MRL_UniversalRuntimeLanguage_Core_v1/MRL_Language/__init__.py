# MRL_Language layer
# origin_signature: MrLiouWord
"""語言層：UniversalParser → MrLiouIR → ParticleIR → PerceptionKernel。

Canonical 名稱（v2，單一真實來源）：
    MRL_MrLiouIR     → MRL_MrLiouIR_Compiler   （MrLiou 中介語義層）
    MRL_ParticleIR   → MRL_ParticleIR_Engine
    MRL_UniversalParser_Core / MRL_PerceptionKernel 為正式名

Compatibility alias（歷史名稱，非 canonical 主體）：
    MRL_MetaIR       → MRL_MrLiouIR_Compiler（= MetaIR Adapter）
"""

from . import (
    MRL_MrLiouIR_Compiler,
    MRL_ParticleIR_Engine,
    MRL_PerceptionKernel,
    MRL_UniversalParser_Core,
)

# Canonical 短名（單一真實來源）
MRL_MrLiouIR = MRL_MrLiouIR_Compiler
MRL_ParticleIR = MRL_ParticleIR_Engine

# Compatibility alias layer（MetaIR = 歷史/Adapter，僅向後兼容）
from . import MRL_MetaIR_Compiler  # noqa: E402  (alias shim module)
MRL_MetaIR = MRL_MrLiouIR_Compiler

__all__ = [
    "MRL_UniversalParser_Core",
    "MRL_MrLiouIR_Compiler",
    "MRL_ParticleIR_Engine",
    "MRL_PerceptionKernel",
    "MRL_MrLiouIR",
    "MRL_ParticleIR",
    # compatibility alias
    "MRL_MetaIR",
    "MRL_MetaIR_Compiler",
]
