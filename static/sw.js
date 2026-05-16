const CACHE_NAME  = 'goldshop-monitor-v1';
const OFFLINE_URL = '/mobile/';

const PRECACHE_ASSETS = [
    '/mobile/',
    '/static/css/mobile.css',
    '/static/icons/icon-192.png',
    '/static/icons/icon-512.png',
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE_ASSETS))
    );
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
        )
    );
    self.clients.claim();
});

self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);
    if (event.request.method !== 'GET' || url.origin !== location.origin) return;

    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.match(event.request).then(cached =>
                cached || fetch(event.request).then(response => {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(c => c.put(event.request, clone));
                    return response;
                })
            )
        );
        return;
    }

    if (url.pathname.startsWith('/mobile/')) {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(c => c.put(event.request, clone));
                    return response;
                })
                .catch(() =>
                    caches.match(event.request).then(c => c || caches.match(OFFLINE_URL))
                )
        );
    }
});