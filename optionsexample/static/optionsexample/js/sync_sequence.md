# Client-Server Synchronization Sequence

```mermaid
sequenceDiagram
    participant Client
    participant Server

    Note over Client: 1. Calculate full trie
    Note over Client: 2. Send first level with hash/count
    Client->>Server: POST /sync/level1
    Note right of Client: {<br/>  "01": {hash: "abc", count: 5},<br/>  "02": {hash: "def", count: 3}<br/>}

    Note over Server: 3. Compare client trie
    Server-->>Client: 200 OK<br/>{"01": "match", "02": "diff"}

    Note over Server: 4. Send different keys with subtrees
    Server-->>Client: GET /sync/level2/02
    Note left of Server: {<br/>  "02/H9": {hash: "xyz", count: 2},<br/>  "02/H8": {hash: "uvw", count: 1}<br/>}

    Note over Client: 5. Match subtrees
    Client->>Server: POST /sync/level2/02
    Note right of Client: {<br/>  "02/H9": {hash: "diff", count: 3},<br/>  "02/H8": "match"<br/>}

    Note over Server: 6. Compare subtrees
    Server-->>Client: GET /sync/values/02/H9
    Note left of Server: [<br/>  {id: "02H9...", ...},<br/>  {id: "02H9...", ...}<br/>]

    Note over Client: Update local data
```

## Explanation

1. **Client Calculates Full Trie**
   - Client builds complete trie structure
   - Each node contains hash and count

2. **Client Sends First Level**
   - Sends only top-level nodes (2-char prefixes)
   - Includes hash and count for each node
   - Example: `{"01": {hash: "abc", count: 5}}`

3. **Server Comparison**
   - Server compares hashes and counts
   - Identifies which nodes need synchronization
   - Returns list of matching/different nodes

4. **Server Sends Subtree Info**
   - For each different node, sends its subtree
   - Only sends hash and count for each subtree node
   - Example: `{"02/H9": {hash: "xyz", count: 2}}`

5. **Client Matches Subtrees**
   - Client compares subtree hashes and counts
   - Identifies which subtrees need full data
   - Sends back list of different subtrees

6. **Server Sends Full Values**
   - For each different subtree, sends complete data
   - Includes all object details
   - Example: `[{id: "02H9...", ...}]`

## Server-Side Comparison Logic

### First Level Comparison
```typescript
interface FirstLevelNode {
    hash: string;
    count: number;
}

interface ComparisonResult {
    [key: string]: 'match' | 'diff';
}

function compareFirstLevel(
    clientTrie: Record<string, FirstLevelNode>,
    serverTrie: Record<string, FirstLevelNode>
): ComparisonResult {
    const result: ComparisonResult = {};

    // Check all client nodes against server
    for (const [key, clientNode] of Object.entries(clientTrie)) {
        const serverNode = serverTrie[key];
        
        if (!serverNode) {
            result[key] = 'diff';
            continue;
        }

        // Compare hash and count
        if (clientNode.hash === serverNode.hash && 
            clientNode.count === serverNode.count) {
            result[key] = 'match';
        } else {
            result[key] = 'diff';
        }
    }

    // Check for server nodes not in client
    for (const key of Object.keys(serverTrie)) {
        if (!(key in clientTrie)) {
            result[key] = 'diff';
        }
    }

    return result;
}
```

### Second Level Comparison
```typescript
interface SecondLevelNode {
    hash: string;
    count: number;
}

interface SecondLevelComparison {
    [key: string]: 'match' | 'diff';
}

function compareSecondLevel(
    clientSubtree: Record<string, SecondLevelNode>,
    serverSubtree: Record<string, SecondLevelNode>
): SecondLevelComparison {
    const result: SecondLevelComparison = {};

    // Check all client nodes against server
    for (const [key, clientNode] of Object.entries(clientSubtree)) {
        const serverNode = serverSubtree[key];
        
        if (!serverNode) {
            result[key] = 'diff';
            continue;
        }

        // Compare hash and count
        if (clientNode.hash === serverNode.hash && 
            clientNode.count === serverNode.count) {
            result[key] = 'match';
        } else {
            result[key] = 'diff';
        }
    }

    // Check for server nodes not in client
    for (const key of Object.keys(serverSubtree)) {
        if (!(key in clientSubtree)) {
            result[key] = 'diff';
        }
    }

    return result;
}
```

## Benefits
- Minimizes data transfer by only sending differences
- Uses hash comparison to quickly identify changes
- Hierarchical approach reduces network traffic
- Count validation ensures data integrity 