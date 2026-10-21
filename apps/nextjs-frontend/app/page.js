// MRLiou control-plane landing (server component). origin_signature: MrLiouWord
const MODULES = [
  { name: 'FireCore Auth', desc: '邊緣身分 / PBKDF2 / refresh 輪替；簽章交 DL580' },
  { name: 'FireCore Store', desc: '文件鏡像 + 版本 + 軟刪除' },
  { name: 'FireCore Vault', desc: '物件註冊；簽章 URL 交 DL580' },
  { name: 'FireCore Live', desc: '有序事件 + poll 訂閱；WS 交 DO 橋接' },
  { name: 'FireCore Push', desc: '裝置註冊 + 派送佇列；派送交 DL580' },
  { name: 'FireCore Trace', desc: '事件收集 + rollup' },
  { name: 'Vector Attention Engine', desc: 'scaled dot-product attention + 相似度檢索' },
  { name: 'Orchestrator', desc: '多步管線 + SimHash 去重' },
];

export default function Home() {
  return (
    <main>
      <h1>🧬 MRLiou Control Plane</h1>
      <p className="lead">© 2025 Mr.liou — 邊緣模組總覽。權威狀態由 DL580 母體 Runtime 持有。</p>
      <p><a href="/api/health" style={{ color: '#c9b8f0' }}>/api/health</a></p>
      <div className="grid">
        {MODULES.map((m) => (
          <div className="card" key={m.name}>
            <h2>{m.name}</h2>
            <p>{m.desc}</p>
          </div>
        ))}
      </div>
      <p className="sig">origin_signature: MrLiouWord</p>
    </main>
  );
}
