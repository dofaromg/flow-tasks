// MRL_Formula_Parameter_Registry_v1 驗收檢查
// 規則：未登錄參數不得進入母體運算；每筆記錄必須可回放、可反推、可比較、可回滾；
// 高影響參數需進 parameter_review，不可自動放行。
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const SCHEMA_PATH = path.join(ROOT, "schemas", "MRL_Formula_Parameter_Record.schema.json");
const REGISTRY_PATH = process.argv[2]
  ? path.resolve(process.argv[2])
  : path.join(ROOT, "data", "MRL_formula_parameter_registry.json");
const ORIGIN_SIGNATURE = "MrLiouWord";

// 必須管控的核心公式參數（6 大類）
const CORE_PARAMETERS = {
  "MRL_創世公式": ["P_k", "N_k", "eta_k"],
  "MRL_放大縮小公式": ["alpha", "beta", "scale_mode"],
  "MRL_反推公式": ["inverse_epsilon", "stability_clip", "loss_bound"],
  "MRL_源代碼壓縮公式": ["compression_ratio", "hash", "simhash", "roundtrip_score"],
  "MRL_環境變化公式": ["context_weight", "runtime_weight", "dependency_weight", "external_noise", "trust_score"],
  "MRL_莫比斯反轉鏡像轉正公式": ["inversion_axis", "mirror_axis", "correction_axis", "orientation_hash", "mismatch_score"]
};

function loadJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function validateRecord(record, schema, errors, label) {
  for (const field of schema.required) {
    if (!(field in record)) {
      errors.push(`${label}: 缺少必填欄位 ${field}`);
    }
  }
  for (const key of Object.keys(record)) {
    if (!(key in schema.properties)) {
      errors.push(`${label}: 未知欄位 ${key}`);
    }
  }
  for (const [key, spec] of Object.entries(schema.properties)) {
    if (!(key in record)) continue;
    const value = record[key];
    if (spec.type === "string" && typeof value !== "string") {
      errors.push(`${label}: ${key} 必須為字串`);
      continue;
    }
    if (spec.type === "boolean" && typeof value !== "boolean") {
      errors.push(`${label}: ${key} 必須為布林值`);
      continue;
    }
    if (spec.enum && !spec.enum.includes(value)) {
      errors.push(`${label}: ${key} 值 ${JSON.stringify(value)} 不在允許範圍 ${JSON.stringify(spec.enum)}`);
    }
    if (spec.const !== undefined && value !== spec.const) {
      errors.push(`${label}: ${key} 必須為 ${JSON.stringify(spec.const)}`);
    }
    if (spec.format === "date-time" && Number.isNaN(Date.parse(value))) {
      errors.push(`${label}: ${key} 不是合法的 date-time`);
    }
  }
}

function checkGovernance(record, errors, label) {
  if (record.origin_signature !== ORIGIN_SIGNATURE) {
    errors.push(`${label}: origin_signature 不符母體簽名`);
  }
  if (JSON.stringify(record.after_value) !== JSON.stringify(record.parameter_value)) {
    errors.push(`${label}: after_value 必須等於 parameter_value（可比較性破壞）`);
  }
  if (typeof record.rollback_ref !== "string" || record.rollback_ref.length === 0) {
    errors.push(`${label}: rollback_ref 為空，變更不可回滾`);
  }
  if (typeof record.change_reason !== "string" || record.change_reason.length === 0) {
    errors.push(`${label}: change_reason 為空`);
  }
  if (record.impact_scope === "high") {
    if (record.replay_required !== true) {
      errors.push(`${label}: 高影響參數必須 replay_required=true（可回放性破壞）`);
    }
    if (!["parameter_review", "verified"].includes(record.verification_status)) {
      errors.push(`${label}: 高影響參數需進 parameter_review，不可自動放行（目前 ${record.verification_status}）`);
    }
  }
}

function buildImpactReport(records) {
  const byImpact = { high: [], medium: [], low: [] };
  const byFormula = {};
  for (const record of records) {
    byImpact[record.impact_scope].push(`${record.formula_name}.${record.parameter_name}`);
    if (!byFormula[record.formula_name]) byFormula[record.formula_name] = [];
    byFormula[record.formula_name].push({
      parameter: record.parameter_name,
      impact_scope: record.impact_scope,
      verification_status: record.verification_status,
      replay_required: record.replay_required,
      rollback_ref: record.rollback_ref
    });
  }
  return {
    report_name: "MRL_Formula_Parameter_Impact_Report_v1",
    origin_signature: ORIGIN_SIGNATURE,
    generated_at: new Date().toISOString(),
    total_parameters: records.length,
    impact_summary: {
      high: byImpact.high.length,
      medium: byImpact.medium.length,
      low: byImpact.low.length
    },
    high_impact_parameters: byImpact.high,
    formulas: byFormula
  };
}

(function main() {
  const errors = [];
  const schema = loadJson(SCHEMA_PATH);
  const registry = loadJson(REGISTRY_PATH);

  if (registry.origin_signature !== ORIGIN_SIGNATURE) {
    errors.push("registry: origin_signature 不符母體簽名");
  }
  if (!Array.isArray(registry.records) || registry.records.length === 0) {
    errors.push("registry: records 為空，未登錄參數不得進入母體運算");
  }

  const registered = new Set();
  for (const record of registry.records || []) {
    const label = `${record.formula_name || "?"}.${record.parameter_name || "?"}`;
    validateRecord(record, schema, errors, label);
    checkGovernance(record, errors, label);
    registered.add(label);
  }

  const missing = [];
  for (const [formula, params] of Object.entries(CORE_PARAMETERS)) {
    for (const param of params) {
      if (!registered.has(`${formula}.${param}`)) {
        missing.push(`${formula}.${param}`);
      }
    }
  }
  if (missing.length > 0) {
    errors.push(`核心公式參數缺少 registry record: ${missing.join(", ")}`);
  }

  const report = buildImpactReport(registry.records || []);
  console.log(JSON.stringify(report, null, 2));

  if (errors.length > 0) {
    for (const err of errors) console.error(`MRL_REGISTRY_ERROR: ${err}`);
    console.error("MRL_FORMULA_PARAMETER_REGISTRY_FAIL");
    process.exit(1);
  }
  console.log("MRL_FORMULA_PARAMETER_REGISTRY_PASS");
})();
