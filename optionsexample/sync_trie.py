from datetime import datetime
from typing import Dict, List, Optional, Any, TypedDict
from dataclasses import dataclass

@dataclass
class Option:
    group: str
    value: str
    last_updated: datetime

class TrieNode(TypedDict, total=False):
    count: int
    children: Dict[str, 'TrieNode']

class LastUpdatedTrie:
    def __init__(self, options: List[Option] = None):
        self.trie: TrieNode = {}
        if options:
            self.build_trie(options)

    def build_trie(self, options: List[Option]) -> None:
        """Build the trie structure from a list of options."""
        for option in options:
            self._add_to_trie(option)

    def _add_to_trie(self, option: Option) -> None:
        """Add a single option to the trie."""
        date = option.last_updated
        path = [
            str(date.year),
            str(date.month),
            str(date.day),
            str(date.hour),
            str(date.minute),
            str(date.second)
        ]
        
        current = self.trie
        for key in path:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        if 'count' not in current:
            current['count'] = 0
        current['count'] += 1

    def find_missing_objects(self, all_objects: List[Option]) -> List[Option]:
        """Find objects that are missing from the trie."""
        missing: List[Option] = []
        timestamp_counts = {}

        # Count timestamps in all objects
        for obj in all_objects:
            timestamp = obj.last_updated.isoformat()
            timestamp_counts[timestamp] = timestamp_counts.get(timestamp, 0) + 1

        # Count timestamps in trie
        trie_timestamp_counts = {}
        self._count_timestamps(self.trie, trie_timestamp_counts)

        # Find missing objects
        for obj in all_objects:
            timestamp = obj.last_updated.isoformat()
            expected_count = timestamp_counts.get(timestamp, 0)
            actual_count = trie_timestamp_counts.get(timestamp, 0)

            if actual_count < expected_count:
                missing.append(obj)

        return missing

    def _count_timestamps(self, node: TrieNode, counts: Dict[str, int], current_path: List[int] = None) -> None:
        """Count timestamps in the trie structure."""
        if current_path is None:
            current_path = []

        if len(current_path) == 6 and 'count' in node:
            # We have a complete path (year, month, day, hour, minute, second)
            year, month, day, hour, minute, second = current_path
            date = datetime(year, month, day, hour, minute, second)
            timestamp = date.isoformat()
            counts[timestamp] = counts.get(timestamp, 0) + node['count']

        for key, child in node.items():
            if key != 'count':
                self._count_timestamps(child, counts, current_path + [int(key)])

    def debug_trie(self) -> None:
        """Print the trie structure for debugging."""
        def _print_node(node: TrieNode, level: int = 0) -> None:
            indent = '  ' * level
            for key, value in node.items():
                if key == 'count':
                    print(f"{indent}count: {value}")
                else:
                    print(f"{indent}{key}:")
                    _print_node(value, level + 1)

        _print_node(self.trie) 