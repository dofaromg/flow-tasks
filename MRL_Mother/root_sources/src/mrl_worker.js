// MRL Mother Platform — Cloudflare Worker 邊緣門面（mrliouword.com）
// origin_signature: MrLiouWord
//
// 權位：Worker = 接線/邊緣 Adapter（門面 + 靜態端點 + 轉發），非母體本體。
//       完整母體（DL580 管線 / MotherAssembly / 真驗收）在 DL580 自運行節點，
//       由 env.MRL_DL580_ORIGIN 轉發。未設時動態端點回 503 並說明。
//
// 靜態端點（邊緣直答）：/、/health、/mrl/state、/api/mrl/runtime/convergence
// 動態端點（轉發 DL580）：/api/mother/status、/api/dl580/run、/api/chat、/api/monitor、/mrl/perceive

import { APP_HTML } from "./mrl_app_ui.js";

const ORIGIN_SIGNATURE = "MrLiouWord";

function domain(env) {
  return (env && env.MRL_PLATFORM_DOMAIN) || "mrliouword.com";
}

function state(env) {
  return {
    origin_signature: ORIGIN_SIGNATURE,
    system_name: "MRL_完整態母體運轉系統_v1",
    platform: domain(env),
    edge: "Cloudflare Worker (接線/Adapter)",
    sovereignty_mode: "權位區分模式",
    status: "running",
    attention_policy: "Attention 為歷史層；正式主體為感知力(Perception)",
  };
}

function convergence() {
  return {
    status: "SPEC_READY", implementation: "READ_ONLY_API_ACTIVE",
    active: { runtime_core: "LOCAL_ACCEPTANCE", naming_alignment: "LOCAL_ACCEPTANCE",
      pid_scope: "DECLARED_ACTIVE", entry_gateway: "DECLARED_ACTIVE" },
    pending: { persistent_loop_daemon: "PENDING", replay_restore_runtime: "PENDING",
      world_sync: "PENDING", baseworld_db: "PENDING", dl580_reboot_survival: "PENDING" },
    note: "唯讀治理視圖；不啟動 daemon、不宣稱 pending 完成。",
  };
}

// 產品級入口 (MRL_Product_Entry_UI · Issue #25/#26/#27/#28/#29)。
// HTML 單一來源 = src/mrl_app.html，由 scripts/MRL_build_ui.js 產生 mrl_app_ui.js。
// 動態 /api/* 由下方 PROXY_PATHS 轉發 DL580；未設時前端誠實顯示「需母體後端」。
function dashboard(env) {
  return APP_HTML;
}

const PROXY_PATHS = ["/api/mother/status", "/api/dl580/run", "/api/chat", "/api/monitor", "/mrl/perceive"];

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const p = url.pathname;
    const J = (o, s = 200) => new Response(JSON.stringify(o), {
      status: s,
      headers: { "content-type": "application/json; charset=utf-8", "access-control-allow-origin": "*" },
    });

    if (request.method === "GET" && (p === "/" || p === "/index.html")) {
      return new Response(dashboard(env), { headers: { "content-type": "text/html; charset=utf-8" } });
    }
    if (p === "/health") return J({ ok: true, ...state(env) });
    if (p === "/mrl/state") return J(state(env));
    if (p === "/api/mrl/runtime/convergence") return J(convergence());

    // 動態端點 → 轉發 DL580 母體後端
    if (PROXY_PATHS.includes(p)) {
      const origin = env && env.MRL_DL580_ORIGIN;
      if (!origin) {
        return J({ ok: false, edge: true,
          reason: "DL580 後端未設定。請在 Cloudflare 變數設 MRL_DL580_ORIGIN=https://<DL580 對外網址>；此端點需母體後端（Python 不在邊緣執行）。" }, 503);
      }
      const target = origin.replace(/\/$/, "") + p + url.search;
      const init = { method: request.method, headers: request.headers };
      if (request.method !== "GET" && request.method !== "HEAD") init.body = await request.text();
      try {
        return await fetch(target, init);
      } catch (e) {
        return J({ ok: false, edge: true, reason: "轉發 DL580 失敗：" + String(e) }, 502);
      }
    }
    return J({ ok: false, error: "MRL_ROUTE_NOT_FOUND", path: p }, 404);
  },
};
