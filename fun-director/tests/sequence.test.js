'use strict';
/**
 * FunDirector Sequence 測試套件 (v1.1.0)
 *
 * 驗證項目：
 *   1. LAW-2：相同 seed 產生可重現序列
 *   2. 視窗數量正確
 *   3. totalDuration_s = windows × 10
 *   4. 每個視窗均為合法 FunDirector 輸出
 *   5. 預設 windows = 6
 *   6. 三種人格均可正常運作
 *   7. 不同 seed 產生不同序列
 *   8. 邊界值：windows=1、windows=100
 *   9. origin_signature 格式正確
 */

const { runFunSequence } = require('../src/director');

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
// 測試 1：LAW-2 — 相同 seed 產生可重現序列
// ============================================================
function testDeterministic() {
  console.log('\n【測試 1】LAW-2：相同 seed 可重現序列');
  const opts = {
    windows: 4,
    playerState: { hp: 100, combo: 0 },
    roomState: { wave: 1, enemyCount: 5 },
    personaState: 'HYPE',
    seed: 42
  };
  const seq1 = runFunSequence(opts);
  const seq2 = runFunSequence(opts);

  assert(
    JSON.stringify(seq1.windows.map(w => w.twistRecipe)) ===
    JSON.stringify(seq2.windows.map(w => w.twistRecipe)),
    '兩次呼叫 windows[*].twistRecipe 完全一致'
  );
  assert(
    seq1.totalDuration_s === seq2.totalDuration_s,
    'totalDuration_s 一致'
  );
  assert(
    seq1.cooldown_s === seq2.cooldown_s,
    'cooldown_s 一致'
  );
}

// ============================================================
// 測試 2：視窗數量正確
// ============================================================
function testWindowCount() {
  console.log('\n【測試 2】視窗數量正確');
  [1, 3, 6, 10].forEach(n => {
    const seq = runFunSequence({ windows: n, seed: n * 100 });
    assertEqual(seq.windows.length, n, `windows=${n} 時序列長度`);
  });
}

// ============================================================
// 測試 3：totalDuration_s = windows × 10
// ============================================================
function testTotalDuration() {
  console.log('\n【測試 3】totalDuration_s = windows × 10');
  [2, 4, 6, 8].forEach(n => {
    const seq = runFunSequence({ windows: n, seed: n });
    assertEqual(seq.totalDuration_s, n * 10, `windows=${n} totalDuration_s`);
  });
}

// ============================================================
// 測試 4：每個視窗均為合法 FunDirector 輸出
// ============================================================
function testWindowValidity() {
  console.log('\n【測試 4】每個視窗均為合法 FunDirector 輸出');
  const seq = runFunSequence({ windows: 5, seed: 999 });
  const HIGH_IMPACT_IDS = [
    'HIT_STOP', 'SCREEN_SHAKE', 'KNOCKBACK',
    'RAGDOLL', 'CHAIN_REACTION', 'COMEDY_CHAIN_REACTION'
  ];

  seq.windows.forEach((w, i) => {
    assert(Array.isArray(w.twistRecipe) && w.twistRecipe.length >= 1,
      `window[${i}] twistRecipe 非空`);
    assert(HIGH_IMPACT_IDS.includes(w.twistRecipe[0].moduleId),
      `window[${i}] 保底爆點成立（第一模組為高衝擊）`);
    assert(w.duration_s === 10,
      `window[${i}] duration_s === 10`);
    assert(typeof w.eventLog === 'object' && w.eventLog !== null,
      `window[${i}] eventLog 存在`);
    assert(typeof w.eventLog.id === 'string' && w.eventLog.id.startsWith('evt_'),
      `window[${i}] eventLog.id 格式正確`);
  });
}

// ============================================================
// 測試 5：預設 windows = 6
// ============================================================
function testDefaultWindows() {
  console.log('\n【測試 5】預設 windows = 6（= 60 秒場次）');
  const seq = runFunSequence({ seed: 777 });
  assertEqual(seq.windows.length, 6, '預設 windows 數量');
  assertEqual(seq.totalDuration_s, 60, '預設 totalDuration_s');
}

// ============================================================
// 測試 6：三種人格均可正常運作
// ============================================================
function testPersonas() {
  console.log('\n【測試 6】三種人格均可正常運作');
  ['HYPE', 'PRANK', 'SPOOKY'].forEach(persona => {
    const seq = runFunSequence({ windows: 3, seed: 55, personaState: persona });
    assert(seq.windows.length === 3, `人格 ${persona} 序列長度正確`);
    seq.windows.forEach((w, i) => {
      assert(w.persona === persona, `人格 ${persona} window[${i}].persona 正確`);
    });
  });
}

// ============================================================
// 測試 7：不同 seed 產生不同序列
// ============================================================
function testDiversity() {
  console.log('\n【測試 7】不同 seed 產生不同序列');
  const signatures = new Set();
  for (let i = 0; i < 20; i++) {
    const seq = runFunSequence({ windows: 2, seed: i });
    signatures.add(seq.windows.map(w => w.eventLog.what).join('|'));
  }
  assert(signatures.size > 1,
    `20 個 seed 中有 ${signatures.size} 種不同組合（多樣性 > 1）`);
}

// ============================================================
// 測試 8：邊界值 — windows=1 和 windows=100
// ============================================================
function testBoundary() {
  console.log('\n【測試 8】邊界值：windows=1 與 windows=100');

  const single = runFunSequence({ windows: 1, seed: 1 });
  assertEqual(single.windows.length, 1, 'windows=1 序列長度');
  assertEqual(single.totalDuration_s, 10, 'windows=1 totalDuration_s');

  const many = runFunSequence({ windows: 100, seed: 100 });
  assertEqual(many.windows.length, 100, 'windows=100 序列長度');
  assertEqual(many.totalDuration_s, 1000, 'windows=100 totalDuration_s');
}

// ============================================================
// 測試 9：origin_signature 格式正確
// ============================================================
function testOriginSignature() {
  console.log('\n【測試 9】origin_signature 與 sessionId 格式正確');
  const seq = runFunSequence({ windows: 2, seed: 'hello' });
  assert(
    seq.origin_signature === 'MrLiouWord.FunDirector.Sequence',
    `origin_signature 值正確（${seq.origin_signature}）`
  );
  assert(
    typeof seq.sessionId === 'string' && seq.sessionId.startsWith('ses_'),
    `sessionId 格式正確（${seq.sessionId}）`
  );
  assert(
    typeof seq.law === 'string' && seq.law.includes('LAW-2'),
    'law 欄位含 LAW-2'
  );
}

// ============================================================
// 執行所有測試
// ============================================================
console.log('╔══════════════════════════════════════════╗');
console.log('║   FunDirector Sequence 測試套件 v1.1.0  ║');
console.log('╚══════════════════════════════════════════╝');

testDeterministic();
testWindowCount();
testTotalDuration();
testWindowValidity();
testDefaultWindows();
testPersonas();
testDiversity();
testBoundary();
testOriginSignature();

console.log(`\n${'─'.repeat(44)}`);
console.log(`✅ 通過：${passed}  ❌ 失敗：${failed}`);
console.log('─'.repeat(44));

if (failed > 0) {
  process.exit(1);
}
