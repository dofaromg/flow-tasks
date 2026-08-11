import { readFileSync } from "node:fs";
import { resolve } from "node:path";

export function loadDotEnv(path = resolve(".env"), env = process.env) {
  let content;
  try {
    content = readFileSync(path, "utf8");
  } catch (error) {
    if (error.code === "ENOENT") return env;
    throw error;
  }
  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const separator = line.indexOf("=");
    if (separator < 1) continue;
    const key = line.slice(0, separator).trim();
    let value = line.slice(separator + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    if (env[key] === undefined) env[key] = value;
  }
  return env;
}
