// Save groups to IndexedDB
function saveGroups(groups) {
    return new Promise((resolve, reject) => {
        const transaction = DB.getTransaction(DB.GROUPS_STORE, 'readwrite');
        const store = DB.getStore(transaction, DB.GROUPS_STORE);

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
        const transaction = DB.getTransaction(DB.GROUPS_STORE, 'readonly');
        const store = DB.getStore(transaction, DB.GROUPS_STORE);
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
        const lastSync = await DB.getLastUpdated(DB.GROUPS_STORE);
        const groups = await fetchGroups(lastSync);
        
        if (groups.length > 0) {
            await saveGroups(groups);
            const allGroups = await getAllGroups();
            updateTable(allGroups);
            highlightUpdatedRows(groups);
        }

        document.getElementById('lastSyncTime').textContent = new Date().toLocaleString();
    } catch (error) {
        console.error('Error during sync:', error);
    }
}

// Initialize and start periodic sync
async function init() {
    try {
        await DB.initDB();
        await syncGroups();
        setInterval(syncGroups, 5000);
    } catch (error) {
        console.error('Initialization error:', error);
    }
}

// Start the application
document.addEventListener('DOMContentLoaded', init); 