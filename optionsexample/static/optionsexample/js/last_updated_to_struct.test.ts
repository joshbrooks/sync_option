import { describe, it, expect, beforeEach } from 'vitest';
import { LastUpdatedTrie } from './last_updated_to_struct';

describe('LastUpdatedTrie', () => {
    let trie: LastUpdatedTrie;
    const mockOptions = [
        {
            group: 'testGroup',
            value: 'option1',
            last_updated: '2024-04-15T10:30:00Z'  // 10:30 AM UTC
        },
        {
            group: 'testGroup',
            value: 'option2',
            last_updated: '2024-04-15T10:30:00Z'  // Same timestamp
        },
        {
            group: 'testGroup',
            value: 'option3',
            last_updated: '2024-04-15T11:30:00Z'  // 11:30 AM UTC
        },
        {
            group: 'testGroup',
            value: 'option4',
            last_updated: '2024-04-16T10:30:00Z'  // Next day at 10:30 AM UTC
        }
    ];

    beforeEach(() => {
        trie = new LastUpdatedTrie(mockOptions);
        trie.buildTrie();
    });

    it('should build trie correctly', () => {
        // Check count for specific timestamp
        const date1 = new Date('2024-04-15T10:30:00Z');
        expect(trie.getCountByDate(date1)).toBe(2);  // Two options at this timestamp

        const date2 = new Date('2024-04-15T11:30:00Z');
        expect(trie.getCountByDate(date2)).toBe(1);  // One option at this timestamp
    });

    it('should return correct counts by prefix', () => {
        // Debug the trie structure
        trie.debugTrie();

        // Check count for entire day
        const dayCount = trie.getCountByPrefix([2024, 4, 15]);
        console.log('Day count:', dayCount);
        expect(dayCount).toBe(3);  // Three options on April 15

        // Check count for specific hour
        const hourCount = trie.getCountByPrefix([2024, 4, 15, 10]);
        console.log('Hour count:', hourCount);
        expect(hourCount).toBe(2);  // Two options at 10 AM

        // Check count for non-existent prefix
        expect(trie.getCountByPrefix([2024, 4, 15, 12])).toBe(0);  // No options at 12 PM
    });

    it('should handle empty input', () => {
        const emptyTrie = new LastUpdatedTrie([]);
        emptyTrie.buildTrie();

        // All counts should be 0
        expect(emptyTrie.getCountByDate(new Date())).toBe(0);
        expect(emptyTrie.getCountByPrefix([2024, 4, 15])).toBe(0);
    });

    it('should handle invalid dates', () => {
        const invalidOptions = [
            {
                group: 'testGroup',
                value: 'option1',
                last_updated: 'invalid-date'
            }
        ];

        const invalidTrie = new LastUpdatedTrie(invalidOptions);
        invalidTrie.buildTrie();

        // Should handle invalid dates gracefully
        expect(invalidTrie.getCountByDate(new Date())).toBe(0);
    });

    it('should find missing objects', () => {
        // Create a trie with only some objects
        const partialOptions = [
            mockOptions[0],  // First object
            mockOptions[2],  // Third object
        ];
        const partialTrie = new LastUpdatedTrie(partialOptions);
        partialTrie.buildTrie();

        // Debug the trie structure
        console.log('Partial trie:');
        partialTrie.debugTrie();

        // Find missing objects
        const missing = partialTrie.findMissingObjects(mockOptions);
        console.log('Missing objects:', missing);

        // Should find three missing objects
        expect(missing).toHaveLength(3);
        expect(missing).toContainEqual(mockOptions[0]);  // Second object
        expect(missing).toContainEqual(mockOptions[1]);  // Second object
        expect(missing).toContainEqual(mockOptions[3]);  // Fourth object

        // Verify the missing objects have the correct timestamps
        expect(new Date(missing[0].last_updated).toISOString())
            .toBe('2024-04-15T10:30:00.000Z');
        expect(new Date(missing[2].last_updated).toISOString())
            .toBe('2024-04-16T10:30:00.000Z');
    });
}); 