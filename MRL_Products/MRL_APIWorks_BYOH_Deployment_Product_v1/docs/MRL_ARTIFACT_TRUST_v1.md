# MRL Runtime Artifact Trust Gate v1

origin_signature: MrLiouWord  
canonical_authority: Mr.liou  
Task: MRL-33; dependency: MRL-32  
Parent: PR #704 exact head `82b657edc314c502e365ebf1f3e3a1d3e1ae4a4e`.
MRL-native extension of `MRL_hardware_admission_v1.py`; upstream repositories retain their identities.

## Contract / 等價 Manifest schema

`MRL_artifact_trust_v1.verify()` enforces the following exact keys (unknown,
missing and empty values deny). This executable validator is the normative schema.

| Object | Required fields / constraints |
|---|---|
| root | schema=`MRL_Artifact_Trust_Manifest_v1`, origin_signature=`MrLiouWord`, artifact, sbom, provenance, signing, exception_approver=`NONE` |
| artifact | id, kind=`wheel`/`native`/`oci_manifest`, version (full numeric release; no latest/main), repository (exact HTTPS GitHub identity), source_commit (40 lowercase hex), digest (`sha256:` + 64 hex), path (confined relative regular file) |
| sbom | path, digest; CycloneDX 1.5 JSON with nonempty components and metadata.component.hashes binding the artifact SHA-256 |
| provenance | path, digest; in-toto Statement v1 / SLSA provenance v1 with exact subject digest, resolvedDependencies repository/gitCommit, and builder identity |
| signing | algorithm=`Ed25519`, fingerprint (SHA-256 of DER SubjectPublicKeyInfo), signature (base64 detached 64-byte signature) |

Publisher signature covers UTF-8 canonical JSON of every root field except
`signing`: sorted keys, separators `,` and `:`, ensure_ascii=False, no NaN.
It therefore binds version, repository, commit, artifact bytes and evidence bytes.
This is an explicitly supported signature profile, not a claim to support every
upstream signature format. Unsupported Sigstore/DSSE/GPG profiles deny until an
adapter is implemented and reviewed. An MRL-created signature cannot replace
missing publisher provenance or prove the publisher's identity.

The separately reviewed `trust/MRL_artifact_trust_policy_v1.json` must contain
an active Ed25519 public key AND an exact allowlist identity containing id, kind,
version, repository, source_commit, digest and fingerprint. Each record also pins
sbom_digest and provenance_digest, plus stage. No keys or artifacts are approved
in the shipped policy. Status `retired`, `revoked`, unknown key and newly presented
key all deny. No artifact may supply its own release trust policy. Policy paths
provided to the standalone offline CLI are operator-selected trusted inputs;
archived policies are not automatically current release authorization.

A `release_approved` record additionally binds a MRL-32 clearance file by path and
digest. Its identity must match, isolation_verified must be true, and approved_by
must be recorded. Only Mr.liou-approved policy changes may introduce such records.
An `isolated_canary` can pass engineering verification with purpose=canary but
release_allowed remains false. LiteLLM 1.106.6 is a requested candidate, not an
approved/safe runtime. No real upstream version/hash/signature is invented here.

## Execution / 離線驗證

Requires Python 3.10+ and OpenSSL 3+ (`openssl` on PATH, or Git for Windows' existing
OpenSSL). Missing verifier fails closed. No package install, network fetch, runtime
import or service operation is performed by the gate.

Run from the product directory with independently obtained evidence:

```sh
python scripts/MRL_artifact_trust_v1.py --manifest incoming/manifest.json --artifact-root incoming --receipt receipt-001.json --export-evidence replay-001
python scripts/MRL_artifact_trust_v1.py --manifest replay-001/MRL_TRUST_MANIFEST.json --policy trust/MRL_artifact_trust_policy_v1.json --artifact-root replay-001 --replay receipt-001.json --receipt replay-receipt-001.json
```

Default purpose is release. Use `--purpose canary` for an isolated candidate;
exit 0 then means canary verification only. Read status and release_allowed.
Receipts include verifier version, verification time, manifest/policy digests,
signature result, identity and denial reasons; outputs use exclusive creation.
Replay rehashes artifacts and evidence and rechecks signatures/current policy.
Changed policy, key, bytes, signature, identity or verifier decisions deny replay.
Replay timestamps are fresh and not compared. Receipts are unsigned audit records;
trust in a receipt never replaces verification. Preserve the executable verifier
version and public policy snapshot alongside the export for historical replay.
For current admission, always use current owner-approved policy.

Evidence export copies only explicit artifact/SBOM/provenance/clearance references
and public manifest/policy/receipt. No recursive input copying or private signing
key collection. It reverifies staged bytes and checks exact file coverage.
OCI mode verifies exported manifest bytes/digest, not downloaded layer blobs or a
running container. Layer/materialization verification is still required before
OCI deployment; composed runtime admission requires actual runner/runtime bytes.

## Existing Admission and bundle integration

`evaluate_delivery()` and `MRL_runtime_delivery_admission_v1.py` compose the existing
hardware gate with trust for BOTH runner and runtime. The signed id/version/digest
and actual paths must match the workload. Hardware receipts never satisfy source
trust; source trust never satisfies hardware acceptance.

```sh
python scripts/MRL_runtime_delivery_admission_v1.py --host host.json --workload workload.json --artifact-paths artifact-paths.json --runtime-manifests runtime-manifests.json --artifact-root incoming --receipt delivery-001.json
```

`runtime-manifests.json` is an object with `runner` and `runtime`, each containing
a complete signed trust manifest. The composed CLI uses the shipped release policy.

The existing source bundle builder remains source-only by default. Optional
`--third-party-runtime path/to/manifest.json --runtime-evidence-root incoming`
adds only release-trust-verified artifacts and their complete replay evidence.
Rejected/canary artifacts raise before ZIP publication. The entire persisted ZIP
is still read back against its actual file inventory. This source package does
not claim formal deployment admission: hardware, licensing, order and DL580 gates
remain separate. Use the composed gate before formal runtime delivery/deployment.
No currently running service or legacy allocation path is activated by this PR.

## Evidence and approvals still missing

| Boundary | Actual state |
|---|---|
| Engineering | Synthetic signatures and negative tests; no fixture is production trust |
| MRL-32 supply-chain isolation | Unresolved; requires exact affected inventory and approved clearance |
| LiteLLM 1.106.6 candidate | No acquired wheel/image, immutable digest, upstream commit/tag binding, publisher key/signature, SBOM or provenance verified |
| Production trust | keys=[], artifacts=[]; default DENY |
| Formal delivery | DENIED until all required gates and owner approvals pass |
| DL580 | No live execution or acceptance performed |

No formal merge, deployment, policy exception, key addition/rotation, license
expansion or MRL-32 clearance is authorized by engineering success. Proposed next
operations must show exact policy diff, issuer fingerprints, affected identities,
rollback and risks for explicit owner approval. Rollback before activation is to
close this draft / leave the branch unused. After a separately approved activation,
revert code and policy as a reviewed change; preserve all historical receipts.

Dependency tree: bundle builder -> trust export -> trust validator -> existing
artifact_digest; composed admission -> hardware.evaluate AND trust for runner/runtime;
CI -> source/parent checksum verifiers + product tests. No parent is replaced.
