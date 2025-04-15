/**
 * Extracts timestamp from ULID.
 * Returns milliseconds since Unix epoch.
 */
export function extractTimestampFromUlid(ulid: string): number {
    // ULID timestamp is first 10 characters
    const timestampChars = ulid.substring(0, 10);

    // Convert from base32 to milliseconds
    const timestampMs = decodeBase32(timestampChars);

    return timestampMs;
}

/**
 * Decodes a base32 string to a number.
 * ULID uses Crockford's base32 alphabet.
 */
function decodeBase32(str: string): number {
    const alphabet = '0123456789ABCDEFGHJKMNPQRSTVWXYZ';
    let result = 0;

    for (let i = 0; i < str.length; i++) {
        const char = str[i].toUpperCase();
        const value = alphabet.indexOf(char);
        if (value === -1) throw new Error('Invalid base32 character');
        result = result * 32 + value;
    }

    return result;
}

/**
 * Calculates the optimal chunk size for a ULID trie based on:
 * - Desired trie depth
 * - Memory efficiency
 * - Query performance
 * 
 * @param targetDepth Desired maximum depth of the trie
 * @returns Recommended chunk size
 */
export function calculateOptimalChunkSize(targetDepth: number = 7): number {
    // ULID timestamp is 10 characters
    // We want to achieve roughly targetDepth levels
    return Math.ceil(10 / targetDepth);
}

/**
 * Aggregates a 2-level trie into a 1-level trie by combining second-level hashes and counts
 * @param trie The 2-level trie structure
 * @returns A 1-level trie with aggregated hashes and counts
 */
export function aggregateToFirstLevel(trie: Record<string, Record<string, { hash: string; count: number }>>): Record<string, { hash: string; count: number }> {
    const result: Record<string, { hash: string; count: number }> = {};

    for (const [firstLevel, secondLevel] of Object.entries(trie)) {
        let combinedHash = 0;
        let totalCount = 0;

        // XOR all second-level hashes and sum counts
        for (const { hash, count } of Object.values(secondLevel)) {
            // Convert hash string to number for XOR operation
            const hashNum = parseInt(hash, 32);
            combinedHash ^= hashNum;
            totalCount += count;
        }

        // Convert combined hash back to base32 string
        result[firstLevel] = {
            hash: combinedHash.toString(32).padStart(3, '0'),
            count: totalCount
        };
    }

    return result;
}

/**
 * @typedef {Object} TriePathResult
 * @property {string[]} path - The trie path components
 */

/**
 * Converts a ULID to a trie path
 * @param {string} ulid - The ULID to convert
 * @returns {TriePathResult} The trie path result
 */
export function ulidToTriePath(ulid) {
    return {
        path: [
            ulid.substring(0, 2),  // First level (17.5 days)
            ulid.substring(2, 4)   // Second level (13.1 hours)
        ]
    };
}

/**
 * Calculates the collection hash by XORing the first 5 characters of the random part
 * @param {string[]} ulids - Array of ULIDs in the collection
 * @returns {string} The collection hash in base32
 */
export function calculateCollectionHash(ulids) {
    let hash = 0;
    for (const ulid of ulids) {
        const randomPart = ulid.substring(10, 15);  // First 5 chars of random part
        for (let i = 0; i < randomPart.length; i++) {
            hash ^= randomPart.charCodeAt(i);
        }
    }
    return hash.toString(32).padStart(3, '0');
}

/**
 * Represents a collection node in the trie
 * @typedef {Object} CollectionNode
 * @property {string} hash - The collection hash
 * @property {number} count - The number of objects in the collection
 */

/**
 * Creates a collection node with hash and count
 * @param {string[]} ulids - Array of ULIDs in the collection
 * @returns {CollectionNode} The collection node
 */
export function createCollectionNode(ulids) {
    return {
        hash: calculateCollectionHash(ulids),
        count: ulids.length
    };
} 