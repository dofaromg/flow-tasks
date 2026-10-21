# Usage Guide - ISA-L RS Encoding Bundle

## Quick Start

```bash
# Build everything
make

# Run demo (creates 8MB random input, encodes with k=4 m=2)
bash scripts/run_demo.sh

# Check output
ls -lh out/data/ out/parity/
cat out/manifest.json
cat out/trace.json
cat out/.merkle_root
```

## Manual Usage

### 1. Direct C Encoder Usage

```bash
# Prepare data shards manually (all must be same size)
mkdir -p input_data
dd if=/dev/urandom of=input_data/shard_00.bin bs=1M count=2
dd if=/dev/urandom of=input_data/shard_01.bin bs=1M count=2
dd if=/dev/urandom of=input_data/shard_02.bin bs=1M count=2
dd if=/dev/urandom of=input_data/shard_03.bin bs=1M count=2

# Encode parity shards
mkdir -p output_parity
./bin/isal_rs_encode \
  --k 4 \
  --m 2 \
  --w 8 \
  --size 2097152 \
  --in input_data \
  --out output_parity

# Result: output_parity/shard_04.bin, shard_05.bin
```

### 2. Go Wrapper Usage (Recommended)

The Go wrapper handles splitting, encoding, and metadata generation:

```bash
# Create test input
dd if=/dev/urandom of=/tmp/myfile.bin bs=1M count=16

# Encode with wrapper
./bin/rswrap \
  --in /tmp/myfile.bin \
  --out /tmp/encoded \
  --k 4 \
  --m 2 \
  --w 8 \
  --persona "my_system_id"

# Output structure:
# /tmp/encoded/
#   data/shard_00.bin ... shard_03.bin  (k data shards)
#   parity/shard_04.bin ... shard_05.bin (m parity shards)
#   manifest.json                        (metadata)
#   trace.json                           (event trace)
#   .merkle_root                         (directory hash)
```

## Parameters

### Reed-Solomon Parameters

- **k**: Number of data shards (minimum 2)
- **m**: Number of parity shards (minimum 1)
- **w**: Galois Field width (currently only 8 supported = GF(2^8))

Common configurations:
- `k=4, m=2`: Can lose any 2 shards, uses 50% extra storage
- `k=6, m=3`: Can lose any 3 shards, uses 50% extra storage
- `k=8, m=2`: Can lose any 2 shards, uses 25% extra storage
- `k=10, m=4`: Can lose any 4 shards, uses 40% extra storage

### Go Wrapper Parameters

```
--in <path>         Input file to encode (required)
--out <dir>         Output directory (default: "out")
--k <int>           Data shards (default: 4)
--m <int>           Parity shards (default: 2)
--w <int>           GF width, only 8 supported (default: 8)
--persona <string>  Persona ID for trace (default: "partner_persona")
```

## Output Files

### manifest.json
Contains complete encoding metadata:
```json
{
  "k": 4,
  "m": 2,
  "w": 8,
  "shard_size": 2097152,
  "input_size": 8388608,
  "input_blake3": "a5a1382804...",
  "data_shards": ["out/data/shard_00.bin", ...],
  "parity_shards": ["out/parity/shard_04.bin", ...]
}
```

### trace.json
Event tracking and merkle root:
```json
{
  "event_id": "60422ace455675fd",
  "rid": "23b94abf71d1e085",
  "tick": 1770620255982348146,
  "persona_id": "partner_persona",
  "merkle_root": "987e201af616e6e83c3e50..."
}
```

### .merkle_root
Deterministic hash of entire output directory for verification

## Integration with Other Systems

### Using Output in Your Pipeline

```bash
# After encoding, you can:

# 1. Verify integrity
EXPECTED_MERKLE=$(cat out/.merkle_root)
ACTUAL_MERKLE=$(bash scripts/merkle_dir.sh out /dev/stdout)
if [ "$EXPECTED_MERKLE" = "$ACTUAL_MERKLE" ]; then
  echo "Integrity verified"
fi

# 2. Archive shards separately
tar -czf data_shards.tar.gz out/data/
tar -czf parity_shards.tar.gz out/parity/

# 3. Distribute to storage nodes
for shard in out/data/*.bin out/parity/*.bin; do
  upload_to_storage "$shard"
done

# 4. Store manifest for later reconstruction
cp out/manifest.json metadata_store/
```

### Decoding (Phase B - Future)

Phase B will add single shard repair capability:
```bash
# Future interface (not yet implemented)
./bin/isal_rs_decode \
  --k 4 --m 2 --w 8 \
  --manifest manifest.json \
  --available "0,1,2,4" \
  --repair 3 \
  --out recovered_shard_03.bin
```

## Troubleshooting

### Build Issues

**ISA-L not found:**
```bash
sudo apt-get update
sudo apt-get install -y libisal-dev
```

**Manual ISA-L path:**
```bash
cd isal_rs_c
make ISAL_INC=/usr/local/include ISAL_LIB=/usr/local/lib
```

### Runtime Issues

**Shard size mismatch:**
All input data shards must be exactly the same size. The Go wrapper handles this automatically by padding.

**Out of memory:**
Large shard sizes may require more memory. Consider splitting input into smaller chunks.

**Merkle root mismatch:**
Ensure no files were modified after encoding. The merkle root is computed over ALL files in the output directory.

## Performance Notes

- ISA-L uses SIMD instructions (SSE, AVX) for acceleration
- Shard size affects performance: 1MB-4MB per shard is optimal
- Encoding throughput: typically 1-3 GB/s on modern CPUs
- Memory usage: approximately `(k+m) * shard_size`

## Security

- BLAKE3 provides cryptographic content addressing
- Merkle root enables tamper detection
- No shell injection vulnerabilities (pure Go implementation)
- All random IDs use crypto/rand for security

## Next Steps

This is Phase A - stable encode pipeline. Phase B will add:
- Single shard repair (decode with missing shards)
- Batch processing support
- Streaming interface
- Performance metrics and benchmarking tools
