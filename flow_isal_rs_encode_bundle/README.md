# flow_isal_rs_encode_bundle

交付：ISA-L RS(預設 k=4,m=2,w=8) 編碼可執行檔 + Go 封裝器（分片、呼叫、manifest、trace、merkle_root）。

## 需求
- Ubuntu 22.04+ / gcc / make
- Go 1.21+
- ISA-L 已安裝 (libisal, isal.h)
  - 例：sudo apt-get update && sudo apt-get install -y libisal-dev

## Build
make

## Demo
bash scripts/run_demo.sh

## 產出
out/
  data/ shard_00..shard_03
  parity/ shard_04..shard_05
  manifest.json
  trace.json
  .merkle_root
