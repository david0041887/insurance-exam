const CACHE = 'ins-exam-v34';
// 只預快取開站必要的小檔；題庫與解析改為第一次用到時才快取
const ASSETS = ['./', './index.html', './manifest.json', './icon.svg', './icon-192.png', './icon-512.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
  // 不在這裡 skipWaiting：由頁面端 applyUpdate() 發訊息觸發，才能在作答中延後切換
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ).then(() => self.clients.claim()));
});

self.addEventListener('message', e => {
  if (e.data === 'skip-waiting') self.skipWaiting();
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  // 只處理本站資源；跨網域（登入 API）一律放行，不得快取
  if (url.origin !== self.location.origin) return;
  const isHTML = req.mode === 'navigate' || req.destination === 'document' ||
                 url.pathname.endsWith('/') || url.pathname.endsWith('.html');
  const isAuth = /(?:config|auth)\.js$/.test(url.pathname) || url.pathname.endsWith('admin.html');
  const isQuestions = url.pathname.endsWith('questions.json') || url.pathname.endsWith('study.json') || /\/exp\/[a-z]+\.json$/.test(url.pathname) || url.pathname.endsWith('laws.json') || url.pathname.endsWith('law-refs.json');

  if (isHTML || isQuestions || isAuth) {
    e.respondWith(
      fetch(req).then(r => {
        const copy = r.clone();
        caches.open(CACHE).then(c => c.put(req, copy));
        return r;
      }).catch(() => caches.match(req).then(c => c || caches.match('./index.html')))
    );
    return;
  }
  e.respondWith(
    caches.match(req).then(cached => cached || fetch(req).then(r => {
      const copy = r.clone();
      caches.open(CACHE).then(c => c.put(req, copy));
      return r;
    }))
  );
});
