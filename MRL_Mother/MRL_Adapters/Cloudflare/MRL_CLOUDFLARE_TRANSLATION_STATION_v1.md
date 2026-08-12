# MRL Cloudflare Translation Station v1

`origin_signature: MrLiouWord`

## 1. Purpose／用途

This station is a bidirectional boundary node between MRL/GitHub history and
Cloudflare Pages/Workers execution grammar. It translates parameters and
returns evidence without renaming, flattening, or rewriting either side.

本轉譯站把 Cloudflare 視為莫比斯環中的外部 Adapter 節點：MRL 意圖沿正向
轉成供應商參數，供應商結果沿反向回填成 MRL 證據。兩側名稱、語法、歷史與
權責保持獨立。

```text
MRL canonical intent
  -> mapping version + difference vector
  -> forward translator T_f
  -> Cloudflare external project grammar
  -> provider result + actual parameter snapshot
  -> reverse translator T_r
  -> append-only MRL trace and provenance
```

The station is additive. It does not change existing Worker code, Pages code,
Cloudflare project settings, GKE deployment settings, or provider-owned names.

## 2. Evidence-aligned boundary state／證據對齊狀態

PR `dofaromg/flow-tasks#616` at source SHA
`43ff96f75833c4ef2da92afd1f415cd533e848d1` produced one Pages failure and
three Workers failures:

| External node | Current MRL-side evidence | Translation state |
|---|---|---|
| Pages `flow-tasks` | Root Next.js frontend is documented as GKE `standalone` | historical shadow; identity/root/build parameters unverified |
| Worker `flow-tasks` | `flowos-neural-gate` is the canonical in-repo Worker identity | historical failure scope only; external identity link unverified |
| Worker `mrlflow-tasks` | System hub records the name as `shell` and `requires_deployment` | same name, incompatible runtime/promotion state |
| Worker `mrl-store` | Critical inventory records `UNVERIFIED_IN_THIS_REPOSITORY` | name similarity to `mrl-firecore-store` is not identity evidence |

The repository's historical authority evidence records the same four-node
failure scope around an earlier corrupted FlowOS entry. The current head no
longer contains the prior three-copy entry corruption. The remaining boundary
must therefore be diagnosed as a mapping/parameter loop until provider logs and
project settings prove a narrower cause.

## 3. Three-state difference model／三態差異模型

Every parameter has exactly one state:

```text
MATCH    = 0     evidence proves both sides agree
MISMATCH = 1     evidence proves both sides differ
UNKNOWN  = null  required evidence is absent or cannot be joined
```

`UNKNOWN` is never converted to `MATCH`. Similar names, shared repositories,
shared commits, or simultaneous failures are correlation evidence only.

### Difference parameters

| Parameter | Weight | Critical | Difference measured |
|---|---:|:---:|---|
| `delta_identity` | 5 | yes | canonical identity ↔ external project identity |
| `delta_runtime` | 5 | yes | MRL runtime grammar ↔ Pages/Workers runtime |
| `delta_source_root` | 3 | no | source root ↔ provider build root |
| `delta_entrypoint` | 4 | yes | canonical entrypoint ↔ provider entrypoint |
| `delta_build_method` | 4 | yes | canonical build method ↔ provider command |
| `delta_deploy_policy` | 5 | yes | MRL promotion authority ↔ automatic deploy policy |
| `delta_binding_contract` | 5 | yes | KV/D1/R2/DO requirements ↔ configured bindings |
| `delta_trigger` | 3 | no | approved trigger ↔ observed Git trigger |
| `delta_method_signature` | 4 | yes | boundary method and argument semantics |
| `delta_encoding_invariant` | 5 | yes | UTF-8/Base64 equivalence across implementations |
| `delta_history_return` | 4 | yes | append-only evidence ↔ mutable status comment |
| `delta_timing` | 2 | no | same-SHA callback timing discontinuity |
| `delta_provenance` | 4 | yes | SHA/map/build/parameter evidence coverage |

### Weighted formulas

For parameter `i`, let `w_i` be its weight and `delta_i` its state.

```text
W = Σ w_i
K = Σ w_i where delta_i ∈ {MATCH, MISMATCH}
M = Σ w_i where delta_i = MISMATCH
C = K / W
S = M / K, when K > 0; otherwise UNKNOWN
```

- `C` is evidence confidence, not success probability.
- `S` is the known-boundary singularity score.
- A critical `MISMATCH` returns `HOLD_SINGULARITY`.
- A critical `UNKNOWN`, or `C < 0.8`, returns
  `HOLD_INSUFFICIENT_EVIDENCE` unless a stronger known singularity already
  requires HOLD.
- `S >= 0.25` returns `HOLD_SINGULARITY`.
- A noncritical resolvable mismatch returns `TRANSLATE_REQUIRED`.
- Only a complete, verified vector with no mismatch returns `PASS`.

The score never authorizes deployment. It only determines whether a verified
mapping is eligible to produce a provider request.

## 4. Forward translation／正向轉譯

```text
T_f(intent, map_v) =
  provider_request,
    when identity_link = active_verified
     and forward_action = TRANSLATE
     and all critical parameters are known
     and deploy_policy permits the requested promotion
     and all remaining mismatches have declared formulas;
  HOLD(reason_vector), otherwise.
```

The forward trace must preserve both identities:

```text
canonical_profile
canonical_identity
provider = Cloudflare
provider_kind
external_project
source_sha
mapping_version
parameter_snapshot
delta_vector
```

Provider project names are emitted unchanged. The canonical MRL identity is
carried beside the provider alias and is never replaced by it.

## 5. Reverse translation／反向轉譯

```text
T_r(event, map_v) = append_only_evidence(
  canonical_profile,
  external_project,
  source_sha,
  build_id,
  sanitized_parameter_snapshot,
  delta_vector,
  score,
  result,
  observed_at
)
```

The deterministic evidence ID is:

```text
event_id = "mrl-cf-" + SHA256(canonical_json(return_record_without_event_id))
```

Secret-like values (`token`, `secret`, `password`, `credential`, API/private/
master keys) are replaced with `[REDACTED]`. Parameter names remain visible so
the binding contract can still be audited.

Cloudflare bot comments are mutable provider surfaces. The station copies each
observed state into a new append-only MRL record; it never edits historical MRL
evidence to match a later comment update.

## 6. Round-trip invariant／回環不變量

Let `P` project the identity and provenance fields from a record:

```text
P(x) = {
  canonical_identity,
  external_project,
  provider_kind,
  source_sha,
  mapping_version
}
```

For every actively verified mapping:

```text
P(T_r(T_f(x, map_v), map_v)) = P(x)
```

This is the minimum condition for a Möbius-loop return. If any projected field
changes, disappears, or becomes inferred, the translation is a singularity and
must HOLD.

## 7. UTF-8/Base64 method invariant／編碼公式

The three observed `utf8ToBase64()` implementations changed how a
`Uint8Array` chunk was passed to `String.fromCharCode`, but the required output
contract is independent of that implementation detail.

For text `x`, UTF-8 bytes `U = UTF8(x)`, and any chunk size `c > 0`:

```text
B64_c(x) = Base64(concat(U[k*c : (k+1)*c]))
DecodeBase64(B64_c(x)) = U
B64_a(x) = B64_b(x) for all a,b > 0
```

Tests cover ASCII, Traditional Chinese, punctuation, large payloads, and chunk
sizes `1, 2, 3, 127, 1024, 32768, 65535`. A digest difference is classified as
`delta_encoding_invariant = MISMATCH`; it is not repaired by changing either
external project or canonical identity.

## 8. Current safety decision／目前安全裁決

All four current Cloudflare nodes are `HOLD`:

- Pages `flow-tasks`: provider root/build parameters are missing and its
  deployment grammar conflicts with the documented GKE frontend carrier.
- Worker `flow-tasks`: the link to `flowos-neural-gate` is historical evidence,
  not an active identity mapping.
- Worker `mrlflow-tasks`: the MRL record is a shell awaiting explicit promotion.
- Worker `mrl-store`: its repository identity remains unverified; it cannot be
  silently mapped to `mrl-firecore-store`, whose policy is local backfill and
  `MRL_FIRECORE_NO_DEPLOY=1`.

HOLD means: preserve the event, expose missing parameters, and prevent a blind
forward translation. It does not delete, disable, or rename a provider project.

## 9. Commands／操作

```bash
# Validate map, parameters, formulas, nodes and invariants
python scripts/mrl_cloudflare_translation_station.py validate

# Inspect one current node without side effects
python scripts/mrl_cloudflare_translation_station.py inspect \
  --provider-kind workers --project mrl-store

# Translate an intent; unsafe mappings return a structured HOLD
python scripts/mrl_cloudflare_translation_station.py forward --event intent.json

# Normalize a provider callback into append-only evidence
python scripts/mrl_cloudflare_translation_station.py reverse --event callback.json

# Verify the chunk-independent encoding formula
python scripts/mrl_cloudflare_translation_station.py verify-encoding \
  --text "MrLiouWord／怎麼過去，就怎麼回來"

# Unit tests
python -m unittest -v tests.test_mrl_cloudflare_translation_station
```

## 10. Promotion requirements／映射升級條件

An external node can change to `active_verified` only when one evidence record
contains all of the following:

1. External Cloudflare project name and kind.
2. Repository and full source SHA.
3. Configured root directory, build command, deploy command and entrypoint.
4. Binding names and non-secret presence status.
5. Canonical MRL profile and explicit identity link.
6. Promotion authority and deploy policy.
7. Forward translation result and reverse evidence result.
8. Passing round-trip and encoding invariants.

Until then, missing values remain `UNKNOWN`; no side is modified to manufacture
agreement.
