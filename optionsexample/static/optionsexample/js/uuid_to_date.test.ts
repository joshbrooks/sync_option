import { describe, it, expect } from 'vitest';
import { extractDateFromUuid, uuidToTriePath } from './uuid_to_date';

describe('UUIDv7 Date Extraction', () => {
    it('should extract correct date components from UUIDv7', () => {
        // UUIDv7 generated on August 3, 2024 at 12:09:56 UTC
        const uuid = "01911825-7f8f-74c9-85bc-55b034e2af75";

        const date = extractDateFromUuid(uuid);

        expect(date.getUTCFullYear()).toBe(2024);
        expect(date.getUTCMonth() + 1).toBe(8); // getUTCMonth returns 0-11
        expect(date.getUTCDate()).toBe(3);
        expect(date.getUTCHours()).toBe(12);
        expect(date.getUTCMinutes()).toBe(9);
        expect(date.getUTCSeconds()).toBe(56);
        expect(date.getUTCMilliseconds()).toBe(0);
    });

    it('should create correct trie path from UUIDv7', () => {
        const uuid = "01911825-7f8f-74c9-85bc-55b034e2af75";

        const path = uuidToTriePath(uuid);

        expect(path).toEqual([2024, 8, 3, 12, 9, 56]);
    });
}); 