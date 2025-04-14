import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from sync_option.models import Option, OptionRelation
from tests.conftest import OptionFactory, OptionGroupFactory

pytestmark = pytest.mark.django_db

def test_option_value_type_validation():
    """Test that options validate their value types correctly"""
    # Test integer values
    option = Option(value_type='integer', value='123')
    option.clean()  # Should not raise
    assert option.typed_value == 123
    
    # Test string values
    option = Option(value_type='string', value='abc')
    option.clean()  # Should not raise
    assert option.typed_value == 'abc'
    
    # Test invalid integer
    option = Option(value_type='integer', value='not_an_int')
    with pytest.raises(ValidationError):
        option.clean()
    
    # Test value type choices
    option = Option(value_type='invalid_type', value='123')
    with pytest.raises(ValidationError):
        option.full_clean()

def test_option_unique_constraints(option_group):
    """Test that options maintain uniqueness constraints"""
    Option.objects.create(
        group=option_group,
        value='1',
        value_type='integer',
        names={'en': 'test', 'tet': 'test'},
        descriptions={'en': 'test', 'tet': 'test'}
    )
    
    # Test duplicate value in same group
    with pytest.raises(IntegrityError):
        Option.objects.create(
            group=option_group,
            value='1',
            value_type='integer',
            names={'en': 'test', 'tet': 'test'},
            descriptions={'en': 'test', 'tet': 'test'}
        )
    
    # Test same value in different group (should succeed)
    other_group = OptionGroupFactory()
    Option.objects.create(
        group=other_group,
        value='1',
        value_type='integer',
        names={'en': 'test', 'tet': 'test'},
        descriptions={'en': 'test', 'tet': 'test'}
    )

def test_option_translations(option):
    """Test option translation handling"""
    option.names = {'en': 'English', 'tet': 'Tetum'}
    option.descriptions = {'en': 'English Desc', 'tet': 'Tetum Desc'}
    option.save()
    
    option.refresh_from_db()
    assert option.names['en'] == 'English'
    assert option.names['tet'] == 'Tetum'
    assert option.descriptions['en'] == 'English Desc'
    assert option.descriptions['tet'] == 'Tetum Desc'

def test_option_relationships(related_options):
    """Test relationship querying and integrity"""
    parent = related_options['parent']
    children = related_options['children']
    
    # Test forward relationships
    child_relations = children[0].relations_from.all()
    assert len(child_relations) == 1
    assert child_relations[0].to_option == parent
    
    # Test reverse relationships
    parent_relations = parent.relations_to.all()
    assert len(parent_relations) == 3
    
    # Test relationship type filtering
    belongs_to = parent.relations_to.filter(relation_type='belongs_to')
    assert len(belongs_to) == 3

def test_relationship_constraints():
    """Test relationship validation and constraints"""
    # Test self-referential relationship
    option = OptionFactory()
    relation = OptionRelation(from_option=option, to_option=option)
    with pytest.raises(ValidationError):
        relation.clean()
    
    # Test circular relationships
    opt1 = OptionFactory()
    opt2 = OptionFactory()
    OptionRelation.objects.create(from_option=opt1, to_option=opt2)
    
    relation = OptionRelation(from_option=opt2, to_option=opt1)
    with pytest.raises(ValidationError):
        relation.clean()

def test_option_soft_delete(option):
    """Test soft delete functionality"""
    assert option.is_active
    
    # Test soft delete
    option.delete()
    option.refresh_from_db()
    assert not option.is_active
    
    # Test that soft-deleted options are excluded from default queryset
    assert not Option.objects.filter(id=option.id, is_active=True).exists()
    assert Option.objects.filter(id=option.id, is_active=False).exists()

def test_cascade_soft_delete(related_options):
    """Test that relationships are maintained with soft deletes"""
    parent = related_options['parent']
    children = related_options['children']
    
    # Soft delete parent
    parent.delete()
    parent.refresh_from_db()
    
    # Check that relationships are maintained
    for child in children:
        assert child.relations_from.filter(to_option=parent).exists()
        
    # Check that parent is not in active options
    assert not Option.objects.filter(id=parent.id, is_active=True).exists()
    assert Option.objects.filter(id=parent.id, is_active=False).exists()

def test_last_updated_tracking(option_group, option):
    """Test that last_updated is properly maintained"""
    original_group_updated = option_group.last_updated
    original_option_updated = option.last_updated
    
    # Wait a moment to ensure timestamp difference
    import time
    time.sleep(0.001)
    
    # Update objects
    option_group.name = 'new_name'
    option_group.save()
    
    option.value = 123  # Use integer value instead of string
    option.save()
    
    # Check timestamps were updated
    assert option_group.last_updated > original_group_updated
    assert option.last_updated > original_option_updated 