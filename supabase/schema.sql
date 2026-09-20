-- 保險經紀人考古題練習 — Supabase 結構
-- 在 Supabase 主控台的 SQL Editor 貼上執行一次即可。

-- ─────────────────────────────────────────────
-- 1. 使用者檔案
-- ─────────────────────────────────────────────
create table if not exists public.profiles (
  id           uuid primary key references auth.users on delete cascade,
  email        text,
  full_name    text,
  avatar_url   text,
  is_admin     boolean     not null default false,
  is_blocked   boolean     not null default false,
  blocked_note text,
  created_at   timestamptz not null default now(),
  last_seen_at timestamptz
);

-- 註冊時自動建立 profile
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, email, full_name, avatar_url)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'name'),
    new.raw_user_meta_data->>'avatar_url'
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ─────────────────────────────────────────────
-- 2. 累計統計
-- ─────────────────────────────────────────────
create table if not exists public.user_stats (
  user_id        uuid primary key references auth.users on delete cascade,
  total_answered int  not null default 0,
  total_correct  int  not null default 0,
  wrong_pool     int  not null default 0,
  bookmarks      int  not null default 0,
  streak_days    int  not null default 0,
  section_stats  jsonb not null default '{}'::jsonb,
  updated_at     timestamptz not null default now()
);

-- ─────────────────────────────────────────────
-- 3. 每日活動（後台趨勢用）
-- ─────────────────────────────────────────────
create table if not exists public.daily_activity (
  user_id  uuid not null references auth.users on delete cascade,
  day      date not null,
  answered int  not null default 0,
  correct  int  not null default 0,
  primary key (user_id, day)
);
create index if not exists daily_activity_day_idx on public.daily_activity (day desc);

-- ─────────────────────────────────────────────
-- 4. 權限判斷輔助函式
--    security definer + 直接查表，避免 RLS 遞迴
-- ─────────────────────────────────────────────
create or replace function public.is_admin(uid uuid)
returns boolean
language sql
security definer set search_path = public
stable
as $$ select coalesce((select is_admin from public.profiles where id = uid), false) $$;

create or replace function public.is_blocked(uid uuid)
returns boolean
language sql
security definer set search_path = public
stable
as $$ select coalesce((select is_blocked from public.profiles where id = uid), false) $$;

-- ─────────────────────────────────────────────
-- 5. RLS
-- ─────────────────────────────────────────────
alter table public.profiles       enable row level security;
alter table public.user_stats     enable row level security;
alter table public.daily_activity enable row level security;

-- profiles：本人可讀自己（即使被鎖，否則前端無從得知自己被鎖）
drop policy if exists profiles_select_own on public.profiles;
create policy profiles_select_own on public.profiles
  for select using (auth.uid() = id);

drop policy if exists profiles_update_own on public.profiles;
create policy profiles_update_own on public.profiles
  for update using (auth.uid() = id and not public.is_blocked(auth.uid()))
  with check (
    auth.uid() = id
    -- 禁止自行提權或解鎖
    and is_admin   = (select p.is_admin   from public.profiles p where p.id = auth.uid())
    and is_blocked = (select p.is_blocked from public.profiles p where p.id = auth.uid())
  );

drop policy if exists profiles_admin_all on public.profiles;
create policy profiles_admin_all on public.profiles
  for all using (public.is_admin(auth.uid()))
  with check (public.is_admin(auth.uid()));

-- user_stats：本人讀寫（被鎖則不可）
drop policy if exists stats_own on public.user_stats;
create policy stats_own on public.user_stats
  for all using (auth.uid() = user_id and not public.is_blocked(auth.uid()))
  with check (auth.uid() = user_id and not public.is_blocked(auth.uid()));

drop policy if exists stats_admin on public.user_stats;
create policy stats_admin on public.user_stats
  for select using (public.is_admin(auth.uid()));

-- daily_activity：同上
drop policy if exists daily_own on public.daily_activity;
create policy daily_own on public.daily_activity
  for all using (auth.uid() = user_id and not public.is_blocked(auth.uid()))
  with check (auth.uid() = user_id and not public.is_blocked(auth.uid()));

drop policy if exists daily_admin on public.daily_activity;
create policy daily_admin on public.daily_activity
  for select using (public.is_admin(auth.uid()));

-- ─────────────────────────────────────────────
-- 6. 後台彙總檢視（只有管理員讀得到，靠底層表的 RLS 把關）
-- ─────────────────────────────────────────────
create or replace view public.admin_overview
with (security_invoker = true) as
select
  p.id,
  p.email,
  p.full_name,
  p.avatar_url,
  p.is_admin,
  p.is_blocked,
  p.blocked_note,
  p.created_at,
  p.last_seen_at,
  coalesce(s.total_answered, 0) as total_answered,
  coalesce(s.total_correct, 0)  as total_correct,
  case when coalesce(s.total_answered,0) > 0
       then round(100.0 * s.total_correct / s.total_answered, 1)
       else 0 end               as accuracy,
  coalesce(s.wrong_pool, 0)     as wrong_pool,
  coalesce(s.streak_days, 0)    as streak_days,
  s.section_stats,
  s.updated_at
from public.profiles p
left join public.user_stats s on s.user_id = p.id;

-- ─────────────────────────────────────────────
-- 7. 心跳：更新 last_seen_at
-- ─────────────────────────────────────────────
create or replace function public.touch_last_seen()
returns void
language sql
security definer set search_path = public
as $$
  update public.profiles set last_seen_at = now() where id = auth.uid()
$$;

-- ─────────────────────────────────────────────
-- 8. 設定自己為管理員（把 email 換成你的 Google 帳號後執行）
-- ─────────────────────────────────────────────
-- update public.profiles set is_admin = true where email = 'davidyoudavid@gmail.com';
