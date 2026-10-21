'use strict';
/**
 * FunDirector 測試套件
 *
 * 驗證項目：
 *   1. LAW-2：相同 seed 產生可重現輸出
 *   2. 保底爆點：每次至少 1 個高衝擊模組
 *   3. LAW-1：eventLog 欄位完整
 *   4. 冷卻值計算正確
 *   5. 片段時長固定 10 秒
 *   6. 三種人格均可正常運作
 *   7. 不同 seed 產生不同輸出
 */

const { runDirector, mulberry32, seedToNumber } = require('../src/director');

let passed = 0;
let failed = 0;

function assert(condition, message) {
  if (condition) {
    console.log(`  ✅ ${message}`);
    passed++;
  } else {
    console.error(`  ❌ ${message}`);
    failed++;
  }
}

function assertEqual(a, b, message) {
  assert(a === b, `${message} (預期 ${b}，實際 ${a})`);
}

// ============================================================
// 測試 1：LAW-2 — 相同 seed 產生可重現輸出
// ============================================================
function testDeterministic() {
  console.log('\n【測試 1】LAW-2：相同 seed 可重現');
  const input = {
    playerState: { hp: 80, combo: 5 },
    roomState: { wave: 2, enemyCount: 3 },
    personaState: 'HYPE',
    seed: 42
  };
  const result1 = runDirector(input);
  const result2 = runDirector(input);

  assert(
    JSON.stringify(result1.twistRecipe) === JSON.stringify(result2.twistRecipe),
    'seed=42 兩次呼叫 twistRecipe 完全一致'
  );
  assert(
    result1.eventLog.what === result2.eventLog.what,
    'eventLog.what 一致'
  );
  assert(
    result1.cooldown_s === result2.cooldown_s,
    'cooldown_s 一致'
  );
}

// ============================================================
// 測試 2：保底爆點 — 50 個 seed 第一個模組必定是高衝擊模組
// ============================================================
function testBoomGuarantee() {
  console.log('\n【測試 2】保底爆點：50 個 seed 第一個模組必定是高衝擊模組');
  const highImpactIds = [
    'HIT_STOP', 'SCREEN_SHAKE', 'KNOCKBACK',
    'RAGDOLL', 'CHAIN_REACTION', 'COMEDY_CHAIN_REACTION'
  ];
  let allPass = true;
  for (let i = 0; i < 50; i++) {
    const result = runDirector({ seed: i });
    // 第一個模組必須是高衝擊粒子（保底保證）
    const firstIsImpact = highImpactIds.includes(result.twistRecipe[0].moduleId);
    if (!firstIsImpact) {
      console.error(`  ❌ seed=${i} 保底失敗：第一模組=${result.twistRecipe[0].moduleId}`);
      allPass = false;
      failed++;
    }
  }
  if (allPass) {
    console.log('  ✅ 50 個 seed 的第一個模組全部是高衝擊模組（保底生效）');
    passed++;
  }
}

// ============================================================
// 測試 3：LAW-1 — eventLog 欄位完整
// ============================================================
function testEventLog() {
  console.log('\n【測試 3】LAW-1：eventLog 欄位完整');
  const result = runDirector({ seed: 'test123', personaState: 'PRANK' });
  const log = result.eventLog;

  const requiredFields = [
    'id', 'timestamp', 'seed', 'persona', 'why', 'what',
    'duration_s', 'cooldown_s', 'intensity', 'inputs', 'modules'
  ];
  for (const field of requiredFields) {
    assert(log[field] !== undefined, `eventLog.${field} 存在`);
  }
  assert(typeof log.id === 'string' && log.id.startsWith('evt_'), 'eventLog.id 格式正確');
  assert(typeof log.why === 'string' && log.why.length > 0, 'eventLog.why 非空');
  assert(Array.isArray(log.modules) && log.modules.length > 0, 'eventLog.modules 為非空陣列');
  assert(log.inputs.seed === 'test123', 'eventLog.inputs.seed 正確');
}

// ============================================================
// 測試 4：冷卻值正確
// ============================================================
function testCooldown() {
  console.log('\n【測試 4】冷卻值計算正確');
  for (let s = 0; s < 20; s++) {
    const result = runDirector({ seed: s });
    const maxCooldown = Math.max(...result.twistRecipe.map(r => r.cooldown_s));
    assert(result.cooldown_s === maxCooldown, `seed=${s} cooldown_s 等於最大模組冷卻`);
  }
}

// ============================================================
// 測試 5：duration_s 固定 10 秒
// ============================================================
function testDuration() {
  console.log('\n【測試 5】片段時長固定 10 秒');
  for (let s = 0; s < 10; s++) {
    const result = runDirector({ seed: s });
    assertEqual(result.duration_s, 10, `seed=${s} duration_s`);
  }
}

// ============================================================
// 測試 6：三種人格均可正常運作
// ============================================================
function testPersonas() {
  console.log('\n【測試 6】三種人格均可正常運作');
  const personas = ['HYPE', 'PRANK', 'SPOOKY'];
  for (const p of personas) {
    const result = runDirector({ seed: 100, personaState: p });
    assert(result.persona === p, `人格 ${p} 輸出正確`);
    assert(result.twistRecipe.length >= 1, `人格 ${p} twistRecipe 非空`);
    assert(result.origin_signature === 'MrLiouWord.FunDirector', `人格 ${p} origin_signature 正確`);
  }
}

// ============================================================
// 測試 7：不同 seed 至少有差異
// ============================================================
function testDiversity() {
  console.log('\n【測試 7】不同 seed 產生多樣化輸出');
  const results = new Set();
  for (let i = 0; i < 20; i++) {
    const r = runDirector({ seed: i });
    results.add(r.eventLog.what);
  }
  assert(results.size > 1, `20 個 seed 中有 ${results.size} 種不同 what 組合（多樣性 > 1）`);
}

// ============================================================
// 測試 8：Mulberry32 PRNG — 相同 seed 序列相同
// ============================================================
function testPRNG() {
  console.log('\n【測試 8】Mulberry32 PRNG 可重現性');
  const seq1 = [];
  const seq2 = [];
  const rng1 = mulberry32(seedToNumber(999));
  const rng2 = mulberry32(seedToNumber(999));
  for (let i = 0; i < 10; i++) {
    seq1.push(rng1());
    seq2.push(rng2());
  }
  assert(JSON.stringify(seq1) === JSON.stringify(seq2), '相同 seed 999 產生相同序列');
}

// ============================================================
// 執行所有測試
// ============================================================
console.log('╔═══════════════════════════════════╗');
console.log('║   FunDirector 測試套件 v1.0.0    ║');
console.log('╚═══════════════════════════════════╝');

testDeterministic();
testBoomGuarantee();
testEventLog();
testCooldown();
testDuration();
testPersonas();
testDiversity();
testPRNG();

console.log(`\n${'─'.repeat(40)}`);
console.log(`✅ 通過：${passed}  ❌ 失敗：${failed}`);
console.log('─'.repeat(40));

if (failed > 0) {
  process.exit(1);
}
