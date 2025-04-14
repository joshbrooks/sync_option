// IndexedDB setup
const DB_NAME = 'optionsDB';
const DB_VERSION = 1;
const STORE_NAME = 'optionGroups';
let db;

// Initialize IndexedDB
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
            if (!db.objectStoreNames.contains(STORE_NAME)) {
                const store = db.createObjectStore(STORE_NAME, { keyPath: 'name' });
                store.createIndex('last_updated', 'last_updated', { unique: false });
            }
        };
    });
}

// Save groups to IndexedDB
function saveGroups(groups) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([STORE_NAME], 'readwrite');
        const store = transaction.objectStore(STORE_NAME);

        groups.forEach(group => {
            store.put(group);
        });

        transaction.oncomplete = () => resolve();
        transaction.onerror = () => reject(transaction.error);
    });
}

// Get all groups from IndexedDB
function getAllGroups() {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([STORE_NAME], 'readonly');
        const store = transaction.objectStore(STORE_NAME);
        const request = store.getAll();

        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

// Fetch groups from API
async function fetchGroups(lastSync = null) {
    const url = new URL(GROUPS_API_URL, window.location.origin);
    if (lastSync) {
        url.searchParams.append('last_sync', lastSync);
    }

    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

// Update the table with groups data
function updateTable(groups) {
    const tbody = document.getElementById('groupsTableBody');
    tbody.innerHTML = '';

    groups.forEach(group => {
        const row = document.createElement('tr');
        row.dataset.name = group.name;
        
        row.innerHTML = `
            <td>${group.name}</td>
            <td>${group.names.en || ''}</td>
            <td>${group.descriptions.en || ''}</td>
            <td>${new Date(group.last_updated).toLocaleString()}</td>
            <td><a href="/groups/${group.name}/" class="options-link">Options</a></td>
        `;
        
        tbody.appendChild(row);
    });
}

// Highlight updated rows
function highlightUpdatedRows(updatedGroups) {
    updatedGroups.forEach(group => {
        const row = document.querySelector(`tr[data-name="${group.name}"]`);
        if (row) {
            row.classList.add('updated');
            setTimeout(() => row.classList.remove('updated'), 1000);
        }
    });
}

// Main sync function
async function syncGroups() {
    try {
        const lastSync = localStorage.getItem('lastSync');
        const groups = await fetchGroups(lastSync);
        
        if (groups.length > 0) {
            await saveGroups(groups);
            const allGroups = await getAllGroups();
            updateTable(allGroups);
            highlightUpdatedRows(groups);
        }

        localStorage.setItem('lastSync', new Date().toISOString());
        document.getElementById('lastSyncTime').textContent = new Date().toLocaleString();
    } catch (error) {
        console.error('Error during sync:', error);
    }
}

// Initialize and start periodic sync
async function init() {
    try {
        await initDB();
        await syncGroups();
        setInterval(syncGroups, 5000);
    } catch (error) {
        console.error('Initialization error:', error);
    }
}

// Start the application
document.addEventListener('DOMContentLoaded', init); 