/**
 * particle-system-hub v2.2.0 — 粒子系統中樞控制台
 * 
 * MR.liou Particle Universe Central Hub
 * 統一入口 | 健檢監控 | 層級路由 | 系統拓撲
 * 
 * v2.2.0 Changes (2026-03-17):
 *   - total_workers: 143 → 144 (+ toolbox-router)
 *   - Service Bindings for /health and /full-scan (fixes Worker-to-Worker 1042)
 *   - kernel version updated to v2.0.0 (F++ endpoints added by another session)
 *   - Added particle-toolbox-router to L3
 * v2.1.0 Changes (2026-03-16):
 *   - total_workers: 133 → 143
 *   - 新增 L(-1)-MetaEnv 層
 *   - 新增 MRL管理層 Workers (librarian/bridge/collapse/sync/globe/observer...)
 *   - 健康探測改 /health 端點 (修 Worker-to-Worker subdomain 404 bug)
 *   - 根據 Phase R 實測更新全部 status (64活/42死)
 *   - 新增 /full-scan 端點 (掃描全部143)
 * 
 * Architecture:
 *   L(-1)-MetaEnv → metaenv-ctrl, mrl-particle-collapse-engine
 *   L0-Trust      → particle-auth-gateway, particle-sig-verify
 *   L1-Kernel     → mrl-kernel, particle-boot, particle-atom
 *   L2-Memory     → particle-memory, particle-simhash, particle-reversible
 *   L3-Execution  → particle-pvm, particle-attention, particle-chat
 *   L4-Interface  → mrl-globe, mrl-observer, particle-console
 *   L5-Ecosystem  → particle-registry, particle-sync, mrl-librarian
 *   L6-Flow       → flowagent-mother, particle-fusion, particle-flowagent-api
 *   L7-Meta       → mrliou-metaenv, mrliouword-system, particle-universe-pack
 *   L∞-Apps       → shengai-isp, kiosk-agent, douhua, mrl-care-kit...
 * 
 * origin_signature: MrLiouWord
 * 怎麼過去就怎麼回來
 */

const SUBDOMAIN = "z814241.workers.dev";

const SYSTEM_MAP = {
  meta: {
    name: "MR.liou Particle Universe",
    version: "2.2.0",
    creator: "MRLiouWord",
    philosophy: "怎麼過去就怎麼回來",
    law: "Liou Closure: observable → resolvable → verifiable",
    total_workers: 144,
    subdomain: SUBDOMAIN,
    last_scan: "2026-03-16T21:30:00Z",
    phase_r_result: "101 alive / 42 shell(1042)"
  },

  layers: {
    "L(-1)-MetaEnv": {
      description: "元環境層 — 自我擴縮、快照遷移、崩塌引擎、MetaEnv控制平面",
      particles: [
        { id: "metaenv-ctrl", role: "MetaEnv 9端點控制平面 (spawn/health/policy/attest/snapshot/channel/reverse/lockdown/backtrace)", status: "active", version: "1.0.0" },
        { id: "mrl-particle-collapse-engine", role: "五層崩塌引擎 + LAW-0/1/2 + 通行證 + Schumann 7.83Hz", status: "active", version: "2.1.1" },
        { id: "mrl-cloud-bridge", role: "投影橋接 Guard/Channel/Reverse/Isotope", status: "active", version: "1.0.0" },
        { id: "mrl-network-layer", role: "OSI×MRLiou 8層映射 + Merkle同步 + 粒子路由", status: "active", version: "1.0.0" }
      ]
    },
    "L0-Trust": {
      description: "信任層 — 認證閘道、簽章驗證、權限",
      particles: [
        { id: "particle-auth-gateway", role: "認證閘道 L0 (initialized, bpm=72, guardian)", status: "active", version: "1.1.0" },
        { id: "particle-sig-verify", role: "PGP簽章驗證", status: "active", origin: "Git Trust Model" },
        { id: "particle-permissions", role: "權限控制", status: "active" },
        { id: "particle-privacy", role: "隱私保護", status: "active" }
      ]
    },
    "L1-Kernel": {
      description: "核心層 — ASI核心、啟動、種子、原子結構",
      particles: [
        { id: "mrl-kernel", role: "ASI主核心 (SINDy/Quantum/Attention/放大鏡 + F++ Bridge)", status: "active", version: "2.0.0" },
        { id: "particle-boot", role: "系統啟動", status: "active" },
        { id: "particle-atom", role: "atom_t 40byte 結構", status: "active" },
        { id: "particle-config", role: "系統配置", status: "active" },
        { id: "particle-seedkernel", role: "種子核心", status: "shell" },
        { id: "particle-seed-installer", role: "種子安裝器", status: "shell" }
      ]
    },
    "L2-Memory": {
      description: "記憶層 — SimHash64、可逆引擎、δP₀、MemoryVault",
      particles: [
        { id: "particle-memory", role: "MemoryVault 七層記憶", status: "active" },
        { id: "particle-simhash", role: "SimHash64 語意指紋 (64-bit LSH)", status: "active", version: "1.0.0" },
        { id: "particle-reversible", role: "可逆計算引擎 (20操作+逆映射)", status: "active", version: "1.0.0" },
        { id: "particle-delta", role: "δP₀ 微差分", status: "active" },
        { id: "particle-snapshot", role: "狀態快照", status: "active" },
        { id: "particle-auto-snapshot", role: "自動快照", status: "shell" },
        { id: "particle-memory-loader", role: "記憶載入器", status: "shell" },
        { id: "particle-memory-trainer", role: "記憶訓練器", status: "shell" }
      ]
    },
    "L3-Execution": {
      description: "執行層 — PVM虛擬機、AI閘道、對話、研究",
      particles: [
        { id: "particle-pvm", role: "粒子虛擬機 (25 opcodes, 5 registers)", status: "active", version: "1.0.0" },
        { id: "particle-ai-gateway", role: "AI模型代理 v1-v4", status: "active", origin: "GitLab ai-assist" },
        { id: "particle-chat", role: "Particle Chat v4.2", status: "active" },
        { id: "particle-research", role: "深度研究", status: "active" },
        { id: "particle-deepresearch", role: "深度研究引擎", status: "active" },
        { id: "particle-websearch", role: "網路搜尋", status: "active" },
        { id: "particle-api", role: "API主入口", status: "redirect" },
        { id: "mrl-sync-engine", role: "D1↔KV雙向同步 (5不變量)", status: "active", version: "2.0.0" },
        { id: "particle-toolbox-router", role: "跨Worker統一調度 (Call/Pipeline/Parallel/Fan-out, 16 Service Bindings)", status: "active", version: "1.1.0" }
      ]
    },
    "L4-Interface": {
      description: "介面層 — 世界模組、觀測者、控制台、語音、相機",
      particles: [
        { id: "mrl-globe", role: "世界模組地球儀 (686粒子+F3+F8+294衛星)", status: "active", version: "2.0.0" },
        { id: "mrl-observer", role: "Observer δP₀神經總線", status: "active", version: "1.0.0" },
        { id: "particle-console", role: "系統控制台", status: "active" },
        { id: "particle-browser", role: "瀏覽器粒子", status: "active" },
        { id: "particle-voice", role: "語音處理", status: "active" },
        { id: "particle-speech", role: "語音合成", status: "active" },
        { id: "particle-camera", role: "3D AI Camera", status: "active" },
        { id: "particle-emoji", role: "表情系統", status: "active" },
        { id: "particle-haptic", role: "觸覺回饋", status: "active" },
        { id: "particle-shortcuts", role: "快捷指令", status: "active" }
      ]
    },
    "L5-Ecosystem": {
      description: "生態層 — 圖書館管理員、註冊、同步、健康監控",
      particles: [
        { id: "mrl-librarian", role: "圖書館管理員 (8端點, KV索引)", status: "active", version: "1.0.0" },
        { id: "mrl-health-monitor", role: "統一健康監控", status: "active", version: "1.0.0" },
        { id: "particle-registry", role: "粒子註冊中心", status: "active" },
        { id: "particle-sync", role: "跨平台同步", status: "active" },
        { id: "particle-connector", role: "外部連接器", status: "active" },
        { id: "particle-export", role: "匯出引擎", status: "active" },
        { id: "particle-share", role: "分享系統", status: "active" },
        { id: "particle-skills", role: "技能系統", status: "active" },
        { id: "particle-user", role: "使用者系統", status: "active" },
        { id: "particle-usage", role: "使用量追蹤", status: "active" },
        { id: "particle-search", role: "搜尋引擎", status: "active" },
        { id: "particle-notify", role: "通知系統", status: "active" },
        { id: "particle-error", role: "錯誤處理", status: "active" },
        { id: "particle-style", role: "樣式系統", status: "active" },
        { id: "particle-font", role: "字體系統", status: "active" },
        { id: "particle-darkmode", role: "深色模式", status: "active" },
        { id: "particle-theme", role: "主題系統", status: "active" },
        { id: "particle-time", role: "時間管理", status: "active" },
        { id: "particle-location", role: "位置服務", status: "active" },
        { id: "particle-inspire", role: "靈感引擎", status: "active" },
        { id: "particle-reminder", role: "提醒系統", status: "active" },
        { id: "particle-file", role: "檔案系統", status: "active" },
        { id: "particle-project", role: "專案管理", status: "active" },
        { id: "particle-message", role: "訊息系統", status: "active" },
        { id: "particle-branch", role: "分支管理", status: "active" },
        { id: "particle-artifact", role: "構件管理", status: "active" },
        { id: "particle-diff-chart", role: "差異圖表", status: "shell" },
        { id: "particle-diff-compress", role: "差異壓縮", status: "shell" },
        { id: "particle-diff-tracker", role: "差異追蹤", status: "shell" },
        { id: "particle-diffmerge", role: "差異合併", status: "shell" }
      ]
    },
    "L6-Flow": {
      description: "流動層 — FlowAgent、Persona、注意力、融合引擎",
      particles: [
        { id: "particle-flowagent-api", role: "FlowAgent API", status: "active" },
        { id: "flowagent-mother", role: "FlowAgent 母體", status: "active" },
        { id: "particle-fusion", role: "粒子融合引擎", status: "active" },
        { id: "particle-synapse", role: "突觸連接", status: "active" },
        { id: "particle-attention", role: "MR.liou 注意力機制 (FOCUS→CHECK→SPREAD→REWEIGHT)", status: "active", version: "1.0.0" },
        { id: "particle-health-dashboard", role: "健康儀表板", status: "active" },
        { id: "particle-doctor", role: "系統醫生 (已知: subdomain probe bug)", status: "active" },
        { id: "particle-flowshell", role: "Flow Shell", status: "shell" },
        { id: "particle-hexflow", role: "六角流動", status: "shell" },
        { id: "particle-flowmap", role: "流動拓撲", status: "shell" },
        { id: "particle-flowmap-html", role: "流動拓撲HTML", status: "shell" },
        { id: "particle-flowmap-svg", role: "流動拓撲SVG", status: "shell" },
        { id: "particle-persona-manager", role: "Persona管理器", status: "shell" },
        { id: "particle-persona-loader", role: "Persona載入器", status: "shell" },
        { id: "particle-persona-autoloader", role: "Persona自動載入", status: "shell" },
        { id: "particle-persona-bundle", role: "Persona封包", status: "shell" },
        { id: "particle-persona-diff", role: "Persona差異", status: "shell" },
        { id: "particle-persona-emulator", role: "Persona模擬器", status: "shell" },
        { id: "particle-persona-gui", role: "Persona GUI", status: "shell" }
      ]
    },
    "L7-Meta": {
      description: "元層 — MetaEnv(舊版)、系統全局、宇宙打包、封包系統",
      particles: [
        { id: "mrliou-metaenv", role: "MetaEnv 沙箱 (舊版, 已被 metaenv-ctrl 取代)", status: "legacy" },
        { id: "mrliouword-system", role: "MRLiouWord 系統", status: "active" },
        { id: "particle-universe-pack", role: "宇宙打包", status: "active" },
        { id: "particle-syntax", role: "語法引擎", status: "active" },
        { id: "particle-qflpkg", role: "QFL套件格式", status: "shell" },
        { id: "particle-qflpkg-compress", role: "QFL壓縮", status: "shell" },
        { id: "particle-qflpkg-diff", role: "QFL差異", status: "shell" },
        { id: "particle-qflpkg-loader", role: "QFL載入器", status: "shell" },
        { id: "particle-pkg-creator", role: "套件建立器", status: "shell" },
        { id: "particle-pkg-loader", role: "套件載入器", status: "shell" },
        { id: "particle-unpacker", role: "解包器", status: "shell" },
        { id: "particle-version-tree", role: "版本樹", status: "shell" },
        { id: "particle-replay", role: "重播引擎", status: "shell" },
        { id: "particle-snapshot-export", role: "快照匯出", status: "shell" },
        { id: "particle-syntax-check", role: "語法檢查", status: "shell" },
        { id: "particle-fluin-codec", role: "Fluin編解碼 [REPLACED by Parser v2.0]", status: "replaced" },
        { id: "particle-fluin-expand", role: "Fluin展開", status: "shell" }
      ]
    },
    "Linfinity-Apps": {
      description: "應用層 — 聖愛ISP、豆花、CareOS、Google整合、外部服務",
      particles: [
        { id: "shengai-isp", role: "聖愛ISP案管系統", status: "active" },
        { id: "kiosk-agent", role: "豆花點餐代理", status: "active" },
        { id: "kiosk-api", role: "豆花API", status: "active" },
        { id: "zhizhang-system", role: "紙張系統", status: "active" },
        { id: "mrliouword", role: "MRLiouWord主站", status: "active" },
        { id: "mrliouword-app", role: "MRLiouWord App", status: "active" },
        { id: "mrliouword-private", role: "MRLiouWord私密", status: "active" },
        { id: "mrliouword-ai-gateway", role: "AI閘道", status: "active" },
        { id: "mrliouword-ai-memory", role: "AI記憶", status: "active" },
        { id: "mrliou-partner", role: "夥伴入口", status: "active" },
        { id: "mrliou-l1-gate-runtime", role: "L1閘道運行時", status: "shell" },
        { id: "fluin-lifeform", role: "Fluin生命體", status: "active" },
        { id: "flow-tasks", role: "Flow Tasks", status: "shell" },
        { id: "mrlflow-tasks", role: "MRL Flow Tasks", status: "shell" },
        { id: "particle-gcalendar", role: "Google Calendar", status: "active" },
        { id: "particle-gdrive", role: "Google Drive", status: "active" },
        { id: "particle-gmail", role: "Gmail整合", status: "active" },
        { id: "particle-calendar", role: "行事曆", status: "active" },
        { id: "particle-map", role: "地圖服務", status: "active" },
        { id: "mrl-care-kit", role: "教養院套件", status: "shell" },
        { id: "mrl-esign", role: "電子簽名", status: "shell" },
        { id: "mrl-flow-forge", role: "Flow Forge", status: "shell" },
        { id: "mrl-forge-gateway", role: "Forge閘道", status: "shell" },
        { id: "mrl-forge-loop", role: "Forge迴圈", status: "shell" },
        { id: "mrl-forge-seal", role: "Forge封印", status: "shell" },
        { id: "mrl-form-engine", role: "表單引擎", status: "shell" },
        { id: "mrl-messaging", role: "訊息系統", status: "shell" },
        { id: "mrl-schedule-kit", role: "排程套件", status: "shell" },
        { id: "mrl-voice-io", role: "語音IO", status: "shell" },
        { id: "particle-agent-emulator", role: "代理模擬器", status: "shell" },
        { id: "particle-autopack", role: "自動打包", status: "shell" },
        { id: "particle-dev-cli", role: "開發CLI", status: "shell" },
        { id: "particle-dualsim", role: "雙卡模擬", status: "shell" },
        { id: "particle-flow-cli", role: "Flow CLI", status: "shell" },
        { id: "particle-modules-loader", role: "模組載入器", status: "shell" },
        { id: "particle-patch", role: "修補系統", status: "shell" }
      ]
    }
  },

  storage: {
    kv: [
      { id: "mrliouword-vault", nsid: "01275832766148bfbcaa00ee4aeb9946", role: "主金庫" },
      { id: "particle-auth-vault", nsid: "8cd99b4a67f74afea367f394995d5c50", role: "認證金庫 (通行證+hexsig)" },
      { id: "3d-camera-origin", role: "3D相機來源" },
      { id: "kiosk-douhua-cache", role: "豆花快取" },
      { id: "kiosk-douhua-assets", role: "豆花資源" },
      { id: "shengai-isp-cache", role: "聖愛ISP快取" },
      { id: "mrl-physics-vault", role: "物理金庫" }
    ],
    d1: [
      { name: "mrliouword-db", id: "7980baaf-48d3-43cc-8be7-dd8c9590f3d1", role: "主資料庫 (23表/100資源/211標籤)" },
      { name: "mrl-ai-db", role: "AI資料庫" },
      { name: "kiosk-douhua-db", role: "豆花資料庫" },
      { name: "hcra-spec-db", role: "HCRA規格庫" },
      { name: "shengai-isp-db", role: "聖愛ISP庫" },
      { name: "careos-db", id: "bcc5aaaa-474d-43ee-a290-9c141ef71763", role: "CareOS資料庫" }
    ],
    r2: [
      { name: "mrlioubook", role: "電子書存儲" },
      { name: "mrl-tools", role: "工具存儲" },
      { name: "kiosk-douhua-images", role: "豆花圖片" },
      { name: "shengai-isp-files", role: "聖愛ISP檔案" }
    ]
  },

  trust_chain: {
    flow: "metaenv-ctrl(L-1) → collapse-engine(L-1) → auth-gateway(L0) → kernel(L1) → ai-gateway(L3) → chat(L3) → memory(L2) → metaenv(L7)",
    principle: "每個粒子可獨立驗證、可逆回溯、完整自足",
    git_mapping: "SHA-1 chain → SimHash64 fingerprint chain",
    passports: ["passport:unbound:v1", "passport:origin:v1"],
    hexsig: "LIOU-CORE-FLOW-PASS-UNBOUND-20250804"
  }
};

// Service Bindings map: particle-id → env binding name
const BINDING_MAP = {
  "metaenv-ctrl": "METAENV",
  "mrl-particle-collapse-engine": "COLLAPSE",
  "mrl-cloud-bridge": "BRIDGE",
  "mrl-network-layer": "NETWORK",
  "particle-auth-gateway": "AUTH",
  "mrl-kernel": "KERNEL",
  "particle-pvm": "PVM",
  "particle-attention": "ATTENTION",
  "particle-simhash": "SIMHASH",
  "particle-reversible": "REVERSIBLE",
  "mrl-sync-engine": "SYNC",
  "particle-toolbox-router": "TOOLBOX",
  "mrl-globe": "GLOBE",
  "mrl-observer": "OBSERVER",
  "mrl-librarian": "LIBRARIAN",
  "mrl-health-monitor": "MONITOR"
};

// ─── Helper: count particles by status ───
function countByStatus(layers) {
  let active = 0, shell = 0, legacy = 0, replaced = 0, redirect = 0;
  for (const data of Object.values(layers)) {
    for (const p of data.particles) {
      if (p.status === "active") active++;
      else if (p.status === "shell") shell++;
      else if (p.status === "legacy") legacy++;
      else if (p.status === "replaced") replaced++;
      else if (p.status === "redirect") redirect++;
    }
  }
  return { active, shell, legacy, replaced, redirect, total: active + shell + legacy + replaced + redirect };
}

// ─── Route Handler ───
export default {
  async fetch(request, env) {
    const _env = env;
    const url = new URL(request.url);
    const path = url.pathname;

    const cors = {
      "Content-Type": "application/json; charset=utf-8",
      "Access-Control-Allow-Origin": "*",
      "X-Particle-System": "hub",
      "X-Particle-Layer": "L-Root",
      "X-Origin-Signature": "MrLiouWord"
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: { ...cors, "Access-Control-Allow-Methods": "GET, POST, OPTIONS" } });
    }

    const json = (data, status = 200) => new Response(JSON.stringify(data, null, 2), { status, headers: cors });

    // ── Root: System Overview ──
    if (path === "/" || path === "") {
      const counts = countByStatus(SYSTEM_MAP.layers);
      return json({
        particle: "system-hub",
        layer: "L-Root",
        law: "liou-closure",
        timestamp: new Date().toISOString(),
        origin_signature: "MrLiouWord",
        system: {
          ...SYSTEM_MAP.meta,
          active_particles: counts.active,
          shell_particles: counts.shell,
          layers_count: Object.keys(SYSTEM_MAP.layers).length,
          storage: {
            kv_namespaces: SYSTEM_MAP.storage.kv.length,
            d1_databases: SYSTEM_MAP.storage.d1.length,
            r2_buckets: SYSTEM_MAP.storage.r2.length
          }
        },
        endpoints: {
          overview: "/",
          layers: "/layers",
          layer_detail: "/layers/L0 ... /layers/L7 | /layers/L(-1) | /layers/Linfinity",
          health: "/health",
          "full-scan": "/full-scan (probes ALL 143 Workers)",
          topology: "/topology",
          storage: "/storage",
          trust: "/trust",
          particle: "/particle/:id",
          dormant: "/dormant",
          shells: "/shells",
          wake: "POST /wake/:id"
        }
      });
    }

    // ── Layers Overview ──
    if (path === "/layers") {
      const summary = {};
      for (const [layer, data] of Object.entries(SYSTEM_MAP.layers)) {
        summary[layer] = {
          description: data.description,
          total: data.particles.length,
          active: data.particles.filter(p => p.status === "active").length,
          shell: data.particles.filter(p => p.status === "shell").length,
          particles: data.particles.map(p => ({ id: p.id, role: p.role, status: p.status, version: p.version || null }))
        };
      }
      return json({ particle: "system-hub", layer: "L-Root", timestamp: new Date().toISOString(), origin_signature: "MrLiouWord", layers: summary });
    }

    // ── Layer Detail ──
    const layerMatch = path.match(/^\/layers\/(L\(-1\)|L[0-7]|Linfinity)/i);
    if (layerMatch) {
      const search = layerMatch[1].toLowerCase();
      const layerKey = Object.keys(SYSTEM_MAP.layers).find(k => k.toLowerCase().includes(search));
      if (layerKey) {
        const layer = SYSTEM_MAP.layers[layerKey];
        return json({
          particle: "system-hub", layer: layerKey, timestamp: new Date().toISOString(),
          data: {
            ...layer,
            particles: layer.particles.map(p => ({
              ...p,
              url: `https://${p.id}.${SUBDOMAIN}`
            }))
          }
        });
      }
    }

    // ── Health Check (probe active Workers via /health, using Service Bindings when available) ──
    if (path === "/health") {
      const allActive = Object.entries(SYSTEM_MAP.layers)
        .flatMap(([layer, data]) => data.particles
          .filter(p => p.status === "active")
          .map(p => ({ ...p, layer })));

      const results = await Promise.allSettled(
        allActive.map(async (p) => {
          const start = Date.now();
          try {
            const bindingName = BINDING_MAP[p.id];
            const binding = bindingName ? _env[bindingName] : null;
            let resp;

            if (binding) {
              // Use Service Binding (avoids subdomain 1042 bug)
              resp = await binding.fetch(new Request("https://internal/health", {
                signal: AbortSignal.timeout(4000)
              }));
              if (resp.status === 404 || resp.status === 405) {
                resp = await binding.fetch(new Request("https://internal/", {
                  signal: AbortSignal.timeout(3000)
                }));
              }
            } else {
              // Fallback to subdomain (may 1042)
              resp = await fetch(`https://${p.id}.${SUBDOMAIN}/health`, {
                signal: AbortSignal.timeout(4000)
              });
              if (resp.status === 404 || resp.status === 405) {
                resp = await fetch(`https://${p.id}.${SUBDOMAIN}/`, {
                  signal: AbortSignal.timeout(3000)
                });
              }
            }
            const alive = resp.status >= 200 && resp.status < 400;
            return { id: p.id, layer: p.layer, http: resp.status, ms: Date.now() - start, alive, binding: !!binding };
          } catch (e) {
            return { id: p.id, layer: p.layer, http: 0, ms: Date.now() - start, alive: false, error: e.message };
          }
        })
      );

      const health = results.map(r => r.status === "fulfilled" ? r.value : { error: String(r.reason) });
      const alive = health.filter(h => h.alive).length;
      const totalMs = health.reduce((s, h) => s + (h.ms || 0), 0);

      return json({
        particle: "system-hub", layer: "L-Root", timestamp: new Date().toISOString(),
        origin_signature: "MrLiouWord",
        health: {
          probed: health.length,
          alive,
          dead: health.length - alive,
          avg_ms: health.length ? Math.round(totalMs / health.length) : 0,
          results: health
        }
      });
    }

    // ── Full Scan (probe ALL 144 Workers, Service Bindings when available) ──
    if (path === "/full-scan") {
      const ALL_WORKERS = Object.values(SYSTEM_MAP.layers)
        .flatMap(data => data.particles.map(p => p.id));

      const batchSize = 20;
      const allResults = [];

      for (let i = 0; i < ALL_WORKERS.length; i += batchSize) {
        const batch = ALL_WORKERS.slice(i, i + batchSize);
        const batchResults = await Promise.allSettled(
          batch.map(async (id) => {
            const start = Date.now();
            try {
              const bindingName = BINDING_MAP[id];
              const binding = bindingName ? _env[bindingName] : null;
              let resp;

              if (binding) {
                resp = await binding.fetch(new Request("https://internal/health", {
                  signal: AbortSignal.timeout(3000)
                }));
                if (resp.status === 404 || resp.status === 405) {
                  resp = await binding.fetch(new Request("https://internal/", {
                    signal: AbortSignal.timeout(2000)
                  }));
                }
              } else {
                resp = await fetch(`https://${id}.${SUBDOMAIN}/health`, {
                  signal: AbortSignal.timeout(3000)
                });
                if (resp.status === 404 || resp.status === 405) {
                  resp = await fetch(`https://${id}.${SUBDOMAIN}/`, {
                    signal: AbortSignal.timeout(2000)
                  });
                }
              }
              return { id, http: resp.status, ms: Date.now() - start, alive: resp.status >= 200 && resp.status < 400, binding: !!binding };
            } catch (e) {
              return { id, http: 0, ms: Date.now() - start, alive: false };
            }
          })
        );
        allResults.push(...batchResults.map(r => r.status === "fulfilled" ? r.value : { id: "unknown", alive: false }));
      }

      const alive = allResults.filter(r => r.alive);
      const dead = allResults.filter(r => !r.alive);

      return json({
        particle: "system-hub", scan: "full", timestamp: new Date().toISOString(),
        origin_signature: "MrLiouWord",
        summary: { total: allResults.length, alive: alive.length, dead: dead.length },
        alive: alive.map(r => r.id),
        dead: dead.map(r => ({ id: r.id, http: r.http }))
      });
    }

    // ── Topology ──
    if (path === "/topology") {
      return json({
        particle: "system-hub", layer: "L-Root", timestamp: new Date().toISOString(),
        origin_signature: "MrLiouWord",
        topology: {
          trust_chain: SYSTEM_MAP.trust_chain,
          data_flow: {
            input: "User / API Request",
            "L(-1)": "metaenv-ctrl → collapse-engine → cloud-bridge → network-layer",
            L0: "auth-gateway → sig-verify → permissions",
            L1: "kernel → boot → atom → config",
            L2: "memory ←→ simhash ←→ snapshot ←→ reversible ←→ delta",
            L3: "pvm → ai-gateway → chat / research → sync-engine",
            L4: "globe ←→ observer ←→ console ←→ voice ←→ camera",
            L5: "librarian → health-monitor → registry ←→ sync ←→ connector",
            L6: "flowagent-api → mother → fusion → synapse → attention",
            L7: "metaenv(legacy) → universe-pack → version-tree → replay",
            "L∞": "shengai-isp → kiosk → care-kit → gcalendar → gdrive → gmail",
            output: "Response / State Change / δP₀"
          },
          cross_layer: [
            { from: "L(-1):collapse-engine", to: "L0:auth-gateway", type: "passport", protocol: "LAW-0+hexsig" },
            { from: "L(-1):metaenv-ctrl", to: "L(-1):cloud-bridge", type: "channel-map", protocol: "Guard.v1" },
            { from: "L3:chat", to: "L2:memory", type: "read/write", protocol: "LAW-0" },
            { from: "L3:ai-gateway", to: "L0:sig-verify", type: "verify", protocol: "LAW-1" },
            { from: "L6:attention", to: "L2:simhash", type: "fingerprint", protocol: "SimHash64" },
            { from: "L(-1):metaenv-ctrl", to: "L1:config", type: "bootstrap", protocol: "LAW-2" },
            { from: "L4:observer", to: "L6:attention", type: "δP₀-bus", protocol: "Schumann 7.83Hz" },
            { from: "L4:globe", to: "L2:simhash", type: "686-particle-fingerprint", protocol: "F3+F8" },
            { from: "L5:librarian", to: "L(-1):cloud-bridge", type: "index-sync", protocol: "KV" },
            { from: "L∞:shengai-isp", to: "L3:ai-gateway", type: "api-proxy", protocol: "REST" }
          ]
        }
      });
    }

    // ── Storage Map ──
    if (path === "/storage") {
      return json({ particle: "system-hub", layer: "L-Root", timestamp: new Date().toISOString(), origin_signature: "MrLiouWord", storage: SYSTEM_MAP.storage });
    }

    // ── Trust Chain ──
    if (path === "/trust") {
      return json({
        particle: "system-hub", layer: "L-Root", timestamp: new Date().toISOString(),
        origin_signature: "MrLiouWord",
        trust: {
          ...SYSTEM_MAP.trust_chain,
          laws: ["LAW-0: origin_signature不變", "LAW-1: 完整可驗證", "LAW-2: 完全可逆"],
          closure_laws: ["AUTHORITY_INVARIANCE", "NO_DELETE", "ADDITIVE_RESOLUTION"],
          git_evolution: {
            "SHA-1": "SimHash64 semantic fingerprint",
            "GPG signed tag": "blockchain notarization + OpenTimestamps",
            "Object Database": "atom_t + L(-1)-L7 architecture",
            "blob/tree/commit/tag": "4 particle types (data/structure/event/auth)",
            "3-stage workflow": "API → Workers → Notion",
            "pack files": "4-layer cache compression",
            "dangling objects + gc": "MemoryVault lifecycle + wake key"
          }
        }
      });
    }

    // ── Single Particle Info ──
    const particleMatch = path.match(/^\/particle\/(.+)/);
    if (particleMatch) {
      const id = particleMatch[1];
      for (const [layer, data] of Object.entries(SYSTEM_MAP.layers)) {
        const found = data.particles.find(p => p.id === id);
        if (found) {
          return json({
            particle: "system-hub", layer: "L-Root", timestamp: new Date().toISOString(),
            target: { ...found, layer, url: `https://${found.id}.${SUBDOMAIN}`, layer_description: data.description }
          });
        }
      }
      return json({ error: "particle not found", id, hint: "try /layers to see all particles" }, 404);
    }

    // ── Dormant List (legacy compat) ──
    if (path === "/dormant") {
      const dormant = Object.entries(SYSTEM_MAP.layers)
        .flatMap(([layer, data]) => data.particles.filter(p => p.status === "shell" || p.status === "dormant").map(p => ({ ...p, layer })));
      return json({
        particle: "system-hub", layer: "L-Root", timestamp: new Date().toISOString(),
        dormant: { count: dormant.length, particles: dormant }
      });
    }

    // ── Shells List ──
    if (path === "/shells") {
      const shells = Object.entries(SYSTEM_MAP.layers)
        .flatMap(([layer, data]) => data.particles.filter(p => p.status === "shell").map(p => ({ id: p.id, role: p.role, layer })));
      return json({
        particle: "system-hub", layer: "L-Root", timestamp: new Date().toISOString(),
        origin_signature: "MrLiouWord",
        description: "Workers that exist as names but have no code (1042). Available for future implementation.",
        shells: { count: shells.length, particles: shells }
      });
    }

    // ── Wake Particle ──
    const wakeMatch = path.match(/^\/wake\/(.+)/);
    if (wakeMatch && request.method === "POST") {
      const targetId = wakeMatch[1];
      return json({
        particle: "system-hub", action: "wake", target: targetId,
        status: "requires_deployment",
        message: `喚醒 ${targetId} 需要部署實際代碼到 Worker`,
        deploy_method: "curl PUT multipart ES module to Cloudflare API"
      });
    }

    // ── 404 ──
    return json({
      error: "route not found",
      path,
      origin_signature: "MrLiouWord",
      endpoints: ["/", "/layers", "/layers/:layer", "/health", "/full-scan", "/topology", "/storage", "/trust", "/particle/:id", "/dormant", "/shells"]
    }, 404);
  }
};
