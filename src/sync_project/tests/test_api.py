import pytest
from django.utils import timezone
from django.db import connection
from django.test.utils import CaptureQueriesContext
from ..models import Option

pytestmark = pytest.mark.django_db

def test_list_groups(api_client, populated_database):
    """Test GET /options/groups endpoint"""
    response = api_client.get("/options/groups")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) >= 1
    
    group = data[0]
    assert 'name' in group
    assert 'names' in group
    assert 'descriptions' in group
    assert 'last_updated' in group

def test_get_group_options(api_client, populated_database):
    """Test GET /options/groups/{group_name} endpoint"""
    group = populated_database['group']
    
    response = api_client.get(f"/options/groups/{group.name}")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) > 0
    
    option = data[0]
    assert 'value' in option
    assert 'value_type' in option
    assert 'names' in option
    assert 'descriptions' in option
    assert 'is_active' in option

def test_get_nonexistent_group(api_client):
    """Test getting options for a non-existent group"""
    response = api_client.get("/options/groups/nonexistent")
    assert response.status_code == 404

def test_sync_all(api_client, sync_data):
    """Test GET /options/sync endpoint with no parameters"""
    response = api_client.get("/options/sync")
    assert response.status_code == 200
    
    data = response.json()
    assert 'updated_groups' in data
    assert 'updated_options' in data
    assert 'deleted_options' in data
    assert 'last_sync' in data

def test_sync_with_timestamp(api_client, sync_data):
    """Test incremental sync with timestamp"""
    sync_point = sync_data['sync_point'].isoformat()
    response = api_client.get(f"/options/sync?last_sync={sync_point}")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data['updated_groups']) == 1  # Only new_group
    assert len(data['updated_options']) == 2  # Only new_options
    assert len(data['deleted_options']) == 1  # The soft-deleted option
    
    # Verify only new data is included
    group_names = [g['name'] for g in data['updated_groups']]
    assert sync_data['new_group'].name in group_names
    assert sync_data['old_group'].name not in group_names

def test_sync_with_group_filter(api_client, sync_data):
    """Test sync with group filtering"""
    group = sync_data['new_group']
    response = api_client.get(f"/options/sync?groups={group.name}")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data['updated_groups']) == 1
    assert data['updated_groups'][0]['name'] == group.name
    
    # Verify only options from the specified group are included
    option_groups = {opt['group'] for opt in data['updated_options']}
    assert len(option_groups) == 1
    assert group.name in option_groups

def test_get_related_options(api_client, related_options):
    """Test GET /options/relations/{group_name}/{value} endpoint"""
    parent = related_options['parent']
    children = related_options['children']
    
    response = api_client.get(
        f"/options/relations/{parent.group.name}/{parent.value}"
    )
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 3  # Should have all three children
    
    # Verify relationship data
    child_values = {opt['value'] for opt in data}
    expected_values = {str(child.value) for child in children}
    assert child_values == expected_values

def test_get_reverse_relations(api_client, related_options):
    """Test GET /options/relations/reverse/{group_name}/{value} endpoint"""
    child = related_options['children'][0]
    parent = related_options['parent']
    
    response = api_client.get(
        f"/options/relations/reverse/{child.group.name}/{child.value}"
    )
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1  # Should have one parent
    assert data[0]['value'] == str(parent.value)

def test_get_relations_with_type(api_client, related_options):
    """Test relationship filtering by type"""
    parent = related_options['parent']
    
    response = api_client.get(
        f"/options/relations/{parent.group.name}/{parent.value}?relation_type=belongs_to"
    )
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 3
    
    response = api_client.get(
        f"/options/relations/{parent.group.name}/{parent.value}?relation_type=invalid_type"
    )
    assert response.status_code == 200
    assert len(response.json()) == 0

def test_invalid_sync_timestamp(api_client):
    """Test sync endpoint with invalid timestamp"""
    response = api_client.get("/options/sync?last_sync=invalid")
    assert response.status_code == 422  # Validation error

def test_nonexistent_relation_option(api_client, populated_database):
    """Test relations endpoint with non-existent option"""
    group = populated_database['group']
    response = api_client.get(f"/options/relations/{group.name}/99999")
    assert response.status_code == 404

def test_concurrent_sync_requests(api_client, sync_data):
    """Test handling of concurrent sync requests"""
    import threading
    
    results = []
    def make_request():
        response = api_client.get("/options/sync")
        results.append(response.status_code)
    
    threads = [threading.Thread(target=make_request) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    assert all(code == 200 for code in results)

def test_api_performance(api_client, django_assert_num_queries):
    """Test API endpoint performance"""
    # Prepare large dataset
    groups = [OptionGroupFactory() for _ in range(5)]
    for group in groups:
        [OptionFactory(group=group) for _ in range(20)]
    
    # Test groups listing performance
    with django_assert_num_queries(2):  # Should use only 2 queries
        response = api_client.get("/options/groups")
        assert response.status_code == 200
    
    # Test sync endpoint performance
    with django_assert_num_queries(4):  # Queries for groups, options, and deleted options
        response = api_client.get("/options/sync")
        assert response.status_code == 200

def test_api_response_format(api_client, option):
    """Test API response format and data types"""
    response = api_client.get(f"/options/groups/{option.group.name}")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) > 0
    
    option_data = data[0]
    assert isinstance(option_data['value'], str)
    assert isinstance(option_data['names'], dict)
    assert isinstance(option_data['descriptions'], dict)
    assert isinstance(option_data['is_active'], bool)
    assert isinstance(option_data['typed_value'], str) 