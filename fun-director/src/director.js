'use strict';
/**
 * FunDirector — 爽度導演核心模組
 *
 * 金字塔底層三層架構：
 *   Layer 1 (回饋物理層): Feel Physics 粒子 — 命中停頓/震屏/擊退/布娃娃/道具破壞/連鎖反應
 *   Layer 2 (反轉邏輯層): Twist Logic 粒子 — 身分反轉/規則爆衝/搞笑連鎖
 *   Layer 3 (人格導演層): Persona Director — HYPE/PRANK/SPOOKY
 *
 * 遵循 MrLiouWord 粒子系統哲學：
 *   LAW-0: 起源簽名律 — 輸出帶 origin_signature
 *   LAW-1: 記憶體守恆律 — 每次決策產生可追溯 eventLog
 *   LAW-2: 記憶體單調性律 — 相同 seed 產生可重現輸出
 *
 * @module fun-director/src/director
 * @version 1.0.0
 */

const PARTICLES = require('../fun/particles.json');
const MODULES = require('../fun/modules.json');
const MAPPING = require('../fun/mapping.json');

const ORIGIN_SIGNATURE = 'MrLiouWord.FunDirector';
const DIRECTOR_VERSION = '1.1.0';

// Fibonacci hashing constant (2^32 / φ) — 視窗 seed 衍生，確保跨視窗 seed 不重疊
const GOLDEN_INT = 0x9E3779B9;

// ============================================================
// LAW-2：可重現隨機數生成器 — Mulberry32 PRNG
// ============================================================

/**
 * 將任意 seed 值轉為 32 位無號整數
 * @param {string|number} seed
 * @returns {number}
 */
function seedToNumber(seed) {
  if (typeof seed === 'number') return seed >>> 0;
  let h = 0;
  for (let i = 0; i < seed.length; i++) {
    h = (Math.imul(31, h) + seed.charCodeAt(i)) | 0;
  }
  return h >>> 0;
}

/**
 * Mulberry32 — 快速、高品質的 32 位 PRNG
 * 相同 seed 每次產生相同序列，滿足 LAW-2
 * @param {number} seed
 * @returns {function(): number} 每次呼叫回傳 [0, 1) 的浮點數
 */
function mulberry32(seed) {
  let s = seed >>> 0;
  return function () {
    s += 0x6D2B79F5;
    let t = Math.imul(s ^ (s >>> 15), s | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ============================================================
// 工具函式
// ============================================================

/**
 * 依照 weight 加權隨機選取一個項目
 * @param {function} rng
 * @param {Array<{weight?: number}>} items
 * @returns {object}
 */
function weightedPick(rng, items) {
  if (!items || items.length === 0) throw new Error('weightedPick: items 不可為空');
  const total = items.reduce((s, item) => s + (item.weight || 1), 0);
  let threshold = rng() * total;
  for (const item of items) {
    threshold -= item.weight || 1;
    if (threshold <= 0) return item;
  }
  return items[items.length - 1];
}

/**
 * 根據人格偏好動態調整模組權重
 * @param {Array} modules
 * @param {string} personaId
 * @returns {Array}
 */
function applyPersonaBias(modules, personaId) {
  const persona = PARTICLES.personaDirector.find(p => p.id === personaId);
  if (!persona) return modules;

  return modules.map(mod => {
    let weight = mod.weight;

    // 幽默偏好 → 提升搞笑失控類粒子
    if (persona.bias.humor > 0.4) {
      if (['RAGDOLL', 'COMEDY_CHAIN_REACTION', 'RULE_GLITCH_BURST', 'PROP_BREAK'].includes(mod.id)) {
        weight *= 1 + persona.bias.humor;
      }
    }
    // 刺激偏好 → 提升衝擊感粒子
    if (persona.bias.thrill > 0.3) {
      if (['SCREEN_SHAKE', 'KNOCKBACK', 'CHAIN_REACTION'].includes(mod.id)) {
        weight *= 1 + persona.bias.thrill;
      }
    }
    // 力量偏好 → 提升打擊感粒子
    if (persona.bias.power > 0.3) {
      if (['HIT_STOP', 'KNOCKBACK'].includes(mod.id)) {
        weight *= 1 + persona.bias.power;
      }
    }

    return { ...mod, weight };
  });
}

/**
 * 依照人格 preset 與 rng 噪音計算模組參數
 * @param {string} moduleId
 * @param {string} personaId
 * @param {function} rng
 * @returns {object}
 */
function buildParams(moduleId, personaId, rng) {
  const preset = MAPPING.personaPresets[personaId] || MAPPING.personaPresets['HYPE'];
  const allParticles = [...PARTICLES.feelPhysics, ...PARTICLES.twistLogic];
  const particle = allParticles.find(p => p.id === moduleId);
  if (!particle) return {};

  const params = JSON.parse(JSON.stringify(particle.params));
  const scale = preset.funIntensity || 1.0;
  const chaos = preset.chaos || 1.0;
  // 加入微量隨機噪音（0.8 ~ 1.2），保持每次有細微差異但不影響爽度等級
  const noise = 0.8 + rng() * 0.4;

  if (params.intensity !== undefined) params.intensity = +((params.intensity * scale * noise).toFixed(2));
  if (params.amplitude !== undefined) params.amplitude = Math.round(params.amplitude * scale * noise);
  if (params.force !== undefined) params.force = Math.round(params.force * scale * noise);
  if (params.joint_loose !== undefined) params.joint_loose = Math.min(1.0, +((params.joint_loose * chaos * noise).toFixed(2)));
  if (params.chain_count !== undefined) params.chain_count = Math.max(1, Math.round(params.chain_count * chaos));
  if (params.burst_count !== undefined) params.burst_count = Math.max(1, Math.round(params.burst_count * chaos));
  if (params.laugh_factor !== undefined) params.laugh_factor = +((params.laugh_factor * chaos * noise).toFixed(2));
  if (params.probability !== undefined) params.probability = Math.min(1.0, +((params.probability * chaos).toFixed(2)));

  params.slowMo = preset.slowMo;
  params.vfxScale = +((preset.vfxScale * noise).toFixed(2));
  params.sfxPunch = +((preset.sfxPunch * noise).toFixed(2));

  return params;
}

// ============================================================
// 高衝擊模組 ID 清單 — 用於「保底爆點」邏輯
// ============================================================
const HIGH_IMPACT_IDS = [
  'HIT_STOP', 'SCREEN_SHAKE', 'KNOCKBACK',
  'RAGDOLL', 'CHAIN_REACTION', 'COMEDY_CHAIN_REACTION'
];

// ============================================================
// 導演核心函式
// ============================================================

/**
 * runDirector — 計算下一段（10 秒）要啟動的 twist recipe
 *
 * @param {object} input
 * @param {object}  [input.playerState]   玩家狀態 (hp, combo, position 等)
 * @param {object}  [input.roomState]     房間狀態 (wave, enemyCount, hazards 等)
 * @param {string}  [input.personaState]  人格 ID ('HYPE'|'PRANK'|'SPOOKY')
 * @param {string|number} [input.seed]   隨機種子；相同 seed 必定產生相同輸出（LAW-2）
 *
 * @returns {{
 *   twistRecipe: Array,
 *   duration_s: number,
 *   cooldown_s: number,
 *   persona: string,
 *   eventLog: object,
 *   law: string,
 *   origin_signature: string
 * }}
 */
function runDirector({
  playerState = {},
  roomState = {},
  personaState = 'HYPE',
  seed = Date.now()
} = {}) {
  const rng = mulberry32(seedToNumber(seed));
  const timestamp = new Date().toISOString();

  // 驗證人格
  const validPersonas = PARTICLES.personaDirector.map(p => p.id);
  const persona = validPersonas.includes(personaState) ? personaState : 'HYPE';

  // 套用人格偏好到權重
  const biasedModules = applyPersonaBias(MODULES, persona);

  // ──────────────────────────────────────────────────────────
  // 保底爆點（LAW-1）：第一個模組必須是高衝擊粒子
  // 確保 10 秒內至少 1 個爆點事件；不可預測性落在演出不落在懲罰
  // ──────────────────────────────────────────────────────────
  const highImpactPool = biasedModules.filter(m => HIGH_IMPACT_IDS.includes(m.id));
  const firstPick = weightedPick(rng, highImpactPool);

  const selected = [firstPick];
  const usedIds = new Set([firstPick.id]);

  // 50% 機率再加一個搭配模組
  if (rng() < 0.5) {
    const remaining = biasedModules.filter(m => !usedIds.has(m.id));
    if (remaining.length > 0) {
      const secondPick = weightedPick(rng, remaining);
      selected.push(secondPick);
      usedIds.add(secondPick.id);
    }
  }

  // 組建 twist recipe
  const twistRecipe = selected.map(mod => ({
    moduleId: mod.id,
    category: mod.category,
    duration_s: mod.duration_s,
    cooldown_s: mod.cooldown_s,
    params: buildParams(mod.id, persona, rng)
  }));

  // 片段時長固定 10 秒；冷卻取所有選中模組的最大值
  const duration_s = 10;
  const cooldown_s = Math.max(...selected.map(m => m.cooldown_s));

  // ──────────────────────────────────────────────────────────
  // LAW-1：eventLog — 每次決策完整可追溯
  // ──────────────────────────────────────────────────────────
  const seedNum = seedToNumber(seed);
  const eventLog = {
    id: `evt_${seedNum.toString(16).padStart(8, '0')}_${Date.now().toString(36)}`,
    timestamp,
    seed: String(seed),
    persona,
    why: buildWhyReason(persona, playerState, roomState, selected),
    what: selected.map(m => m.id).join(' + '),
    duration_s,
    cooldown_s,
    intensity: computeIntensity(twistRecipe),
    inputs: {
      playerState,
      roomState,
      personaState: persona,
      seed: String(seed)
    },
    modules: twistRecipe.map(r => ({
      id: r.moduleId,
      category: r.category,
      duration_s: r.duration_s,
      cooldown_s: r.cooldown_s
    }))
  };

  return {
    twistRecipe,
    duration_s,
    cooldown_s,
    persona,
    eventLog,
    law: 'LAW-1: 記憶體守恆律 — 每次決策可追溯',
    origin_signature: ORIGIN_SIGNATURE,
    version: DIRECTOR_VERSION
  };
}

// ============================================================
// 私有輔助函式
// ============================================================

/**
 * 依人格與狀態產生 why 說明（中文，可追溯）
 */
function buildWhyReason(persona, playerState, roomState, selected) {
  const personaMeta = PARTICLES.personaDirector.find(p => p.id === persona);
  const personaName = personaMeta ? personaMeta.name : persona;
  const moduleNames = selected
    .map(m => PARTICLES.feelPhysics.concat(PARTICLES.twistLogic).find(p => p.id === m.id))
    .filter(Boolean)
    .map(p => p.name)
    .join('、');

  const wave = roomState.wave || '?';
  const hp = playerState.hp !== undefined ? playerState.hp : '?';

  return `人格[${personaName}]在第 ${wave} 波（玩家 HP=${hp}）偵測到爆點條件，啟動保底爆點：${moduleNames}`;
}

/**
 * 從 twistRecipe 計算綜合強度指標
 */
function computeIntensity(twistRecipe) {
  let max = 0;
  for (const r of twistRecipe) {
    const p = r.params;
    const v = p.intensity || (p.amplitude ? p.amplitude / 30 : 0) || (p.force ? p.force / 1200 : 0) || 1;
    if (v > max) max = v;
  }
  return +max.toFixed(2);
}

// ============================================================
// runFunSequence — 生成完整場次爽度序列 (v1.1.0 新增)
// ============================================================

/**
 * 生成連續多個 10 秒視窗的爽度序列
 *
 * 遵循 MrLiouWord 粒子系統哲學：
 *   LAW-0: 起源簽名律 — 輸出帶 origin_signature
 *   LAW-1: 記憶體守恆律 — 每個視窗含完整可追溯 eventLog
 *   LAW-2: 記憶體單調性律 — 相同 seed + windows 永遠產生相同序列
 *
 * @param {object} opts
 * @param {number}        opts.windows      視窗數量（每個 10 秒，預設 6 = 60 秒）
 * @param {object}        opts.playerState  玩家狀態
 * @param {object}        opts.roomState    房間狀態
 * @param {string}        opts.personaState 人格 ID：HYPE / PRANK / SPOOKY
 * @param {string|number} opts.seed         基礎隨機種子（相同 seed 可重現）
 * @returns {object} { sessionId, windows, totalDuration_s, cooldown_s, origin_signature, version, law }
 */
function runFunSequence({
  windows = 6,
  playerState = {},
  roomState = {},
  personaState = 'HYPE',
  seed = Date.now()
} = {}) {
  // 限制視窗數量在合理範圍
  const windowCount = Math.max(1, Math.min(100, Math.floor(windows)));

  const baseSeed = seedToNumber(seed);

  // 每個視窗使用衍生 seed：baseSeed + i * 黃金比例整數常數（Fibonacci 合流數）
  // 確保視窗間 seed 不重疊、不規律，同時序列完全可重現（LAW-2）
  const windowResults = [];
  for (let i = 0; i < windowCount; i++) {
    const windowSeed = (baseSeed + Math.imul(i + 1, GOLDEN_INT)) >>> 0;
    windowResults.push(runDirector({
      playerState,
      roomState,
      personaState,
      seed: windowSeed
    }));
  }

  const totalDuration_s = windowResults.reduce((sum, r) => sum + r.duration_s, 0);
  const cooldown_s = Math.max(...windowResults.map(r => r.cooldown_s));

  // sessionId：可追溯但不影響可重現性（baseSeed 決定視窗內容）
  const sessionId = `ses_${baseSeed.toString(16).padStart(8, '0')}_${Date.now().toString(36)}`;

  return {
    sessionId,
    windows: windowResults,
    totalDuration_s,
    cooldown_s,
    law: 'LAW-2: 記憶體單調性律 — 相同 seed 序列永遠可重現',
    origin_signature: `${ORIGIN_SIGNATURE}.Sequence`,
    version: DIRECTOR_VERSION
  };
}

// ============================================================
// 匯出
// ============================================================
module.exports = {
  runDirector,
  runFunSequence,
  mulberry32,
  seedToNumber,
  ORIGIN_SIGNATURE,
  DIRECTOR_VERSION
};
