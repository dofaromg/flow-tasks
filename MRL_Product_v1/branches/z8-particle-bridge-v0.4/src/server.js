import http from "node:http";
import { pathToFileURL } from "node:url";
import { dependencyStatus, loadConfig } from "./config.js";
import { loadDotEnv } from "./env.js";
import { BridgeError, DependencyError } from "./errors.js";
import { JsonlLedger } from "./ledger.js";
import { LineMessagingClient } from "./line.js";
import { LocalModelClient, LocalVoiceClient } from "./model.js";
import { Z8BridgeRuntime } from "./runtime.js";
import { safeEqual, verifyDeviceSignature, verifyLineSignature } from "./security.js";

const MAX_BODY_BYTES = 10 * 1024 * 1024;

async function readBody(request) {
  const chunks = [];
  let total = 0;
  for await (const chunk of request) {
    total += chunk.length;
    if (total > MAX_BODY_BYTES) {
      throw new BridgeError("request body exceeds 10 MiB", {
        code: "BODY_TOO_LARGE",
        status: 413,
      });
    }
    chunks.push(chunk);
  }
  return Buffer.concat(chunks);
}

function parseJson(rawBody) {
  try {
    return JSON.parse(rawBody.toString("utf8"));
  } catch {
    throw new BridgeError("request body must be valid JSON", {
      code: "INVALID_JSON",
      status: 400,
    });
  }
}

function sendJson(response, status, body) {
  const payload = Buffer.from(JSON.stringify(body), "utf8");
  response.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": payload.length,
    "cache-control": "no-store",
  });
  response.end(payload);
}

function requireControl(request, config) {
  if (!config.controlToken) {
    throw new DependencyError("Z8_CONTROL_TOKEN is not configured", {
      dependency: "Z8_CONTROL_TOKEN",
    });
  }
  const supplied = request.headers.authorization?.replace(/^Bearer\s+/i, "") ?? "";
  if (!safeEqual(supplied, config.controlToken)) {
    throw new BridgeError("control token rejected", {
      code: "UNAUTHORIZED",
      status: 401,
    });
  }
}

export function buildRuntime(config, { fetchImpl = globalThis.fetch, now } = {}) {
  const ledger = new JsonlLedger(config.ledgerPath, { now });
  const lineClient = new LineMessagingClient({
    accessToken: config.lineChannelAccessToken,
    apiBase: config.lineApiBase,
    fetchImpl,
  });
  const modelClient = new LocalModelClient({
    qwenEndpoint: config.qwenEndpoint,
    qwenModel: config.qwenModel,
    museEndpoint: config.museEndpoint,
    museModel: config.museModel,
    fetchImpl,
  });
  const voiceClient = new LocalVoiceClient({
    sttEndpoint: config.sttEndpoint,
    chatgptVoiceEndpoint: config.chatgptVoiceEndpoint,
    lineVoiceEndpoint: config.lineVoiceEndpoint,
    fetchImpl,
  });
  return new Z8BridgeRuntime({ config, ledger, lineClient, modelClient, voiceClient, now });
}

export function createHttpServer({ config, runtime, logger = console }) {
  return http.createServer(async (request, response) => {
    const url = new URL(request.url, `http://${request.headers.host || "localhost"}`);
    try {
      if (request.method === "GET" && url.pathname === "/health") {
        const records = await runtime.ledger.snapshot();
        sendJson(response, 200, {
          status: "ok",
          service: "MRL_Z8_ParticleBridge",
          version: "0.4.0",
          ...runtime.state(),
          dependencies: dependencyStatus(config),
          ledger_records: records.length,
        });
        return;
      }

      if (request.method === "POST" && url.pathname === "/v1/z8/events") {
        if (!config.deviceSharedSecret) {
          throw new DependencyError("Z8_DEVICE_SHARED_SECRET is not configured", {
            dependency: "Z8_DEVICE_SHARED_SECRET",
          });
        }
        const rawBody = await readBody(request);
        if (!verifyDeviceSignature(rawBody, request.headers["x-mrl-signature"], config.deviceSharedSecret)) {
          throw new BridgeError("device HMAC rejected", {
            code: "INVALID_DEVICE_SIGNATURE",
            status: 401,
          });
        }
        const result = await runtime.ingestZ8Event(parseJson(rawBody));
        sendJson(response, result.status === "duplicate" ? 200 : 202, result);
        return;
      }

      if (request.method === "POST" && url.pathname === "/webhook/line") {
        if (!config.lineChannelSecret) {
          throw new DependencyError("LINE_CHANNEL_SECRET is not configured", {
            dependency: "LINE_CHANNEL_SECRET",
          });
        }
        const rawBody = await readBody(request);
        if (!verifyLineSignature(rawBody, request.headers["x-line-signature"], config.lineChannelSecret)) {
          throw new BridgeError("LINE raw-body HMAC rejected", {
            code: "INVALID_LINE_SIGNATURE",
            status: 401,
          });
        }
        const payload = parseJson(rawBody);
        sendJson(response, 200, { status: "accepted" });
        setImmediate(() => {
          runtime.ingestLineWebhook(payload).catch(async (error) => {
            await runtime.ledger.append({
              stage: "error",
              entrypoint: "line.webhook",
              code: error.code ?? "UNEXPECTED_ERROR",
              message: error.message,
            });
            logger.error("LINE webhook processing failed", {
              code: error.code ?? "UNEXPECTED_ERROR",
              message: error.message,
            });
          });
        });
        return;
      }

      if (request.method === "GET" && url.pathname === "/v1/ledger") {
        requireControl(request, config);
        const eventId = url.searchParams.get("event_id");
        const records = eventId
          ? await runtime.ledger.findByEventId(eventId)
          : await runtime.ledger.snapshot();
        sendJson(response, 200, { records });
        return;
      }

      if (request.method === "POST" && url.pathname.startsWith("/v1/control/")) {
        requireControl(request, config);
        const rawBody = await readBody(request);
        const body = parseJson(rawBody);
        let result;
        if (url.pathname === "/v1/control/mode") {
          result = await runtime.setMode(String(body.mode ?? "").toLowerCase());
        } else if (url.pathname === "/v1/control/engine") {
          result = await runtime.setEngine(String(body.engine ?? "").toLowerCase());
        } else if (url.pathname === "/v1/control/voice") {
          result = await runtime.setVoiceMode(String(body.voice_mode ?? "").toLowerCase());
        } else if (url.pathname === "/v1/control/revert") {
          result = await runtime.revert(body.event_id, body.reason);
        } else {
          throw new BridgeError("control route not found", { code: "NOT_FOUND", status: 404 });
        }
        sendJson(response, 200, result);
        return;
      }

      throw new BridgeError("route not found", { code: "NOT_FOUND", status: 404 });
    } catch (error) {
      const status = Number(error.status) || 500;
      const code = error.code ?? "INTERNAL_ERROR";
      if (status >= 500) {
        logger.error("Z8 bridge request failed", { code, message: error.message });
      }
      if (!response.headersSent) {
        sendJson(response, status, {
          error: code,
          message: status >= 500 && code === "INTERNAL_ERROR" ? "internal error" : error.message,
          details: error.details,
        });
      } else {
        response.end();
      }
    }
  });
}

export async function main() {
  loadDotEnv();
  const config = loadConfig();
  const runtime = buildRuntime(config);
  await runtime.ledger.load();
  const server = createHttpServer({ config, runtime });
  server.listen(config.port, config.host, () => {
    const address = server.address();
    const port = typeof address === "object" && address ? address.port : config.port;
    console.log(`MRL_Z8_ParticleBridge v0.4 listening on http://${config.host}:${port} (${runtime.mode})`);
  });

  const close = (signal) => {
    console.log(`${signal}: stopping Z8 bridge`);
    server.close(() => process.exit(0));
  };
  process.once("SIGINT", () => close("SIGINT"));
  process.once("SIGTERM", () => close("SIGTERM"));
  return server;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
}
