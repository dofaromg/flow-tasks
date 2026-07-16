const express = require("express");
const manifest = require("./data/MRL_runtime_gateway_manifest.json");

const app = express();
app.use(express.json());

const {
  convergence_view: MRL_CONVERGENCE_VIEW,
  perception: MRL_PERCEPTION,
  ...MRL_STATE
} = manifest;
app.get("/health", (req, res) => {
  res.json({
    ok: true,
    ...MRL_STATE
  });
});
app.get("/mrl/state", (req, res) => {
  res.json(MRL_STATE);
});
app.get("/api/mrl/runtime/convergence", (req, res) => {
  res.json(MRL_CONVERGENCE_VIEW);
});
app.post("/mrl/perceive", (req, res) => {
  res.json({
    ok: true,
    route: MRL_PERCEPTION.route,
    input: req.body,
    flow: MRL_PERCEPTION.flow,
    sovereignty: MRL_PERCEPTION.sovereignty
  });
});
const port = process.env.MRL_PORT || 8790;
app.listen(port, () => {
  console.log(`MRL Runtime running on port ${port}`);
});
