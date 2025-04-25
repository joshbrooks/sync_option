// Database configuration
const DB_NAME = 'optionsDB';
const DB_VERSION = 1;
const CACHE_STORE = 'sync_option_cache';

// Database instance
let db;

// Initialize IndexedDB with cache store
async function initDB() {
    try {
        db = await idb.openDB(DB_NAME, DB_VERSION, {
            upgrade(db) {
                // Create cache store if it doesn't exist
                if (!db.objectStoreNames.contains(CACHE_STORE)) {
                    const store = db.createObjectStore(CACHE_STORE, { keyPath: 'url' });
                    store.createIndex('etag', 'etag', { unique: false });
                }
            },
        });
        return db;
    } catch (error) {
        console.error('Error opening database:', error);
        throw error;
    }
}

// Get cached data for a URL
async function getCachedData(url) {
    try {
        return await db.get(CACHE_STORE, url);
    } catch (error) {
        console.error('Error getting cached data:', error);
        throw error;
    }
}

// Update cache with new data
async function updateCache(url, etag, content) {
    try {
        await db.put(CACHE_STORE, { url, etag, content });
    } catch (error) {
        console.error('Error updating cache:', error);
        throw error;
    }
}

// Sync data from manifest
async function syncData() {
    try {
        const manifestResponse = await fetch('/api/sync-option/manifest', {cache: "no-store"});
        const manifest = await manifestResponse.json();

        for (const entry of manifest) {
            const cached = await getCachedData(entry.url);
            if (cached && cached.etag === entry.etag) {
                continue;
            }
            // If no cache or etag different, fetch new data
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