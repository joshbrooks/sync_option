# ULID Trie Structure Design

## Overview
This document outlines the design of a trie structure for organizing ULIDs in a time-based hierarchical manner, with additional metadata for collection management.

## Structure

### Trie Levels
1. **First Level (2 characters)**
   - Uses the first 2 characters of the ULID timestamp
   - Covers approximately 17.5 days per node
   - Example: `01` in `01H9Z8Z7Z6Z5Z4Z3Z2Z1Z0Z`

2. **Second Level (2 characters)**
   - Uses the next 2 characters of the ULID timestamp
   - Covers approximately 13.1 hours per node
   - Example: `H9` in `01H9Z8Z7Z6Z5Z4Z3Z2Z1Z0Z`

### Collection Metadata
Each collection node (leaf) contains:

1. **Collection Hash**
   - Calculated by XORing the first 5 characters of the random part of all ULIDs in the collection
   - Provides a quick way to verify collection integrity
   - Example: XOR of `Z8Z7Z6Z5Z4` from all ULIDs in the collection

2. **Object Count**
   - Tracks the total number of objects in the collection
   - Used for quick size queries and validation

## Example Structure
```
root/
├── 01/                  # First level (17.5 days)
│   ├── H9/             # Second level (13.1 hours)
│   │   ├── {hash: "abc", count: 5}  # Collection metadata
│   │   └── ...
│   └── ...
├── 02/
│   └── ...
└── ...
```

## Implementation Details

### Path Generation
```javascript
function ulidToTriePath(ulid) {
    return {
        path: [
            ulid.substring(0, 2),  // First level
            ulid.substring(2, 4)   // Second level
        ]
    };
}
```

### Collection Hash Calculation
```javascript
function calculateCollectionHash(ulids) {
    let hash = 0;
    for (const ulid of ulids) {
        const randomPart = ulid.substring(10, 15);  // First 5 chars of random part
        for (let i = 0; i < randomPart.length; i++) {
            hash ^= randomPart.charCodeAt(i);
        }
    }
    return hash.toString(32).padStart(3, '0');
}
```

## Benefits
1. **Efficient Time-based Lookups**
   - Two-level structure provides good granularity for time-based queries
   - Each level covers a meaningful time range (days/hours)

2. **Collection Integrity**
   - XOR-based hash provides quick way to verify collection contents
   - Count provides immediate size information

3. **Storage Efficiency**
   - Minimal metadata per collection
   - Shallow trie structure (only 2 levels)

4. **Scalability**
   - Natural time-based partitioning
   - Easy to add new items while maintaining structure 