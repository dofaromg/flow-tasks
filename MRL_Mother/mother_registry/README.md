# MRL Mother Registry

This package implements the deterministic local reconstruction core for the MRL
Mother Registry. It discovers every regular file in each **available** source,
creates content-addressed canonical identities, preserves every physical copy as
an evidence record, infers version lineage, validates references, and emits all
machine-readable registries and reproducible report views required by the v1.0
specification.

## Run

```bash
python -m MRL_Mother.mother_registry.registry \
  --source dropbox=/mnt/dropbox \
  --source github=/workspace/repos \
  --source local-runtime=/opt/mrl \
  --output /var/lib/mrl/mother-registry
```

Pass every mounted or exported source with a repeated `--source NAME=PATH`.
Unavailable SaaS sources must first be mounted or exported; the scanner fails
closed for a declared path that does not exist and never pretends it was scanned.
Source names matching the specification are processed in its priority order.

The output directory contains the sixteen cross-referenced JSON registries,
fifteen Markdown reports, and `.scan-cache.json`. Subsequent runs reuse hashes
only when file size and nanosecond modification time are unchanged, while still
rebuilding and validating registry views. Generated output is excluded when it
is located below a scanned source.

## Identity and evidence model

Canonical IDs are UUIDv5 values derived from SHA-256 content hashes. Exact copies
therefore share one identity, while each source/path remains a separate immutable
evidence record. Files with the same normalized logical name but different
content receive distinct IDs and directional `evolved_into` lineage edges. The
registry never deletes or overwrites source evidence.
