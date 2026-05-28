const CACHE_NAME = 'roadsos-v3.1.0-a7f3b2c';
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

  if (url.pathname.startsWith('/api/track') || url.pathname.startsWith('/track/')) {
    e.respondWith(fetch(e.request));
    return;
  }

  if (url.pathname.startsWith('/api/search') || url.pathname.startsWith('/api/incidents')) {
    e.respondWith(
      fetch(e.request)
        .catch(() => caches.match(e.request))
    );
    return;
  }

  if (url.pathname.startsWith('/api/firstaid') ||
      url.pathname.startsWith('/api/version') ||
      url.pathname.startsWith('/static/') ||
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