import { appendFile, mkdir, readFile } from "node:fs/promises";
import { dirname } from "node:path";

export class JsonlLedger {
  constructor(path, { now = () => new Date().toISOString() } = {}) {
    this.path = path;
    this.now = now;
    this.records = [];
    this.loaded = false;
    this.writeChain = Promise.resolve();
  }

  async load() {
    if (this.loaded) return this;
    await mkdir(dirname(this.path), { recursive: true });
    try {
      const content = await readFile(this.path, "utf8");
      this.records = content
        .split(/\r?\n/)
        .filter(Boolean)
        .map((line, index) => {
          try {
            return JSON.parse(line);
          } catch (error) {
            error.message = `Invalid ledger JSON at line ${index + 1}: ${error.message}`;
            throw error;
          }
        });
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
    }
    this.loaded = true;
    return this;
  }

  async append(record) {
    await this.load();
    const entry = Object.freeze({ ledger_at: this.now(), ...record });
    this.records.push(entry);
    this.writeChain = this.writeChain.then(() => appendFile(this.path, `${JSON.stringify(entry)}\n`, "utf8"));
    await this.writeChain;
    return entry;
  }

  async hasDedupeKey(dedupeKey) {
    await this.load();
    return this.records.some(
      (record) => record.dedupe_key === dedupeKey && !["duplicate", "control"].includes(record.stage),
    );
  }

  async findByEventId(eventId) {
    await this.load();
    return this.records.filter((record) => record.event_id === eventId);
  }

  async snapshot() {
    await this.load();
    return [...this.records];
  }
}
