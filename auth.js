/* 登入閘門 + 進度同步 — 保險經紀人考古題練習
   後端：Cloudflare Worker + D1，Google OAuth，JWT 存 localStorage
   注意：這是介面閘門。questions.json / explanations.json 仍是公開檔案。 */
(function () {
  'use strict';

  var API = window.AUTH_API || '';
  var LS_TOKEN = 'ins_auth_token_v1';
  var PROFILE = null;
  window.AUTH_USER = null;

  function el(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function getToken() { try { return localStorage.getItem(LS_TOKEN) || ''; } catch (e) { return ''; } }
  function setToken(t) { try { t ? localStorage.setItem(LS_TOKEN, t) : localStorage.removeItem(LS_TOKEN); } catch (e) {} }

  function api(path, opts) {
    opts = opts || {};
    var h = opts.headers || {};
    var t = getToken();
    if (t) h['Authorization'] = 'Bearer ' + t;
    if (opts.body) h['Content-Type'] = 'application/json';
    return fetch(API + path, { method: opts.method || 'GET', headers: h, body: opts.body })
      .then(function (r) { return r.json().then(function (j) { return { status: r.status, data: j }; }); });
  }
  window.authApi = api;

  // ── 閘門畫面 ───────────────────────────────────────────
  var GOOGLE_SVG =
    '<svg viewBox="0 0 18 18" width="17" height="17" aria-hidden="true">'
    + '<path fill="#4285F4" d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.92c1.7-1.57 2.68-3.88 2.68-6.62z"/>'
    + '<path fill="#34A853" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.8.54-1.84.86-3.04.86-2.34 0-4.32-1.58-5.03-3.7H.96v2.33A9 9 0 0 0 9 18z"/>'
    + '<path fill="#FBBC05" d="M3.97 10.72a5.4 5.4 0 0 1 0-3.44V4.95H.96a9 9 0 0 0 0 8.1l3.01-2.33z"/>'
    + '<path fill="#EA4335" d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.58C13.46.89 11.43 0 9 0A9 9 0 0 0 .96 4.95l3.01 2.33C4.68 5.16 6.66 3.58 9 3.58z"/>'
    + '</svg>';

  function gateHTML(state, msg) {
    if (state === 'config') {
      return '<div class="gate-card"><div class="gate-logo">&#128203;</div><h1>尚未設定登入</h1>'
        + '<p>請在 <code>config.js</code> 填入 Worker 網址，並完成 Google OAuth 設定。</p></div>';
    }
    if (state === 'blocked') {
      return '<div class="gate-card"><div class="gate-logo">&#128274;</div><h1>帳號已停用</h1>'
        + '<p>這個帳號目前無法使用本站。'
        + (msg ? '<br><span class="gate-note">' + esc(msg) + '</span>' : '')
        + '</p><button class="gate-btn ghost" id="gate-signout">登出</button></div>';
    }
    if (state === 'loading') {
      return '<div class="gate-card"><div class="gate-logo">&#8987;</div><h1>登入中…</h1></div>';
    }
    return '<div class="gate-card"><div class="gate-logo">&#128203;</div>'
      + '<h1>保險經紀人 考古題</h1>'
      + '<p class="gate-sub">民國 99–115 年考古題 4,247 題，附逐題解析</p>'
      + '<button class="gate-btn" id="gate-google">' + GOOGLE_SVG + '<span>使用 Google 登入</span></button>'
      + (msg ? '<p class="gate-err">' + esc(msg) + '</p>' : '')
      + '<p class="gate-note">登入後進度會跨裝置同步</p></div>';
  }

  function renderGate(state, msg) {
    var g = el('auth-gate');
    if (!g) return;
    g.innerHTML = gateHTML(state, msg);
    g.style.display = 'flex';
    document.body.classList.add('gated');
    var b = el('gate-google'); if (b) b.onclick = signIn;
    var o = el('gate-signout'); if (o) o.onclick = signOut;
  }
  function hideGate() {
    var g = el('auth-gate'); if (g) g.style.display = 'none';
    document.body.classList.remove('gated');
  }

  function signIn() { location.href = API + '/auth/start'; }
  function signOut() { setToken(''); location.href = location.pathname; }
  window.signOut = signOut;

  // ── 使用者晶片 ─────────────────────────────────────────
  function renderUserChip() {
    var host = document.querySelector('.header-stats');
    if (!host || !PROFILE) return;
    var old = el('user-chip'); if (old) old.remove();
    var name = PROFILE.name || PROFILE.email || '使用者';
    var d = document.createElement('div');
    d.className = 'user-chip'; d.id = 'user-chip';
    d.innerHTML =
      (PROFILE.avatar
        ? '<img src="' + esc(PROFILE.avatar) + '" alt="" referrerpolicy="no-referrer">'
        : '<span class="user-ini">' + esc(name.slice(0, 1)) + '</span>')
      + '<span class="user-name">' + esc(name) + '</span>'
      + (PROFILE.is_admin ? '<a class="user-admin" href="admin.html">後台</a>' : '')
      + '<button class="user-out" title="登出">登出</button>';
    d.querySelector('.user-out').onclick = signOut;
    host.insertBefore(d, host.firstChild);
  }

  // ── 進度同步 ───────────────────────────────────────────
  function todayStr() {
    var t = new Date();
    return t.getFullYear() + '-' + String(t.getMonth() + 1).padStart(2, '0')
      + '-' + String(t.getDate()).padStart(2, '0');
  }

  function collectStats() {
    var stats = loadD(LS_STATS), answered = 0, correct = 0;
    for (var k in stats) { answered += (stats[k].answered || 0); correct += (stats[k].correct || 0); }
    // 各科練習狀況：總題數 / 練過 / 精熟(3星) / 錯題池 / 星數合計
    var sec = {};
    try {
      var stars = loadD(LS_STARS), wrong = loadD(LS_WRONG);
      (window.ALL_QUESTIONS || []).forEach(function (q, i) {
        var s = sec[q.section] || (sec[q.section] = { total: 0, seen: 0, mastered: 0, wrong: 0, stars: 0 });
        var k = window.qk ? window.qk(i) : i;   // 內容雜湊鍵
        s.total++;
        if (stars[k] != null) {
          s.seen++; s.stars += stars[k];
          if (stars[k] >= 3) s.mastered++;
        }
        if (wrong[k]) s.wrong++;
      });
    } catch (e) {}
    var day = todayStr();
    var d = stats[day] || { answered: 0, correct: 0 };
    return {
      total_answered: answered, total_correct: correct,
      wrong_pool: Object.keys(loadD(LS_WRONG)).length,
      bookmarks: Object.keys(loadD(LS_BOOKMARKS)).length,
      streak_days: (typeof getStreakDays === 'function' ? getStreakDays() : 0),
      section_stats: sec,
      day: day, day_answered: d.answered || 0, day_correct: d.correct || 0
    };
  }

  function pushStats() {
    if (!getToken()) return Promise.resolve();
    return api('/api/stats', { method: 'POST', body: JSON.stringify(collectStats()) })
      .then(function (r) {
        if (r.status === 403 && r.data && r.data.error === 'blocked') {
          renderGate('blocked', r.data.note);
        }
      })
      .catch(function () {});
  }
  window.pushStats = pushStats;

  var timer = null;
  function scheduleSync() { clearTimeout(timer); timer = setTimeout(pushStats, 4000); }

  function hookStats() {
    if (typeof window.recordAnswerStat !== 'function') return;
    var orig = window.recordAnswerStat;
    window.recordAnswerStat = function (c) { orig(c); scheduleSync(); };
    window.addEventListener('beforeunload', function () { try { pushStats(); } catch (e) {} });
  }

  // ── 啟動 ───────────────────────────────────────────────
  function boot() {
    if (!API) { renderGate('config'); return; }

    // 從網址 fragment 取回登入後的 token
    if (location.hash) {
      var m = location.hash.match(/token=([^&]+)/);
      if (m) {
        setToken(decodeURIComponent(m[1]));
        history.replaceState(null, '', location.pathname + location.search);
      } else if (location.hash.indexOf('err=') >= 0) {
        var e = location.hash.match(/err=([^&]+)/);
        history.replaceState(null, '', location.pathname + location.search);
        renderGate('signin', '登入失敗：' + (e ? e[1] : 'unknown'));
        return;
      }
    }

    if (!getToken()) { renderGate('signin'); return; }

    renderGate('loading');
    api('/api/me').then(function (r) {
      if (r.status === 403 && r.data.error === 'blocked') { renderGate('blocked', r.data.note); return; }
      if (r.status !== 200 || !r.data.user) { setToken(''); renderGate('signin'); return; }
      PROFILE = r.data.user;
      window.AUTH_USER = r.data.user;
      hideGate();
      renderUserChip();
      hookStats();
      pushStats();
    }).catch(function () {
      renderGate('signin', '無法連線到登入服務，請稍後再試');
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
