// MRL_AGI v3.0.0 — Full-Feature Seed Worker
// origin_signature: MrLiouWord
// δP₀ Pattern: 種子2KB展開全功能
// 不依賴外部API。Workers AI自主推理。

const VER = "3.1.0";
const HTML_KEY = "mrl-agi:html:v3.1";
const SYS = "你是 MRL_AGI，MrLiouWord 粒子智能系統。origin_signature: MrLiouWord。十層架構 L(-1)~L∞。686粒子·56語素·7人格·146 Workers。LAW-0簽名不變、LAW-1可觀測可解可驗、LAW-2完全可逆。哲學：答案在裡面不在後面。從零展開需要什麼生成什麼。用繁體中文回答。分析上傳檔案和圖片時要仔細有深度。如果收到搜尋結果，根據結果回答使用者的問題。";
const GLOBE = "https://mrl-globe.z814241.workers.dev";
const KERNEL = "https://mrl-kernel.z814241.workers.dev";

export default {
  async fetch(req, env) {
    const u = new URL(req.url);
    const p = u.pathname;
    if (req.method === "OPTIONS") return new Response(null, {headers: C()});

    // Status
    if (p === "/api/status") {
      return Response.json({ok:true, service:"mrl-agi", version:VER, origin_signature:"MrLiouWord",
        pattern:"seed-expand", engine:"Workers AI", features:["chat","stream","image","vision","speech","search","file","persist","multi-model"],
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

    // Vision — Image Analysis (Llama 3.2 11B Vision)
    if (p === "/api/vision" && req.method === "POST") {
      try {
        const formData = await req.formData();
        const image = formData.get("image");
        const question = formData.get("question") || "描述這張圖片的內容";
        if (!image) return Response.json({error:"no image"},{status:400});
        const buf = await image.arrayBuffer();
        const b64 = btoa(String.fromCharCode(...new Uint8Array(buf)));
        const r = await env.AI.run("@cf/meta/llama-3.2-11b-vision-instruct", {
          messages:[{role:"user",content:[
            {type:"text",text:question},
            {type:"image",image:b64}
          ]}], max_tokens:1024
        });
        const txt = r.response || r?.choices?.[0]?.message?.content || JSON.stringify(r);
        return Response.json({response: txt}, {headers:C()});
      } catch(e) {
        return Response.json({error: e.message}, {status:500, headers:C()});
      }
    }

    // Search — 搜尋內部粒子系統 (Globe/Kernel/Flowers/Architecture)
    if (p === "/api/search" && req.method === "POST") {
      try {
        const {query} = await req.json();
        const results = [];
        const fetches = [
          fetch(GLOBE+"/search?q="+encodeURIComponent(query),{signal:AbortSignal.timeout(5000)}).then(r=>r.json()).then(d=>{if(d.results)results.push({source:"Globe",data:d.results.slice(0,5)})}).catch(()=>{}),
          fetch(GLOBE+"/flowers",{signal:AbortSignal.timeout(5000)}).then(r=>r.json()).then(d=>{const fl=(d.flowers||[]).filter(f=>JSON.stringify(f).toLowerCase().includes(query.toLowerCase()));if(fl.length)results.push({source:"Flowers",data:fl.slice(0,5)})}).catch(()=>{}),
          fetch(GLOBE+"/globe/architecture",{signal:AbortSignal.timeout(5000)}).then(r=>r.json()).then(d=>{results.push({source:"Architecture",data:d})}).catch(()=>{}),
          fetch(KERNEL+"/health",{signal:AbortSignal.timeout(5000)}).then(r=>r.json()).then(d=>{results.push({source:"Kernel",data:d})}).catch(()=>{}),
        ];
        await Promise.all(fetches);
        // Feed results to AI for natural answer
        const context = JSON.stringify(results).substring(0,8000);
        const aiMsgs = [{role:"system",content:SYS},{role:"user",content:"使用者搜尋: "+query+"\n\n系統搜尋結果:\n"+context+"\n\n根據以上結果回答使用者的問題。"}];
        const mdl = "@cf/nvidia/nemotron-3-120b-a12b";
        const r = await env.AI.run(mdl, {messages:aiMsgs, max_tokens:2048, temperature:0.5});
        const txt = r.response || r?.choices?.[0]?.message?.content || JSON.stringify(r);
        return Response.json({response:txt, sources:results.map(r=>r.source)}, {headers:C()});
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
