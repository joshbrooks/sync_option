importScripts('https://storage.googleapis.com/workbox-cdn/releases/7.0.0/workbox-sw.js');

// Check if Workbox loaded successfully
if (workbox) {
  console.log('Workbox is loaded');
} else {
  console.log('Workbox failed to load');
}

// Force development builds
workbox.setConfig({ debug: true });

// Cache name with version
const CACHE_NAME = 'sync-option-cache-v1';

// API routes to cache
const API_ROUTES = [
  '/api/options/groups',
  '/api/options/groups/*',
  '/api/options/relations'
];

// Register route for API endpoints
workbox.routing.registerRoute(
  ({ url }) => API_ROUTES.some(route => {
    // Convert route pattern to regex
    const pattern = new RegExp(route.replace('*', '.*'));
    return pattern.test(url.pathname);
  }),
  new workbox.strategies.StaleWhileRevalidate({
    cacheName: CACHE_NAME,
    plugins: [
      // Cache for 1 hour
      new workbox.expiration.ExpirationPlugin({
        maxAgeSeconds: 60 * 60,
      }),
      // Ensure we respect the cache headers from the server
      new workbox.cacheableResponse.CacheableResponsePlugin({
        statuses: [0, 200],
        headers: {
          'X-Is-Cacheable': 'true',
        },
      }),
      // Add cache header to track sync_id
      {
        cachedResponseWillBeUsed: async ({ cachedResponse, request }) => {
          if (!cachedResponse) return null;
          
          try {
            const data = await cachedResponse.clone().json();
            const syncId = Array.isArray(data) 
              ? Math.max(...data.map(item => item.sync_id || 0))
              : (data.sync_id || 0);
            
            // Add sync_id to response headers for debugging
            const headers = new Headers(cachedResponse.headers);
            headers.set('X-Sync-Id', syncId);
            
            return new Response(cachedResponse.body, {
              status: cachedResponse.status,
              statusText: cachedResponse.statusText,
              headers
            });
          } catch (error) {
            console.error('Error processing cached response:', error);
            return cachedResponse;
          }
        }
      }
    ]
  })
); 