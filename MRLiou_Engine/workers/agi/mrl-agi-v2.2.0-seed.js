// MRL_AGI v2.2.0 — Seed Worker (δP₀ Pattern)
// origin_signature: MrLiouWord
// 從0展開，需要什麼生成什麼。
// Worker = 種子，HTML = KV 裡的粒子，需要時展開。

const SYS = "你是 MRL_AGI，MrLiouWord 粒子智能系統。origin_signature: MrLiouWord。十層架構 L(-1)~L∞。686粒子·56語素·7人格·146 Workers。LAW-0簽名不變、LAW-1可觀測可解可驗、LAW-2完全可逆。答案在裡面不在後面。從零展開需要什麼生成什麼。用繁體中文回答。如果使用者上傳了檔案，仔細分析內容。";
const VER = "2.2.0";
const HTML_KEY = "mrl-agi:html:v2.1";

export default {
  async fetch(req, env) {
    const u = new URL(req.url);
    if (req.method === "OPTIONS") return new Response(null, {headers: C()});

    // Status
    if (u.pathname === "/api/status") {
      return Response.json({ok:true, service:"mrl-agi", version:VER, origin_signature:"MrLiouWord",
        pattern:"seed-expand", engine:"Workers AI", workers:146, particles:686, personas:7, flowers:56});
    }

    // Chat — Workers AI
    if (u.pathname === "/api/chat" && req.method === "POST") {
      try {
        const {messages, model} = await req.json();
        const m = model || "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b";
        const r = await env.AI.run(m, {messages:[{role:"system",content:SYS},...(messages||[]).slice(-10)], max_tokens:2048, temperature:0.7});
        return Response.json({response: r.response || JSON.stringify(r)}, {headers:C()});
      } catch(e) {
        return Response.json({error: e.message}, {status:500, headers:C()});
      }
    }

    // HTML — 從 KV 展開 (δP₀ → P₀)
    const html = await env.KV.get(HTML_KEY, "text");
    if (!html) return new Response("種子展開失敗：KV 中找不到 " + HTML_KEY, {status:500});
    return new Response(html, {headers:{"Content-Type":"text/html;charset=UTF-8","Cache-Control":"public,max-age=300"}});
  }
};

function C() {
  return {"Access-Control-Allow-Origin":"*","Access-Control-Allow-Methods":"GET,POST,OPTIONS","Access-Control-Allow-Headers":"Content-Type"};
}
