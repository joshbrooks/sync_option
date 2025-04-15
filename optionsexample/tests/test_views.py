from django.test import TestCase, Client
from django.urls import reverse
import json

class SyncViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_compare_first_level_view(self):
        client_trie = {
            '01': {'hash': 'abc', 'count': 5},
            '02': {'hash': 'def', 'count': 3}
        }
        
        response = self.client.post(
            reverse('compare_first_level'),
            data=json.dumps(client_trie),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        # Since server_trie is empty in the view, all nodes should be 'diff'
        self.assertEqual(data, {
            '01': 'diff',
            '02': 'diff'
        })

    def test_compare_second_level_view(self):
        client_subtree = {
            '01/H9': {'hash': 'abc', 'count': 3},
            '01/H8': {'hash': 'def', 'count': 2}
        }
        
        response = self.client.post(
            reverse('compare_second_level', kwargs={'prefix': '01'}),
            data=json.dumps(client_subtree),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        # Since server_subtree is empty in the view, all nodes should be 'diff'
        self.assertEqual(data, {
            '01/H9': 'diff',
            '01/H8': 'diff'
        })

    def test_invalid_json(self):
        response = self.client.post(
            reverse('compare_first_level'),
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Invalid JSON') 