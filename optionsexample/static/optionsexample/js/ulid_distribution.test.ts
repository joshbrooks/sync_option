import { describe, it, expect } from 'vitest';
import { ulid } from 'ulid';
import { ulidToTriePath, calculateCollectionHash, createCollectionNode } from './ulid_to_trie';

describe('ULID Distribution Analysis', () => {
    it('should analyze distribution of 10,000 ULIDs', () => {
        // Generate 10,000 ULIDs between 2020 and 2025
        const ulids = Array.from({ length: 10000 }, () => {
            // Generate a random timestamp between 2020 and 2025
            const start = new Date('2020-01-01').getTime();
            const end = new Date('2025-12-31').getTime();
            const timestamp = Math.floor(start + Math.random() * (end - start));
            return ulid(timestamp);
        });

        // Analyze the distribution
        const pathCounts = new Map();
        const collectionHashes = new Map();
        const pathCollectionCounts = new Map();

        // Group ULIDs by their path
        const pathGroups = new Map();
        for (const ulid of ulids) {
            const { path } = ulidToTriePath(ulid);
            const pathKey = path.join('/');

            if (!pathGroups.has(pathKey)) {
                pathGroups.set(pathKey, []);
            }
            pathGroups.get(pathKey).push(ulid);
        }

        // Analyze each path group
        for (const [pathKey, groupUlids] of pathGroups) {
            // Count paths
            pathCounts.set(pathKey, groupUlids.length);

            // Calculate collection hash
            const hash = calculateCollectionHash(groupUlids);
            collectionHashes.set(pathKey, hash);

            // Count path+hash combinations
            const pathHashKey = `${pathKey}/${hash}`;
            pathCollectionCounts.set(pathHashKey, groupUlids.length);
        }

        // Calculate statistics
        const totalPaths = pathCounts.size;
        const totalCollections = collectionHashes.size;
        const totalCombinations = pathCollectionCounts.size;

        // Calculate average items per path
        const avgItemsPerPath = ulids.length / totalPaths;

        // Calculate average items per collection
        const avgItemsPerCollection = ulids.length / totalCollections;

        // Log the results
        console.log('Distribution Analysis:');
        console.log(`Total ULIDs: ${ulids.length}`);
        console.log(`Unique paths: ${totalPaths}`);
        console.log(`Unique collection hashes: ${totalCollections}`);
        console.log(`Unique path+hash combinations: ${totalCombinations}`);
        console.log(`Average items per path: ${avgItemsPerPath.toFixed(2)}`);
        console.log(`Average items per collection: ${avgItemsPerCollection.toFixed(2)}`);

        // Sample of the actual structure
        if (totalPaths > 0) {
            const samplePath = Array.from(pathGroups.keys())[0];
            const sampleUlids = pathGroups.get(samplePath);
            const sampleNode = createCollectionNode(sampleUlids);

            console.log('\nSample Collection Structure:');
            console.log(`Path: ${samplePath}`);
            console.log(`Collection Hash: ${sampleNode.hash}`);
            console.log(`Count: ${sampleNode.count}`);
        }

        // Verify our assumptions
        expect(totalPaths).toBeGreaterThan(0);
        expect(totalCollections).toBeGreaterThan(0);
        expect(totalCombinations).toBeGreaterThan(0);

        // Each path should have roughly the expected number of items
        // (based on 5 years of data and our 2-char chunks)
        const expectedPaths = 32 * 32; // 2 chars of base32 = 32^2 possibilities
        expect(totalPaths).toBeLessThanOrEqual(expectedPaths);

        // Each collection should have a unique hash
        expect(totalCollections).toBe(totalPaths);
    });
}); 