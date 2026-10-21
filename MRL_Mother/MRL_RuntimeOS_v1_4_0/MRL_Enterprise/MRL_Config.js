const fs = require('fs');
const path = require('path');
function MRL_loadConfig(root) {
  const cfg = {
    product:'MRL_UniversalRuntimeLanguage_Core_v1_2_0',
    origin_signature:'MrLiouWord',
    port:Number(process.env.MRL_PORT || 8788),
    host:process.env.MRL_HOST || '0.0.0.0',
    auth_required:String(process.env.MRL_AUTH_REQUIRED || 'false').toLowerCase() === 'true',
    storage_dir:path.join(root,'MRL_Storage'),
    max_body_bytes:Number(process.env.MRL_MAX_BODY_BYTES || 50*1024*1024)
  };
  fs.mkdirSync(cfg.storage_dir,{recursive:true});
  return cfg;
}
function MRL_validateConfig(cfg) {
  const errors=[];
  if (!cfg.port || cfg.port < 1 || cfg.port > 65535) errors.push('MRL_PORT_INVALID');
  if (cfg.auth_required && !process.env.MRL_API_TOKEN) errors.push('MRL_API_TOKEN_REQUIRED_WHEN_AUTH_ENABLED');
  return { ok:errors.length===0, errors, cfg };
}
module.exports = { MRL_loadConfig, MRL_validateConfig };
