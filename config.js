// Supabase 連線設定
// 1. 到 https://supabase.com 建立專案
// 2. Project Settings → API，複製 Project URL 與 anon public key 貼到下面
// 3. Authentication → Providers → Google 啟用，並填入 Google Cloud 的 Client ID / Secret
//
// anon key 出現在公開網頁是正常設計，安全性靠資料庫的 RLS 政策把關，不是靠藏 key。
// 千萬不要把 service_role key 放進來 —— 那把是後台萬能鑰匙，會繞過所有 RLS。
window.SUPABASE_URL = '';
window.SUPABASE_ANON_KEY = '';
