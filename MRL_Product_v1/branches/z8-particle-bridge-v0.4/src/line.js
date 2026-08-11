import { BridgeError, DependencyError } from "./errors.js";

function validateMessages(messages) {
  if (!Array.isArray(messages) || messages.length === 0 || messages.length > 5) {
    throw new BridgeError("LINE messages must contain between 1 and 5 messages", {
      code: "INVALID_LINE_MESSAGE",
    });
  }
  return messages;
}

export class LineMessagingClient {
  constructor({ accessToken, apiBase = "https://api.line.me", fetchImpl = globalThis.fetch } = {}) {
    this.accessToken = accessToken;
    this.apiBase = apiBase.replace(/\/$/, "");
    this.fetch = fetchImpl;
  }

  async request(path, body) {
    if (!this.accessToken) {
      throw new DependencyError("LINE_CHANNEL_ACCESS_TOKEN is required in apply mode", {
        dependency: "LINE_CHANNEL_ACCESS_TOKEN",
      });
    }
    const response = await this.fetch(`${this.apiBase}${path}`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: `Bearer ${this.accessToken}`,
      },
      body: JSON.stringify(body),
    });
    const raw = await response.text();
    if (!response.ok) {
      throw new BridgeError(`LINE Messaging API returned HTTP ${response.status}`, {
        code: "LINE_API_ERROR",
        status: 502,
        details: { response: raw.slice(0, 1000) },
      });
    }
    return raw ? JSON.parse(raw) : { ok: true };
  }

  async reply(replyToken, messages) {
    if (!replyToken) {
      throw new BridgeError("LINE replyToken is required", { code: "INVALID_LINE_REPLY" });
    }
    return this.request("/v2/bot/message/reply", {
      replyToken,
      messages: validateMessages(messages),
    });
  }

  async push(to, messages) {
    if (!to) {
      throw new BridgeError("LINE push target is required", { code: "INVALID_LINE_TARGET" });
    }
    return this.request("/v2/bot/message/push", {
      to,
      messages: validateMessages(messages),
    });
  }
}
