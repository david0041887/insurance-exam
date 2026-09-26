-- 跨裝置進度同步：整份錯題池／星星／收藏／筆記存成一筆 JSON
CREATE TABLE IF NOT EXISTS user_progress (
  user_id    TEXT PRIMARY KEY,
  data       TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
