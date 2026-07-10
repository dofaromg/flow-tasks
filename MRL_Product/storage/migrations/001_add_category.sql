-- Migration 001: analyses 補 category
-- origin_signature: MrLiouWord
-- 執行方式: sqlite3 /path/to/db.sqlite < 001_add_category.sql

-- 先確認欄位不存在才 ALTER（SQLite 無 IF NOT EXISTS 的 ALTER）
-- 若 column 已存在此 migration 會報錯，可忽略
ALTER TABLE analyses ADD COLUMN category TEXT DEFAULT NULL;
ALTER TABLE analyses ADD COLUMN example_prompt_used INTEGER DEFAULT 0;  -- 0/1 boolean

-- 在 event_logs 補 category 欄位（方便過濾）
ALTER TABLE event_logs ADD COLUMN category TEXT DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_analyses_category ON analyses(category);
CREATE INDEX IF NOT EXISTS idx_evlog_category ON event_logs(category);
