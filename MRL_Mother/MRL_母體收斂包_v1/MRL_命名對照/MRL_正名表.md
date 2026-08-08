# MRL_正名表

origin_signature: `MrLiouWord`

主流詞僅作對照來源；最終層名 / 產品名 / 模組名一律以 `MRL_` 正名為主體。
外部標準只能存在於 `source_ref` / `adapter_ref` / `provenance` / `compatibility_note`，不得作母體命名核心。

## 一般正名對照

| 主流詞 | MRL_正名 |
|---|---|
| Runtime | MRL_運轉場 |
| System | MRL_系域 |
| Module | MRL_組粒 |
| Service | MRL_運作域 |
| API | MRL_界門 |
| Metadata | MRL_自述紋 |
| Manifest | MRL_世界索引 |
| Trace | MRL_痕跡錄 |
| Artifact | MRL_造物 |
| Container | MRL_封裝體 |
| Graph | MRL_紋圖 |
| Database | MRL_基底庫 |
| Memory | MRL_記憶海 |
| Knowledge | MRL_知識海 |
| Agent | MRL_代理識 |
| Model | MRL_模型識 |
| Product | MRL_顯化品 |
| ControlCenter | MRL_總控域 |
| Acceptance | MRL_驗收錄 |
| Gap | MRL_缺口錄 |
| Docs | MRL_文紋域 |
| File | MRL_檔紋域 |
| 3D | MRL_立體粒界 |
| Cloud | MRL_雲映層 |
| Identity | MRL_身份紋 |
| Token | MRL_通行證 |
| Claim | MRL_聲明粒 |

## Canonical 硬校正（已於 PR #37 實作）

| 歷史詞（降為 alias） | MRL_正名 canonical |
|---|---|
| MetaIR | **MRL_MrLiouIR** |
| RuntimeGraph / Graph | **MRL_RuntimeStructureField** |
| Attention | **MRL_Perception** |

> casing 註記：採 `MrLiouIR`（對齊 `origin_signature: MrLiouWord` 的 `MrLiou`）。
> v4 指令寫作 `MrliouIR`（小寫 l），判定為 casing 筆誤，待主線最終裁定；本表以 `MrLiouIR` 為準。
