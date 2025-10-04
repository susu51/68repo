// Kuryecini Service Worker
// Handles caching, offline functionality, and background sync

const CACHE_NAME = 'kuryecini-v2.0.0-' + Date.now();
const OFFLINE_URL = '/offline.html';

// Files to cache for offline functionality
const STATIC_CACHE_FILES = [
  '/',
  '/offline.html',
  '/static/css/main.css',
  '/static/js/main.js',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png'
];

// API endpoints to cache with network-first strategy
const API_CACHE_PATTERNS = [
  /\/api\/businesses$/,
  /\/api\/products/,
  /\/api\/healthz$/
];

// Install event - cache static resources
self.addEventListener('install', (event) => {
  console.log('🔧 Service Worker: Install event');
  
  event.waitUntil(
    (async () => {
      try {
        const cache = await caches.open(CACHE_NAME);
        
        // Cache essential files
        await cache.addAll(STATIC_CACHE_FILES);
        
        console.log('✅ Service Worker: Static files cached');
        
        // Skip waiting to activate immediately
        self.skipWaiting();
      } catch (error) {
        console.error('❌ Service Worker: Install failed', error);
      }
    })()
  );
});

// Activate event - cleanup old caches
self.addEventListener('activate', (event) => {
  console.log('🚀 Service Worker: Activate event');
  
  event.waitUntil(
    (async () => {
      try {
        // Delete old caches
        const cacheNames = await caches.keys();
        await Promise.all(
          cacheNames
            .filter(name => name !== CACHE_NAME)
            .map(name => {
              console.log('🗑️ Service Worker: Deleting old cache:', name);
              return caches.delete(name);
            })
        );
        
        // Take control of all pages
        await self.clients.claim();
        
        console.log('✅ Service Worker: Activated and controlling pages');
      } catch (error) {
        console.error('❌ Service Worker: Activation failed', error);
      }
    })()
  );
});

// Fetch event - handle all network requests
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip chrome-extension and other protocols
  if (!url.protocol.startsWith('http')) {
    return;
  }
  
  event.respondWith(handleFetch(request));
});

async function handleFetch(request) {
  const url = new URL(request.url);
  
  try {
    // Strategy 1: API requests - Network first, cache fallback
    if (isApiRequest(url)) {
      return await networkFirst(request);
    }
    
    // Strategy 2: Static assets - Cache first, network fallback  
    if (isStaticAsset(url)) {
      return await cacheFirst(request);
    }
    
    // Strategy 3: Navigation requests - Network first with offline page
    if (request.mode === 'navigate') {
      return await navigationHandler(request);
    }
    
    // Strategy 4: Other requests - Network first
    return await networkFirst(request);
    
  } catch (error) {
    console.error('❌ Service Worker: Fetch failed', error);
    return new Response('Network Error', { status: 500 });
  }
}

// Check if request is for API
function isApiRequest(url) {
  return url.pathname.startsWith('/api/') || 
         API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname));
}

// Check if request is for static asset
function isStaticAsset(url) {
  return url.pathname.startsWith('/static/') ||
         url.pathname.startsWith('/icons/') ||
         url.pathname.includes('.css') ||
         url.pathname.includes('.js') ||
         url.pathname.includes('.png') ||
         url.pathname.includes('.jpg') ||
         url.pathname.includes('.svg');
}

// Network first strategy (for API and dynamic content)
async function networkFirst(request, cacheName = CACHE_NAME) {
  try {
    // Try network first
    const networkResponse = await fetch(request);
    
    // Cache successful responses
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
    
  } catch (error) {
    console.log('🌐 Service Worker: Network failed, trying cache for:', request.url);
    
    // Fall back to cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // If API request and no cache, return error JSON
    if (isApiRequest(new URL(request.url))) {
      return new Response(
        JSON.stringify({ 
          error: 'Bağlantı hatası', 
          message: 'İnternet bağlantınızı kontrol edin',
          offline: true 
        }), 
        { 
          status: 503,
          headers: { 'Content-Type': 'application/json' }
        }
      );
    }
    
    throw error;
  }
}

// Cache first strategy (for static assets)
async function cacheFirst(request, cacheName = CACHE_NAME) {
  // Try cache first
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }
  
  // Fall back to network
  try {
    const networkResponse = await fetch(request);
    
    // Cache the response
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
    
  } catch (error) {
    console.error('❌ Service Worker: Cache and network both failed for:', request.url);
    throw error;
  }
}

// Navigation handler (for page requests)
async function navigationHandler(request) {
  try {
    // Try network first
    return await fetch(request);
    
  } catch (error) {
    console.log('🌐 Service Worker: Navigation offline, serving offline page');
    
    // Serve offline page
    const cache = await caches.open(CACHE_NAME);
    const offlineResponse = await cache.match(OFFLINE_URL);
    
    if (offlineResponse) {
      return offlineResponse;
    }
    
    // Fallback offline page
    return new Response(`
      <!DOCTYPE html>
      <html lang="tr">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Kuryecini - Çevrimdışı</title>
        <style>
          body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            display: flex; 
            flex-direction: column;
            justify-content: center; 
            align-items: center; 
            min-height: 100vh; 
            margin: 0;
            background: linear-gradient(135deg, #ea580c 0%, #dc2626 100%);
            color: white;
            text-align: center;
            padding: 20px;
          }
          .offline-icon { font-size: 4rem; margin-bottom: 1rem; }
          .offline-title { font-size: 2rem; margin-bottom: 1rem; font-weight: bold; }
          .offline-message { font-size: 1.1rem; margin-bottom: 2rem; opacity: 0.9; }
          .retry-button { 
            background: white; 
            color: #ea580c; 
            padding: 12px 24px; 
            border: none; 
            border-radius: 8px; 
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
          }
          .retry-button:hover { transform: translateY(-2px); }
        </style>
      </head>
      <body>
        <div class="offline-icon">📱</div>
        <h1 class="offline-title">Kuryecini</h1>
        <p class="offline-message">
          İnternet bağlantınız kesildi.<br>
          Bağlantı sağlandığında otomatik olarak yenilenecektir.
        </p>
        <button class="retry-button" onclick="window.location.reload()">
          🔄 Tekrar Dene
        </button>
        
        <script>
          // Auto-retry when online
          window.addEventListener('online', () => {
            window.location.reload();
          });
        </script>
      </body>
      </html>
    `, {
      headers: { 'Content-Type': 'text/html' }
    });
  }
}

// Background sync for failed requests
self.addEventListener('sync', (event) => {
  console.log('🔄 Service Worker: Background sync:', event.tag);
  
  if (event.tag === 'cart-sync') {
    event.waitUntil(syncCart());
  } else if (event.tag === 'order-sync') {
    event.waitUntil(syncOrders());
  }
});

async function syncCart() {
  try {
    // Sync cart data when online
    console.log('🛒 Service Worker: Syncing cart data');
    // Implementation would sync pending cart changes
  } catch (error) {
    console.error('❌ Service Worker: Cart sync failed', error);
  }
}

async function syncOrders() {
  try {
    // Sync pending orders when online
    console.log('📦 Service Worker: Syncing order data');
    // Implementation would sync pending orders
  } catch (error) {
    console.error('❌ Service Worker: Order sync failed', error);
  }
}

// Push notification handler
self.addEventListener('push', (event) => {
  console.log('🔔 Service Worker: Push received');
  
  const options = {
    body: 'Yeni bir bildirimin var!',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: '1'
    },
    actions: [
      {
        action: 'explore',
        title: 'Aç',
        icon: '/icons/checkmark.png'
      },
      {
        action: 'close',
        title: 'Kapat',
        icon: '/icons/xmark.png'
      }
    ]
  };
  
  if (event.data) {
    try {
      const data = event.data.json();
      options.body = data.message || options.body;
      options.title = data.title || 'Kuryecini';
    } catch (error) {
      console.error('❌ Service Worker: Invalid push data', error);
    }
  }
  
  event.waitUntil(
    self.registration.showNotification('Kuryecini', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  console.log('🔔 Service Worker: Notification clicked');
  
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(clients.openWindow('/'));
  } else if (event.action === 'close') {
    // Just close notification
  } else {
    // Default action - open app
    event.waitUntil(clients.openWindow('/'));
  }
});

// Message handler for communication with main thread
self.addEventListener('message', (event) => {
  console.log('💬 Service Worker: Message received', event.data);
  
  if (event.data && event.data.type) {
    switch (event.data.type) {
      case 'SKIP_WAITING':
        self.skipWaiting();
        break;
        
      case 'GET_VERSION':
        event.ports[0].postMessage({ version: CACHE_NAME });
        break;
        
      case 'CACHE_CART':
        // Cache cart data for offline access
        cacheCartData(event.data.cartData);
        break;
        
      default:
        console.log('❓ Service Worker: Unknown message type:', event.data.type);
    }
  }
});

// Cache cart data for offline access
async function cacheCartData(cartData) {
  try {
    const cache = await caches.open(CACHE_NAME + '-data');
    await cache.put(
      new Request('/offline-cart'),
      new Response(JSON.stringify(cartData), {
        headers: { 'Content-Type': 'application/json' }
      })
    );
    console.log('✅ Service Worker: Cart data cached');
  } catch (error) {
    console.error('❌ Service Worker: Failed to cache cart data', error);
  }
}

console.log('🚀 Kuryecini Service Worker loaded successfully');