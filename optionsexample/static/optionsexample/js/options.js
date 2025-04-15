// Save options to IndexedDB
function saveOptions(options) {
    return new Promise((resolve, reject) => {
        const transaction = DB.getTransaction(DB.OPTIONS_STORE, 'readwrite');
        const store = DB.getStore(transaction, DB.OPTIONS_STORE);

        options.forEach(option => {
            // Add group_name to the option data
            const optionData = {
                ...option,
                group_name: GROUP_NAME
            };
            store.put(optionData);
        });

        transaction.oncomplete = () => resolve();
        transaction.onerror = () => reject(transaction.error);
    });
}

// Get all options from IndexedDB
function getAllOptions() {
    return new Promise((resolve, reject) => {
        const transaction = DB.getTransaction(DB.OPTIONS_STORE, 'readonly');
        const store = DB.getStore(transaction, DB.OPTIONS_STORE);
        const request = store.getAll();

        request.onsuccess = () => resolve(request.result);
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

    // Filter options by the current group
    const filteredOptions = options.filter(option => option.group_name === GROUP_NAME);

    filteredOptions.forEach(option => {
        const row = document.createElement('tr');
        row.dataset.id = option.id;
        
        row.innerHTML = `
            <td>${option.value}</td>
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
        const row = document.querySelector(`tr[data-id="${option.id}"]`);
        if (row) {
            row.classList.add('updated');
            setTimeout(() => row.classList.remove('updated'), 1000);
        }
    });
}

// Main sync function
async function syncOptions() {
    try {
        const lastSync = await DB.getLastUpdated(DB.OPTIONS_STORE, GROUP_NAME);
        const options = await fetchOptions(lastSync);
        
        if (options.length > 0) {
            await saveOptions(options);
            const allOptions = await getAllOptions();
            updateTable(allOptions);
            highlightUpdatedRows(options);
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
        await syncOptions();
        setInterval(syncOptions, 5000);
    } catch (error) {
        console.error('Initialization error:', error);
    }
}

// Start the application
document.addEventListener('DOMContentLoaded', init); 