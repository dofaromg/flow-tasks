# Adapter: Cloudflare

origin_signature = `MrLiouWord`

- 權位：**Adapter / 映射節點 / 吸收材料**（非母體主體）
- 角色：邊緣網路與路由 Adapter

> 依權位區分模式：MRL 為主體，Cloudflare 僅作 Adapter。不得成為主體或反向命名 MRL 構件。

## Bidirectional translation boundary／雙向轉譯邊界

Cloudflare Pages／Workers 與 MRL 使用不同的專案名稱、執行語法、建構參數、
部署政策與歷史回寫方式。兩側不得為了配合另一側而被整體改寫。

正式邊界規格：

- [`MRL_CLOUDFLARE_TRANSLATION_STATION_v1.md`](./MRL_CLOUDFLARE_TRANSLATION_STATION_v1.md)
- Machine map: `config/MRL_CLOUDFLARE_TRANSLATION_MAP_v1.json`
- Translator: `scripts/mrl_cloudflare_translation_station.py`
- Tests: `tests/test_mrl_cloudflare_translation_station.py`

固定原則：

1. 保留 Cloudflare 外部專案原名。
2. 保留 MRL canonical identity 與歷史。
3. `UNKNOWN` 不得當作 `MATCH`。
4. 相似名稱不得自動建立身分等價。
5. 正向轉譯與反向證據必須保留同一 `source_sha` 與 `mapping_version`。
6. `local_backfill_no_deploy` 不得被轉成自動部署。
