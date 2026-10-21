// app.js — MRL_Product_v1 前端互動核心
// origin_signature: MrLiouWord
// 流程：輸入 → analyze API → partial_result 顯示 → 付款解鎖 → full_result
'use strict';

// ── 狀態 ────────────────────────────────────────────────────────
const state = {
  token: null,
  sessionId: null,
  analysisId: null,
  isPartial: true,
  category: null,
  examplePromptUsed: false,
  hasSubscription: false,      // 第十九包：是否有有效訂閱
  subscriptionExpires: null,   // 訂閱到期時間
};

// ── DOM refs ─────────────────────────────────────────────────────
const phaseInput   = document.getElementById('phase-input');
const phaseLoading = document.getElementById('phase-loading');
const phaseResult  = document.getElementById('phase-result');
const problemInput = document.getElementById('problem-input');
const analyzeBtn   = document.getElementById('analyze-btn');
const charCount    = document.getElementById('char-count');
const resultContent = document.getElementById('result-content');
const lockSection  = document.getElementById('lock-section');
const fullActions  = document.getElementById('full-actions');
const toastArea    = document.getElementById('toast-area');
const sessionInfo  = document.getElementById('session-info');

// ── Init ─────────────────────────────────────────────────────────
async function init() {
  // 載入 token
  state.token = localStorage.getItem('mrl_token') || '';

  // 初始化 session（無 token）或確認訂閱狀態（有 token）
  if (!state.token) {
    await initSession();
  } else {
    // 有 token：靜默查訂閱狀態
    await _refreshSubscriptionStatus();
  }

  // 檢查 URL params（從 success 頁導回）
  const params = new URLSearchParams(window.location.search);
  const analysisId = params.get('analysis');
  const unlocked   = params.get('unlocked');

  if (analysisId) {
    state.analysisId = analysisId;
    if (unlocked === '1') {
      await loadResult(analysisId, false); // 直接顯示完整版
    } else {
      await loadResult(analysisId);
    }
    return;
  }

  setupInputListeners();
}

// ── Session 初始化 ────────────────────────────────────────────────
async function initSession() {
  try {
    const res = await apiFetch('/api/session', { method: 'POST', skipAuth: true });
    if (res.token) {
      state.token = res.token;
      state.sessionId = res.sessionId;
      localStorage.setItem('mrl_token', res.token);
      if (sessionInfo) {
        sessionInfo.textContent = `session: ${res.sessionId?.slice(0, 12)}...`;
      }
    }
    // 第十九包：同步訂閱狀態
    if (res.has_subscription) {
      state.hasSubscription = true;
      state.subscriptionExpires = res.subscription_expires || null;
      _applySubscriptionUI();
    }
  } catch (e) {
    // session 失敗不阻斷
  }
}

// ── Input Listeners ───────────────────────────────────────────────
function setupInputListeners() {
  // 字數計數
  problemInput?.addEventListener('input', () => {
    const len = problemInput.value.length;
    charCount.textContent = `${len} / 3000`;
    charCount.classList.toggle('warn', len > 2800);
    analyzeBtn.disabled = len < 10;
  });

  // 分析按鈕
  analyzeBtn?.addEventListener('click', () => startAnalysis());

  // Ctrl+Enter 送出
  problemInput?.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      if (!analyzeBtn.disabled) startAnalysis();
    }
  });

  // 快速範例
  document.querySelectorAll('.quick-example')?.forEach(btn => {
    btn.addEventListener('click', () => {
      problemInput.value = btn.dataset.text;
      problemInput.dispatchEvent(new Event('input'));
      problemInput.focus();
    });
  });

  // 再分析
  document.getElementById('new-analysis-btn')?.addEventListener('click', resetToInput);

  // 複製結果
  document.getElementById('copy-btn')?.addEventListener('click', copyResult);

  // 第七包：category chips
  setupCategoryChips();

  // 第七包：URL param 讀取
  readUrlParams();
  // 第十一包：product quick modes
  setupProductModes();
}

// ── 分析流程 ──────────────────────────────────────────────────────
async function startAnalysis() {
  const text = problemInput.value.trim();
  if (text.length < 10) return;

  // 第十一包：product 專屬 loading 文案
  const loadingText = document.querySelector('#phase-loading .loading-box__text');
  const loadingSub  = document.querySelector('#phase-loading .loading-box__sub');
  if (state.category === 'product') {
    if (loadingText) loadingText.textContent = '正在幫你整理第一版產品 / 網站方案、頁面結構與上線順序...';
    if (loadingSub)  loadingSub.textContent  = '請稍等，正在把你的想法轉成可執行的第一版計畫';
  } else {
    if (loadingText) loadingText.textContent = '正在幫你整理問題、拆解結構、生成方案...';
    if (loadingSub)  loadingSub.textContent  = '請稍等，正在把你的內容轉成可執行結果';
  }
  showPhase('loading');

  try {
    const data = await apiFetch('/api/analyze', {
      method: 'POST',
      body: {
        problem_text: text,
        category: state.category || null,
        example_prompt_used: state.examplePromptUsed ? 1 : 0,
      },
    });

    state.analysisId = data.analysis_id;
    state.isPartial  = data.is_partial ?? true;
    // 第十九包：同步 category
    if (data.category && !state.category) state.category = data.category;

    // 儲存 analysisId 給 cancel 頁使用
    localStorage.setItem('mrl_last_analysis', data.analysis_id);

    // 更新 URL（不 reload）
    history.replaceState({}, '', `/app.html?analysis=${data.analysis_id}`);

    renderResult(data.result, data.problem_text, data.is_partial);
    showPhase('result');

  } catch (e) {
    showToast(e.message || '分析失敗，請重試', 'error');
    showPhase('input');
  }
}

// ── 載入已有分析 ──────────────────────────────────────────────────
async function loadResult(analysisId, autoPartial = true) {
  showPhase('loading');
  try {
    const data = await apiFetch(`/api/result/${analysisId}`);
    // 第十九包：從 API 結果同步 category 回 state（success 跳轉後需要）
    if (data.category && !state.category) {
      state.category = data.category;
    }
    // 同步 analysis_id
    state.analysisId = analysisId;
    const isPartial = autoPartial ? (data.is_partial ?? data.isPartial ?? true) : false;
    state.isPartial  = isPartial;
    renderResult(data.result, data.problemText || data.problem_text, isPartial);
    showPhase('result');
    if (!isPartial) {
      const planType = localStorage.getItem('mrl_last_plan') || 'once';
      showPostUnlockUI(planType);
    }
  } catch (e) {
    showToast('無法載入分析結果', 'error');
    showPhase('input');
  }
}

// ── 結果渲染 ──────────────────────────────────────────────────────
function renderResult(result, problemText, isPartial) {
  if (!result || !resultContent) return;

  // 更新問題預覽
  const prevEl = document.getElementById('result-problem-preview');
  if (prevEl && problemText) {
    prevEl.textContent = problemText.slice(0, 60) + (problemText.length > 60 ? '...' : '');
  }

  resultContent.innerHTML = '';

  // 第十三包 / 第十九包：Template Registry 分派
  // state.category 優先；若未設則嘗試 result 的 _template_id（normalized data 含有）
  const _catForTemplate = state.category
    || (result && result._normalized && result._template_id ? null : null); // placeholder
  const templateId = typeof templateIdFromCategory === 'function'
    ? (templateIdFromCategory(state.category) || (result && result._template_id) || null)
    : (result && result._template_id) || null;

  if (templateId && typeof renderDeliveryTemplate === 'function') {
    // 走 template renderer
    const frag = renderDeliveryTemplate(templateId, result, isPartial);
    if (frag) {
      resultContent.appendChild(frag);
      // 鎖定 / 完整動作（下方繼續處理）
      if (isPartial) {
        lockSection?.classList.remove('hidden');
        fullActions?.classList.add('hidden');
        setupPaymentButtons();
      } else {
        lockSection?.classList.add('hidden');
        fullActions?.classList.remove('hidden');
        const planType = localStorage.getItem('mrl_last_plan') || 'once';
        showPostUnlockUI(planType);
      }
      return;  // template 路徑結束，不走舊邏輯
    }
  }

  // 非 template category — 沿用原始邏輯（fallback）
  const doc = document.createElement('div');
  doc.className = 'result-doc';

  if (result.summary) {
    doc.appendChild(makeBlock('問題核心', result.summary, 'text'));
  }
  if (result.breakdown?.length) {
    doc.appendChild(makeBlock('問題拆解', result.breakdown, 'list'));
  }
  if (result.directions?.length) {
    const visibleDirs = isPartial ? result.directions.slice(0, 1) : result.directions;
    doc.appendChild(makeBlock('方案方向', visibleDirs, 'list'));
  }
  if (!isPartial && result.steps?.length) {
    doc.appendChild(makeBlock('執行步驟', result.steps, 'numbered'));
  }
  if (!isPartial && result.priorities?.length) {
    doc.appendChild(makeBlock('優先順序', result.priorities, 'list'));
  }
  if (!isPartial && result.supplements?.length) {
    doc.appendChild(makeBlock('補充建議', result.supplements, 'list'));
  }
  if (!isPartial && result.warning) {
    const warn = document.createElement('div');
    warn.className = 'warning-block';
    warn.textContent = result.warning;
    resultContent.appendChild(doc);
    resultContent.appendChild(warn);
  } else {
    resultContent.appendChild(doc);
  }

  // 鎖定區塊 or 完整動作
  if (isPartial) {
    lockSection?.classList.remove('hidden');
    fullActions?.classList.add('hidden');
    setupPaymentButtons();
  } else {
    lockSection?.classList.add('hidden');
    fullActions?.classList.remove('hidden');
    // 第六包：full_result 解鎖後掛升級提示 + feedback 區塊
    const planType = localStorage.getItem('mrl_last_plan') || 'once';
    showPostUnlockUI(planType);
  }
}

// ── 建立 Result Block ─────────────────────────────────────────────
function makeBlock(label, content, type = 'text', variant = '') {
  const block = document.createElement('div');
  block.className = variant ? `result-block result-block--${variant}` : 'result-block';

  const labelEl = document.createElement('div');
  labelEl.className = 'result-block__label';
  labelEl.textContent = label;
  block.appendChild(labelEl);

  if (type === 'text') {
    const p = document.createElement('div');
    p.className = 'result-block__text';
    p.textContent = content;
    block.appendChild(p);
  } else if (type === 'list' || type === 'numbered') {
    const list = document.createElement('div');
    list.className = 'result-list';
    const arr = Array.isArray(content) ? content : [content];
    arr.forEach((item, i) => {
      const li = document.createElement('div');
      li.className = 'result-list__item';
      if (type === 'numbered') {
        li.innerHTML = `<span class="num">0${i + 1}</span><span>${escHtml(item)}</span>`;
      } else {
        li.innerHTML = `<span class="num">—</span><span>${escHtml(item)}</span>`;
      }
      list.appendChild(li);
    });
    block.appendChild(list);
  }

  return block;
}

// ── 付款按鈕 ──────────────────────────────────────────────────────
function setupPaymentButtons() {
  // 訂閱者不需要付款按鈕
  if (state.hasSubscription) {
    lockSection?.classList.add('hidden');
    fullActions?.classList.remove('hidden');
    showPostUnlockUI('subscription');
    return;
  }
  const onceBtn = document.getElementById('pay-once-btn');
  const subBtn  = document.getElementById('pay-sub-btn');

  onceBtn?.addEventListener('click', () => payOnce());
  subBtn?.addEventListener('click', () => paySub());
}

async function payOnce() {
  const btn = document.getElementById('pay-once-btn');
  if (!btn) return;
  btn.disabled = true;
  btn.textContent = '建立中...';
  localStorage.setItem('mrl_last_plan', 'once');

  try {
    const data = await apiFetch('/api/pay/once', {
      method: 'POST',
      body: { analysis_id: state.analysisId },
    });
    if (data.checkoutUrl) {
      window.location.href = data.checkoutUrl;
    } else throw new Error('建立失敗');
  } catch (e) {
    showToast(e.message, 'error');
    btn.disabled = false;
    btn.textContent = '解鎖完整方案 · NT$299';
  }
}

async function paySub() {
  const btn = document.getElementById('pay-sub-btn');
  if (!btn) return;
  btn.disabled = true;
  btn.textContent = '建立中...';
  localStorage.setItem('mrl_last_plan', 'subscription');

  try {
    const data = await apiFetch('/api/pay/subscription', { method: 'POST', body: {} });
    if (data.checkoutUrl) {
      window.location.href = data.checkoutUrl;
    } else throw new Error('建立失敗');
  } catch (e) {
    showToast(e.message, 'error');
    btn.disabled = false;
    btn.textContent = '月訂閱方案 · NT$499/月';
  }
}

// ── Phase 切換 ────────────────────────────────────────────────────
function showPhase(phase) {
  phaseInput?.classList.toggle('hidden', phase !== 'input');
  phaseLoading?.classList.toggle('hidden', phase !== 'loading');
  phaseResult?.classList.toggle('hidden', phase !== 'result');
}

function resetToInput() {
  state.analysisId = null;
  state.isPartial = true;
  state.category = null;
  state.examplePromptUsed = false;
  problemInput.value = '';
  if (charCount) charCount.textContent = '0 / 3000';
  if (analyzeBtn) analyzeBtn.disabled = true;
  resultContent.innerHTML = '';
  lockSection?.classList.add('hidden');
  fullActions?.classList.add('hidden');
  // 重置 category chips + example prompts
  document.querySelectorAll('.cat-chip').forEach(b => b.classList.remove('active'));
  const epEl = document.getElementById('example-prompts');
  if (epEl) { epEl.innerHTML = ''; epEl.classList.remove('visible'); }
  // 第十一包：重置 product UI
  document.getElementById('product-hint')?.classList.add('hidden');
  document.getElementById('product-modes')?.classList.add('hidden');
  document.querySelectorAll('.product-mode-btn').forEach(b => b.classList.remove('active'));
  // 清 pack / scaffold / deploy 結果區
  const packSection = document.getElementById('pack-section');
  if (packSection) packSection.classList.add('hidden');
  const packResult = document.getElementById('pack-result');
  if (packResult) { packResult.innerHTML = ''; packResult.classList.add('hidden'); }
  const scaffoldResult = document.getElementById('scaffold-result');
  if (scaffoldResult) scaffoldResult.innerHTML = '';
  const deploypackResult = document.getElementById('deploypack-result');
  if (deploypackResult) deploypackResult.innerHTML = '';
  window._lastPack = null;
  window._lastDeployPackId = null;
  history.replaceState({}, '', '/app.html');
  showPhase('input');
  problemInput?.focus();
}

// ── Copy ──────────────────────────────────────────────────────────
function copyResult() {
  const text = resultContent?.innerText || '';
  navigator.clipboard?.writeText(text)
    .then(() => showToast('已複製到剪貼簿', 'success'))
    .catch(() => showToast('複製失敗', 'error'));
}

// ── API Helper ────────────────────────────────────────────────────
async function apiFetch(url, opts = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (!opts.skipAuth && state.token) {
    headers['Authorization'] = `Bearer ${state.token}`;
  }

  const fetchOpts = {
    method: opts.method || 'GET',
    headers,
  };

  if (opts.body) {
    fetchOpts.body = JSON.stringify(opts.body);
  }

  const res = await fetch(url, fetchOpts);

  // 儲存新 token（如果 session 剛建立）
  const newToken = res.headers.get('X-Session-Token');
  if (newToken) {
    state.token = newToken;
    localStorage.setItem('mrl_token', newToken);
  }

  const data = await res.json();

  if (!res.ok) {
    const err = new Error(data.error || `請求失敗（${res.status}）`);
    err.status = res.status;
    throw err;
  }

  return data;
}

// ── Toast ─────────────────────────────────────────────────────────
function showToast(msg, type = '') {
  if (!toastArea) return;
  const el = document.createElement('div');
  el.className = `toast toast--${type}`;
  el.textContent = msg;
  toastArea.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

// ── Utils ─────────────────────────────────────────────────────────
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── 第七包：Category 定義 ──────────────────────────────────────────
const CATEGORIES = {
  product: {
    label: '做網站 / 做產品',
    placeholder: '例如：我想做一個可收費網站，第一版要切哪些頁面、付款流程怎麼排、最小可上線版本是什麼？',
    prompts: [
      '我想做一個可收費網站，請幫我切第一版產品：要哪些頁面、付款流程、上線前最少要做什麼',
      '我有一個產品想法但不知道第一版該做什麼、先做哪個功能、哪些先不做，請幫我排',
      '我想把服務產品化讓陌生人可以付費，請幫我整理：賣給誰、賣什麼、怎麼定價、第一步怎麼開始',
    ],
    // 第十一包：子模板
    subModes: {
      website:  '我想做一個可上線、可收費的第一版網站，請幫我拆成頁面、流程、付款與執行步驟',
      mvp:      '我有一個產品想法，請幫我切出第一版功能、使用流程與優先順序，並告訴我哪些先不做',
      payment:  '我想把能力做成可收費入口，請幫我整理 pricing、付款流程、解鎖邏輯與上線步驟',
      converge: '我現在產品想法太多，請幫我收斂出最小可行版本、先做什麼、先不做什麼、什麼最快能上線',
    },
  },
  system: {
    label: '系統收斂',
    placeholder: '例如：我有一套系統很亂，請幫我拆成模組、流程、優先順序與第一步。',
    prompts: [
      '我有一套系統很亂，請幫我拆成模組、流程、優先順序與第一步',
      '我的工作流程越來越複雜，不知道從哪裡收斂，請幫我整理出清楚架構',
      '我想建立一個自動化系統，有很多想法但不知道先做哪個，請幫我排序',
    ],
  },
  business: {
    label: '商業模式',
    placeholder: '例如：我想把一個能力變成商品，請幫我整理客群、定價、第一版產品與收費方式。',
    prompts: [
      '我想把一個能力變成商品，請幫我整理客群、定價、第一版產品與收費方式',
      '我想開始接案或賣課程，不知道怎麼定位自己和定價，請幫我整理',
      '我有一個商業想法但還沒驗證，請幫我找出最快可以收到錢的方法',
    ],
  },
  decision: {
    label: '決策排序',
    placeholder: '例如：我現在卡在幾個方向，請幫我比較代價、找出優先選項，給出先做什麼。',
    prompts: [
      '我現在有幾個方向卡住了，請幫我列出各選項的代價、找出優先順序、給出先做哪個',
      '我在幾個工作或產品方向之間猶豫，每個都有道理，請幫我用取捨分析選出先走哪條',
      '我現在的時間和資源有限，有太多想做的事，請幫我判斷哪件事最值得先投入',
    ],
  },
  content: {
    label: '內容整理',
    placeholder: '例如：我有一堆混亂內容，請幫我整理成清楚架構、關鍵重點與下一步。',
    prompts: [
      '我有一堆混亂的筆記和想法，請幫我整理成清楚架構與關鍵重點',
      '我想把自己知道的東西整理成可以分享的內容，不知道怎麼架構',
      '我有很多資料但不知道怎麼切重點，請幫我找出核心並整理成可用格式',
    ],
  },
};

// ── Category Chips 邏輯 ────────────────────────────────────────────
function setupCategoryChips() {
  document.querySelectorAll('.cat-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      const cat = btn.dataset.cat;
      const isAlreadyActive = btn.classList.contains('active');

      // 取消所有選中
      document.querySelectorAll('.cat-chip').forEach(b => b.classList.remove('active'));

      if (isAlreadyActive) {
        // 再點一次 → 取消選擇
        state.category = null;
        updateExamplePrompts(null);
        updatePlaceholder(null);
        localStorage.removeItem('mrl_last_category');
      } else {
        btn.classList.add('active');
        state.category = cat;
        updateExamplePrompts(cat);
        updatePlaceholder(cat);
        localStorage.setItem('mrl_last_category', cat);
      }
    });
  });
}

function updateExamplePrompts(cat) {
  const el = document.getElementById('example-prompts');
  if (!el) return;

  el.innerHTML = '';

  // 第十一包：product 專屬 UI
  const hint  = document.getElementById('product-hint');
  const modes = document.getElementById('product-modes');
  if (hint)  hint.classList.toggle('hidden',  cat !== 'product');
  if (modes) modes.classList.toggle('hidden', cat !== 'product');

  if (!cat || !CATEGORIES[cat]) {
    el.classList.remove('visible');
    return;
  }

  const prompts = CATEGORIES[cat].prompts || [];
  prompts.forEach(text => {
    const btn = document.createElement('button');
    btn.className = 'example-prompt-btn';
    btn.textContent = text;
    btn.addEventListener('click', () => {
      if (!problemInput) return;
      problemInput.value = text;
      problemInput.dispatchEvent(new Event('input'));
      state.examplePromptUsed = true;
      // 捲動到輸入框
      problemInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
      problemInput.focus();
    });
    el.appendChild(btn);
  });

  el.classList.add('visible');
}

function updatePlaceholder(cat) {
  if (!problemInput) return;
  if (cat && CATEGORIES[cat]) {
    problemInput.placeholder = CATEGORIES[cat].placeholder;
  } else {
    problemInput.placeholder = '把你現在最卡的問題丟進來，不用整理，直接描述就好。\n\n例如：我想做一個可收費的網站，第一版要怎麼規劃？';
  }
}

// ── Product Modes 初始化 ─────────────────────────────────────────
function initProductModes() {
  setupProductModes();
}

// ── URL param 讀取（支援 ?cat=product&prompt=xxx 進站）────────────
function readUrlParams() {
  const params = new URLSearchParams(window.location.search);
  const cat    = params.get('cat');
  const prompt = params.get('prompt');

  if (cat && CATEGORIES[cat]) {
    // 模擬點擊 category chip
    const chip = document.querySelector(`.cat-chip[data-cat="${cat}"]`);
    if (chip) {
      chip.classList.add('active');
      state.category = cat;
      updateExamplePrompts(cat);
      updatePlaceholder(cat);
    }
  } else {
    // 嘗試從 localStorage 恢復，否則預設 primary_category = product
    const lastCat = localStorage.getItem('mrl_last_category');
    const defaultCat = lastCat && CATEGORIES[lastCat] ? lastCat : 'product';
    const chip = document.querySelector(`.cat-chip[data-cat="${defaultCat}"]`);
    if (chip) {
      chip.classList.add('active');
      state.category = defaultCat;
      updateExamplePrompts(defaultCat);
      updatePlaceholder(defaultCat);
    }
  }

  if (prompt) {
    if (problemInput) {
      problemInput.value = decodeURIComponent(prompt);
      problemInput.dispatchEvent(new Event('input'));
      state.examplePromptUsed = true;
    }
  }
}

// ── 第十一包：Product Quick Modes ────────────────────────────────
const PRODUCT_SUB_MODES = {
  website:  '我想做一個可上線、可收費的第一版網站，請幫我拆成頁面、流程、付款與執行步驟',
  mvp:      '我有一個產品想法，請幫我切出第一版功能、使用流程與優先順序，並告訴我哪些先不做',
  payment:  '我想把能力做成可收費入口，請幫我整理 pricing、付款流程、解鎖邏輯與上線步驟',
  converge: '我現在產品想法太多，請幫我收斂出最小可行版本、先做什麼、先不做什麼、什麼最快能上線',
};

function setupProductModes() {
  document.querySelectorAll('.product-mode-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const mode = btn.dataset.mode;
      const prompt = PRODUCT_SUB_MODES[mode];
      if (!prompt || !problemInput) return;

      // 高亮選中的 mode btn
      document.querySelectorAll('.product-mode-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      // 填入 textarea
      problemInput.value = prompt;
      problemInput.dispatchEvent(new Event('input'));
      state.examplePromptUsed = true;

      // 捲動到輸入框
      problemInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
      problemInput.focus();
    });
  });
}

// ── 第十五包：ProductPack Generator ─────────────────────────────
function setupPackGenerator() {
  const btn = document.getElementById('generate-pack-btn');
  if (!btn || btn._packSetup) return;
  btn._packSetup = true;

  btn.addEventListener('click', async () => {
    if (!state.analysisId) return;
    const mode = document.getElementById('pack-mode-select')?.value || 'website';

    btn.disabled = true;
    btn.textContent = '生成中...';

    try {
      const data = await apiFetch('/api/pack/generate', {
        method: 'POST',
        body: { analysis_id: state.analysisId, mode },
      });

      renderPackResult(data);
    } catch (e) {
      showToast(e.message || 'Pack 生成失敗', 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = '生成 ProductPack';
    }
  });
}

function renderPackResult(data) {
  const el = document.getElementById('pack-result');
  if (!el || !data.pack) return;

  const pack = data.pack;
  const pagesHtml = (pack.pages || []).map(p =>
    `<div style="display:flex;gap:8px;font-size:11px;color:var(--text-2);padding:4px 0;border-bottom:1px solid var(--border);">
      <span style="color:var(--accent);font-weight:600;min-width:70px;">${p.name}</span>
      <span>${p.purpose}</span>
      <span style="color:var(--muted);margin-left:auto;">${p.priority}</span>
    </div>`
  ).join('');

  const flowHtml = (pack.flows || []).map(f =>
    `<div style="font-size:11px;color:var(--text-2);padding:3px 0;">
      <span style="color:var(--accent);font-family:'DM Mono',monospace;margin-right:6px;">${String(f.step).padStart(2,'0')}</span>
      ${escHtml(f.description)}
    </div>`
  ).join('');

  const stepsHtml = (pack.execution_steps || []).map((s, i) =>
    `<div style="font-size:11px;color:var(--text-2);padding:3px 0;">
      <span style="color:var(--accent);font-family:'DM Mono',monospace;margin-right:6px;">${String(i+1).padStart(2,'0')}</span>
      ${escHtml(s)}
    </div>`
  ).join('');

  el.innerHTML = [
    '<div style="border:1px solid rgba(232,184,75,0.25);border-radius:var(--r-md);padding:16px;background:var(--accent-dim);margin-bottom:10px;">',
    '  <div style="font-size:11px;color:var(--accent);font-weight:600;letter-spacing:0.04em;margin-bottom:6px;">' + escHtml(pack.title) + ' · ' + (pack.mode_label || pack.mode) + '</div>',
    '  <div style="font-size:12px;color:var(--text-2);margin-bottom:12px;">' + escHtml(pack.summary) + '</div>',
    '  <div style="font-size:10px;color:var(--muted);font-family:\'DM Mono\',monospace;">pack_id: ' + pack.pack_id + ' · template: ' + pack.template_id + '</div>',
    '</div>',
    '<div style="margin-bottom:12px;"><div style="font-size:10px;color:var(--muted);letter-spacing:0.08em;text-transform:uppercase;margin-bottom:6px;">頁面清單</div>' + pagesHtml + '</div>',
    '<div style="margin-bottom:12px;"><div style="font-size:10px;color:var(--muted);letter-spacing:0.08em;text-transform:uppercase;margin-bottom:6px;">執行順序</div>' + stepsHtml + '</div>',
    '<div style="margin-bottom:14px;"><div style="font-size:10px;color:var(--muted);letter-spacing:0.08em;text-transform:uppercase;margin-bottom:6px;">使用者流程</div>' + flowHtml + '</div>',
    '<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">',
    '  <a href="/api/pack/' + pack.pack_id + '/download" class="btn btn--outline btn--sm" download="' + pack.pack_id + '.json">下載 Pack JSON</a>',
    '  <button class="btn btn--ghost btn--sm" onclick="navigator.clipboard&&navigator.clipboard.writeText(JSON.stringify(window._lastPack,null,2)).then(function(){window.showToast&&window.showToast(\'已複製 JSON\',\'success\')})">複製 JSON</button>',
    '  <button class="btn btn--outline btn--sm" style="border-color:rgba(61,220,90,0.4);color:#3ddc5a;" onclick="generateScaffoldFromPack(window._lastPack&&window._lastPack.pack_id)">⬡ 生成 Scaffold</button>',
    '  <button id="generate-deploypack-btn" class="btn btn--outline btn--sm" style="border-color:rgba(232,184,75,0.4);color:var(--accent);" onclick="generateDeployPack(window._lastPack&&window._lastPack.pack_id)">▶ 生成 Deploy Pack</button>',
    '</div>',
    '<div id="scaffold-result" style="margin-top:10px;"></div>',
    '<div id="deploypack-result"></div>',
  ].join('\n');
  el.classList.remove('hidden');

  // 存到 window 供 copy 使用
  window._lastPack = pack;
}

// ── 第十六包：Scaffold Generator ────────────────────────────────
async function generateScaffoldFromPack(packId) {
  if (!packId) { showToast('請先生成 Pack', 'error'); return; }
  const btn = document.querySelector('[onclick*="generateScaffoldFromPack"]');
  if (btn) { btn.disabled = true; btn.textContent = '生成中...'; }

  const resultEl = document.getElementById('scaffold-result');
  if (resultEl) resultEl.innerHTML = '';

  try {
    const data = await apiFetch('/api/scaffold/generate', {
      method: 'POST',
      body: { pack_id: packId },
    });

    if (resultEl) {
      resultEl.innerHTML = `
        <div style="padding:14px 16px;background:var(--surface);border:1px solid rgba(61,220,90,0.25);border-radius:var(--r-md);">
          <div style="font-size:10px;color:#3ddc5a;font-family:'DM Mono',monospace;margin-bottom:8px;letter-spacing:0.06em;">
            ✓ SCAFFOLD GENERATED · ${data.scaffold_id || ''}
          </div>
          <div style="font-size:12px;color:var(--text-2);margin-bottom:8px;">
            路徑：<code style="font-family:'DM Mono',monospace;color:var(--text);">${data.scaffold_dir || ''}</code>
          </div>
          <div style="font-size:12px;color:var(--text-2);">
            生成檔案：${data.file_count || 0} 個
          </div>
          <div style="margin-top:8px;font-size:11px;color:var(--muted);">
            ${(data.file_list || []).slice(0, 12).map(f => `<span style="display:inline-block;margin:2px 4px 2px 0;padding:2px 6px;background:var(--surface-2);border-radius:3px;">${f}</span>`).join('')}
            ${(data.file_list || []).length > 12 ? `<span style="color:var(--muted);">...等 ${(data.file_list || []).length} 個</span>` : ''}
          </div>
        </div>
      `;
    }
    showToast('Scaffold 已生成', 'success');
  } catch (e) {
    showToast(e.message || 'Scaffold 生成失敗', 'error');
    if (resultEl) resultEl.innerHTML = '';
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '⬡ 生成 Scaffold'; }
  }
}

// ── 第十七包：Deploy Pack Generator ─────────────────────────────
async function generateDeployPack(packId) {
  if (!packId) { showToast('請先生成 Scaffold', 'error'); return; }
  const btn = document.getElementById('generate-deploypack-btn');
  if (btn) { btn.disabled = true; btn.textContent = '生成中...'; }
  const resultEl = document.getElementById('deploypack-result');
  if (resultEl) resultEl.innerHTML = '';

  try {
    const data = await apiFetch('/api/deploypack/generate', {
      method: 'POST',
      body: { pack_id: packId },
    });

    const v = data.validation || {};
    const scoreColor = (v.runnable_score || 0) >= 80 ? '#3ddc5a' : (v.runnable_score || 0) >= 50 ? '#e8b84b' : '#ff6b6b';

    if (resultEl) {
      resultEl.innerHTML = `
        <div style="padding:14px 16px;background:var(--surface);border:1px solid rgba(61,220,90,0.3);border-radius:var(--r-md);margin-top:10px;">
          <div style="font-size:10px;color:#3ddc5a;font-family:'DM Mono',monospace;margin-bottom:8px;letter-spacing:0.06em;">
            ✓ DEPLOY PACK READY · ${data.deploy_pack_id || ''}
          </div>
          <div style="font-size:12px;color:var(--text-2);margin-bottom:6px;">
            路徑：<code style="color:var(--text);font-family:'DM Mono',monospace;">${data.deploy_dir || ''}</code>
          </div>
          <div style="font-size:12px;color:var(--text-2);margin-bottom:10px;">
            檔案：${data.file_count || 0} 個 ·
            <span style="color:${scoreColor};font-weight:600;">Runnable Score: ${v.runnable_score ?? '-'}/100</span> ·
            <span style="color:${v.can_compose_up ? '#3ddc5a' : '#e8b84b'};">${v.can_compose_up ? '✓ 可 compose up' : '⚠ 需補完'}</span>
          </div>
          ${(v.missing_files || []).length ? `<div style="font-size:11px;color:#ff6b6b;margin-bottom:6px;">缺：${v.missing_files.join(', ')}</div>` : ''}
          ${(v.warnings || []).length ? `<div style="font-size:11px;color:var(--amber);">${v.warnings.slice(0,3).join(' · ')}</div>` : ''}
          <div style="margin-top:10px;font-size:11px;color:var(--text-2);font-family:'DM Mono',monospace;background:var(--surface-2);padding:10px;border-radius:4px;">
cd ${data.deploy_dir || 'storage/deploypacks/...'}/deploy<br>
docker compose up -d --build<br>
bash health-check.sh
          </div>
        </div>
      `;
    }
    window._lastDeployPackId = packId;
    showToast('Deploy Pack 已生成', 'success');
  } catch (e) {
    showToast(e.message || 'Deploy Pack 生成失敗', 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '▶ 生成 Deploy Pack'; }
  }
}

// ── 第十九包：訂閱者 UI ─────────────────────────────────────────

/**
 * 訂閱者識別 UI：
 *  - 隱藏 lock-section（不需要付款）
 *  - nav 顯示小標記
 *  - setupPaymentButtons 時不顯示鎖定按鈕
 */
function _applySubscriptionUI() {
  if (!state.hasSubscription) return;

  // 若 lock-section 已顯示，訂閱者不需要看到
  lockSection?.classList.add('hidden');

  // nav 加訂閱標記
  const logo = document.querySelector('.nav__logo');
  if (logo && !logo.querySelector('.sub-badge')) {
    const badge = document.createElement('span');
    badge.className = 'sub-badge';
    badge.textContent = '✦';
    badge.title = '訂閱中';
    badge.style.cssText = 'font-size:10px;color:var(--accent);margin-left:4px;vertical-align:super;';
    logo.appendChild(badge);
  }
}

/**
 * 訂閱者到期前 3 天顯示提示
 */
function _checkSubscriptionExpiry() {
  if (!state.hasSubscription || !state.subscriptionExpires) return;
  const expiresAt = new Date(state.subscriptionExpires);
  const daysLeft = Math.ceil((expiresAt - Date.now()) / (1000 * 60 * 60 * 24));
  if (daysLeft <= 3) {
    showToast(`訂閱將於 ${daysLeft} 天後到期`, 'warn');
  }
}

// ── 第十九包：訂閱狀態刷新 ─────────────────────────────────────
async function _refreshSubscriptionStatus() {
  try {
    const data = await apiFetch('/api/session/status');
    if (data.has_subscription) {
      state.hasSubscription = true;
      state.subscriptionExpires = data.subscription_expires || null;
      _applySubscriptionUI();
    }
  } catch { /* 靜默失敗 */ }
}

// ── 第十九包：Email 登入（owner 帳號入口）──────────────────────
async function loginWithEmail(email) {
  if (!email || !email.includes('@')) return;
  try {
    const data = await apiFetch('/api/login', { method: 'POST', body: { email } });
    if (data.token) {
      state.token     = data.token;
      state.sessionId = data.sessionId;
      localStorage.setItem('mrl_token', data.token);
    }
    if (data.has_subscription || data.is_owner) {
      state.hasSubscription = true;
      state.subscriptionExpires = data.subscription_expires || null;
      _applySubscriptionUI();
      _checkSubscriptionExpiry();
    }
    return data;
  } catch (e) {
    console.warn('loginWithEmail failed:', e.message);
    return null;
  }
}

// ── Boot ──────────────────────────────────────────────────────────
init().catch(console.error);

// ── 第六包：升級按鈕 + 回饋功能 ──────────────────────────────────

// 升級月費按鈕
document.getElementById('upgrade-to-sub-btn')?.addEventListener('click', () => {
  window.location.href = '/pricing.html';
});

// full_result 顯示後：顯示升級提示（僅限單次付費者）+ 回饋區
function showPostUnlockUI(planType) {
  // 第十二包：product full 時強化 copy btn
  if (state.category === 'product') {
    document.getElementById('copy-btn')?.classList.add('copy-btn--product');
    // 第十五包：顯示 ProductPack 生成區
    const packSection = document.getElementById('pack-section');
    if (packSection) {
      packSection.classList.remove('hidden');
      setupPackGenerator();
    }
  }
  const upgradeHint = document.getElementById('upgrade-hint');
  const feedbackSection = document.getElementById('feedback-section');

  // 升級提示：單次付費者才顯示
  if (planType === 'once' && upgradeHint) {
    upgradeHint.classList.remove('hidden');
  }

  // 回饋區：所有完整結果者都顯示
  if (feedbackSection) {
    feedbackSection.classList.remove('hidden');
    setupFeedback();
  }
}

// ── 星評互動 ──────────────────────────────────────────────────────
let selectedRating = 0;

function setupFeedback() {
  const stars = document.querySelectorAll('.star-btn');
  const commentRow = document.getElementById('feedback-comment-row');
  const submitBtn = document.getElementById('feedback-submit-btn');
  const thanks = document.getElementById('feedback-thanks');

  stars.forEach(btn => {
    btn.addEventListener('mouseenter', () => highlightStars(parseInt(btn.dataset.v)));
    btn.addEventListener('mouseleave', () => highlightStars(selectedRating));
    btn.addEventListener('click', () => {
      selectedRating = parseInt(btn.dataset.v);
      highlightStars(selectedRating);
      // 4分以下才顯示文字框（低分鼓勵說明）
      if (selectedRating <= 3 && commentRow) {
        commentRow.style.display = 'flex';
        commentRow.classList.remove('hidden');
      }
      // 5星直接送出
      if (selectedRating === 5) {
        submitFeedback(5, '');
      }
    });
  });

  submitBtn?.addEventListener('click', () => {
    const comment = document.getElementById('feedback-comment')?.value.trim() || '';
    submitFeedback(selectedRating, comment);
  });
}

function highlightStars(val) {
  document.querySelectorAll('.star-btn').forEach(b => {
    const v = parseInt(b.dataset.v);
    b.textContent = v <= val ? '★' : '☆';
    b.classList.toggle('active', v <= val);
  });
}

async function submitFeedback(rating, comment) {
  if (!state.analysisId || !rating) return;
  try {
    await apiFetch('/api/feedback', {
      method: 'POST',
      body: {
        analysis_id: state.analysisId,
        rating,
        comment: comment || null,
        feedback_type: 'result_quality',
      },
    });
    const feedbackSection = document.getElementById('feedback-section');
    const thanks = document.getElementById('feedback-thanks');
    if (feedbackSection) {
      // 隱藏互動，顯示感謝
      feedbackSection.querySelectorAll('div:not(#feedback-thanks)').forEach(el => el.style.display = 'none');
      thanks?.classList.remove('hidden');
    }
  } catch { /* 回饋失敗不影響體驗 */ }
}

// ── patch renderResult：full_result 後呼叫 showPostUnlockUI ──────
const _origRenderResult = renderResult;
