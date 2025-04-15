from django.test import TestCase
from optionsexample.trie import compare_first_level, compare_second_level, FirstLevelNode, SecondLevelNode

class TrieComparisonTest(TestCase):
    def test_compare_first_level_matching(self):
        client_trie = {
            '01': {'hash': 'abc', 'count': 5},
            '02': {'hash': 'def', 'count': 3}
        }
        server_trie = {
            '01': {'hash': 'abc', 'count': 5},
            '02': {'hash': 'def', 'count': 3}
        }

        result = compare_first_level(client_trie, server_trie)
        self.assertEqual(result, {
            '01': 'match',
            '02': 'match'
        })

    def test_compare_first_level_different(self):
        client_trie = {
            '01': {'hash': 'abc', 'count': 5},
            '02': {'hash': 'def', 'count': 3}
        }
        server_trie = {
            '01': {'hash': 'abc', 'count': 4},  # Different count
            '02': {'hash': 'xyz', 'count': 3}   # Different hash
        }

        result = compare_first_level(client_trie, server_trie)
        self.assertEqual(result, {
            '01': 'diff',
            '02': 'diff'
        })

    def test_compare_first_level_missing(self):
        client_trie = {
            '01': {'hash': 'abc', 'count': 5}
        }
        server_trie = {
            '01': {'hash': 'abc', 'count': 5},
            '02': {'hash': 'def', 'count': 3}  # Extra node in server
        }

        result = compare_first_level(client_trie, server_trie)
        self.assertEqual(result, {
            '01': 'match',
            '02': 'diff'
        })

    def test_compare_second_level_matching(self):
        client_subtree = {
            '01/H9': {'hash': 'abc', 'count': 3},
            '01/H8': {'hash': 'def', 'count': 2}
        }
        server_subtree = {
            '01/H9': {'hash': 'abc', 'count': 3},
            '01/H8': {'hash': 'def', 'count': 2}
        }

        result = compare_second_level(client_subtree, server_subtree)
        self.assertEqual(result, {
            '01/H9': 'match',
            '01/H8': 'match'
        })

    def test_compare_second_level_different(self):
        client_subtree = {
            '01/H9': {'hash': 'abc', 'count': 3},
            '01/H8': {'hash': 'def', 'count': 2}
        }
        server_subtree = {
            '01/H9': {'hash': 'abc', 'count': 4},  # Different count
            '01/H8': {'hash': 'xyz', 'count': 2}   # Different hash
        }

        result = compare_second_level(client_subtree, server_subtree)
        self.assertEqual(result, {
            '01/H9': 'diff',
            '01/H8': 'diff'
        })

    def test_compare_second_level_missing(self):
        client_subtree = {
            '01/H9': {'hash': 'abc', 'count': 3}
        }
        server_subtree = {
            '01/H9': {'hash': 'abc', 'count': 3},
            '01/H8': {'hash': 'def', 'count': 2}  # Extra node in server
        }

        result = compare_second_level(client_subtree, server_subtree)
        self.assertEqual(result, {
            '01/H9': 'match',
            '01/H8': 'diff'
        }) 