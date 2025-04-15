/**
 * Extracts date components from a UUIDv7.
 * UUIDv7 format: [timestamp (48 bits)][rand_a (12 bits)][rand_b (62 bits)]
 * The timestamp is Unix time in milliseconds
 */
export function extractDateFromUuid(uuid: string): Date {
    // Remove hyphens and extract the timestamp part (first 12 characters)
    const parts = uuid.split("-");
    const highBitsHex = parts[0] + parts[1].slice(0, 4);

    // Convert hex to milliseconds since Unix epoch
    const timestampMs = parseInt(highBitsHex, 16);

    // Create a Date object from the timestamp
    // Round to nearest second to avoid millisecond precision issues
    return new Date(Math.floor(timestampMs / 1000) * 1000);
}

/**
 * Creates a path array from a UUIDv7 for use in the trie structure.
 * Returns an array of numbers: [year, month, day, hour, minute, second]
 */
export function uuidToTriePath(uuid: string): number[] {
    const date = extractDateFromUuid(uuid);
    return [
        date.getUTCFullYear(),
        date.getUTCMonth() + 1, // getUTCMonth returns 0-11
        date.getUTCDate(),
        date.getUTCHours(),
        date.getUTCMinutes(),
        date.getUTCSeconds()
    ];
} 