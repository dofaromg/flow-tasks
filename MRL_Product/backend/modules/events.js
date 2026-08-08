'use strict';
// modules/events.js — 最小事件追蹤引擎（漏斗觀測）
// origin_signature: MrLiouWord
//
// 追蹤的漏斗事件（順序代表轉換路徑）：
//   page_view_home       首頁進入
//   page_view_app        app 頁進入
//   page_view_pricing    pricing 頁進入
//   analyze_started      點了「開始分析」
//   analyze_success      AI 分析完成，partial_result 可見
//   analyze_failed       分析失敗
//   pay_click_once       點擊單次解鎖
//   pay_click_sub        點擊月費訂閱
//   payment_success      Stripe 付款成功（webhook 觸發）
//   unlock_success       full_result 成功解鎖
//   result_full_view     使用者成功取得 full_result
//   sub_activated        訂閱成立

const { getDb } = require('./db');
const { uuid } = require('../utils/ids');
const { now } = require('../utils/time');
const logger = require('../utils/logger');

/**
 * 記錄事件（非阻塞，失敗不影響主流程）
 */
function track(eventName, ctx = {}) {
  const {
    sessionId, userId, analysisId, orderId,
    page, meta, ip, ua, category,
  } = ctx;

  try {
    const db = getDb();
    db.prepare(`
      INSERT INTO event_logs
        (id, session_id, user_id, analysis_id, order_id, event_name, category, page, meta_json, ip, ua, created_at)
      VALUES
        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      uuid(),
      sessionId  || null,
      userId     || null,
      analysisId || null,
      orderId    || null,
      eventName,
      ctx.category || null,
      page       || null,
      meta       ? JSON.stringify(meta) : null,
      ip         ? String(ip).slice(0, 45)  : null,
      ua         ? String(ua).slice(0, 200) : null,
      now()
    );
  } catch (e) {
    // 事件追蹤失敗不可影響主流程
    logger.debug('Event track failed', { eventName, err: e.message });
  }
}

/**
 * Express middleware：自動追蹤頁面瀏覽
 * 掛在 page router 上
 */
function pageViewMiddleware(eventName) {
  return (req, res, next) => {
    // 非同步追蹤，不等待
    setImmediate(() => {
      track(eventName, {
        sessionId: req.sessionId,
        userId: req.userId,
        page: req.path,
        ip: req.ip,
        ua: req.headers['user-agent'],
      });
    });
    next();
  };
}

/**
 * 從 request 中提取追蹤 context（給 API handler 用）
 */
function ctxFromReq(req, extra = {}) {
  return {
    sessionId:  req.sessionId,
    userId:     req.userId,
    ip:         req.ip,
    ua:         req.headers?.['user-agent'],
    ...extra,
  };
}

/**
 * 漏斗查詢：某事件在某時間範圍的計數
 */
function countEvent(eventName, { days = 7 } = {}) {
  const db = getDb();
  return db.prepare(`
    SELECT COUNT(*) as c FROM event_logs
    WHERE event_name = ?
    AND created_at >= datetime('now', ? || ' days')
  `).get(eventName, `-${days}`).c;
}

/**
 * 每日分組計數（最近 N 天）
 */
function dailyCounts(eventName, days = 7) {
  const db = getDb();
  return db.prepare(`
    SELECT
      date(created_at) as day,
      COUNT(*) as count
    FROM event_logs
    WHERE event_name = ?
    AND created_at >= datetime('now', ? || ' days')
    GROUP BY date(created_at)
    ORDER BY day DESC
  `).all(eventName, `-${days}`);
}

/**
 * 完整漏斗統計
 */
function getFunnel(days = 7) {
  const events = [
    'page_view_home',
    'page_view_app',
    'analyze_started',
    'analyze_success',
    'pay_click_once',
    'payment_success',
    'unlock_success',
  ];

  const funnel = {};
  events.forEach(e => {
    funnel[e] = countEvent(e, { days });
  });

  // 轉換率計算
  const toRate = (a, b) => b > 0 ? ((a / b) * 100).toFixed(1) + '%' : 'n/a';
  const toNum  = (a, b) => b > 0 ? (a / b) * 100 : 0;

  funnel._rates = {
    home_to_app:       toRate(funnel.page_view_app,    funnel.page_view_home),
    app_to_analyze:    toRate(funnel.analyze_success,  funnel.page_view_app),
    analyze_to_pay:    toRate(funnel.payment_success,  funnel.analyze_success),
    pay_to_unlock:     toRate(funnel.unlock_success,   funnel.payment_success),
    overall:           toRate(funnel.unlock_success,   funnel.page_view_home),
  };

  // 第九包：診斷摘要（找出最大流失點）
  const stages = [
    { key: 'home_to_app',    label: '首頁 → App',      from: funnel.page_view_home,   to: funnel.page_view_app },
    { key: 'app_to_analyze', label: 'App → 分析',       from: funnel.page_view_app,    to: funnel.analyze_success },
    { key: 'analyze_to_pay', label: '分析 → 付款',      from: funnel.analyze_success,  to: funnel.payment_success },
    { key: 'pay_to_unlock',  label: '付款 → 解鎖',      from: funnel.payment_success,  to: funnel.unlock_success },
  ];

  // 找出流失最大的階段（rate 最低的非 0 來源）
  let worstStage = null;
  let worstRate  = 101;
  stages.forEach(s => {
    if (s.from > 0) {
      const rate = toNum(s.to, s.from);
      if (rate < worstRate) { worstRate = rate; worstStage = s; }
    }
  });

  // 診斷建議
  const diagnosisMap = {
    home_to_app:    '首頁 CTA 不夠強，考慮優化 Hero 文案或熱門情境順序',
    app_to_analyze: 'App 啟動摩擦高，考慮改善 category 文案或 example prompts',
    analyze_to_pay: 'Partial 吸引力不足，考慮改善鎖定區塊文案或 partial 切法',
    pay_to_unlock:  '付款流程有摩擦，確認 webhook / confirmation 是否正常',
  };

  funnel._diagnosis = {
    worst_stage:       worstStage ? worstStage.label : 'n/a',
    worst_rate:        worstStage ? worstRate.toFixed(1) + '%' : 'n/a',
    suggestion:        worstStage ? diagnosisMap[worstStage.key] : '數據不足，繼續收集',
    data_sufficient:   funnel.page_view_home >= 20,  // 至少 20 訪客才有意義
  };

  return funnel;
}

/**
 * 近期事件（debug 用）
 */
function recentEvents(limit = 30) {
  return getDb().prepare(`
    SELECT id, event_name, session_id, analysis_id, order_id, page, created_at
    FROM event_logs
    ORDER BY created_at DESC
    LIMIT ?
  `).all(limit);
}

/**
 * 今日 + 近 7 日 metrics 摘要
 */
function getMetrics() {
  const db = getDb();

  const countWhere = (table, where, days) => db.prepare(`
    SELECT COUNT(*) as c FROM ${table}
    WHERE ${where}
    AND created_at >= datetime('now', '-${days} days')
  `).get().c;

  const sumWhere = (table, col, where, days) => db.prepare(`
    SELECT COALESCE(SUM(${col}), 0) as s FROM ${table}
    WHERE ${where}
    AND created_at >= datetime('now', '-${days} days')
  `).get().s;

  return {
    today: {
      home_views:      countEvent('page_view_home',   { days: 1 }),
      app_views:       countEvent('page_view_app',    { days: 1 }),
      analyzes:        countEvent('analyze_success',  { days: 1 }),
      payments:        countEvent('payment_success',  { days: 1 }),
      unlocks:         countEvent('unlock_success',   { days: 1 }),
      revenue_twd:     Math.floor(sumWhere('payments', 'amount', "status='succeeded'", 1) / 100),
    },
    week: {
      home_views:      countEvent('page_view_home',   { days: 7 }),
      app_views:       countEvent('page_view_app',    { days: 7 }),
      analyzes:        countEvent('analyze_success',  { days: 7 }),
      payments:        countEvent('payment_success',  { days: 7 }),
      unlocks:         countEvent('unlock_success',   { days: 7 }),
      revenue_twd:     Math.floor(sumWhere('payments', 'amount', "status='succeeded'", 7) / 100),
      new_orders:      countWhere('orders', "status IN ('paid','unlocked')", 7),
      active_subs:     db.prepare("SELECT COUNT(*) as c FROM subscriptions WHERE status='active'").get().c,
    },
    funnel: getFunnel(7),
  };
}

module.exports = { track, pageViewMiddleware, ctxFromReq, countEvent, dailyCounts, getFunnel, recentEvents, getMetrics };

// ── 第七包：category 統計 ────────────────────────────────────────

/**
 * 各 category 的分析次數（近 N 天）
 */
function categoryBreakdown(days = 7) {
  const db = getDb();
  return db.prepare(`
    SELECT
      COALESCE(category, 'uncategorized') as category,
      COUNT(*) as count
    FROM event_logs
    WHERE event_name = 'analyze_success'
    AND created_at >= datetime('now', '-' || ? || ' days')
    GROUP BY category
    ORDER BY count DESC
  `).all(days);
}

/**
 * 各 category 的付款點擊次數
 */
function categoryPaymentClicks(days = 7) {
  const db = getDb();
  return db.prepare(`
    SELECT
      COALESCE(category, 'uncategorized') as category,
      COUNT(*) as count
    FROM event_logs
    WHERE event_name = 'pay_click_once'
    AND created_at >= datetime('now', '-' || ? || ' days')
    GROUP BY category
    ORDER BY count DESC
  `).all(days);
}

/**
 * 各 category 的解鎖成功次數
 */
function categoryUnlocks(days = 7) {
  const db = getDb();
  return db.prepare(`
    SELECT
      COALESCE(category, 'uncategorized') as category,
      COUNT(*) as count
    FROM event_logs
    WHERE event_name = 'unlock_success'
    AND created_at >= datetime('now', '-' || ? || ' days')
    GROUP BY category
    ORDER BY count DESC
  `).all(days);
}

/**
 * 完整 category funnel（分析→點擊→解鎖）
 */
function getCategoryFunnel(days = 7) {
  const analyzes = categoryBreakdown(days);
  const clicks   = categoryPaymentClicks(days);
  const unlocks  = categoryUnlocks(days);

  // 合併成 category → { analyzes, clicks, unlocks, click_rate, unlock_rate }
  const map = {};
  analyzes.forEach(r => {
    map[r.category] = { category: r.category, analyzes: r.count, clicks: 0, unlocks: 0 };
  });
  clicks.forEach(r => {
    if (!map[r.category]) map[r.category] = { category: r.category, analyzes: 0, clicks: 0, unlocks: 0 };
    map[r.category].clicks = r.count;
  });
  unlocks.forEach(r => {
    if (!map[r.category]) map[r.category] = { category: r.category, analyzes: 0, clicks: 0, unlocks: 0 };
    map[r.category].unlocks = r.count;
  });

  const rows = Object.values(map);
  const maxAnalyzes = Math.max(...rows.map(r => r.analyzes), 1);

  return rows.map(d => {
    // 數值率
    const clickRateNum   = d.analyzes > 0 ? (d.clicks   / d.analyzes) * 100 : 0;
    const unlockRateNum  = d.clicks   > 0 ? (d.unlocks  / d.clicks)   * 100 : 0;
    const paymentRateNum = d.clicks   > 0 ? (d.unlocks  / d.clicks)   * 100 : 0; // unlock ≈ payment

    // heat_score：分析次數相對比例 0–100
    const heatScore = Math.round((d.analyzes / maxAnalyzes) * 100);

    // recommendation 規則（第九包）
    let recommendation = '';
    if (d.analyzes === 0) {
      recommendation = '暫無數據';
    } else if (heatScore >= 40 && clickRateNum >= 5) {
      recommendation = '主打候選';        // 熱度高 + 點擊轉換好
    } else if (heatScore >= 40 && clickRateNum < 5) {
      recommendation = '需優化 partial';  // 熱度高但沒點解鎖
    } else if (heatScore < 40 && clickRateNum >= 10) {
      recommendation = '需增加流量';      // 成交率高但流量少
    } else if (heatScore < 20) {
      recommendation = '暫不主打';        // 熱度太低
    } else {
      recommendation = '持續觀察';
    }

    return {
      ...d,
      heat_score:   heatScore,
      click_rate:   d.analyzes > 0 ? clickRateNum.toFixed(1) + '%'   : 'n/a',
      unlock_rate:  d.clicks   > 0 ? unlockRateNum.toFixed(1) + '%'  : 'n/a',
      payment_rate: d.clicks   > 0 ? paymentRateNum.toFixed(1) + '%' : 'n/a',
      recommendation,
    };
  }).sort((a, b) => b.analyzes - a.analyzes)
  .map((d, i) => ({
    ...d,
    rank: i === 0 ? 'PRIMARY' : i === 1 ? 'SECONDARY' : '',
  }));
}

module.exports.categoryBreakdown    = categoryBreakdown;
module.exports.categoryPaymentClicks = categoryPaymentClicks;
module.exports.categoryUnlocks      = categoryUnlocks;
module.exports.getCategoryFunnel    = getCategoryFunnel;
