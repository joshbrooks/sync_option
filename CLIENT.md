# Client Side

## Overview
The sync-option API uses a manifest-based caching strategy to efficiently manage data synchronization.

## Implementation Guide
We'll follow the pattern described in https://blog.stackademic.com/efficient-http-get-caching-in-angular-with-etag-3681d597068c

### Cache Storage
Set up an IndexedDB (IDB) database with the following schema:
- Table: `sync_option_cache`
- Fields:
  - `url`: string (primary key)
  - `etag`: UUID
  - `content`: JSON

### Sync Process

1. First, fetch the manifest from `/api/sync-option/manifest`
   ```typescript
   interface ManifestEntry {
     url: string;      // Full URL to the endpoint
     etag: string;     // UUID representing latest change (sync_id)
   }
   ```

2. The manifest will include entries for:
   - `/api/sync-option/options/groups` - List of all option groups
   - `/api/sync-option/options/groups/{group_name}` - Options for specific groups
   - `/api/sync-option/options/relations/{group_name}` - Relations for specific groups

3. For each entry in the manifest:
   - Compare the `etag` with the stored value in IDB
   - If different or not in IDB:
     - Fetch the URL
     - Store the new content and etag in IDB
   - If same:
     - Use cached content from IDB

### Example Implementation
```typescript
async function syncData() {
  const manifest = await fetch('/api/sync-option/manifest').then(r => r.json());
  const db = await openSyncOptionDB();
  
  for (const entry of manifest) {
    const cached = await db.get('sync_option_cache', entry.url);
    if (!cached || cached.etag !== entry.etag) {
      const response = await fetch(entry.url);
      const content = await response.json();
      await db.put('sync_option_cache', {
        url: entry.url,
        etag: entry.etag,
        content
      });
    }
  }
}
```