import { describe, it } from 'vitest';
import { ulid } from 'ulid';
import { ulidToTriePath } from './ulid_to_trie';

describe('Request Size Analysis', () => {
    it('should analyze JSON request sizes', () => {
        // Generate sample ULIDs
        const sampleSizes = [10, 100, 1000, 10000];

        for (const size of sampleSizes) {
            const ulids = Array.from({ length: size }, () => {
                const timestamp = Date.now();
                return ulid(timestamp);
            });

            // Create request payload
            const payload = {
                updates: ulids.map(id => ({
                    id,
                    ...ulidToTriePath(id)
                }))
            };

            // Calculate sizes
            const jsonString = JSON.stringify(payload);
            const rawSize = jsonString.length;
            const gzippedSize = require('zlib').gzipSync(jsonString).length;

            // Calculate size per item
            const rawSizePerItem = rawSize / size;
            const gzippedSizePerItem = gzippedSize / size;

            console.log(`\nSize Analysis for ${size} items:`);
            console.log(`Raw JSON size: ${(rawSize / 1024).toFixed(2)} KB`);
            console.log(`Gzipped size: ${(gzippedSize / 1024).toFixed(2)} KB`);
            console.log(`Raw size per item: ${rawSizePerItem.toFixed(2)} bytes`);
            console.log(`Gzipped size per item: ${gzippedSizePerItem.toFixed(2)} bytes`);

            // Sample of the actual JSON structure
            if (size === 10) {
                console.log('\nSample JSON structure (10 items):');
                console.log(JSON.stringify(payload, null, 2).slice(0, 500) + '...');
            }
        }
    });
}); 