// delivery-renderer.js — MRL Delivery Template Renderer
// origin_signature: MrLiouWord
// phase: 第十三包 MRL_Delivery_Template_Product_v1
//
// Template Registry：
//   renderDeliveryTemplate(templateId, data, container)
//   → 依 templateId 分派到對應的 renderer
//   → 目前只有 product template，未來可直接 register 新的
'use strict';

// ── Style Role → CSS mapping ─────────────────────────────────────
// 將語義 style role 映射到 CSS class / 行為
const STYLE_ROLE_MAP = {
  accent:           { blockClass: 'result-block result-block--accent', labelClass: '' },
  doc_section:      { blockClass: 'result-block', labelClass: '' },
  step_list:        { blockClass: 'result-block', labelClass: '' },
  contrast_warning: { blockClass: 'result-block result-block--warn', labelClass: '' },
  failure_warning:  { blockClass: 'warning-block warning-block--product', isSpecial: 'warning' },
  footer_cta:       { blockClass: 'product-result-footer', isSpecial: 'footer' },
};

// ── MRL_Delivery_Template_Product_v1 Renderer ────────────────────
/**
 * product template 的欄位定義
 * section → { label, styleRole, blockType }
 */
const PRODUCT_TEMPLATE_DEF = {
  template_id:  'MRL_Delivery_Template_Product_v1',
  title:        '你的第一版產品方案',
  subtitle:     '以下內容已根據你的問題，整理成可開始執行的第一版方案。可直接照順序往下做。',
  footer_text:  '這份方案可以直接作為你下一步實作、討論或交付的起點。',
  footer_note:  '複製下來存到你的工具、傳給工程師、或直接開始第一步都可以。',
  sections: [
    { key: 'core_judgment',       label: '核心判斷',      styleRole: 'accent',           blockType: 'text',     aiField: 'summary' },
    { key: 'problem_breakdown',   label: '問題拆解',      styleRole: 'doc_section',      blockType: 'list',     aiField: 'breakdown' },
    { key: 'first_version_scope', label: '第一版範圍建議', styleRole: 'doc_section',      blockType: 'list',     aiField: 'directions' },
    { key: 'execution_steps',     label: '執行順序',      styleRole: 'step_list',        blockType: 'numbered', aiField: 'steps' },
    { key: 'do_vs_not_do',        label: '先做 vs 先不做', styleRole: 'contrast_warning', blockType: 'list',     aiField: 'priorities' },
    { key: 'next_actions',        label: '下一步建議',    styleRole: 'doc_section',      blockType: 'list',     aiField: 'supplements' },
    { key: 'common_failures',     label: '常見失敗原因',  styleRole: 'failure_warning',  blockType: 'text',     aiField: 'warning' },
    { key: 'delivery_footer',     label: null,            styleRole: 'footer_cta',       blockType: 'footer',   aiField: null },
  ],
};

// ── Render helpers ────────────────────────────────────────────────
function _escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function _makeDocBlock(label, content, blockType, styleRole) {
  const roleStyle = STYLE_ROLE_MAP[styleRole] || STYLE_ROLE_MAP.doc_section;
  const block = document.createElement('div');
  block.className = roleStyle.blockClass;

  // 標籤
  if (label) {
    const lbl = document.createElement('div');
    lbl.className = 'result-block__label';
    lbl.textContent = label;
    block.appendChild(lbl);
  }

  // 內容
  if (blockType === 'text') {
    const p = document.createElement('div');
    p.className = 'result-block__text';
    p.textContent = content;
    block.appendChild(p);
  } else if (blockType === 'list' || blockType === 'numbered') {
    const list = document.createElement('div');
    list.className = 'result-list';
    const arr = Array.isArray(content) ? content : [content];
    arr.forEach((item, i) => {
      const li = document.createElement('div');
      li.className = 'result-list__item';
      li.innerHTML = blockType === 'numbered'
        ? `<span class="num">0${i + 1}</span><span>${_escHtml(item)}</span>`
        : `<span class="num">—</span><span>${_escHtml(item)}</span>`;
      list.appendChild(li);
    });
    block.appendChild(list);
  }

  return block;
}

// ── Product Template Renderer ─────────────────────────────────────
/**
 * 渲染 MRL_Delivery_Template_Product_v1
 * @param {object} rawResult  — AI 原始輸出（含 summary/breakdown/... 欄位）
 * @param {boolean} isPartial — 是否為 partial（決定顯示哪些 sections）
 * @returns {DocumentFragment} — 可直接 append 到容器
 */
function renderProductDeliveryTemplate(rawResult, isPartial) {
  const def = PRODUCT_TEMPLATE_DEF;
  const frag = document.createDocumentFragment();

  // Header（僅 full）
  if (!isPartial) {
    const header = document.createElement('div');
    header.className = 'product-result-header';
    header.innerHTML =
      `<div class="product-result-header__title">${def.title}</div>` +
      `<div class="product-result-header__sub">${def.subtitle}</div>`;
    frag.appendChild(header);
  }

  const doc = document.createElement('div');
  doc.className = isPartial ? 'result-doc' : 'result-doc result-doc--product';

  def.sections.forEach(sec => {
    const roleStyle = STYLE_ROLE_MAP[sec.styleRole];

    // 跳過 footer（full 時單獨處理）
    if (sec.blockType === 'footer') return;

    // 取資料
    const val = sec.aiField ? rawResult[sec.aiField] : null;
    if (!val || (Array.isArray(val) && val.length === 0)) return;

    // warning 特殊處理
    if (roleStyle?.isSpecial === 'warning') {
      if (!isPartial) {
        const warn = document.createElement('div');
        warn.className = 'warning-block warning-block--product';
        warn.innerHTML =
          '<span style="font-size:11px;letter-spacing:0.06em;text-transform:uppercase;color:var(--accent);margin-right:8px;">⚠ 常見失敗原因</span>' +
          _escHtml(val);
        frag.appendChild(doc);
        frag.appendChild(warn);
      }
      return;
    }

    // Partial 只顯示前三個 sections（core_judgment / problem_breakdown / first_version_scope 部分）
    if (isPartial) {
      const partialSections = ['core_judgment', 'problem_breakdown', 'first_version_scope'];
      if (!partialSections.includes(sec.key)) return;
      // first_version_scope partial 只給第一個
      const displayVal = sec.key === 'first_version_scope' && Array.isArray(val)
        ? [val[0]]
        : val;
      doc.appendChild(_makeDocBlock(sec.label, displayVal, sec.blockType, sec.styleRole));
      return;
    }

    // Full：顯示所有 sections
    doc.appendChild(_makeDocBlock(sec.label, val, sec.blockType, sec.styleRole));
  });

  if (!frag.contains(doc)) frag.appendChild(doc);

  // Footer（僅 full）
  if (!isPartial) {
    const footer = document.createElement('div');
    footer.className = 'product-result-footer';
    footer.innerHTML =
      `<div class="product-result-footer__text">${def.footer_text}</div>` +
      `<div class="product-result-footer__note">${def.footer_note}</div>`;
    frag.appendChild(footer);
  }

  return frag;
}

// ── Template Registry ─────────────────────────────────────────────
/**
 * Template registry：template_id → renderer function
 * 新增 category 模板時，只需在這裡 register。
 */
const TEMPLATE_REGISTRY = {
  'MRL_Delivery_Template_Product_v1': renderProductDeliveryTemplate,
};

/**
 * 通用分派入口：依 templateId 分派到對應 renderer
 * @param {string} templateId
 * @param {object} rawResult
 * @param {boolean} isPartial
 * @returns {DocumentFragment | null}
 */
function renderDeliveryTemplate(templateId, rawResult, isPartial) {
  const renderer = TEMPLATE_REGISTRY[templateId];
  if (!renderer) return null;
  return renderer(rawResult, isPartial);
}

/**
 * 根據 category 推斷 template_id
 */
function templateIdFromCategory(category) {
  const map = {
    product: 'MRL_Delivery_Template_Product_v1',
    // 未來擴充：
    // decision: 'MRL_Delivery_Template_Decision_v1',
    // system:   'MRL_Delivery_Template_System_v1',
  };
  return map[category] || null;
}
