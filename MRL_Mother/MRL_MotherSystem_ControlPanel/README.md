# MRL_MotherSystem 控制面板（聚集點空間面板）
origin_signature: MrLiouWord

完成 Manus 未竟任務:在已銜接的神經位置建聚集點面板,映射各區域現狀,寫入即同步。

## 部署現況（DL580 實機,當下狀態 2026-06-02 沙盒實測 PASS）
- 部署於 DL580 `D:\mrl\MRL_MotherSystem_ControlPanel.py`,聽埠 **7950**,已註冊開機自啟(schtasks)。
- 聚合 **10/11 條母體神經線**現狀:7500 粒子推理(Qwen2.5-32B)/7700 ASI/7810 推理/
  7811 工具/7812 記憶/7815/7820/7900 FlowAgent/8080 WebConsole/8787。
- `/` 面板 UI(自動 5s 刷新映射現狀)、`/api/aggregate` 聚合 JSON、
  `/api/chat` 代理至 7500 真模型(Qwen2.5-32B)。
- 端到端實測:面板→真模型生成 PASS(6.95s)。

## 連線方式
- Bridge API: `https://bridge.mrliouword.com/MRL_run?key=...&cmd=...`(DL580 指令執行)
- 面板本機: `http://127.0.0.1:7950`(經 cloudflared/反代對外可再掛網域)
