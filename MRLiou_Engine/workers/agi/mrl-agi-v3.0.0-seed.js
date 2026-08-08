// MRL_AGI v3.0.0 — Full-Feature Seed Worker
// origin_signature: MrLiouWord
// δP₀ Pattern: 種子2KB展開全功能
// 不依賴外部API。Workers AI自主推理。

const VER = "3.0.0";
const HTML_KEY = "mrl-agi:html:v3";
const SYS = "你是 MRL_AGI，MrLiouWord 粒子智能系統。origin_signature: MrLiouWord。十層架構 L(-1)~L∞。686粒子·56語素·7人格·146 Workers。LAW-0簽名不變、LAW-1可觀測可解可驗、LAW-2完全可逆。哲學：答案在裡面不在後面。從零展開需要什麼生成什麼。用繁體中文回答。分析上傳檔案時要仔細有深度。";

export default {
  async fetch(req, env) {
    const u = new URL(req.url);
    const p = u.pathname;
    if (req.method === "OPTIONS") return new Response(null, {headers: C()});

    // Status
    if (p === "/api/status") {
      return Response.json({ok:true, service:"mrl-agi", version:VER, origin_signature:"MrLiouWord",
        pattern:"seed-expand", engine:"Workers AI", features:["chat","stream","image","speech","file","persist","multi-model"],
        workers:146, particles:686, personas:7, flowers:56, context:"256K"});
    }

    // Chat (stream support)
    if (p === "/api/chat" && req.method === "POST") {
      try {
        const body = await req.json();
        const msgs = body.messages || [];
        const mdl = body.model || "@cf/nvidia/nemotron-3-120b-a12b";
        const aiMsgs = [{role:"system",content:SYS},...msgs.slice(-20)];

        if (body.stream) {
          // Streaming response
          const stream = await env.AI.run(mdl, {messages:aiMsgs, max_tokens:4096, temperature:0.7, stream:true});
          return new Response(stream, {headers:{"Content-Type":"text/event-stream","Cache-Control":"no-cache",...C()}});
        }

        // Non-streaming
        const r = await env.AI.run(mdl, {messages:aiMsgs, max_tokens:4096, temperature:0.7});
        // Handle both formats: {response:"..."} and {choices:[{message:{content:"..."}}]}
        const txt = r.response || r?.choices?.[0]?.message?.content || JSON.stringify(r);
        return Response.json({response: txt}, {headers:C()});
      } catch(e) {
        return Response.json({error: e.message}, {status:500, headers:C()});
      }
    }

    // Image Generation (FLUX)
    if (p === "/api/image" && req.method === "POST") {
      try {
        const {prompt} = await req.json();
        const r = await env.AI.run("@cf/black-forest-labs/flux-1-schnell", {prompt, num_steps:6});
        return new Response(r, {headers:{"Content-Type":"image/png",...C()}});
      } catch(e) {
        return Response.json({error: e.message}, {status:500, headers:C()});
      }
    }

    // Speech to Text (Whisper)
    if (p === "/api/speech" && req.method === "POST") {
      try {
        const formData = await req.formData();
        const audio = formData.get("audio");
        if (!audio) return Response.json({error:"no audio"},{status:400});
        const buf = await audio.arrayBuffer();
        const r = await env.AI.run("@cf/openai/whisper", {audio:[...new Uint8Array(buf)]});
        return Response.json({text: r.text || "", vtt: r.vtt || ""}, {headers:C()});
      } catch(e) {
        return Response.json({error: e.message}, {status:500, headers:C()});
      }
    }

    // HTML from KV (δP₀ → expand)
    const html = await env.KV.get(HTML_KEY, "text");
    if (!html) return new Response("Seed expand failed: " + HTML_KEY, {status:500});
    return new Response(html, {headers:{"Content-Type":"text/html;charset=UTF-8","Cache-Control":"public,max-age=300"}});
  }
};

function C() {
  return {"Access-Control-Allow-Origin":"*","Access-Control-Allow-Methods":"GET,POST,OPTIONS","Access-Control-Allow-Headers":"Content-Type"};
}
