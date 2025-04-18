import pytest
from django.utils import timezone
from django.db import connection
from django.test.utils import CaptureQueriesContext
from sync_option.models import Option, OptionGroup
from tests.conftest import OptionGroupFactory, OptionFactory
from urllib.parse import quote

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

def test_sync_with_group_filter(api_client, sync_data):
    """Test sync endpoint with group filter"""
    # Clean up existing data
    Option.objects.all().delete()
    OptionGroup.objects.all().delete()
    
    # Create options in different groups
    group1 = OptionGroupFactory()
    group2 = OptionGroupFactory()
    options1 = [OptionFactory(group=group1) for _ in range(2)]
    options2 = [OptionFactory(group=group2) for _ in range(2)]
    
    # Sync with group filter - pass as comma-separated list
    response = api_client.get(f"/options/sync?groups={group1.name},{group2.name}")
    assert response.status_code == 200
    data = response.json()
    
    # Verify options from specified groups are returned
    assert len(data['updated_options']) == 4  # Both groups
    group1_values = [str(o.value) for o in options1]
    group2_values = [str(o.value) for o in options2]
    all_values = group1_values + group2_values
    assert all(opt['value'] in all_values for opt in data['updated_options'])
    assert len(data['updated_groups']) == 2
    group_names = {g['name'] for g in data['updated_groups']}
    assert group1.name in group_names
    assert group2.name in group_names

def test_get_related_options(api_client, related_options):
    """Test GET /options/relations/{group_name}/{value} endpoint"""
    parent = related_options['parent']
    children = related_options['children']
    relations = related_options['relations']
    
    # Verify the relationships were created
    assert len(relations) == 3
    assert all(r.from_option in children for r in relations)  # Children are from_option
    assert all(r.to_option == parent for r in relations)  # Parent is to_option
    
    # Test getting related options using reverse_relations endpoint
    # since our relationships are child -> parent
    response = api_client.get(
        f"/options/relations/reverse/{parent.group.name}/{parent.value}"
    )
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 3  # Should have all three children
    
    # Verify relationship data
    child_values = {opt['value'] for opt in data}
    expected_values = {str(child.value) for child in children}
    assert child_values == expected_values

def test_get_reverse_relations(api_client, related_options):
    """Test GET /options/relations/{group_name}/{value} endpoint for finding parent"""
    child = related_options['children'][0]
    parent = related_options['parent']
    
    # Since our relationships are child -> parent (from -> to)
    # we should use the regular relations endpoint to find the parent
    response = api_client.get(
        f"/options/relations/{child.group.name}/{child.value}"
    )
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1  # Should have one parent
    assert data[0]['value'] == str(parent.value)

def test_get_relations_with_type(api_client, related_options):
    """Test relationship filtering by type"""
    parent = related_options['parent']
    
    response = api_client.get(
        f"/options/relations/reverse/{parent.group.name}/{parent.value}?relation_type=belongs_to"
    )
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 3
    
    response = api_client.get(
        f"/options/relations/reverse/{parent.group.name}/{parent.value}?relation_type=invalid_type"
    )
    assert response.status_code == 200
    assert len(response.json()) == 0

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
    with django_assert_num_queries(1):  # Only one query needed for listing groups
        response = api_client.get("/options/groups")
        assert response.status_code == 200
    
    # Test sync endpoint performance
    with django_assert_num_queries(3):  # Queries for deleted options, groups, and options
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