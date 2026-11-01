# Mrliou_MRL_ParticleDict_PaniniClusterInsight_v1.0.0

origin_signature: MrLiouWord · canonical_authority: Mr.liou · stage: S4.5

This module extends the existing `MRL_Bridge/server.js`. It is a read/computation organ of the MRL mother, not a second mother runtime. ChatGPT/MCP clients delegate to the existing mother Bridge; the stdio adapter does not compute a local substitute result.

## Identity and recovered ancestry

- Original supplied by Mr.liou: `sources/Mrliou_MRL_ParticleDict_PaniniClusterInsight_v1.0.0.json`, 14,639 UTF-8 bytes, SHA-256 `92dd5c24c1e7f9e85b097b4fb3e54b9205d275323208c732a68105277fd0659a`. Library identity: `libfile_4d89b2327fd4819191b9e2610091180a`. The complete supplied text is retained; runtime verifies its byte hash before loading.
- Canonical schema `panini_cluster_insight/v1.0.0`; internal ID `Mrliou.ParticleDict.PaniniClusterInsight.v1`. Adapter/input schemas have distinct identities; they do not rename the canonical source.
- Historical authority: [MRL｜來源起點與跨載體閉環原則 v1.0](https://app.notion.com/p/0fa016ab4a96448fb2d3524b3b2f230c), including the 2026-10-25 APPEND_ONLY correction; [MRL母體本地](https://app.notion.com/p/3e9e7f4e6c5580e49f3dc8292dda835a).
- Engineering parent: `MRL_Bridge/server.js` and `mrl_bridge_translation_center.cjs`, base commit `36dc69d98ec3e28e5cca744e82013ed32b203b61`. The existing audit middleware, admission and rate limiting still wrap the new routes.
- Existing dictionary material inspected: `MRL_Mother/MRL_MotherSource_Lineage_v1/粒子字典ai/工程師給的/下載 Fluin_Particle_BilingualDict.json`, including `⋄fx.noun.024`, `⋄fx.flow.007`, `⋄fx.flow.018`. `core/particle_dict.py` and `MRL_Mother/09_workflow/MRL_MCP_Server_v1.py` were inspected; their schemas are not silently treated as S4 or replaced.
- Source-declared parent: `/MRL_Mother_Anatomy/30_particle_dictionary_reverse_engineering_direction_20261031.md`; upstream S3.5 FxDualContextBridge and S4 CrossLayerIDMap v1.0.0; downstream S5 ReversibilityBatchTest, S6 UI, S7 .flpkg. These names remain unchanged.
- S3.5/S4 originals and the source-declared parent/companion documents were not recovered in this run. Searches covered the complete flow-tasks main tree, accessible GitHub default-branch search, Library titles/content, Notion search and Drive. Zero matches do not establish absence on the mother or other branches. Current authenticated Bridge file access returned 401, so local mother discovery could not continue through that route.

## Function behavior

| Function / tool | Input | Deterministic output |
| --- | --- | --- |
| F1 `cluster_activity_ranker` | Registered cluster dataset | particle count × distinct layer count, descending activity; exact root spelling orders ties; competition ranks |
| F2 `ontology_aspect_detector` | Dataset, optional exact `cluster_root` | Layers and all matching canonical phase labels. Triple requires L0+LC+LF; L0+LN mirror, LF+LN bridge, L0+LC grounding. Unspecified multi-layer combinations retain `cross_layer_active`. |
| F3 `fractal_self_similarity_scorer` | Full dataset and explicit ratio 0 < r < 1 | D = log(cluster_count)/log(1/r); input counts and ratio provenance |
| F4 `panini_ontology_profiler` | Dataset, optional exact `cluster_root` | Original kriyā/smṛti profile, JSON source pointer and attribution; other roots explicitly return `profile_not_present_in_source`, without invented citations |
| F5 `concept_intensity_map` | Full dataset | activity + 10 only for triple phase; descending intensity and competition ranks |
| F6 `downstream_module_advisor` | Full dataset | Original suggestions selected by kriyā being most active, smṛti triple phase, or heterogeneous sizes with an isolated particle; recommendations never create modules |

The canonical file does not define the denominator or derivation of `avg_cluster_size_ratio`. F3 refuses to guess: a caller must explicitly supply the ratio; the output identifies this as a caller parameter. It does not assert an independently measured fractal dimension. F4 retains source statements as source statements rather than supplying invented historical verification.

The original says 8 clusters/15 roots/27 particles in different passages. Its size distribution sums to 30 particles, and its expanded intensity ranking sums to 70 rather than the stated denominator 85. These are retained source discrepancies, not rewritten constants. Computation uses the registered snapshot's actual counts and reports its pinned scope. No synthetic full S4 dataset is shipped. Test fixtures are explicitly synthetic and temporary.

## Mother-side installation and data registration

Run `npm ci --ignore-scripts --prefix MRL_Bridge` from this repository checkout. `server.js` already mounts the adapter before its 404 handler. Do not copy an old server over the live mother. Reconcile the installed Bridge revision and preserve an existing deployment snapshot before applying the reviewed commit through its normal deployment process.

The Bridge operator supplies two environment settings through the existing service's protected configuration:

- `MRL_PANINI_READ_API_KEY`: a new read-only capability. It must differ from `MRL_BRIDGE_API_KEY`; the adapter rejects reuse. Never put either key in Git or tool arguments.
- `MRL_PANINI_DATASETS_FILE`: absolute path to the operator-owned catalogue generated below. It must be writable only by the operator/service account. Windows operators should apply the same restrictive ACL policy as existing Bridge configuration; POSIX mode alone does not configure Windows ACLs.

Recover the actual S3.5/S4 originals first. Build a separate normalized projection conforming to `input.schema.json`, retaining each original root and particle ID, unique particle IDs within each cluster, and exact source ref/version/byte SHA-256. A particle can participate in multiple clusters with the same layer; conflicting layer declarations are rejected. F3 reports both distinct particle count and membership count. No Unicode normalization or root renaming is performed. Only L0/LC/LF/LN are admitted in this adapter version.

The normalized projection is not a reconstructed upstream original. The operator must verify the projection against those originals. Byte-pinning proves identity and detects drift; it does not independently prove the semantic mapping or grant canonical approval. S4 must be `v1.0.0`; S3.5 retains the actual version obtained from its original, since this S4.5 file does not specify that version. The actual source files remain unchanged.

The registration command accepts five real positional arguments, in order:

`node MRL_Bridge/panini_cluster_insight/register_dataset.cjs ID NORMALIZED_JSON S4_ORIGINAL S3_5_ORIGINAL NEW_CATALOGUE_JSON`

It reads the three real files, validates input/schema/version/lineage/byte pins, then exclusively creates a new catalogue. It refuses an existing output file. Paths are operator-side only; API callers cannot choose paths, upload replacement data, execute commands or write mother files. Each call rereads the pinned inputs and rejects changed bytes. Missing configuration or datasets returns 503 rather than a sample result.

## API and ChatGPT declaration

Six POST endpoints live under `https://bridge.mrliouword.com/MRL_particle/panini/v1/F1` through `/F6`. Use `Content-Type: application/json`, `User-Agent: MRL-Client/1.0` and the dedicated read capability in `x-api-key`. An example body for F1 is:

```json
{
  "dataset_id": "canonical",
  "expected_schema_version": "panini_cluster_insight/v1.0.0",
  "cluster_root": null,
  "avg_cluster_size_ratio": null
}
```

`canonical` is a chosen dataset ID, not a shipped or automatically registered dataset. For F2/F4, select an exact root or null for all profiles. F1/F3/F5/F6 require `cluster_root: null` so aggregate scope is not silently reduced. F3 requires a numeric ratio; other calls use null. All four keys are required; unknown fields are rejected. `call.schema.json` is the callable contract; `input.schema.json` describes the operator projection, not remote file access.

- **ChatGPT Actions:** import `openapi.json`, configure the dedicated API key as header authentication. It declares all six operations. Live calls require deployment and a registered dataset first.
- **Function tool host:** load `chatgpt_tools.json`; it contains six strict function declarations with the original F1–F6 names. Route an accepted tool call to `invoke(name, arguments)` exported by `mcp_stdio.cjs`. The host must execute this dispatch; a JSON declaration alone does not register a tool in an existing ChatGPT conversation.
- **MCP stdio:** run `node MRL_Bridge/panini_cluster_insight/mcp_stdio.cjs` with `MRL_PANINI_READ_API_KEY` bound and optional `MRL_BRIDGE_BASE_URL` (default: the existing HTTPS Bridge origin). It supports initialize, ping, tools/list and tools/call using the existing mother's 2024-11-05 protocol baseline. It emits JSON-RPC only on stdout, reports tool failures with `isError: true`, rejects redirects/insecure origins, and never falls back to local computation. This is a stdio transport, not a deployed remote HTTP MCP endpoint.

Output includes unchanged canonical identity, S4/S3.5 source refs/versions/hashes, normalized snapshot byte hash, canonical source byte hash, request canonical-JSON hash, implementation version, result and result canonical-JSON hash, and `mutation: false`. The hash scopes differ explicitly: source hashes cover exact bytes; input/result hashes cover sorted-key compact JSON without Unicode folding. They are not interchangeable.

Errors are stable and redact private paths/keys: 401 missing read capability, 403 invalid capability, 409 changed source bytes/version/lineage, 413 request bound, 415 media type, 422 invalid schema/unknown ratio/selector, 503 source/config/dataset unavailable. Existing Bridge admission caps incoming bodies at 10 MiB; Panini additionally caps parsed call bodies at 4 KiB. Individual source files are bounded at 5 MiB. Invalid canonical source hash prevents module loading.

## Reproduce validation

```bash
npm ci --ignore-scripts --prefix MRL_Bridge
node --test MRL_Bridge/panini_cluster_insight/test.cjs MRL_Bridge/test_mrl_bridge_translation_center.cjs
node --check MRL_Bridge/server.js
node MRL_Bridge/panini_cluster_insight/audit.cjs --check
```

`node MRL_Bridge/panini_cluster_insight/contracts.cjs` regenerates the seven checked-in contracts. Tests reject contract drift. `.github/workflows/MRL_Panini_Cluster_Insight.yml` runs read/compute, HTTP, stdio, provenance, source immutability and parent Bridge regression checks without live keys or mother data. The existing Bridge workflow also runs lint/build. Tests do not alter the formal mother originals.

Local verification on 2026-11-01: 28/28 Node regressions passed on Node v24.22.1; repository lint and production build passed. Bridge production dependency audit after updating the pinned Ajv and compatible transitive lock entries reported 0 vulnerabilities. These receipts apply to this checkout; remote exact-head CI is recorded separately by the pull request.

## Observed live boundary — 2026-11-01 Asia/Taipei

- GET `/health`: HTTP 200; application timestamp `2026-11-01T11:55:28.835Z` (19:55:28 Asia/Taipei), `MRL_Bridge_API`, version `3.1.0`, `origin_signature: MrLiouWord`, api/pg/redis true. This verifies the health endpoint only.
- POST `/MRL_file/list` with fixed `D:\MRL_Mother`, no bound credential: HTTP 401, `API key required`. `MRL_BRIDGE_API_KEY` is not bound in this execution environment. No private read or source mutation took place.
- POST `/MRL_particle/panini/v1/F1`: HTTP 404, `endpoint not found`. The live Bridge has not installed this branch's new route.
- Actual S3.5/S4 canonical dataset execution: **NOT VERIFIED**. Live F1–F6 and ChatGPT registered-tool invocation: **NOT VERIFIED**. Branch code/tests are not deployment receipts.

Dependency chain: original S3.5 + S4 → separately verified projection + byte pins → existing MRL_Bridge auth/admission/audit → S4.5 engine → API/OpenAPI/function dispatch/MCP stdio → carrier result → S5 priority consumer. The code does not implement or claim the downstream S5/S6/S7 stages.
