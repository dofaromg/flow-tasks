/**
 * edge-node-manager — L3 Meta-Edge 邊緣節點管理器
 * origin_signature: MrLiouWord
 * version: 1.0.0
 * 
 * 管理全球 65 個 L3 邊緣節點
 * 
 * 端點：
 *   GET  /                — 總覽
 *   GET  /regions         — 列出所有區域
 *   GET  /nodes           — 列出所有節點
 *   POST /nodes/register  — 註冊新節點
 *   GET  /nodes/:id       — 節點詳情
 *   POST /nodes/:id/heartbeat — 心跳更新
 *   GET  /topology        — 拓撲圖
 */

const ORIGIN = "MrLiouWord";
const VER = "1.0.0";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type,Authorization"
};

function J(d: any, s = 200) {
  return new Response(JSON.stringify(d, null, 2), {
    status: s,
    headers: { "Content-Type": "application/json", ...cors }
  });
}

function OK(d: any) {
  return J({
    ok: true,
    origin_signature: ORIGIN,
    timestamp: new Date().toISOString(),
    ...d
  });
}

function ERR(m: string, s = 400) {
  return J({
    ok: false,
    origin_signature: ORIGIN,
    error: m,
    timestamp: new Date().toISOString()
  }, s);
}

// L3 邊緣節點預設配置（65個主要城市）
const EDGE_NODES_TEMPLATE = [
  // 亞太區域 (20個)
  { region: "APAC", city: "Tokyo", lat: 35.6762, lon: 139.6503, country: "JP" },
  { region: "APAC", city: "Seoul", lat: 37.5665, lon: 126.9780, country: "KR" },
  { region: "APAC", city: "Taipei", lat: 25.0330, lon: 121.5654, country: "TW" },
  { region: "APAC", city: "Hong Kong", lat: 22.3193, lon: 114.1694, country: "HK" },
  { region: "APAC", city: "Singapore", lat: 1.3521, lon: 103.8198, country: "SG" },
  { region: "APAC", city: "Bangkok", lat: 13.7563, lon: 100.5018, country: "TH" },
  { region: "APAC", city: "Mumbai", lat: 19.0760, lon: 72.8777, country: "IN" },
  { region: "APAC", city: "Delhi", lat: 28.7041, lon: 77.1025, country: "IN" },
  { region: "APAC", city: "Sydney", lat: -33.8688, lon: 151.2093, country: "AU" },
  { region: "APAC", city: "Melbourne", lat: -37.8136, lon: 144.9631, country: "AU" },
  { region: "APAC", city: "Shanghai", lat: 31.2304, lon: 121.4737, country: "CN" },
  { region: "APAC", city: "Beijing", lat: 39.9042, lon: 116.4074, country: "CN" },
  { region: "APAC", city: "Osaka", lat: 34.6937, lon: 135.5023, country: "JP" },
  { region: "APAC", city: "Jakarta", lat: -6.2088, lon: 106.8456, country: "ID" },
  { region: "APAC", city: "Manila", lat: 14.5995, lon: 120.9842, country: "PH" },
  { region: "APAC", city: "Ho Chi Minh", lat: 10.8231, lon: 106.6297, country: "VN" },
  { region: "APAC", city: "Kuala Lumpur", lat: 3.1390, lon: 101.6869, country: "MY" },
  { region: "APAC", city: "Auckland", lat: -36.8485, lon: 174.7633, country: "NZ" },
  { region: "APAC", city: "Bengaluru", lat: 12.9716, lon: 77.5946, country: "IN" },
  { region: "APAC", city: "Shenzhen", lat: 22.5431, lon: 114.0579, country: "CN" },

  // 北美區域 (15個)
  { region: "AMER", city: "New York", lat: 40.7128, lon: -74.0060, country: "US" },
  { region: "AMER", city: "San Francisco", lat: 37.7749, lon: -122.4194, country: "US" },
  { region: "AMER", city: "Los Angeles", lat: 34.0522, lon: -118.2437, country: "US" },
  { region: "AMER", city: "Seattle", lat: 47.6062, lon: -122.3321, country: "US" },
  { region: "AMER", city: "Chicago", lat: 41.8781, lon: -87.6298, country: "US" },
  { region: "AMER", city: "Dallas", lat: 32.7767, lon: -96.7970, country: "US" },
  { region: "AMER", city: "Atlanta", lat: 33.7490, lon: -84.3880, country: "US" },
  { region: "AMER", city: "Miami", lat: 25.7617, lon: -80.1918, country: "US" },
  { region: "AMER", city: "Boston", lat: 42.3601, lon: -71.0589, country: "US" },
  { region: "AMER", city: "Toronto", lat: 43.6532, lon: -79.3832, country: "CA" },
  { region: "AMER", city: "Vancouver", lat: 49.2827, lon: -123.1207, country: "CA" },
  { region: "AMER", city: "Mexico City", lat: 19.4326, lon: -99.1332, country: "MX" },
  { region: "AMER", city: "São Paulo", lat: -23.5505, lon: -46.6333, country: "BR" },
  { region: "AMER", city: "Buenos Aires", lat: -34.6037, lon: -58.3816, country: "AR" },
  { region: "AMER", city: "Santiago", lat: -33.4489, lon: -70.6693, country: "CL" },

  // 歐洲區域 (20個)
  { region: "EMEA", city: "London", lat: 51.5074, lon: -0.1278, country: "GB" },
  { region: "EMEA", city: "Paris", lat: 48.8566, lon: 2.3522, country: "FR" },
  { region: "EMEA", city: "Frankfurt", lat: 50.1109, lon: 8.6821, country: "DE" },
  { region: "EMEA", city: "Amsterdam", lat: 52.3676, lon: 4.9041, country: "NL" },
  { region: "EMEA", city: "Madrid", lat: 40.4168, lon: -3.7038, country: "ES" },
  { region: "EMEA", city: "Milan", lat: 45.4642, lon: 9.1900, country: "IT" },
  { region: "EMEA", city: "Stockholm", lat: 59.3293, lon: 18.0686, country: "SE" },
  { region: "EMEA", city: "Zurich", lat: 47.3769, lon: 8.5417, country: "CH" },
  { region: "EMEA", city: "Dublin", lat: 53.3498, lon: -6.2603, country: "IE" },
  { region: "EMEA", city: "Warsaw", lat: 52.2297, lon: 21.0122, country: "PL" },
  { region: "EMEA", city: "Moscow", lat: 55.7558, lon: 37.6173, country: "RU" },
  { region: "EMEA", city: "Istanbul", lat: 41.0082, lon: 28.9784, country: "TR" },
  { region: "EMEA", city: "Dubai", lat: 25.2048, lon: 55.2708, country: "AE" },
  { region: "EMEA", city: "Tel Aviv", lat: 32.0853, lon: 34.7818, country: "IL" },
  { region: "EMEA", city: "Cairo", lat: 30.0444, lon: 31.2357, country: "EG" },
  { region: "EMEA", city: "Johannesburg", lat: -26.2041, lon: 28.0473, country: "ZA" },
  { region: "EMEA", city: "Copenhagen", lat: 55.6761, lon: 12.5683, country: "DK" },
  { region: "EMEA", city: "Vienna", lat: 48.2082, lon: 16.3738, country: "AT" },
  { region: "EMEA", city: "Brussels", lat: 50.8503, lon: 4.3517, country: "BE" },
  { region: "EMEA", city: "Oslo", lat: 59.9139, lon: 10.7522, country: "NO" },

  // 其他區域 (10個)
  { region: "MENA", city: "Riyadh", lat: 24.7136, lon: 46.6753, country: "SA" },
  { region: "MENA", city: "Doha", lat: 25.2854, lon: 51.5310, country: "QA" },
  { region: "MENA", city: "Kuwait City", lat: 29.3759, lon: 47.9774, country: "KW" },
  { region: "MENA", city: "Muscat", lat: 23.5880, lon: 58.3829, country: "OM" },
  { region: "MENA", city: "Manama", lat: 26.0667, lon: 50.5577, country: "BH" },
  { region: "AFRICA", city: "Lagos", lat: 6.5244, lon: 3.3792, country: "NG" },
  { region: "AFRICA", city: "Nairobi", lat: -1.2864, lon: 36.8172, country: "KE" },
  { region: "AFRICA", city: "Casablanca", lat: 33.5731, lon: -7.5898, country: "MA" },
  { region: "AFRICA", city: "Cape Town", lat: -33.9249, lon: 18.4241, country: "ZA" },
  { region: "AFRICA", city: "Accra", lat: 5.6037, lon: -0.1870, country: "GH" },
];

interface Env {
  EDGE_NODES_KV: KVNamespace;
}

function genId(prefix: string): string {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;
    
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: cors });
    }

    // 根路徑
    if (path === "/" || path === "") {
      return OK({
        service: "edge-node-manager",
        version: VER,
        description: "L3 Meta-Edge 邊緣節點管理器 — 管理全球 65 個邊緣節點",
        regions: {
          APAC: 20,
          AMER: 15,
          EMEA: 20,
          MENA: 5,
          AFRICA: 5
        },
        total_nodes: 65,
        endpoints: {
          "GET /regions": "列出所有區域",
          "GET /nodes": "列出所有節點",
          "POST /nodes/register": "註冊新節點",
          "GET /nodes/:id": "節點詳情",
          "POST /nodes/:id/heartbeat": "心跳更新",
          "GET /topology": "拓撲圖"
        }
      });
    }

    // GET /regions
    if (path === "/regions" && request.method === "GET") {
      const regions: any = {
        APAC: { name: "Asia Pacific", nodes: 20, cities: [] },
        AMER: { name: "Americas", nodes: 15, cities: [] },
        EMEA: { name: "Europe, Middle East & Africa", nodes: 20, cities: [] },
        MENA: { name: "Middle East & North Africa", nodes: 5, cities: [] },
        AFRICA: { name: "Africa", nodes: 5, cities: [] }
      };

      for (const node of EDGE_NODES_TEMPLATE) {
        regions[node.region].cities.push(node.city);
      }

      return OK({ regions, total: 65 });
    }

    // GET /nodes
    if (path === "/nodes" && request.method === "GET") {
      // 從 KV 讀取已註冊節點
      const registeredStr = await env.EDGE_NODES_KV.get("registered_nodes");
      const registered = registeredStr ? JSON.parse(registeredStr) : [];

      return OK({
        template_nodes: EDGE_NODES_TEMPLATE.length,
        registered_nodes: registered.length,
        template: EDGE_NODES_TEMPLATE,
        registered
      });
    }

    // POST /nodes/register
    if (path === "/nodes/register" && request.method === "POST") {
      const body: any = await request.json().catch(() => ({}));
      const { city, region, lat, lon, country, provider } = body;

      if (!city || !region) {
        return ERR("需要: city, region");
      }

      const nodeId = genId("medge");
      const node = {
        node_id: nodeId,
        city,
        region,
        latitude: lat || 0,
        longitude: lon || 0,
        country: country || "Unknown",
        provider: provider || "Cloudflare",
        status: "running",
        registered_at: new Date().toISOString(),
        last_heartbeat: new Date().toISOString()
      };

      // 儲存到 KV
      const registeredStr = await env.EDGE_NODES_KV.get("registered_nodes");
      const registered = registeredStr ? JSON.parse(registeredStr) : [];
      registered.push(node);
      await env.EDGE_NODES_KV.put("registered_nodes", JSON.stringify(registered));

      return OK({ message: "節點已註冊", node });
    }

    // POST /nodes/:id/heartbeat
    if (path.startsWith("/nodes/") && path.endsWith("/heartbeat") && request.method === "POST") {
      const nodeId = path.split("/")[2];
      
      const registeredStr = await env.EDGE_NODES_KV.get("registered_nodes");
      const registered = registeredStr ? JSON.parse(registeredStr) : [];
      
      const idx = registered.findIndex((n: any) => n.node_id === nodeId);
      if (idx === -1) {
        return ERR(`節點 ${nodeId} 不存在`, 404);
      }

      registered[idx].last_heartbeat = new Date().toISOString();
      registered[idx].status = "running";
      await env.EDGE_NODES_KV.put("registered_nodes", JSON.stringify(registered));

      return OK({ message: "心跳已更新", node_id: nodeId });
    }

    // GET /topology
    if (path === "/topology" && request.method === "GET") {
      const registeredStr = await env.EDGE_NODES_KV.get("registered_nodes");
      const registered = registeredStr ? JSON.parse(registeredStr) : [];

      return OK({
        layer: "L3-Meta-Edge",
        total_template_nodes: EDGE_NODES_TEMPLATE.length,
        total_registered_nodes: registered.length,
        coverage: {
          APAC: EDGE_NODES_TEMPLATE.filter(n => n.region === "APAC").length,
          AMER: EDGE_NODES_TEMPLATE.filter(n => n.region === "AMER").length,
          EMEA: EDGE_NODES_TEMPLATE.filter(n => n.region === "EMEA").length,
          MENA: EDGE_NODES_TEMPLATE.filter(n => n.region === "MENA").length,
          AFRICA: EDGE_NODES_TEMPLATE.filter(n => n.region === "AFRICA").length
        }
      });
    }

    return ERR("路徑不存在", 404);
  }
};
