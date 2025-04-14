# Options Client Implementation

## Overview

This document outlines the client-side implementation for consuming the Options API, focusing on IndexedDB storage and sync strategies.

## IDB Structure

```typescript
interface IDBOption {
  group: string;
  value: string;
  value_type: 'string' | 'integer';
  names: Record<string, string>;
  descriptions?: Record<string, string>;
  is_active: boolean;
  last_updated: string;
  typed_value: string | number;
}

interface IDBOptionGroup {
  name: string;
  names: Record<string, string>;
  descriptions?: Record<string, string>;
  last_updated: string;
}

interface IDBOptionRelation {
  from_option: string;  // value
  from_group: string;   // group name
  to_option: string;    // value
  to_group: string;     // group name
  relation_type: string;
  metadata?: Record<string, any>;
}
```

## Database Setup

```typescript
interface IDBStores {
  groups: IDBOptionGroup;
  options: IDBOption;
  relations: IDBOptionRelation;
  meta: string;  // For storing sync timestamp
}

function createOptionsDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('options_db', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = request.result;
      
      // Create stores
      const groups = db.createObjectStore('groups', { keyPath: 'name' });
      const options = db.createObjectStore('options', { keyPath: ['group', 'value'] });
      const relations = db.createObjectStore('relations', { 
        keyPath: ['from_group', 'from_option', 'to_group', 'to_option'] 
      });
      const meta = db.createObjectStore('meta');
      
      // Create indexes
      groups.createIndex('last_updated', 'last_updated');
      options.createIndex('last_updated', 'last_updated');
      options.createIndex('group', 'group');
      options.createIndex('value', 'value');
      relations.createIndex('from', ['from_group', 'from_option']);
      relations.createIndex('to', ['to_group', 'to_option']);
    };
  });
}
```

## Sync Implementation

### Basic Sync

```typescript
async function syncOptions(groups?: string[]) {
  const db = await openOptionsDB();
  const lastSync = await db.get('meta', 'lastSync');
  
  const response = await fetch(
    `/api/options/sync?last_sync=${lastSync}&groups=${groups?.join(',')}`
  );
  const data = await response.json();
  
  const tx = db.transaction(['groups', 'options'], 'readwrite');
  
  // Update groups
  for (const group of data.updated_groups) {
    await tx.objectStore('groups').put(group);
  }
  
  // Update options
  for (const option of data.updated_options) {
    await tx.objectStore('options').put(option);
  }
  
  // Remove deleted
  for (const id of data.deleted_options) {
    await tx.objectStore('options').delete(id);
  }
  
  // Update sync timestamp
  await db.put('meta', data.last_sync, 'lastSync');
  
  await tx.done;
}
```

### Robust Sync with Error Handling

```typescript
class SyncError extends Error {
  constructor(message: string, public details: any) {
    super(message);
    this.name = 'SyncError';
  }
}

async function robustSync(groups?: string[]): Promise<void> {
  try {
    await syncOptions(groups);
  } catch (error) {
    if (error instanceof NetworkError) {
      // Handle network issues
      await scheduleRetry();
    } else if (error instanceof QuotaExceededError) {
      // Handle storage issues
      await cleanupOldData();
      await syncOptions(groups);
    } else {
      throw new SyncError('Sync failed', error);
    }
  }
}
```

## Querying Related Options

```typescript
async function getRelatedOptions(
  group: string,
  value: string,
  relationType?: string
): Promise<IDBOption[]> {
  const db = await openOptionsDB();
  const tx = db.transaction(['relations', 'options'], 'readonly');
  
  // Find all relations
  const relations = await tx.objectStore('relations')
    .index('from')
    .getAll([group, value]);
    
  if (relationType) {
    relations = relations.filter(r => r.relation_type === relationType);
  }
  
  // Get related options
  const options = await Promise.all(
    relations.map(r => 
      tx.objectStore('options').get([r.to_group, r.to_option])
    )
  );
  
  return options.filter(Boolean);
}
```

## Performance Considerations

1. **Indexing**
   - IDB indexes on frequently queried fields
   - Compound indexes for relationship queries
   - Index on `last_updated` for efficient sync

2. **Batch Operations**
   - Use transactions for atomic updates
   - Batch related operations together
   - Minimize transaction commits

3. **Caching**
   - Cache frequently accessed options in memory
   - Implement LRU cache for relationship queries
   - Pre-fetch related options when possible

4. **Sync Optimization**
   - Incremental updates reduce payload size
   - Selective sync by group
   - Debounce frequent sync requests

## Error Handling

1. **Network Issues**
   - Retry failed requests with exponential backoff
   - Queue updates for offline operation
   - Sync queue on reconnection

2. **Storage Issues**
   - Handle quota exceeded errors
   - Implement cleanup strategies
   - Prioritize essential data

3. **Data Integrity**
   - Validate data before storage
   - Maintain referential integrity
   - Handle version conflicts 