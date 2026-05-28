const CACHE_NAME = 'roadsos-v3.2.0-b8e4c1d';
const STATIC_ASSETS = [
  '/',
  '/api/categories',
  '/api/firstaid',
  '/api/version',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return Promise.allSettled(STATIC_ASSETS.map(url => cache.add(url).catch(() => {})));
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // Live tracking: always network-only
  if (url.pathname.startsWith('/api/track') || url.pathname.startsWith('/track/')) {
    e.respondWith(fetch(e.request));
    return;
  }

  // Push subscription endpoints: always network-only
  if (url.pathname.startsWith('/api/push')) {
    e.respondWith(fetch(e.request));
    return;
  }

  // Incident reporting/upvoting: network, fall back to cache for GETs
  if (url.pathname.startsWith('/api/incidents')) {
    if (e.request.method !== 'GET') {
      e.respondWith(fetch(e.request));
    } else {
      e.respondWith(
        fetch(e.request).catch(() => caches.match(e.request))
      );
    }
    return;
  }

  // Search: network first, cache fallback
  if (url.pathname.startsWith('/api/search')) {
    e.respondWith(
      fetch(e.request).catch(() => caches.match(e.request))
    );
    return;
  }

  // Static / first-aid / version: cache first
  if (url.pathname.startsWith('/api/firstaid') ||
      url.pathname.startsWith('/api/version')  ||
      url.pathname.startsWith('/static/')       ||
      url.pathname === '/') {
    e.respondWith(
      caches.match(e.request).then(cached => {
        return cached || fetch(e.request).then(resp => {
          const clone = resp.clone();
          caches.open(CACHE_NAME).then(c => c.put(e.request, clone));
          return resp;
        });
      })
    );
    return;
  }

  // Default: network first, cache fallback + update
  e.respondWith(
    fetch(e.request)
      .then(resp => {
        const clone = resp.clone();
        caches.open(CACHE_NAME).then(c => c.put(e.request, clone));
        return resp;
      })
      .catch(() => caches.match(e.request))
  );
});

// ── Web Push ──────────────────────────────────────────────────────────────────

self.addEventListener('push', e => {
  let data = { title: 'ROADSOS Alert', body: 'A new incident was reported nearby.' };
  try { data = e.data.json(); } catch (_) {}

  const options = {
    body:    data.body  || 'Tap to view on map.',
    icon:    '/static/icons/icon-192.png',
    badge:   '/static/icons/badge-96.png',
    vibrate: [200, 100, 200],
    tag:     'roadsos-incident',
    renotify: true,
    data: {
      lat: data.lat,
      lon: data.lon,
      url: data.lat && data.lon
        ? `/?lat=${data.lat}&lon=${data.lon}`
        : '/',
    },
  };

  e.waitUntil(
    self.registration.showNotification(data.title || 'ROADSOS Alert', options)
  );
});

self.addEventListener('notificationclick', e => {
  e.notification.close();
  const target = (e.notification.data && e.notification.data.url) || '/';
  e.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(list => {
      for (const c of list) {
        if (c.url.includes(self.location.origin) && 'focus' in c) {
          c.navigate(target);
          return c.focus();
        }
      }
      if (clients.openWindow) return clients.openWindow(target);
    })
  );
});