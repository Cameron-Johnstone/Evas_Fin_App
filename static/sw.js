const CACHE_NAME = 'finance-tracker-v1';
const urlsToCache = [
    '/',
    '/static/styles.css',
    'https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css',
    'https://cdn.jsdelivr.net/npm/chart.js'
];

// Install service worker
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
});

// Cache and network race
self.addEventListener('fetch', event => {
    event.respondWith(
        Promise.race([
            fetch(event.request).then(response => {
                // Clone the response because it can only be consumed once
                const responseClone = response.clone();
                
                // Update cache with new response
                caches.open(CACHE_NAME).then(cache => {
                    cache.put(event.request, responseClone);
                });

                return response;
            }),
            new Promise((resolve) => {
                setTimeout(resolve, 1000, caches.match(event.request));
            })
        ]).catch(() => {
            // If both fail, try to get from cache
            return caches.match(event.request);
        })
    );
});

// Clean up old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Handle background sync for offline data
self.addEventListener('sync', event => {
    if (event.tag === 'sync-finances') {
        event.waitUntil(syncFinances());
    }
});

// Function to sync offline data
async function syncFinances() {
    try {
        const offlineData = await getOfflineData();
        for (const item of offlineData) {
            await sendToServer(item);
        }
        await clearOfflineData();
    } catch (error) {
        console.error('Sync failed:', error);
    }
}