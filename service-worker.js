const CACHE_NAME = 'nemesis-shark-pro-v179-pwa-reliable';
const CORE_ASSETS = ['/', '/manifest.json', '/static/manifest.json', '/static/icons/icon-192.png', '/static/icons/icon-512.png'];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(CORE_ASSETS)).catch(() => null));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))));
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.pathname.startsWith('/api/')) return;
  event.respondWith(fetch(event.request).then((response) => {
    const copy = response.clone();
    if (response.ok && (url.origin === self.location.origin)) {
      caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy)).catch(() => null);
    }
    return response;
  }).catch(() => caches.match(event.request).then((cached) => cached || caches.match('/') || new Response('NeMeSiS SHARK PRO offline', {status: 200}))));
});

self.addEventListener('push', function(event) {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch(e) { data = {title:'NeMeSiS SHARK PRO', body:'Nueva alerta SHARK disponible'}; }
  const title = data.title || 'NeMeSiS SHARK PRO';
  const options = {
    body: data.body || 'Nueva señal real disponible.',
    icon: '/static/icons/icon-192.png',
    badge: '/static/icons/icon-192.png',
    data: { url: data.url || data.action_url || '/cliente/pro' },
    tag: data.tag || 'nemesis-shark-alert',
    renotify: false
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  const url = (event.notification && event.notification.data && event.notification.data.url) || '/cliente/pro';
  event.waitUntil(clients.openWindow(url));
});
