#!/usr/bin/env python3
# MRL_runtime_civilization_run
# origin_signature: MrLiouWord
"""端到端執行 Runtime Civilization Stack，並由實際執行結果產出：

  docs/MRL_StructureField_Visualization.mmd   StructureField 視覺化（mermaid）
  docs/MRL_StructureField_Visualization.dot   StructureField 視覺化（graphviz dot）
  docs/MRL_StructureField_Visualization.json  StructureField 結構
  docs/MRL_Verification_Report.md 驗證報告
  docs/MRL_WorldRuntime_Report.md 世界運轉報告

用法：python MRL_UniversalRuntimeLanguage_Core_v1/scripts/MRL_runtime_civilization_run.py [來源檔]
未給來源檔時，預設以本 repo README.md 為輸入。
"""

from __future__ import annotations

import json
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from MRL_UniversalRuntimeLanguage_Core_v1.MRL_Language.MRL_UniversalParser_Core import detect_lang  # noqa: E402
from MRL_UniversalRuntimeLanguage_Core_v1.MRL_Runtime.MRL_DL580_Runtime import MRL_DL580_Runtime  # noqa: E402
from MRL_UniversalRuntimeLanguage_Core_v1.MRL_Runtime import MRL_RuntimeStructureField  # noqa: E402

_DOCS = pathlib.Path(__file__).resolve().parents[1] / "docs"


def main() -> int:
    src_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else (_REPO_ROOT / "README.md")
    source = src_path.read_text(encoding="utf-8")
    lang = detect_lang(src_path.name)

    runtime = MRL_DL580_Runtime()
    result = runtime.run(source, lang=lang, loop_id="civilization_run")
    structurefield = result["structurefield"]
    verification = result["verification"]
    world = result["world"]

    _DOCS.mkdir(parents=True, exist_ok=True)

    # MRL_StructureField_Visualization
    (_DOCS / "MRL_StructureField_Visualization.mmd").write_text(
        MRL_RuntimeStructureField.to_mermaid(structurefield), encoding="utf-8"
    )
    (_DOCS / "MRL_StructureField_Visualization.dot").write_text(
        MRL_RuntimeStructureField.to_dot(structurefield), encoding="utf-8"
    )
    (_DOCS / "MRL_StructureField_Visualization.json").write_text(
        MRL_RuntimeStructureField.to_json(structurefield), encoding="utf-8"
    )

    # 驗證報告
    vlines = [
        "# MRL_Verification_Report",
        "",
        "origin_signature: `MrLiouWord`",
        "",
        f"- 來源：`{src_path.name}`（lang=`{lang}`）",
        f"- 管線：`{' → '.join(result['stages_executed'])}`",
        f"- MrLiouIR node_count：`{result['mrliouir']['node_count']}`",
        f"- RuntimeStructureField：node=`{structurefield['node_count']}` relation=`{structurefield['relation_count']}` hash=`{structurefield['structurefield_hash'][:12]}`",
        "",
        "## 驗收項",
        "",
        "| Check | Result | Detail |",
        "|---|---|---|",
    ]
    for c in verification["checks"]:
        vlines.append(f"| {c['check']} | {'PASS' if c['pass'] else 'FAIL'} | {c['detail']} |")
    vlines += [
        "",
        f"**passed = {verification['passed']}/{verification['total']}**",
        "",
        f"## `{verification['token']}`",
        "",
    ]
    (_DOCS / "MRL_Verification_Report.md").write_text("\n".join(vlines), encoding="utf-8")

    # 世界運轉報告
    wlines = [
        "# MRL_WorldRuntime_Report",
        "",
        "origin_signature: `MrLiouWord`",
        "",
        f"- world_count：`{world['world_count']}`",
        f"- synchronization_active：`{world['synchronization_active']}`",
        f"- sync.merged_keys：`{world.get('sync', {}).get('merged_keys')}`",
        "",
        "## worlds",
        "",
        "```json",
        json.dumps(world["worlds"], ensure_ascii=False, indent=2),
        "```",
        "",
        f"- replay.exact：`{result['replay']['exact']}`",
        f"- restore.exact：`{result['restore']['exact']}`",
        f"- persistent_loop：`{result['persistent_loop']}`",
        f"- roundtrip.exact：`{result['roundtrip']['exact']}`",
        "",
    ]
    (_DOCS / "MRL_WorldRuntime_Report.md").write_text("\n".join(wlines), encoding="utf-8")

    print(f"reports written to {_DOCS}")
    print(verification["token"])
    return 0 if verification["acceptance"] else 1


if __name__ == "__main__":
    sys.exit(main())
