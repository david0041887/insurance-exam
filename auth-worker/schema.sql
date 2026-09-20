-- 保險經紀人考古題 — D1 結構
CREATE TABLE IF NOT EXISTS users (
  id            TEXT PRIMARY KEY,          -- Google sub
  email         TEXT,
  name          TEXT,
  avatar        TEXT,
  is_admin      INTEGER NOT NULL DEFAULT 0,
  is_blocked    INTEGER NOT NULL DEFAULT 0,
  blocked_note  TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  last_seen_at  TEXT
);
CREATE INDEX IF NOT EXISTS users_email_idx ON users(email);

CREATE TABLE IF NOT EXISTS user_stats (
  user_id        TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  total_answered INTEGER NOT NULL DEFAULT 0,
  total_correct  INTEGER NOT NULL DEFAULT 0,
  wrong_pool     INTEGER NOT NULL DEFAULT 0,
  bookmarks      INTEGER NOT NULL DEFAULT 0,
  streak_days    INTEGER NOT NULL DEFAULT 0,
  section_stats  TEXT NOT NULL DEFAULT '{}',
  updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS daily_activity (
  user_id  TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  day      TEXT NOT NULL,
  answered INTEGER NOT NULL DEFAULT 0,
  correct  INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, day)
);
CREATE INDEX IF NOT EXISTS daily_day_idx ON daily_activity(day DESC);
