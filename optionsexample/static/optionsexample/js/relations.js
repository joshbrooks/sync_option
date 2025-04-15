// Save relations to IndexedDB
function saveRelations(relations) {
    return new Promise((resolve, reject) => {
        const transaction = DB.getTransaction(DB.RELATIONS_STORE, 'readwrite');
        const store = DB.getStore(transaction, DB.RELATIONS_STORE);

        relations.forEach(relation => {
            store.put(relation);
        });

        transaction.oncomplete = () => resolve();
        transaction.onerror = () => reject(transaction.error);
    });
}

// Get all relations from IndexedDB
function getAllRelations() {
    return new Promise((resolve, reject) => {
        const transaction = DB.getTransaction(DB.RELATIONS_STORE, 'readonly');
        const store = DB.getStore(transaction, DB.RELATIONS_STORE);
        const request = store.getAll();

        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

// Fetch relations from API
async function fetchRelations(lastSync = null) {
    const url = new URL(RELATIONS_API_URL, window.location.origin);
    if (lastSync) {
        url.searchParams.append('last_sync', lastSync);
    }

    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

// Update the table with relations data
function updateTable(relations) {
    const tbody = document.getElementById('relationsTableBody');
    tbody.innerHTML = '';

    relations.forEach(relation => {
        const row = document.createElement('tr');
        row.dataset.id = relation.id;
        
        row.innerHTML = `
            <td>${relation.from_option.value}</td>
            <td>${relation.to_option.value}</td>
            <td>${relation.relation_type}</td>
            <td>${new Date(relation.last_updated).toLocaleString()}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// Highlight updated rows
function highlightUpdatedRows(updatedRelations) {
    updatedRelations.forEach(relation => {
        const row = document.querySelector(`tr[data-id="${relation.id}"]`);
        if (row) {
            row.classList.add('updated');
            setTimeout(() => row.classList.remove('updated'), 1000);
        }
    });
}

// Main sync function
async function syncRelations() {
    try {
        const lastSync = await DB.getLastUpdated(DB.RELATIONS_STORE);
        const relations = await fetchRelations(lastSync);
        
        if (relations.length > 0) {
            await saveRelations(relations);
            const allRelations = await getAllRelations();
            updateTable(allRelations);
            highlightUpdatedRows(relations);
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
        await syncRelations();
        setInterval(syncRelations, 5000);
    } catch (error) {
        console.error('Initialization error:', error);
    }
}

// Start the application
document.addEventListener('DOMContentLoaded', init); 