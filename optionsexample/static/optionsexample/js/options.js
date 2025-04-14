// IndexedDB setup
const DB_NAME = 'optionsDB';
const DB_VERSION = 1;
const STORE_NAME = 'options';
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
                const store = db.createObjectStore(STORE_NAME, { keyPath: ['group', 'value'] });
                store.createIndex('last_updated', 'last_updated', { unique: false });
            }
        };
    });
}

// Save options to IndexedDB
function saveOptions(options) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([STORE_NAME], 'readwrite');
        const store = transaction.objectStore(STORE_NAME);

        options.forEach(option => {
            store.put({ ...option, group: GROUP_NAME });
        });

        transaction.oncomplete = () => resolve();
        transaction.onerror = () => reject(transaction.error);
    });
}

// Get all options for the current group from IndexedDB
function getAllOptions() {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([STORE_NAME], 'readonly');
        const store = transaction.objectStore(STORE_NAME);
        const request = store.getAll();

        request.onsuccess = () => {
            const options = request.result.filter(option => option.group === GROUP_NAME);
            resolve(options);
        };
        request.onerror = () => reject(request.error);
    });
}

// Fetch options from API
async function fetchOptions(lastSync = null) {
    const url = new URL(OPTIONS_API_URL, window.location.origin);
    if (lastSync) {
        url.searchParams.append('last_sync', lastSync);
    }

    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

// Update the table with options data
function updateTable(options) {
    const tbody = document.getElementById('optionsTableBody');
    tbody.innerHTML = '';

    options.forEach(option => {
        const row = document.createElement('tr');
        row.dataset.value = option.value;
        
        row.innerHTML = `
            <td>${option.value}</td>
            <td>${option.value_type}</td>
            <td>${option.names.en || ''}</td>
            <td>${option.descriptions.en || ''}</td>
            <td>${new Date(option.last_updated).toLocaleString()}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// Highlight updated rows
function highlightUpdatedRows(updatedOptions) {
    updatedOptions.forEach(option => {
        const row = document.querySelector(`tr[data-value="${option.value}"]`);
        if (row) {
            row.classList.add('updated');
            setTimeout(() => row.classList.remove('updated'), 1000);
        }
    });
}

// Main sync function
async function syncOptions() {
    try {
        const lastSync = localStorage.getItem(`lastSync_${GROUP_NAME}`);
        const options = await fetchOptions(lastSync);
        
        if (options.length > 0) {
            await saveOptions(options);
            const allOptions = await getAllOptions();
            updateTable(allOptions);
            highlightUpdatedRows(options);
        }

        localStorage.setItem(`lastSync_${GROUP_NAME}`, new Date().toISOString());
        document.getElementById('lastSyncTime').textContent = new Date().toLocaleString();
    } catch (error) {
        console.error('Error during sync:', error);
    }
}

// Initialize and start periodic sync
async function init() {
    try {
        await initDB();
        await syncOptions();
        setInterval(syncOptions, 5000);
    } catch (error) {
        console.error('Initialization error:', error);
    }
}

// Start the application
document.addEventListener('DOMContentLoaded', init); 