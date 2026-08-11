import { resolve } from "node:path";
import { ENGINES, MODES, VOICE_MODES } from "./constants.js";
import { BridgeError } from "./errors.js";

function enumValue(value, allowed, name, fallback) {
  const normalized = String(value ?? fallback).trim().toLowerCase();
  if (!allowed.includes(normalized)) {
    throw new BridgeError(`${name} must be one of: ${allowed.join(", ")}`, {
      code: "INVALID_CONFIG",
    });
  }
  return normalized;
}

function portValue(value) {
  const port = Number(value ?? 8788);
  if (!Number.isInteger(port) || port < 0 || port > 65535) {
    throw new BridgeError("Z8_BRIDGE_PORT must be an integer from 0 to 65535", {
      code: "INVALID_CONFIG",
    });
  }
  return port;
}

export function loadConfig(env = process.env) {
  return {
    host: env.Z8_BRIDGE_HOST || "127.0.0.1",
    port: portValue(env.Z8_BRIDGE_PORT),
    mode: enumValue(env.Z8_BRIDGE_MODE, MODES, "Z8_BRIDGE_MODE", "dry-run"),
    engine: enumValue(env.Z8_AI_ENGINE, ENGINES, "Z8_AI_ENGINE", "qwen-main"),
    voiceMode: enumValue(env.Z8_VOICE_MODE, VOICE_MODES, "Z8_VOICE_MODE", "chatgpt"),
    ledgerPath: resolve(env.Z8_LEDGER_PATH || "./data/z8-particle-ledger.jsonl"),
    controlToken: env.Z8_CONTROL_TOKEN || "",
    deviceSharedSecret: env.Z8_DEVICE_SHARED_SECRET || "",
    lineChannelSecret: env.LINE_CHANNEL_SECRET || "",
    lineChannelAccessToken: env.LINE_CHANNEL_ACCESS_TOKEN || "",
    lineApiBase: env.LINE_API_BASE || "https://api.line.me",
    qwenEndpoint: env.QWEN_ENDPOINT || "",
    qwenModel: env.QWEN_MODEL || "qwen-main",
    museEndpoint: env.MUSE_ENDPOINT || "",
    museModel: env.MUSE_MODEL || "meta/muse-glimmer",
    sttEndpoint: env.LOCAL_STT_ENDPOINT || "",
    chatgptVoiceEndpoint: env.CHATGPT_VOICE_ENDPOINT || "",
    lineVoiceEndpoint: env.LINE_VOICE_ENDPOINT || "",
  };
}

export function dependencyStatus(config) {
  return {
    device_hmac: Boolean(config.deviceSharedSecret),
    control_auth: Boolean(config.controlToken),
    line_webhook_hmac: Boolean(config.lineChannelSecret),
    line_api: Boolean(config.lineChannelAccessToken),
    qwen_main: Boolean(config.qwenEndpoint),
    muse_agent: Boolean(config.museEndpoint),
    local_stt: Boolean(config.sttEndpoint),
    chatgpt_voice: Boolean(config.chatgptVoiceEndpoint),
    line_voice: Boolean(config.lineVoiceEndpoint),
  };
}
