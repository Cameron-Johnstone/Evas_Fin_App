
/* static/sw.js */
const CACHE_NAME = 'finance-tracker-v0';
const urlsToCache = [
    '/',
    '/static/styles.css',
    'https://cdn.jsdelivr.net/npm/tailwindcss@1.2.19/dist/tailwind.min.css'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => response || fetch(event.request))
    );
});

/* static/manifest.json */
{
    "name": "Performance Finance Tracker",
    "short_name": "Finance",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#ffffff",
    "theme_color": "#3CAF50",
    "icons": [
     
/* static/sw.js */
const CACHE_NAME = 'finance-tracker-v0';
const urlsToCache = [
    '/',
    '/static/styles.css',
    'https://cdn.jsdelivr.net/npm/tailwindcss@1.2.19/dist/tailwind.min.css'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => response || fetch(event.request))
    );
});
