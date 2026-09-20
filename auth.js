/* 登入閘門 + 進度同步 — 保險經紀人考古題練習
   靜態站的介面閘門：未登入不顯示任何練習介面。
   注意：questions.json / explanations.json 仍是公開檔案，這層擋的是一般使用者。 */
(function () {
  'use strict';

  var SB = null;
  var PROFILE = null;
  window.AUTH_USER = null;

  // ── 小工具 ─────────────────────────────────────────────
  function el(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
  function show(id, on) { var e = el(id); if (e) e.style.display = on ? '' : 'none'; }

  function gateHTML(state, msg) {
    if (state === 'config') {
      return '<div class="gate-card"><div class="gate-logo">&#128203;</div>'
        + '<h1>尚未設定登入</h1>'
        + '<p>請先在 <code>config.js</code> 填入 Supabase 的 Project URL 與 anon key，'
        + '並於 Supabase 後台啟用 Google 登入。</p></div>';
    }
    if (state === 'blocked') {
      return '<div class="gate-card"><div class="gate-logo">&#128274;</div>'
        + '<h1>帳號已停用</h1>'
        + '<p>這個帳號目前無法使用本站。' + (msg ? '<br><span class="gate-note">' + esc(msg) + '</span>' : '')
        + '</p><button class="gate-btn ghost" id="gate-signout">登出</button></div>';
    }
    if (state === 'loading') {
      return '<div class="gate-card"><div class="gate-logo">&#8987;</div><h1>登入中…</h1></div>';
    }
    return '<div class="gate-card"><div class="gate-logo">&#128203;</div>'
      + '<h1>保險經紀人 考古題</h1>'
      + '<p class="gate-sub">民國 99–115 年考古題 4,247 題，附逐題解析</p>'
      + '<button class="gate-btn" id="gate-google">'
      + '<svg viewBox="0 0 18 18" width="17" height="17" aria-hidden="true">'
      + '<path fill="#4285F4" d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.92c1.7-1.57 2.68-3.88 2.68-6.62z"/>'
      + '<path fill="#34A853" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.8.54-1.84.86-3.04.86-2.34 0-4.32-1.58-5.03-3.7H.96v2.33A9 9 0 0 0 9 18z"/>'
      + '<path fill="#FBBC05" d="M3.97 10.72a5.4 5.4 0 0 1 0-3.44V4.95H.96a9 9 0 0 0 0 8.1l3.01-2.33z"/>'
      + '<path fill="#EA4335" d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.58C13.46.89 11.43 0 9 0A9 9 0 0 0 .96 4.95l3.01 2.33C4.68 5.16 6.66 3.58 9 3.58z"/>'
      + '</svg><span>使用 Google 登入</span></button>'
      + (msg ? '<p class="gate-err">' + esc(msg) + '</p>' : '')
      + '<p class="gate-note">登入後進度會跨裝置同步</p></div>';
  }

  function renderGate(state, msg) {
    var g = el('auth-gate');
    if (!g) return;
    g.innerHTML = gateHTML(state, msg);
    g.style.display = 'flex';
    document.body.classList.add('gated');
    var b = el('gate-google');
    if (b) b.onclick = signIn;
    var so = el('gate-signout');
    if (so) so.onclick = signOut;
  }

  function hideGate() {
    var g = el('auth-gate');
    if (g) g.style.display = 'none';
    document.body.classList.remove('gated');
  }

  // ── 登入 / 登出 ────────────────────────────────────────
  function signIn() {
    var url = location.origin + location.pathname;
    SB.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: url }
    }).then(function (r) {
      if (r.error) renderGate('signin', r.error.message);
    });
  }

  function signOut() {
    SB.auth.signOut().then(function () { location.reload(); });
  }
  window.signOut = signOut;

  // ── 使用者晶片 ─────────────────────────────────────────
  function renderUserChip() {
    var host = document.querySelector('.header-stats');
    if (!host || !PROFILE) return;
    var old = el('user-chip');
    if (old) old.remove();
    var d = document.createElement('div');
    d.className = 'user-chip';
    d.id = 'user-chip';
    var name = PROFILE.full_name || PROFILE.email || '使用者';
    d.innerHTML =
      (PROFILE.avatar_url
        ? '<img src="' + esc(PROFILE.avatar_url) + '" alt="" referrerpolicy="no-referrer">'
        : '<span class="user-ini">' + esc(name.slice(0, 1)) + '</span>')
      + '<span class="user-name">' + esc(name) + '</span>'
      + (PROFILE.is_admin ? '<a class="user-admin" href="admin.html">後台</a>' : '')
      + '<button class="user-out" title="登出">登出</button>';
    d.querySelector('.user-out').onclick = signOut;
    host.insertBefore(d, host.firstChild);
  }

  // ── 進度同步 ───────────────────────────────────────────
  function collectStats() {
    var stats = loadD(LS_STATS);
    var answered = 0, correct = 0;
    for (var k in stats) {
      answered += (stats[k].answered || 0);
      correct += (stats[k].correct || 0);
    }
    var sec = {};
    try {
      var stars = loadD(LS_STARS);
      (window.ALL_QUESTIONS || []).forEach(function (q, i) {
        if (stars[i] == null) return;
        if (!sec[q.section]) sec[q.section] = { seen: 0, stars: 0 };
        sec[q.section].seen++;
        sec[q.section].stars += stars[i];
      });
    } catch (e) {}
    return {
      total_answered: answered,
      total_correct: correct,
      wrong_pool: Object.keys(loadD(LS_WRONG)).length,
      bookmarks: Object.keys(loadD(LS_BOOKMARKS)).length,
      streak_days: (typeof getStreakDays === 'function' ? getStreakDays() : 0),
      section_stats: sec,
      updated_at: new Date().toISOString()
    };
  }

  function pushStats() {
    if (!SB || !window.AUTH_USER) return Promise.resolve();
    var s = collectStats();
    s.user_id = window.AUTH_USER.id;
    var today = new Date();
    var day = today.getFullYear() + '-'
      + String(today.getMonth() + 1).padStart(2, '0') + '-'
      + String(today.getDate()).padStart(2, '0');
    var d = loadD(LS_STATS)[day] || { answered: 0, correct: 0 };
    return Promise.all([
      SB.from('user_stats').upsert(s, { onConflict: 'user_id' }),
      SB.from('daily_activity').upsert({
        user_id: window.AUTH_USER.id, day: day,
        answered: d.answered || 0, correct: d.correct || 0
      }, { onConflict: 'user_id,day' })
    ]).catch(function () {});
  }
  window.pushStats = pushStats;

  var syncTimer = null;
  function scheduleSync() {
    clearTimeout(syncTimer);
    syncTimer = setTimeout(pushStats, 4000);
  }

  // 掛在既有的計分函式上，不改動原邏輯
  function hookStats() {
    if (typeof window.recordAnswerStat !== 'function') return;
    var orig = window.recordAnswerStat;
    window.recordAnswerStat = function (correct) {
      orig(correct);
      scheduleSync();
    };
    window.addEventListener('beforeunload', function () {
      try { pushStats(); } catch (e) {}
    });
  }

  // ── 啟動 ───────────────────────────────────────────────
  function boot() {
    if (!window.SUPABASE_URL || !window.SUPABASE_ANON_KEY) {
      renderGate('config');
      return;
    }
    SB = window.supabase.createClient(window.SUPABASE_URL, window.SUPABASE_ANON_KEY, {
      auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true }
    });
    window.SB = SB;

    renderGate('loading');

    SB.auth.getSession().then(function (r) {
      var sess = r.data && r.data.session;
      if (!sess) { renderGate('signin'); return; }
      onSignedIn(sess.user);
    });

    SB.auth.onAuthStateChange(function (evt, sess) {
      if (evt === 'SIGNED_OUT') { renderGate('signin'); return; }
      if (sess && sess.user && (!window.AUTH_USER || window.AUTH_USER.id !== sess.user.id)) {
        onSignedIn(sess.user);
      }
    });
  }

  function onSignedIn(user) {
    window.AUTH_USER = user;
    SB.from('profiles').select('*').eq('id', user.id).maybeSingle()
      .then(function (r) {
        PROFILE = r.data || {
          id: user.id, email: user.email,
          full_name: (user.user_metadata || {}).full_name,
          avatar_url: (user.user_metadata || {}).avatar_url,
          is_admin: false, is_blocked: false
        };
        if (PROFILE.is_blocked) { renderGate('blocked', PROFILE.blocked_note); return; }
        hideGate();
        renderUserChip();
        hookStats();
        SB.rpc('touch_last_seen').then(function () {}, function () {});
        pushStats();
      }, function () {
        // 讀不到 profile（例如網路問題）就先放行，不擋住練習
        hideGate();
        hookStats();
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else { boot(); }
})();
