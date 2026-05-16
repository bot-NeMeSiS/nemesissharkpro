// NeMeSiS SHARK PRO - Safe PWA Service Worker Fix
// Version: V323_REAL_PWA_FIX
const CACHE_NAME = 'nemesis-shark-pro-v323-pwa-fix';
const ASSET_CACHE = [
  '/',
  '/manifest.json'
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSET_CACHE).catch(() => null))
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
    )).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Do not cache dynamic/API/auth/admin calls.
  if (
    req.method !== 'GET' ||
    url.pathname.startsWith('/api/') ||
    url.pathname.includes('login') ||
    url.pathname.includes('logout') ||
    url.pathname.startsWith('/admin') ||
    url.pathname.startsWith('/telegram') ||
    url.pathname.startsWith('/webhook')
  ) {
    return;
  }

  // Static assets: cache first with network fallback.
  if (url.pathname.startsWith('/static/') || url.pathname === '/manifest.json' || url.pathname === '/service-worker.js') {
    event.respondWith(
      caches.match(req).then((cached) => cached || fetch(req).then((res) => {
        const copy = res.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(req, copy)).catch(() => null);
        return res;
      }).catch(() => cached))
    );
    return;
  }

  // Pages: network first, no hard failure if offline.
  event.respondWith(
    fetch(req).catch(() => caches.match(req).then((cached) => cached || caches.match('/')))
  );
});
