'use strict';
// backend/core/scaffolds/scaffold-builder.js
// MRL Scaffold Generator — Builder
// origin_signature: MrLiouWord
//
// 職責：讀取 ProductPack，決定生成哪些檔案，建立 manifest + 內容清單
// 輸入：ProductPack object
// 輸出：{ manifest, files: [{ path, content }] }

const { uuid } = require('../../utils/ids');
const { now }  = require('../../utils/time');
const templates = require('./scaffold-templates');

/**
 * 從 ProductPack 建立 scaffold plan
 * @param {object} pack — ProductPack（第十五包 schema）
 * @returns {{ manifest, files }}
 */
function buildScaffoldPlan(pack) {
  if (!pack || pack.pack_type !== 'product') {
    throw Object.assign(
      new Error('Only product packs are supported in this version'),
      { status: 400 }
    );
  }

  const scaffoldId = 'mrl_scaffold_' + uuid().replace(/-/g, '').slice(0, 12);
  const ctx = _buildContext(pack, scaffoldId);

  // ── Manifest ────────────────────────────────────────────────────
  const manifest = {
    scaffold_id:       scaffoldId,
    pack_id:           pack.pack_id,
    category:          pack.category,
    template_id:       pack.template_id,
    mode:              pack.mode,
    mode_label:        pack.mode_label,
    title:             pack.title,
    pages:             pack.pages?.map(p => p.name) || [],
    flows:             pack.flows?.map(f => f.name) || [],
    target_stack:      'node_sqlite_docker_nginx',
    source_pack_path:  `storage/packs/${pack.pack_id}.json`,
    generated_at:      now(),
    origin:            'MrLiouWord',
  };

  // ── File plan ───────────────────────────────────────────────────
  const files = [
    { path: 'manifest.json',                     content: JSON.stringify(manifest, null, 2) },
    { path: 'README.md',                          content: templates.readme(ctx) },
    { path: 'docs/scaffold-notes.md',             content: templates.scaffoldNotes(ctx) },

    // Frontend pages（依 pack.pages 生成）
    ...( pack.pages || [] ).map(p => ({
      path: `frontend/${p.name}.html`,
      content: templates.htmlPage({ ...ctx, page: p }),
    })),
    { path: 'frontend/assets/style.css',          content: templates.cssStub(ctx) },
    { path: 'frontend/assets/app.js',             content: templates.appJsStub(ctx) },

    // Backend
    { path: 'backend/server.js',                  content: templates.serverJs(ctx) },
    { path: 'backend/config.js',                  content: templates.configJs(ctx) },
    { path: 'backend/routes/api.js',              content: templates.routeApiJs(ctx) },
    { path: 'backend/routes/payment.js',          content: templates.routePaymentJs(ctx) },
    { path: 'backend/routes/webhook.js',          content: templates.routeWebhookJs(ctx) },
    { path: 'backend/modules/ai.js',              content: templates.moduleAiJs(ctx) },
    { path: 'backend/modules/order.js',           content: templates.moduleOrderJs(ctx) },
    { path: 'backend/modules/ledger.js',          content: templates.moduleLedgerJs(ctx) },
    { path: 'backend/modules/confirmation.js',    content: templates.moduleConfirmationJs(ctx) },
    { path: 'storage/schema.sql',                 content: templates.schemaSql(ctx) },
    { path: 'package.json',                       content: templates.packageJson(ctx) },

    // Deploy
    { path: 'deploy/Dockerfile',                  content: templates.dockerfile(ctx) },
    { path: 'deploy/docker-compose.yml',          content: templates.dockerCompose(ctx) },
    { path: 'deploy/nginx.conf',                  content: templates.nginxConf(ctx) },
    { path: '.env.example',                       content: templates.envExample(ctx) },
    { path: '.gitignore',                         content: templates.gitignore(ctx) },
  ];

  return { manifest, files };
}

// ── Build context（pack → template 變數）──────────────────────────
function _buildContext(pack, scaffoldId) {
  const title = pack.title || 'MRL Product';
  const slug  = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 30) || 'mrl-product';

  return {
    pack,
    scaffoldId,
    title,
    slug,
    mode:          pack.mode || 'website',
    modeLabel:     pack.mode_label || '做第一版網站',
    summary:       pack.summary || '',
    coreJudgment:  pack.core_judgment || '',
    scope:         pack.first_version_scope || [],
    steps:         pack.execution_steps || [],
    doVsNot:       pack.do_vs_not_do || [],
    pages:         pack.pages || [],
    flows:         pack.flows || [],
    pricing:       pack.pricing_model || { once_amount: 299, sub_amount: 499, currency: 'TWD' },
    deployment:    pack.deployment || {},
    generatedAt:   now(),
    templateId:    pack.template_id,
    packId:        pack.pack_id,
  };
}

module.exports = { buildScaffoldPlan };
