const http = require("http");
const port = process.env.MRL_PORT || 8790;
function get(path) {
  return new Promise((resolve, reject) => {
    http.get(`http://127.0.0.1:${port}${path}`, res => {
      let data = "";
      res.on("data", chunk => data += chunk);
      res.on("end", () => resolve({ status: res.statusCode, body: data }));
    }).on("error", reject);
  });
}
(async () => {
  const health = await get("/health");
  const state = await get("/mrl/state");
  if (health.status !== 200) throw new Error("MRL health failed");
  if (state.status !== 200) throw new Error("MRL state failed");
  const parsed = JSON.parse(state.body);
  const required = [
    "MRL_World_Module",
    "MRL_平行世界模組",
    "MRL_AI",
    "MRL_AGI",
    "MRL_ASI",
    "MRL_World",
    "MRL_感知力核心",
    "MRL_多世界同步",
    "MRL_回放回復",
    "MRL_主權層"
  ];
  for (const key of required) {
    if (!parsed.modules[key]) {
      throw new Error(`missing module: ${key}`);
    }
  }
  if (parsed.origin_signature !== "MrLiouWord") {
    throw new Error("origin_signature mismatch");
  }
  console.log("MRL_COMPLETE_STATE_ACCEPTANCE_PASS");
})();
