import { BridgeError, DependencyError } from "./errors.js";

export class LocalModelClient {
  constructor({ qwenEndpoint, qwenModel, museEndpoint, museModel, fetchImpl = globalThis.fetch } = {}) {
    this.fetch = fetchImpl;
    this.engines = {
      "qwen-main": { endpoint: qwenEndpoint, model: qwenModel || "qwen-main" },
      "muse-agent": { endpoint: museEndpoint, model: museModel || "meta/muse-glimmer" },
    };
  }

  async complete(text, { engine = "qwen-main", system } = {}) {
    const selected = this.engines[engine];
    if (!selected?.endpoint) {
      throw new DependencyError(`${engine} endpoint is not configured`, {
        dependency: engine === "qwen-main" ? "QWEN_ENDPOINT" : "MUSE_ENDPOINT",
      });
    }
    const messages = [];
    if (system) messages.push({ role: "system", content: system });
    messages.push({ role: "user", content: text });
    const response = await this.fetch(selected.endpoint, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ model: selected.model, messages, temperature: 0.2 }),
    });
    const raw = await response.text();
    if (!response.ok) {
      throw new BridgeError(`${engine} returned HTTP ${response.status}`, {
        code: "MODEL_API_ERROR",
        status: 502,
        details: { response: raw.slice(0, 1000) },
      });
    }
    const body = JSON.parse(raw);
    const content = body?.choices?.[0]?.message?.content ?? body?.response ?? body?.text;
    if (typeof content !== "string" || content.trim() === "") {
      throw new BridgeError(`${engine} response did not contain text`, {
        code: "MODEL_RESPONSE_INVALID",
        status: 502,
      });
    }
    return { text: content, engine, model: selected.model };
  }
}

export class LocalVoiceClient {
  constructor({ sttEndpoint, chatgptVoiceEndpoint, lineVoiceEndpoint, fetchImpl = globalThis.fetch } = {}) {
    this.sttEndpoint = sttEndpoint;
    this.chatgptVoiceEndpoint = chatgptVoiceEndpoint;
    this.lineVoiceEndpoint = lineVoiceEndpoint;
    this.fetch = fetchImpl;
  }

  async transcribe(audio) {
    if (!this.sttEndpoint) {
      throw new DependencyError("LOCAL_STT_ENDPOINT is required for 小智 voice apply", {
        dependency: "LOCAL_STT_ENDPOINT",
      });
    }
    const response = await this.fetch(this.sttEndpoint, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ audio }),
    });
    const raw = await response.text();
    if (!response.ok) {
      throw new BridgeError(`STT endpoint returned HTTP ${response.status}`, {
        code: "STT_API_ERROR",
        status: 502,
        details: { response: raw.slice(0, 1000) },
      });
    }
    const body = JSON.parse(raw);
    const text = body.text ?? body.transcript;
    if (typeof text !== "string" || text.trim() === "") {
      throw new BridgeError("STT response did not contain text", {
        code: "STT_RESPONSE_INVALID",
        status: 502,
      });
    }
    return { text };
  }

  async synthesize(text) {
    if (!this.chatgptVoiceEndpoint) {
      throw new DependencyError("CHATGPT_VOICE_ENDPOINT is required for chatgpt voice mode", {
        dependency: "CHATGPT_VOICE_ENDPOINT",
      });
    }
    const response = await this.fetch(this.chatgptVoiceEndpoint, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ input: text, format: "mp3" }),
    });
    const contentType = response.headers.get("content-type") || "";
    if (!response.ok) {
      const raw = await response.text();
      throw new BridgeError(`voice endpoint returned HTTP ${response.status}`, {
        code: "VOICE_API_ERROR",
        status: 502,
        details: { response: raw.slice(0, 1000) },
      });
    }
    if (contentType.includes("application/json")) {
      const body = await response.json();
      return {
        audio_url: body.audio_url ?? body.url ?? null,
        duration_ms: Number(body.duration_ms ?? 0),
        content_type: body.content_type ?? "audio/mpeg",
      };
    }
    const buffer = Buffer.from(await response.arrayBuffer());
    return {
      audio_base64: buffer.toString("base64"),
      duration_ms: 0,
      content_type: contentType || "audio/mpeg",
    };
  }

  async synthesizeLine(text) {
    if (!this.lineVoiceEndpoint) {
      throw new DependencyError("LINE_VOICE_ENDPOINT is required for line voice mode", {
        dependency: "LINE_VOICE_ENDPOINT",
      });
    }
    const response = await this.fetch(this.lineVoiceEndpoint, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ input: text, format: "m4a", transport: "line" }),
    });
    const raw = await response.text();
    if (!response.ok) {
      throw new BridgeError(`LINE voice endpoint returned HTTP ${response.status}`, {
        code: "LINE_VOICE_API_ERROR",
        status: 502,
        details: { response: raw.slice(0, 1000) },
      });
    }
    const body = JSON.parse(raw);
    const audioUrl = body.audio_url ?? body.url;
    const duration = Number(body.duration_ms);
    if (!/^https:\/\//i.test(audioUrl ?? "") || !Number.isInteger(duration) || duration <= 0) {
      throw new BridgeError("LINE voice endpoint must return HTTPS audio_url and positive duration_ms", {
        code: "LINE_VOICE_RESPONSE_INVALID",
        status: 502,
      });
    }
    return { audio_url: audioUrl, duration_ms: duration };
  }
}
