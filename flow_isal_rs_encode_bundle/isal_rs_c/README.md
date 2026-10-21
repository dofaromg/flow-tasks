# isal_rs_c

CLI：讀取 k 個 data shards，輸出 m 個 parity shards。

## Build
make

## 用法
./bin/isal_rs_encode --k 4 --m 2 --w 8 --size <shard_bytes> --in <data_dir> --out <parity_dir>

輸入檔名格式：
  <data_dir>/shard_00.bin .. shard_(k-1).bin
輸出檔名格式：
  <parity_dir>/shard_k.bin .. shard_(k+m-1).bin

備註：
- 只做 encode（穩定交付）。
- repair-one 介面預留，預設未實作，避免把交付拖進解碼複雜度。
