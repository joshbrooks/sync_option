from typing import Dict, Literal, TypedDict

class FirstLevelNode(TypedDict):
    hash: str
    count: int

ComparisonResult = Dict[str, Literal['match', 'diff']]

def compare_first_level(
    client_trie: Dict[str, FirstLevelNode],
    server_trie: Dict[str, FirstLevelNode]
) -> ComparisonResult:
    """
    Compare first level nodes between client and server tries.
    
    Args:
        client_trie: Dictionary of first level nodes from client
        server_trie: Dictionary of first level nodes from server
        
    Returns:
        Dictionary mapping node keys to 'match' or 'diff' status
    """
    result: ComparisonResult = {}

    # Check all client nodes against server
    for key, client_node in client_trie.items():
        server_node = server_trie.get(key)
        
        if not server_node:
            result[key] = 'diff'
            continue

        # Compare hash and count
        if (client_node['hash'] == server_node['hash'] and 
            client_node['count'] == server_node['count']):
            result[key] = 'match'
        else:
            result[key] = 'diff'

    # Check for server nodes not in client
    for key in server_trie:
        if key not in client_trie:
            result[key] = 'diff'

    return result 