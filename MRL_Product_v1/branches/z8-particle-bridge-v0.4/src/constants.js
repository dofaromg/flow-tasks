export const ORIGIN_SIGNATURE = "MrLiouWord";
export const BRANCH = "z8-particle-bridge-v0.4";
export const SCHEMA_VERSION = "0.4.0";

export const PARTICLE_TYPES = Object.freeze({
  XIAOZHI_VOICE: "z8.xiaozhi.voice",
  LINE_TEXT: "z8.line.text",
});

export const MODES = Object.freeze(["dry-run", "apply"]);
export const ENGINES = Object.freeze(["qwen-main", "muse-agent"]);
export const VOICE_MODES = Object.freeze(["chatgpt", "line"]);

export const SOURCE_KIND_MAP = Object.freeze({
  "xiaozhi:voice": PARTICLE_TYPES.XIAOZHI_VOICE,
  "weiliao:text": PARTICLE_TYPES.LINE_TEXT,
  "line:text": PARTICLE_TYPES.LINE_TEXT,
});
