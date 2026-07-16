# MRL_外部標準對照（SPDX / JWT）

origin_signature: `MrLiouWord`

> 本檔**只做對照**，不改 MRL 命名核心。SPDX / JWT 僅作 `MRL_外部對照層`
> （`source_ref` / `adapter_ref` / `provenance` / `compatibility_note`），
> **不得**作為母體層名、產品名、Runtime 名、DB 名、API 名、模組名、核心類別名。

## SPDX 3.0.1 對照（MRL_物件關係 / MRL_來源證明 / MRL_完整性）

SPDX 支援 BOM / AI / Dataset / Build / Provenance / Integrity / Relationship / Lifecycle 等描述。

| MRL_正名 | ↔ | SPDX 概念 |
|---|---|---|
| MRL_造物 | ↔ | Artifact |
| MRL_痕跡錄 | ↔ | Relationship / Provenance |
| MRL_自述紋 | ↔ | CreationInfo |
| MRL_知識海 | ↔ | Dataset |
| MRL_模型識 | ↔ | AI Profile |
| MRL_封裝體 | ↔ | Build Profile |
| MRL_完整性紋 | ↔ | IntegrityMethod |
| MRL_生命週期紋 | ↔ | Lifecycle |

## JWT (RFC 7519) 對照（MRL_通行證 / MRL_身份紋 / MRL_聲明封包）

JWT 為 compact、URL-safe 的 claims 表示格式，可被簽章 / 完整性保護 / 加密。

| MRL_正名 | ↔ | JWT 概念 |
|---|---|---|
| MRL_通行證 | ↔ | JWT |
| MRL_聲明粒 | ↔ | Claim |
| MRL_發出者紋 | ↔ | iss |
| MRL_主體紋 | ↔ | sub |
| MRL_接收界 | ↔ | aud |
| MRL_到期紋 | ↔ | exp |
| MRL_起效紋 | ↔ | nbf |
| MRL_發行時紋 | ↔ | iat |
| MRL_唯一紋 | ↔ | jti |

## 來源註記（provenance）

- 基準資料（SPDX 3.0.1 PDF、RFC 7519、MRL 白皮書）由主線提供之外部參照；
  **本 checkout 內未含該等原始檔**，故本對照表以標準公開定義撰寫，列為 `compatibility_note`，
  不宣稱已逐頁解析原始 PDF。
