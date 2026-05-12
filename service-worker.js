
const CACHE_NAME = "nemesis-shark-pro-v148";
const CORE_ASSETS = [
  "/",
  "/static/manifest.json"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(CORE_ASSETS)).catch(() => null)
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))))
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request).then((cached) => cached || caches.match("/")))
  );
});

// V164_PUSH_NOTIFICATION_FOUNDATION
self.addEventListener('push', function(event) {
  var data = {};
  try { data = event.data ? event.data.json() : {}; } catch(e) { data = {title:'NeMeSiS SHARK PRO', body:'Nueva alerta SHARK disponible'}; }
  var title = data.title || 'NeMeSiS SHARK PRO';
  var options = { body: data.body || 'Nueva señal real disponible.', icon: '/static/manifest-icon-192.png', badge: '/static/manifest-icon-192.png', data: { url: data.url || data.action_url || '/cliente/pro' } };
  event.waitUntil(self.registration.showNotification(title, options));
});
self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  var url = (event.notification && event.notification.data && event.notification.data.url) || '/cliente/pro';
  event.waitUntil(clients.openWindow(url));
});
