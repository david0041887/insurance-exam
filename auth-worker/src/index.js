/**
 * 保險經紀人考古題 — 登入與後台 API
 * Cloudflare Worker + D1，Google OAuth，JWT 存在前端 localStorage
 * （不用 cookie，避免 GitHub Pages 與 workers.dev 的跨站 cookie 問題）
 */

const TOKEN_TTL = 60 * 60 * 24 * 30; // 30 天

// ── 工具 ──────────────────────────────────────────────
const enc = new TextEncoder();

function b64url(buf) {
  const bytes = buf instanceof ArrayBuffer ? new Uint8Array(buf) : buf;
  let s = '';
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
function b64urlDecode(str) {
  str = str.replace(/-/g, '+').replace(/_/g, '/');
  while (str.length % 4) str += '=';
  const bin = atob(str);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

async function hmacKey(secret) {
  return crypto.subtle.importKey('raw', enc.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign', 'verify']);
}

async function signJWT(payload, secret) {
  const header = b64url(enc.encode(JSON.stringify({ alg: 'HS256', typ: 'JWT' })));
  const body = b64url(enc.encode(JSON.stringify(payload)));
  const data = `${header}.${body}`;
  const sig = await crypto.subtle.sign('HMAC', await hmacKey(secret), enc.encode(data));
  return `${data}.${b64url(sig)}`;
}

async function verifyJWT(token, secret) {
  if (!token || token.split('.').length !== 3) return null;
  const [h, b, s] = token.split('.');
  const ok = await crypto.subtle.verify('HMAC', await hmacKey(secret),
    b64urlDecode(s), enc.encode(`${h}.${b}`));
  if (!ok) return null;
  let payload;
  try { payload = JSON.parse(new TextDecoder().decode(b64urlDecode(b))); }
  catch { return null; }
  if (!payload.exp || payload.exp < Math.floor(Date.now() / 1000)) return null;
  return payload;
}

function corsHeaders(req, env) {
  const origin = req.headers.get('Origin') || '';
  const allowed = (env.ALLOWED_ORIGINS || '').split(',').map(s => s.trim()).filter(Boolean);
  const h = {
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Access-Control-Allow-Headers': 'Authorization,Content-Type',
    'Access-Control-Max-Age': '86400',
    'Vary': 'Origin',
  };
  if (allowed.includes(origin)) h['Access-Control-Allow-Origin'] = origin;
  return h;
}

function json(req, env, obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', ...corsHeaders(req, env) },
  });
}

/** 取出目前使用者；每次都查 D1，所以停用會立即生效 */
async function currentUser(req, env) {
  const auth = req.headers.get('Authorization') || '';
  const m = auth.match(/^Bearer\s+(.+)$/i);
  if (!m) return { error: 'no_token', status: 401 };
  const payload = await verifyJWT(m[1], env.JWT_SECRET);
  if (!payload) return { error: 'bad_token', status: 401 };
  const row = await env.DB.prepare(
    'SELECT id,email,name,avatar,is_admin,is_blocked,blocked_note,created_at,last_seen_at FROM users WHERE id=?'
  ).bind(payload.sub).first();
  if (!row) return { error: 'no_user', status: 401 };
  if (row.is_blocked) return { error: 'blocked', note: row.blocked_note || null, status: 403 };
  return { user: row };
}

// ── 路由 ──────────────────────────────────────────────
export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    const path = url.pathname.replace(/\/+$/, '') || '/';

    if (req.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders(req, env) });
    }

    try {
      // ---- 1. 導向 Google ----
      if (path === '/auth/start') {
        if (!env.GOOGLE_CLIENT_ID) return new Response('GOOGLE_CLIENT_ID 尚未設定', { status: 500 });
        const state = b64url(crypto.getRandomValues(new Uint8Array(16)));
        const redirect = `${url.origin}/auth/callback`;
        const g = new URL('https://accounts.google.com/o/oauth2/v2/auth');
        g.searchParams.set('client_id', env.GOOGLE_CLIENT_ID);
        g.searchParams.set('redirect_uri', redirect);
        g.searchParams.set('response_type', 'code');
        g.searchParams.set('scope', 'openid email profile');
        g.searchParams.set('state', state);
        g.searchParams.set('prompt', 'select_account');
        return Response.redirect(g.toString(), 302);
      }

      // ---- 2. Google 回呼 ----
      if (path === '/auth/callback') {
        const code = url.searchParams.get('code');
        const site = env.SITE_URL || '/';
        if (!code) return Response.redirect(site + '#err=no_code', 302);

        const redirect = `${url.origin}/auth/callback`;
        const tok = await fetch('https://oauth2.googleapis.com/token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams({
            code,
            client_id: env.GOOGLE_CLIENT_ID,
            client_secret: env.GOOGLE_CLIENT_SECRET,
            redirect_uri: redirect,
            grant_type: 'authorization_code',
          }),
        }).then(r => r.json());

        if (!tok.id_token) return Response.redirect(site + '#err=token_exchange', 302);

        // id_token 來自 Google 的 TLS 回應，這裡只解 payload
        const claims = JSON.parse(new TextDecoder().decode(b64urlDecode(tok.id_token.split('.')[1])));
        if (claims.aud !== env.GOOGLE_CLIENT_ID) return Response.redirect(site + '#err=bad_aud', 302);
        if (!claims.sub) return Response.redirect(site + '#err=no_sub', 302);

        // 第一位註冊者自動成為管理員
        const { count } = await env.DB.prepare('SELECT COUNT(*) AS count FROM users').first();
        const firstUser = count === 0;

        await env.DB.prepare(
          `INSERT INTO users (id,email,name,avatar,is_admin,last_seen_at)
           VALUES (?1,?2,?3,?4,?5,datetime('now'))
           ON CONFLICT(id) DO UPDATE SET
             email=excluded.email, name=excluded.name,
             avatar=excluded.avatar, last_seen_at=datetime('now')`
        ).bind(claims.sub, claims.email || null, claims.name || null,
               claims.picture || null, firstUser ? 1 : 0).run();

        const jwt = await signJWT({
          sub: claims.sub,
          exp: Math.floor(Date.now() / 1000) + TOKEN_TTL,
        }, env.JWT_SECRET);

        // 放在 fragment，不會進伺服器紀錄
        return Response.redirect(`${site}#token=${jwt}`, 302);
      }

      // ---- 3. 目前使用者 ----
      if (path === '/api/me') {
        const r = await currentUser(req, env);
        if (r.error) return json(req, env, { error: r.error, note: r.note || null }, r.status);
        await env.DB.prepare("UPDATE users SET last_seen_at=datetime('now') WHERE id=?")
          .bind(r.user.id).run();
        return json(req, env, { user: r.user });
      }

      // ---- 4. 上傳進度 ----
      if (path === '/api/stats' && req.method === 'POST') {
        const r = await currentUser(req, env);
        if (r.error) return json(req, env, { error: r.error, note: r.note || null }, r.status);
        const b = await req.json().catch(() => ({}));
        const n = v => Math.max(0, Math.min(1e9, parseInt(v, 10) || 0));

        await env.DB.prepare(
          `INSERT INTO user_stats (user_id,total_answered,total_correct,wrong_pool,bookmarks,streak_days,section_stats,updated_at)
           VALUES (?1,?2,?3,?4,?5,?6,?7,datetime('now'))
           ON CONFLICT(user_id) DO UPDATE SET
             total_answered=excluded.total_answered, total_correct=excluded.total_correct,
             wrong_pool=excluded.wrong_pool, bookmarks=excluded.bookmarks,
             streak_days=excluded.streak_days, section_stats=excluded.section_stats,
             updated_at=datetime('now')`
        ).bind(r.user.id, n(b.total_answered), n(b.total_correct), n(b.wrong_pool),
               n(b.bookmarks), n(b.streak_days),
               JSON.stringify(b.section_stats || {}).slice(0, 20000)).run();

        if (b.day && /^\d{4}-\d{2}-\d{2}$/.test(b.day)) {
          await env.DB.prepare(
            `INSERT INTO daily_activity (user_id,day,answered,correct) VALUES (?1,?2,?3,?4)
             ON CONFLICT(user_id,day) DO UPDATE SET
               answered=excluded.answered, correct=excluded.correct`
          ).bind(r.user.id, b.day, n(b.day_answered), n(b.day_correct)).run();
        }
        return json(req, env, { ok: true });
      }

      // ---- 5. 後台：帳號清單 ----
      if (path === '/api/admin/users') {
        const r = await currentUser(req, env);
        if (r.error) return json(req, env, { error: r.error }, r.status);
        if (!r.user.is_admin) return json(req, env, { error: 'not_admin' }, 403);
        const { results } = await env.DB.prepare(
          `SELECT u.id,u.email,u.name,u.avatar,u.is_admin,u.is_blocked,u.blocked_note,
                  u.created_at,u.last_seen_at,
                  COALESCE(s.total_answered,0) AS total_answered,
                  COALESCE(s.total_correct,0)  AS total_correct,
                  COALESCE(s.wrong_pool,0)     AS wrong_pool,
                  COALESCE(s.streak_days,0)    AS streak_days,
                  s.section_stats, s.updated_at
           FROM users u LEFT JOIN user_stats s ON s.user_id=u.id
           ORDER BY u.last_seen_at DESC NULLS LAST`
        ).all();
        return json(req, env, { users: results || [] });
      }

      // ---- 6. 後台：停用／解除 ----
      if (path === '/api/admin/block' && req.method === 'POST') {
        const r = await currentUser(req, env);
        if (r.error) return json(req, env, { error: r.error }, r.status);
        if (!r.user.is_admin) return json(req, env, { error: 'not_admin' }, 403);
        const b = await req.json().catch(() => ({}));
        if (!b.id) return json(req, env, { error: 'no_id' }, 400);
        if (b.id === r.user.id) return json(req, env, { error: 'cannot_block_self' }, 400);
        await env.DB.prepare('UPDATE users SET is_blocked=?1, blocked_note=?2 WHERE id=?3')
          .bind(b.blocked ? 1 : 0, b.blocked ? (b.note || null) : null, b.id).run();
        return json(req, env, { ok: true });
      }

      // ---- 7. 後台：設定／取消管理員 ----
      if (path === '/api/admin/role' && req.method === 'POST') {
        const r = await currentUser(req, env);
        if (r.error) return json(req, env, { error: r.error }, r.status);
        if (!r.user.is_admin) return json(req, env, { error: 'not_admin' }, 403);
        const b = await req.json().catch(() => ({}));
        if (!b.id) return json(req, env, { error: 'no_id' }, 400);
        if (b.id === r.user.id) return json(req, env, { error: 'cannot_change_self' }, 400);
        await env.DB.prepare('UPDATE users SET is_admin=?1 WHERE id=?2')
          .bind(b.admin ? 1 : 0, b.id).run();
        return json(req, env, { ok: true });
      }

      if (path === '/health') return json(req, env, { ok: true });
      return json(req, env, { error: 'not_found' }, 404);

    } catch (e) {
      return json(req, env, { error: 'server_error', detail: String(e && e.message || e) }, 500);
    }
  },
};
