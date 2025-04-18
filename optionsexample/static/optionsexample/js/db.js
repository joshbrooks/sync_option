// Shared IndexedDB setup
const DB_NAME = 'optionsDB';
const DB_VERSION = 1;
const CACHE_STORE = 'sync_option_cache';
let db;

// Initialize IndexedDB with cache store
function initDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onerror = () => {
            console.error('Error opening database');
            reject(request.error);
        };

        request.onsuccess = () => {
            db = request.result;
            resolve(db);
        };

        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            
            // Create cache store if it doesn't exist
            if (!db.objectStoreNames.contains(CACHE_STORE)) {
                const cacheStore = db.createObjectStore(CACHE_STORE, { keyPath: 'url' });
                cacheStore.createIndex('etag', 'etag', { unique: false });
            }
        };
    });
}

// Get cached data for a URL
async function getCachedData(url) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([CACHE_STORE], 'readonly');
        const store = transaction.objectStore(CACHE_STORE);
        const request = store.get(url);

        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

// Update cache with new data
async function updateCache(url, etag, content) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([CACHE_STORE], 'readwrite');
        const store = transaction.objectStore(CACHE_STORE);
        const request = store.put({ url, etag, content });

        console.log('Updating cache', url, etag, content)
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
    });
}

// Sync data from manifest
async function syncData() {
    try {
        const manifestResponse = await fetch('/api/sync-option/manifest', {cache: "no-store"});
        const manifest = await manifestResponse.json();
        console.table(manifest)

        for (const entry of manifest) {
            const cached = await getCachedData(entry.url);
            if (cached && cached.etag === entry.etag) {
                continue;
            }
            // If no cache or etag different, fetch new data
            debugger
            const response = await fetch(entry.url, {cache: "no-store"});
            const content = await response.json();
            await updateCache(entry.url, entry.etag, content);
        }
    } catch (error) {
        console.error('Error syncing data:', error);
        throw error;
    }
}

// Get data for a URL (from cache if available, otherwise fetch)
async function getData(url) {
    try {
        const cached = await getCachedData(url);
        if (cached) {
            return cached.content;
        }
        
        // If not in cache, trigger a sync and try again
        await syncData();
        const newCached = await getCachedData(url);
        return newCached ? newCached.content : null;
    } catch (error) {
        console.error('Error getting data:', error);
        throw error;
    }
}

// Export the shared functions and constants
window.DB = {
    initDB,
    syncData,
    getData,
    getCachedData,
    updateCache,
    CACHE_STORE
}; 