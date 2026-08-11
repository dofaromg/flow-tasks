import { ENGINES, MODES, PARTICLE_TYPES, VOICE_MODES } from "./constants.js";
import { BridgeError, DependencyError } from "./errors.js";
import { mapLineWebhookEvent, mapZ8Event } from "./mapping.js";

function assertChoice(value, choices, name) {
  if (!choices.includes(value)) {
    throw new BridgeError(`${name} must be one of: ${choices.join(", ")}`, {
      code: "INVALID_CONTROL_VALUE",
    });
  }
}

export class Z8BridgeRuntime {
  constructor({ config, ledger, lineClient, modelClient, voiceClient, now = () => new Date().toISOString() }) {
    this.config = config;
    this.ledger = ledger;
    this.line = lineClient;
    this.model = modelClient;
    this.voice = voiceClient;
    this.now = now;
    this.mode = config.mode;
    this.engine = config.engine;
    this.voiceMode = config.voiceMode;
  }

  state() {
    return { mode: this.mode, engine: this.engine, voice_mode: this.voiceMode };
  }

  async setMode(mode) {
    assertChoice(mode, MODES, "mode");
    this.mode = mode;
    await this.ledger.append({ stage: "control", control: "mode", value: mode });
    return this.state();
  }

  async setEngine(engine) {
    assertChoice(engine, ENGINES, "engine");
    this.engine = engine;
    await this.ledger.append({ stage: "control", control: "engine", value: engine });
    return this.state();
  }

  async setVoiceMode(voiceMode) {
    assertChoice(voiceMode, VOICE_MODES, "voice_mode");
    this.voiceMode = voiceMode;
    await this.ledger.append({ stage: "control", control: "voice_mode", value: voiceMode });
    return this.state();
  }

  async recordParticle(particle) {
    const dedupeKey = `${particle.direction}:${particle.source.entry}:${particle.event_id}`;
    if (await this.ledger.hasDedupeKey(dedupeKey)) {
      await this.ledger.append({
        stage: "duplicate",
        dedupe_key: dedupeKey,
        event_id: particle.event_id,
        particle_id: particle.particle_id,
      });
      return { duplicate: true, dedupeKey };
    }
    await this.ledger.append({
      stage: "mapped",
      dedupe_key: dedupeKey,
      event_id: particle.event_id,
      particle_id: particle.particle_id,
      particle,
    });
    return { duplicate: false, dedupeKey };
  }

  async ingestZ8Event(input) {
    const particle = mapZ8Event(input, { now: this.now });
    if (particle.source.entry === "line") {
      throw new BridgeError("LINE events must enter through /webhook/line", {
        code: "WRONG_ENTRYPOINT",
      });
    }
    const recorded = await this.recordParticle(particle);
    if (recorded.duplicate) {
      return { status: "duplicate", particle, ...this.state() };
    }

    if (this.mode === "dry-run") {
      await this.ledger.append({
        stage: "dry-run",
        dedupe_key: recorded.dedupeKey,
        event_id: particle.event_id,
        particle_id: particle.particle_id,
        action: particle.particle_type === PARTICLE_TYPES.LINE_TEXT ? "line.push" : "voice.pipeline",
      });
      return { status: "dry-run", particle, ...this.state() };
    }

    if (particle.particle_type === PARTICLE_TYPES.LINE_TEXT) {
      if (!particle.target?.id) {
        throw new DependencyError("微聊 apply requires a LINE target id", {
          dependency: "event.target.id",
        });
      }
      const result = await this.line.push(particle.target.id, [
        { type: "text", text: particle.payload.text },
      ]);
      await this.ledger.append({
        stage: "applied",
        dedupe_key: recorded.dedupeKey,
        event_id: particle.event_id,
        particle_id: particle.particle_id,
        action: "line.push",
      });
      return { status: "applied", particle, result, ...this.state() };
    }

    const transcript = await this.voice.transcribe(particle.payload.audio);
    const completion = await this.model.complete(transcript.text, {
      engine: this.engine,
      system: "You are the local Z8 voice assistant. Reply concisely in Traditional Chinese.",
    });

    let output;
    if (this.voiceMode === "chatgpt") {
      output = await this.voice.synthesize(completion.text);
    } else {
      if (!particle.target?.id) {
        throw new DependencyError("line voice mode requires a LINE target id", {
          dependency: "event.target.id",
        });
      }
      const audio = await this.voice.synthesizeLine(completion.text);
      output = await this.line.push(particle.target.id, [{
        type: "audio",
        originalContentUrl: audio.audio_url,
        duration: audio.duration_ms,
      }]);
    }
    await this.ledger.append({
      stage: "applied",
      dedupe_key: recorded.dedupeKey,
      event_id: particle.event_id,
      particle_id: particle.particle_id,
      action: this.voiceMode === "chatgpt" ? "voice.chatgpt" : "voice.line",
      transcript: transcript.text,
      response_text: completion.text,
    });
    return { status: "applied", particle, transcript, completion, output, ...this.state() };
  }

  async ingestLineWebhook(payload) {
    const results = [];
    for (const event of payload?.events ?? []) {
      const particle = mapLineWebhookEvent(event, { now: this.now });
      if (!particle) {
        results.push({ status: "ignored", event_type: event?.type ?? "unknown" });
        continue;
      }
      const recorded = await this.recordParticle(particle);
      if (recorded.duplicate) {
        results.push({ status: "duplicate", event_id: particle.event_id });
        continue;
      }
      if (this.mode === "dry-run") {
        await this.ledger.append({
          stage: "dry-run",
          dedupe_key: recorded.dedupeKey,
          event_id: particle.event_id,
          particle_id: particle.particle_id,
          action: "line.reply",
        });
        results.push({ status: "dry-run", particle });
        continue;
      }
      const completion = await this.model.complete(particle.payload.text, {
        engine: this.engine,
        system: "You are the local MRL assistant. Reply concisely in Traditional Chinese.",
      });
      const replyToken = event.replyToken;
      const result = await this.line.reply(replyToken, [{ type: "text", text: completion.text }]);
      await this.ledger.append({
        stage: "applied",
        dedupe_key: recorded.dedupeKey,
        event_id: particle.event_id,
        particle_id: particle.particle_id,
        action: "line.reply",
        response_text: completion.text,
      });
      results.push({ status: "applied", particle, completion, result });
    }
    return results;
  }

  async revert(eventId, reason = "operator requested branch revert") {
    const existing = await this.ledger.findByEventId(eventId);
    if (existing.length === 0) {
      throw new BridgeError(`event not found: ${eventId}`, {
        code: "EVENT_NOT_FOUND",
        status: 404,
      });
    }
    const record = await this.ledger.append({
      stage: "reverted",
      event_id: eventId,
      reason,
      external_effect_recalled: false,
      note: "A delivered LINE message cannot be recalled by this branch.",
    });
    return { status: "reverted", record };
  }
}
