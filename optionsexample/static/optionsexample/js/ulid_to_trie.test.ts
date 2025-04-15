import { describe, it, expect } from 'vitest';
import { ulid } from 'ulid';
import { ulidToTriePath, calculateCollectionHash, createCollectionNode, aggregateToFirstLevel } from './ulid_to_trie';

describe('ULID Trie Path Generation', () => {
    it('should create correct two-level trie path', () => {
        const ulid = '01H9Z8Z7Z6Z5Z4Z3Z2Z1Z0Z';
        const result = ulidToTriePath(ulid);

        // Should have exactly two levels
        expect(result.path).toHaveLength(2);

        // First level should be first 2 chars
        expect(result.path[0]).toBe('01');

        // Second level should be next 2 chars
        expect(result.path[1]).toBe('H9');
    });

    it('should handle different ULIDs correctly', () => {
        const testCases = [
            {
                ulid: '01H9Z8Z7Z6Z5Z4Z3Z2Z1Z0Z',
                expected: ['01', 'H9']
            },
            {
                ulid: '01H9Z8Z7Z6Z5Z4Z3Z2Z1Z0Y',
                expected: ['01', 'H9']
            },
            {
                ulid: '01H9Z8Z7Z6Z5Z4Z3Z2Z1Z0X',
                expected: ['01', 'H9']
            }
        ];

        for (const { ulid, expected } of testCases) {
            expect(ulidToTriePath(ulid).path).toEqual(expected);
        }
    });
});

describe('Collection Hash Calculation', () => {
    it('should calculate consistent hash for same ULIDs', () => {
        const ulids = [
            '01H9Z8Z7Z6Z5Z4Z3Z2Z1Z0Z',
            '01H9Z8Z7Z6Z5Z4Z3Z2Z1Z0Y',
            '01H9Z8Z7Z6Z5Z4Z3Z2Z1Z0X'
        ];

        const hash1 = calculateCollectionHash(ulids);
        const hash2 = calculateCollectionHash(ulids);

        expect(hash1).toBe(hash2);
        expect(hash1).toMatch(/^[0-9a-v]{3}$/); // base32
    });

    it('should calculate different hash for different ULIDs', () => {
        // Generate two completely different ULIDs
        const ulids1 = [ulid()];
        const ulids2 = [ulid()];

        const hash1 = calculateCollectionHash(ulids1);
        const hash2 = calculateCollectionHash(ulids2);

        expect(hash1).not.toBe(hash2);
    });
});

describe('Collection Node Creation', () => {
    it('should create collection node with correct hash and count', () => {
        const ulids = [
            '01H9Z8Z7Z6Z5Z4Z3Z2Z1Z0Z',
            '01H9Z8Z7Z6Z5Z4Z3Z2Z1Z0Y',
            '01H9Z8Z7Z6Z5Z4Z3Z2Z1Z0X'
        ];

        const node = createCollectionNode(ulids);

        expect(node).toHaveProperty('hash');
        expect(node).toHaveProperty('count');
        expect(node.hash).toMatch(/^[0-9a-v]{3}$/); // base32
        expect(node.count).toBe(3);
    });
});

describe('Trie Aggregation', () => {
    it('should correctly aggregate a 2-level trie into a 1-level trie', () => {
        const twoLevelTrie = {
            '01': {
                'H9': { hash: 'abc', count: 3 },
                'H8': { hash: 'def', count: 2 }
            },
            '02': {
                'H7': { hash: 'ghi', count: 4 }
            }
        };

        const expected = {
            '01': {
                hash: (parseInt('abc', 32) ^ parseInt('def', 32)).toString(32).padStart(3, '0'),
                count: 5
            },
            '02': {
                hash: 'ghi',
                count: 4
            }
        };

        expect(aggregateToFirstLevel(twoLevelTrie)).toEqual(expected);
    });
});
