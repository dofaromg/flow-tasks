// MRL_Mother_Launch.js — 母體零依賴上線入口（Node 標準庫，無需 npm install）
// origin_signature: MrLiouWord
//
// 目的：讓「MRL_完整態母體運轉系統」在任何環境(沙盒/DL580/任意主機)都能直接上線運行，
//       不依賴 express。完整版見 MRL_RuntimeServer.js（需 npm install express）。
// 啟動：node MRL_Mother_Launch.js   （或 PORT 由 MRL_PORT 指定，預設 8790）
// 路由與 MRL_RuntimeServer.js 對齊，之後可慢慢更新擴充。

const http = require("http");
const manifest = require("./data/MRL_runtime_gateway_manifest.json");

const {
  convergence_view: MRL_CONVERGENCE_VIEW,
  perception: MRL_PERCEPTION,
  ...MRL_STATE_BASE
} = manifest;

const MRL_STATE = {
  ...MRL_STATE_BASE,
  launcher: "MRL_Mother_Launch (zero-dependency stdlib)"
};

function sendJSON(res, status, obj) {
  const body = JSON.stringify(obj);
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(body),
    "access-control-allow-origin": "*"
  });
  res.end(body);
}

function readBody(req) {
  return new Promise((resolve) => {
    let data = "";
    req.on("data", (c) => (data += c));
    req.on("end", () => {
      try { resolve(data ? JSON.parse(data) : {}); }
      catch { resolve({ _raw: data }); }
    });
  });
}

function sendHTML(res, status, html) {
  res.writeHead(status, {
    "content-type": "text/html; charset=utf-8",
    "content-length": Buffer.byteLength(html)
  });
  res.end(html);
}

// 平台首頁（自包含，無外部依賴）— 對外網域 bridge.mrliouhan.ai 的「臉」
function dashboardHTML() {
  return `<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MRL 完整態母體運轉系統</title>
<style>
:root{color-scheme:dark}body{margin:0;font-family:system-ui,"Noto Sans TC",sans-serif;
background:#0b0d10;color:#e8eef2}header{padding:28px 20px;border-bottom:1px solid #1d2a22;
background:linear-gradient(180deg,#0f1a12,#0b0d10)}h1{margin:0;font-size:22px;color:#8de08a}
.sig{color:#5a7d5a;font-size:13px;margin-top:6px}main{max-width:880px;margin:0 auto;padding:20px}
.card{background:#111418;border:1px solid #1d2a22;border-radius:12px;padding:16px 18px;margin:14px 0}
.card h2{margin:0 0 10px;font-size:15px;color:#8de08a}.row{display:flex;justify-content:space-between;
padding:5px 0;border-bottom:1px solid #161b20;font-size:14px}.k{color:#9fb0a8}.v{color:#cfe}
.b{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px}
.ok{background:#13361a;color:#7ee787}.pend{background:#3a2f12;color:#e3b341}
button{background:#1f6f3f;color:#fff;border:0;border-radius:8px;padding:9px 14px;cursor:pointer;font-size:14px}
pre{background:#0a0c0e;border:1px solid #1d2a22;border-radius:8px;padding:12px;overflow:auto;font-size:13px}
</style></head><body>
<header><h1>🌌 MRL 完整態母體運轉系統</h1>
<div class="sig">origin_signature = MrLiouWord ｜ 權位區分模式 ｜ 入口 MRL_Mother_Launch</div></header>
<main>
<div class="card"><h2>母體狀態</h2><div id="state">載入中…</div></div>
<div class="card"><h2>收斂治理視圖（唯讀）</h2><div id="conv">載入中…</div></div>
<div class="card"><h2>感知力核心</h2>
<button onclick="perceive()">送出感知測試</button><pre id="perc">點上方按鈕</pre></div>
</main>
<script>
async function j(u,o){return (await fetch(u,o)).json()}
(async()=>{
 const s=await j('/mrl/state');
 document.getElementById('state').innerHTML=
   '<div class="row"><span class="k">system</span><span class="v">'+s.system_name+'</span></div>'+
   '<div class="row"><span class="k">status</span><span class="v"><span class="b ok">'+s.status+'</span></span></div>'+
   Object.entries(s.modules).map(([k,v])=>'<div class="row"><span class="k">'+k+'</span><span class="v"><span class="b ok">'+v+'</span></span></div>').join('');
 const c=await j('/api/mrl/runtime/convergence');
 document.getElementById('conv').innerHTML=
   Object.entries(c.active).map(([k,v])=>'<div class="row"><span class="k">'+k+'</span><span class="v"><span class="b ok">'+v+'</span></span></div>').join('')+
   Object.entries(c.pending).map(([k,v])=>'<div class="row"><span class="k">'+k+'</span><span class="v"><span class="b pend">'+v+'</span></span></div>').join('');
})();
async function perceive(){
 const r=await j('/mrl/perceive',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({q:'platform ping'})});
 document.getElementById('perc').textContent=JSON.stringify(r,null,2);
}
</script></body></html>`;
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://localhost");
  const path = url.pathname;

  if (req.method === "GET" && (path === "/" || path === "/index.html")) {
    return sendHTML(res, 200, dashboardHTML());
  }
  if (req.method === "GET" && path === "/health") {
    return sendJSON(res, 200, { ok: true, ...MRL_STATE });
  }
  if (req.method === "GET" && path === "/mrl/state") {
    return sendJSON(res, 200, MRL_STATE);
  }
  if (req.method === "GET" && path === "/api/mrl/runtime/convergence") {
    return sendJSON(res, 200, MRL_CONVERGENCE_VIEW);
  }
  if (req.method === "POST" && path === "/mrl/perceive") {
    const input = await readBody(req);
    return sendJSON(res, 200, {
      ok: true,
      route: MRL_PERCEPTION.route,
      input,
      flow: MRL_PERCEPTION.flow,
      sovereignty: MRL_PERCEPTION.sovereignty
    });
  }
  return sendJSON(res, 404, { ok: false, error: "MRL_ROUTE_NOT_FOUND", path });
});

const port = process.env.MRL_PORT || 8790;
server.listen(port, () => {
  console.log(`MRL Mother (zero-dep launcher) running on port ${port} — origin_signature=MrLiouWord`);
});

module.exports = { server, MRL_STATE, MRL_CONVERGENCE_VIEW };
