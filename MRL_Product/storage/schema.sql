-- MRL_Product_v1 Schema
-- origin_signature: MrLiouWord
-- 所有時間均 UTC ISO8601

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- 使用者
CREATE TABLE IF NOT EXISTS users (
  id          TEXT PRIMARY KEY,         -- uuid
  email       TEXT UNIQUE,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Session（訪客也有 session）
CREATE TABLE IF NOT EXISTS sessions (
  id          TEXT PRIMARY KEY,
  user_id     TEXT REFERENCES users(id),
  token_hash  TEXT UNIQUE NOT NULL,
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at  TEXT NOT NULL
);

-- 分析任務
CREATE TABLE IF NOT EXISTS analyses (
  id              TEXT PRIMARY KEY,
  session_id      TEXT NOT NULL REFERENCES sessions(id),
  user_id         TEXT REFERENCES users(id),
  problem_text    TEXT NOT NULL,
  partial_result  TEXT,
  full_result     TEXT,
  status          TEXT NOT NULL DEFAULT 'pending',  -- pending | done | failed
  created_at      TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 訂單
CREATE TABLE IF NOT EXISTS orders (
  id              TEXT PRIMARY KEY,
  analysis_id     TEXT REFERENCES analyses(id),
  session_id      TEXT NOT NULL REFERENCES sessions(id),
  user_id         TEXT REFERENCES users(id),
  plan_type       TEXT NOT NULL,   -- once | subscription
  amount          INTEGER NOT NULL,
  currency        TEXT NOT NULL DEFAULT 'twd',
  status          TEXT NOT NULL DEFAULT 'pending',  -- pending | paid | unlocked | failed | refunded
  stripe_session_id TEXT,
  created_at      TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 付款紀錄
CREATE TABLE IF NOT EXISTS payments (
  id              TEXT PRIMARY KEY,
  order_id        TEXT NOT NULL REFERENCES orders(id),
  provider        TEXT NOT NULL DEFAULT 'stripe',
  provider_tx_id  TEXT UNIQUE,        -- Stripe payment_intent id
  amount          INTEGER NOT NULL,
  currency        TEXT NOT NULL DEFAULT 'twd',
  status          TEXT NOT NULL,      -- succeeded | failed | refunded
  raw_event       TEXT,               -- JSON 原始 webhook
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 帳本（唯一真相層）
CREATE TABLE IF NOT EXISTS ledger (
  id              TEXT PRIMARY KEY,
  event_type      TEXT NOT NULL,      -- payment_success | order_paid | result_unlock | sub_activated | sub_expired | refund
  analysis_id     TEXT REFERENCES analyses(id),
  order_id        TEXT REFERENCES orders(id),
  payment_id      TEXT REFERENCES payments(id),
  session_id      TEXT,
  amount          INTEGER,
  status          TEXT NOT NULL DEFAULT 'ok',
  meta_json       TEXT,
  origin_sig      TEXT NOT NULL DEFAULT 'MrLiouWord',
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 訂閱
CREATE TABLE IF NOT EXISTS subscriptions (
  id                TEXT PRIMARY KEY,
  user_id           TEXT REFERENCES users(id),
  session_id        TEXT,
  provider_sub_id   TEXT UNIQUE,    -- Stripe subscription id
  status            TEXT NOT NULL DEFAULT 'active',  -- active | cancelled | expired | past_due
  plan_type         TEXT NOT NULL DEFAULT 'monthly',
  amount            INTEGER NOT NULL,
  currency          TEXT NOT NULL DEFAULT 'twd',
  started_at        TEXT,
  expires_at        TEXT,
  created_at        TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Index
CREATE INDEX IF NOT EXISTS idx_analyses_session ON analyses(session_id);
CREATE INDEX IF NOT EXISTS idx_orders_analysis ON orders(analysis_id);
CREATE INDEX IF NOT EXISTS idx_orders_stripe_session ON orders(stripe_session_id);
CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_payments_tx ON payments(provider_tx_id);
CREATE INDEX IF NOT EXISTS idx_ledger_order ON ledger(order_id);
CREATE INDEX IF NOT EXISTS idx_ledger_analysis ON ledger(analysis_id);
CREATE INDEX IF NOT EXISTS idx_ledger_event ON ledger(event_type);
CREATE INDEX IF NOT EXISTS idx_subs_user ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subs_provider ON subscriptions(provider_sub_id);

-- ── 事件追蹤（第五包新增）────────────────────────────────────────
-- 用途：漏斗觀測 / 使用行為 / debug
-- 原則：只記錄，不修改，不刪除
CREATE TABLE IF NOT EXISTS event_logs (
  id            TEXT PRIMARY KEY,
  session_id    TEXT,
  user_id       TEXT,
  analysis_id   TEXT,
  order_id      TEXT,
  event_name    TEXT NOT NULL,   -- page_view_home / analyze_success / payment_success / ...
  page          TEXT,            -- 來源頁
  meta_json     TEXT,            -- 額外資訊（JSON）
  ip            TEXT,            -- 來源 IP（可選）
  ua            TEXT,            -- User-Agent 前 200 字元
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_evlog_event    ON event_logs(event_name);
CREATE INDEX IF NOT EXISTS idx_evlog_session  ON event_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_evlog_created  ON event_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_evlog_analysis ON event_logs(analysis_id);

-- ── 使用者回饋（第六包新增）─────────────────────────────────────
CREATE TABLE IF NOT EXISTS feedback (
  id            TEXT PRIMARY KEY,
  session_id    TEXT,
  user_id       TEXT,
  analysis_id   TEXT,
  rating        INTEGER,           -- 1–5，NULL 表示未評分
  comment       TEXT,              -- 文字回饋
  feedback_type TEXT DEFAULT 'general',  -- general / result_quality / pricing
  meta_json     TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_feedback_session  ON feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_feedback_rating   ON feedback(rating);
CREATE INDEX IF NOT EXISTS idx_feedback_analysis ON feedback(analysis_id);

-- ── 錯誤記錄（第六包新增）───────────────────────────────────────
CREATE TABLE IF NOT EXISTS error_logs (
  id          TEXT PRIMARY KEY,
  error_type  TEXT NOT NULL,     -- ai_failed / webhook_error / payment_error / server_error
  message     TEXT,
  stack       TEXT,
  session_id  TEXT,
  analysis_id TEXT,
  order_id    TEXT,
  context_json TEXT,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_errlog_type    ON error_logs(error_type);
CREATE INDEX IF NOT EXISTS idx_errlog_created ON error_logs(created_at);

-- ── 第七包：analyses 補 category 欄位 ───────────────────────────
-- 若欄位不存在才加（SQLite migration 用 ALTER TABLE）
-- 在 initDb 之後單獨執行，或直接跑此遷移
