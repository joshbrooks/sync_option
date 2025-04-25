// Constants for API endpoints
const API_BASE = '/api/sync-option';
const MANIFEST_URL = `${API_BASE}/manifest`;

class SyncOptionClient {
    constructor() {
        this.isInitialized = false;
        this.isSyncing = false;
    }

    /**
     * Initialize the sync client
     * @returns {Promise<void>}
     */
    async initialize() {
        if (this.isInitialized) return;
        
        try {
            await DB.initDB();
            this.isInitialized = true;
        } catch (error) {
            console.error('Failed to initialize sync client:', error);
            throw error;
        }
    }

    /**
     * Sync all data from the manifest
     * @param {boolean} force - Force sync even if etags match
     * @returns {Promise<void>}
     */
    async sync(force = false) {
        if (!this.isInitialized) {
            await this.initialize();
        }

        if (this.isSyncing) {
            console.warn('Sync already in progress');
            return;
        }

        this.isSyncing = true;

        try {
            // Fetch and process manifest
            const manifest = await this.fetchManifest();
            await this.processSyncManifest(manifest, force);
            
            // Dispatch event when sync is complete
            window.dispatchEvent(new CustomEvent('sync-option-updated'));
        } catch (error) {
            console.error('Sync failed:', error);
            throw error;
        } finally {
            this.isSyncing = false;
        }
    }

    /**
     * Fetch the manifest from the server
     * @returns {Promise<Array<{url: string, etag: string}>>}
     */
    async fetchManifest() {
        try {
            const response = await fetch(MANIFEST_URL, {cache: "no-store"});
            if (!response.ok) {
                throw new Error(`Failed to fetch manifest: ${response.status}`);
            }
            const json = await response.json();
            return json;
        } catch (error) {
            console.error('Error fetching manifest:', error);
            throw error;
        }
    }

    /**
     * Process the sync manifest and update cache as needed
     * @param {Array<{url: string, etag: string}>} manifest 
     * @param {boolean} force - Force sync even if etags match
     */
    async processSyncManifest(manifest, force = false) {
        const updates = [];

        for (const entry of manifest) {
            try {
                const cached = await DB.getCachedData(entry.url);
                if (force || !cached || cached.etag !== entry.etag) {
                    console.log('Updating', entry.url)
                    updates.push(this.fetchAndCacheEntry(entry));
                } else {
                    // We skipped this one 
                    // console.log('Skipping', entry.url, 'because it is up to date');
                }
            } catch (error) {
                console.error(`Error processing manifest entry ${entry.url}:`, error);
                // Continue with other entries even if one fails
            }
        }

        // Wait for all updates to complete
        await Promise.allSettled(updates);
    }

    /**
     * Fetch and cache a single manifest entry
     * @param {{url: string, etag: string}} entry 
     */
    async fetchAndCacheEntry(entry) {
        try {
            const response = await fetch(entry.url, {cache: "no-store"});
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const content = await response.json();
            // Updated the etag to the new one
            await DB.updateCache(entry.url, entry.etag, content);
        } catch (error) {
            console.error(`Failed to fetch and cache ${entry.url}:`, error);
            throw error;
        }
    }

    /**
     * Get data for a specific URL
     * @param {string} url 
     * @param {boolean} forceSync - Force a fresh sync before getting data
     * @returns {Promise<any>}
     */
    async getData(url, forceSync = false) {
        if (!this.isInitialized) {
            await this.initialize();
        }

        if (forceSync) {
            await this.sync(true);
        }

        return DB.getData(url);
    }

    /**
     * Get all option groups
     * @returns {Promise<Array>}
     */
    async getOptionGroups() {
        return this.getData(`${API_BASE}/options/groups`);
    }

    /**
     * Get options for a specific group
     * @param {string} groupName 
     * @returns {Promise<Array>}
     */
    async getGroupOptions(groupName) {
        return this.getData(`${API_BASE}/options/groups/${groupName}`);
    }

    /**
     * Get relations for a specific group
     * @param {string} groupName 
     * @returns {Promise<Array>}
     */
    async getGroupRelations(groupName) {
        return this.getData(`${API_BASE}/options/relations/${groupName}`);
    }
}

// Create and export a singleton instance
window.syncClient = new SyncOptionClient(); 