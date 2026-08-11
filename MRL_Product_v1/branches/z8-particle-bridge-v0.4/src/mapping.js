import {
  BRANCH,
  ORIGIN_SIGNATURE,
  PARTICLE_TYPES,
  SCHEMA_VERSION,
  SOURCE_KIND_MAP,
} from "./constants.js";
import { contentId, sha256, stableStringify } from "./canonical.js";
import { BridgeError } from "./errors.js";

function requiredString(value, name) {
  if (typeof value !== "string" || value.trim() === "") {
    throw new BridgeError(`${name} must be a non-empty string`, {
      code: "INVALID_EVENT",
      details: { field: name },
    });
  }
  return value.trim();
}

function normalizeTarget(target) {
  if (target == null) return null;
  const type = target.type ?? "user";
  if (!["user", "group", "room"].includes(type)) {
    throw new BridgeError("target.type must be user, group, or room", {
      code: "INVALID_TARGET",
    });
  }
  return { type, id: requiredString(target.id, "target.id") };
}

function normalizeAudio(audio) {
  if (!audio || typeof audio !== "object") {
    throw new BridgeError("xiaozhi voice event requires audio metadata", {
      code: "INVALID_AUDIO",
    });
  }
  const ref = requiredString(audio.ref, "audio.ref");
  const duration = Number(audio.duration_ms ?? 0);
  if (!Number.isFinite(duration) || duration < 0) {
    throw new BridgeError("audio.duration_ms must be a non-negative number", {
      code: "INVALID_AUDIO",
    });
  }
  return {
    ref,
    codec: requiredString(audio.codec ?? "unknown", "audio.codec"),
    mime_type: requiredString(audio.mime_type ?? "application/octet-stream", "audio.mime_type"),
    duration_ms: Math.round(duration),
    sha256: audio.sha256 ? requiredString(audio.sha256, "audio.sha256").toLowerCase() : null,
  };
}

export function mapZ8Event(input, { now = () => new Date().toISOString() } = {}) {
  if (!input || typeof input !== "object" || Array.isArray(input)) {
    throw new BridgeError("event body must be a JSON object", { code: "INVALID_EVENT" });
  }

  const source = requiredString(input.source, "source").toLowerCase();
  const kind = requiredString(input.kind, "kind").toLowerCase();
  const particleType = SOURCE_KIND_MAP[`${source}:${kind}`];
  if (!particleType) {
    throw new BridgeError(`unsupported mapping: ${source}:${kind}`, {
      code: "UNSUPPORTED_MAPPING",
      details: { supported: Object.keys(SOURCE_KIND_MAP) },
    });
  }

  const eventId = input.event_id
    ? requiredString(input.event_id, "event_id")
    : contentId({ source, kind, device_id: input.device_id, occurred_at: input.occurred_at, text: input.text, audio: input.audio });
  const occurredAt = input.occurred_at ? requiredString(input.occurred_at, "occurred_at") : now();
  const target = normalizeTarget(input.target);

  let payload;
  if (particleType === PARTICLE_TYPES.XIAOZHI_VOICE) {
    payload = { audio: normalizeAudio(input.audio) };
  } else {
    payload = { text: requiredString(input.text, "text") };
  }

  const direction = source === "line" ? "inbound" : "outbound";
  const immutable = {
    event_id: eventId,
    type: particleType,
    direction,
    source,
    kind,
    device_id: input.device_id ? requiredString(input.device_id, "device_id") : null,
    occurred_at: occurredAt,
    target,
    payload,
  };

  return {
    particle_id: contentId(immutable, "z8p"),
    event_id: eventId,
    particle_type: particleType,
    schema_version: SCHEMA_VERSION,
    origin_signature: ORIGIN_SIGNATURE,
    branch: BRANCH,
    direction,
    observed_at: now(),
    source: {
      entry: source,
      device_id: immutable.device_id,
      event_id: eventId,
      occurred_at: occurredAt,
    },
    payload,
    target,
    runtime_path: ["Perception", "Fluin", "Runtime", "Action"],
    integrity: {
      algorithm: "sha256",
      value: sha256(stableStringify(immutable)),
    },
  };
}

export function mapLineWebhookEvent(event, options) {
  if (event?.type !== "message" || event?.message?.type !== "text") {
    return null;
  }
  const source = event.source ?? {};
  const targetId = source.userId ?? source.groupId ?? source.roomId ?? null;
  const targetType = source.userId ? "user" : source.groupId ? "group" : source.roomId ? "room" : "user";
  return mapZ8Event(
    {
      event_id: event.webhookEventId ?? event.message.id,
      source: "line",
      kind: "text",
      occurred_at: event.timestamp ? new Date(event.timestamp).toISOString() : undefined,
      text: event.message.text,
      target: targetId ? { type: targetType, id: targetId } : null,
    },
    options,
  );
}
