// Shared IndexedDB setup
const DB_NAME = 'optionsDB';
const DB_VERSION = 1;
const GROUPS_STORE = 'optionGroups';
const OPTIONS_STORE = 'options';
const RELATIONS_STORE = 'optionRelations';
let db;

// Initialize IndexedDB with both stores
function initDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onerror = () => {
            console.error('Error opening database');
            reject(request.error);
        };

        request.onsuccess = () => {
            db = request.result;
            resolve();
        };

        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            
            // Create groups store if it doesn't exist
            if (!db.objectStoreNames.contains(GROUPS_STORE)) {
                const groupsStore = db.createObjectStore(GROUPS_STORE, { keyPath: 'name' });
                groupsStore.createIndex('last_updated', 'last_updated', { unique: false });
            }
            
            // Create options store if it doesn't exist
            if (!db.objectStoreNames.contains(OPTIONS_STORE)) {
                const optionsStore = db.createObjectStore(OPTIONS_STORE, { keyPath: 'value' });
                optionsStore.createIndex('group_name', 'group_name', { unique: false });
                optionsStore.createIndex('last_updated', 'last_updated', { unique: false });
            }

            // Create relations store if it doesn't exist
            if (!db.objectStoreNames.contains(RELATIONS_STORE)) {
                const relationsStore = db.createObjectStore(RELATIONS_STORE, { keyPath: 'id' });
                relationsStore.createIndex('from_option', 'from_option', { unique: false });
                relationsStore.createIndex('to_option', 'to_option', { unique: false });
                relationsStore.createIndex('relation_type', 'relation_type', { unique: false });
                relationsStore.createIndex('last_updated', 'last_updated', { unique: false });
            }
        };
    });
}

// Get a transaction for a specific store
function getTransaction(storeName, mode = 'readonly') {
    return db.transaction([storeName], mode);
}

// Get an object store from a transaction
function getStore(transaction, storeName) {
    return transaction.objectStore(storeName);
}

// Get the most recent last_updated value from a store
function getLastUpdated(storeName, groupName = null) {
    return new Promise((resolve, reject) => {
        const transaction = getTransaction(storeName, 'readonly');
        const store = getStore(transaction, storeName);
        const index = store.index('last_updated');
        const request = index.openCursor(null, 'prev');

        request.onsuccess = (event) => {
            const cursor = event.target.result;
            if (cursor) {
                // If groupName is provided, check if the record belongs to that group
                if (groupName && cursor.value.group_name !== groupName) {
                    cursor.continue();
                    return;
                }
                resolve(cursor.value.last_updated);
            } else {
                resolve(null);
            }
        };
        request.onerror = () => reject(request.error);
    });
}

// Export the shared functions and constants
window.DB = {
    initDB,
    getTransaction,
    getStore,
    getLastUpdated,
    GROUPS_STORE,
    OPTIONS_STORE,
    RELATIONS_STORE
}; 