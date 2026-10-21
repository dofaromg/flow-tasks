# MRL_封存輸出

origin_signature: `MrLiouWord`

封存 zip（`MRL_母體收斂包_v1.zip`）為本包之打包形式，屬可重生二進位產物，
**不入 git**（避免二進位污染）；已另行交付主線。

## 怎麼過去就怎麼回來（重生封存）

```bash
cd <repo root>
python3 MRL_母體收斂包_v1/MRL_源檔索引/_scan.py   # 重新產生 MRL_全域檔案索引.json
zip -r MRL_母體收斂包_v1.zip MRL_母體收斂包_v1/    # 重新打包封存
```

封存內容 = 本資料夾全部文字產物（源檔索引 / 正名表 / 母體分層 / 回返驗證 / SPDX·JWT 對照 / 總報告）。
