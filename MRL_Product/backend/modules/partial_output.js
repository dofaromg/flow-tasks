'use strict';
// modules/partial_output.js — 從 full_result 切出部分預覽
// origin_signature: MrLiouWord
//
// 切分策略（調整後）：
//   summary    → 完整給（核心吸引力）
//   breakdown  → 完整給（讓人感受到問題被真正理解）
//   directions → 只給第 1 個（激發好奇）
//   steps      → 全部鎖住（這是核心價值，不給）
//   priorities → 全部鎖住
//   supplements→ 全部鎖住
//   warning    → 全部鎖住
//
// 設計原則：
//   - partial 要夠有價值，讓人感覺「拿到了一些東西」
//   - 但最關鍵的執行部分（steps/priorities）不可洩漏
//   - 目的是讓付費成為「取得真正能動手做的部分」的自然決定

/**
 * 從完整分析建立部分預覽
 */
function buildPartial(fullResult) {
  if (!fullResult) return null;

  let parsed;
  try {
    parsed = typeof fullResult === 'string' ? JSON.parse(fullResult) : fullResult;
  } catch {
    return null;
  }

  return {
    // ── 完整給 ──────────────────────────────────
    summary:    parsed.summary || '',
    breakdown:  Array.isArray(parsed.breakdown) ? parsed.breakdown : [],

    // ── 只給第一個 → 激發好奇 ───────────────────
    directions: Array.isArray(parsed.directions) && parsed.directions.length > 0
      ? [parsed.directions[0]]
      : [],

    // ── 鎖住 ────────────────────────────────────
    steps:       null,
    priorities:  null,
    supplements: null,
    warning:     null,

    // ── 鎖定提示 ────────────────────────────────
    _locked: true,
    _hint: '付費解鎖完整執行步驟、全部方案方向、優先順序與補充建議',
  };
}

/**
 * 完整輸出（移除內部標記）
 */
function buildFull(fullResult) {
  if (!fullResult) return null;
  try {
    const parsed = typeof fullResult === 'string' ? JSON.parse(fullResult) : fullResult;
    // 移除內部鎖定標記
    const { _locked, _hint, ...clean } = parsed;
    return clean;
  } catch {
    return null;
  }
}

module.exports = { buildPartial, buildFull };
