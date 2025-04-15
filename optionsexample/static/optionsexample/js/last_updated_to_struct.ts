/*
In this file, we will convert the last_updated value to a structured nested object
*/


interface Option {
    group: string;
    value: string;
    last_updated: string;
}

interface TrieNode {
    [key: number]: TrieNode | number;
}

export class LastUpdatedTrie {
    private trie: TrieNode = {};

    constructor(private options: Option[]) { }

    public buildTrie(): void {
        // Reset trie
        this.trie = {};

        // Build trie for each option
        for (const option of this.options) {
            this.addToTrie(option);
        }
    }

    private addToTrie(option: Option): void {
        const date = new Date(option.last_updated);

        // Check if date is valid
        if (isNaN(date.getTime())) {
            return;
        }

        // Extract date components as UTC numbers
        const components = [
            date.getUTCFullYear(),
            date.getUTCMonth() + 1,
            date.getUTCDate(),
            date.getUTCHours(),
            date.getUTCMinutes(),
            date.getUTCSeconds()
        ];

        let current = this.trie;

        // Traverse the trie, creating nodes as needed
        for (const component of components) {
            if (!current[component]) {
                current[component] = {};
            }
            current = current[component] as TrieNode;
        }

        // At the leaf node, increment the count
        if (typeof current['count'] === 'number') {
            current['count']++;
        } else {
            current['count'] = 1;
        }
    }

    public getCountByDate(date: Date): number {
        // Extract date components as UTC numbers
        const components = [
            date.getUTCFullYear(),
            date.getUTCMonth() + 1,
            date.getUTCDate(),
            date.getUTCHours(),
            date.getUTCMinutes(),
            date.getUTCSeconds()
        ];

        let current = this.trie;

        // Traverse the trie
        for (const component of components) {
            if (!current[component]) {
                return 0;
            }
            current = current[component] as TrieNode;
        }

        return current['count'] as number || 0;
    }

    public debugTrie(): void {
        console.log(JSON.stringify(this.trie, null, 2));
    }

    public getCountByPrefix(prefix: number[]): number {
        let current = this.trie;

        // Traverse the trie up to the prefix
        for (const component of prefix) {
            const componentNum = Number(component);
            if (!current[componentNum]) {
                return 0;
            }
            current = current[componentNum] as TrieNode;
        }

        // Sum all counts under this prefix
        return this.sumCounts(current);
    }

    private sumCounts(node: TrieNode): number {
        let sum = 0;

        // Add count at current node if it exists
        if (typeof node['count'] === 'number') {
            sum += node['count'];
        }

        // Recursively sum counts from all child nodes
        for (const key in node) {
            if (key !== 'count' && typeof node[key] === 'object') {
                sum += this.sumCounts(node[key] as TrieNode);
            }
        }

        return sum;
    }

    public findMissingObjects(allObjects: Option[]): Option[] {
        const missing: Option[] = [];
        const timestampCounts = new Map<string, number>();

        // First, count how many times each timestamp appears in allObjects
        for (const obj of allObjects) {
            const date = new Date(obj.last_updated);
            if (isNaN(date.getTime())) continue;

            const timestamp = date.toISOString();
            timestampCounts.set(timestamp, (timestampCounts.get(timestamp) || 0) + 1);
        }

        // Then, count how many times each timestamp appears in our trie
        const trieTimestampCounts = new Map<string, number>();
        this.countTimestamps(this.trie, trieTimestampCounts);

        // Finally, find objects with timestamps that appear fewer times in the trie
        for (const obj of allObjects) {
            const date = new Date(obj.last_updated);
            if (isNaN(date.getTime())) continue;

            const timestamp = date.toISOString();
            const expectedCount = timestampCounts.get(timestamp) || 0;
            const actualCount = trieTimestampCounts.get(timestamp) || 0;

            if (actualCount < expectedCount) {
                missing.push(obj);
            }
        }

        return missing;
    }

    private countTimestamps(node: TrieNode, counts: Map<string, number>, currentPath: number[] = []): void {
        if (currentPath.length === 6 && typeof node['count'] === 'number') {
            // Only count when we have a complete path (year, month, day, hour, minute, second)
            const [year, month, day, hour, minute, second] = currentPath;
            const date = new Date(Date.UTC(year, month - 1, day, hour, minute, second));
            const timestamp = date.toISOString();

            counts.set(timestamp, (counts.get(timestamp) || 0) + node['count']);
        }

        for (const key in node) {
            if (key !== 'count' && typeof node[key] === 'object') {
                this.countTimestamps(node[key] as TrieNode, counts, [...currentPath, Number(key)]);
            }
        }
    }
}