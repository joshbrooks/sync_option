import pytest
from datetime import timedelta
from django.utils import timezone
from factory import Factory, Faker, SubFactory, LazyAttribute
from factory.django import DjangoModelFactory
from ninja.testing import TestClient
from ..models import OptionGroup, Option, OptionRelation
from ..api import api

# Factories
class OptionGroupFactory(DjangoModelFactory):
    class Meta:
        model = OptionGroup
    
    name = Faker('word')
    names = LazyAttribute(lambda _: {'en': Faker('word').generate(), 'tet': Faker('word').generate()})
    descriptions = LazyAttribute(lambda _: {'en': Faker('sentence').generate(), 'tet': Faker('sentence').generate()})

class OptionFactory(DjangoModelFactory):
    class Meta:
        model = Option
    
    group = SubFactory(OptionGroupFactory)
    value = Faker('pyint')
    value_type = 'integer'
    names = LazyAttribute(lambda _: {'en': Faker('word').generate(), 'tet': Faker('word').generate()})
    descriptions = LazyAttribute(lambda _: {'en': Faker('sentence').generate(), 'tet': Faker('sentence').generate()})
    is_active = True

class OptionRelationFactory(DjangoModelFactory):
    class Meta:
        model = OptionRelation
    
    from_option = SubFactory(OptionFactory)
    to_option = SubFactory(OptionFactory)
    relation_type = 'belongs_to'
    metadata = LazyAttribute(lambda _: {})

# Fixtures
@pytest.fixture
def api_client():
    return TestClient(api)

@pytest.fixture
def option_group():
    return OptionGroupFactory()

@pytest.fixture
def option(option_group):
    return OptionFactory(group=option_group)

@pytest.fixture
def related_options():
    """Creates a set of related options for testing relationships"""
    group = OptionGroupFactory()
    parent = OptionFactory(group=group)
    children = [OptionFactory(group=group) for _ in range(3)]
    relations = [
        OptionRelationFactory(
            from_option=child,
            to_option=parent,
            relation_type='belongs_to'
        ) for child in children
    ]
    return {'parent': parent, 'children': children, 'relations': relations}

@pytest.fixture
def populated_database(option_group, related_options):
    """Creates a populated database with groups, options and relationships"""
    return {
        'group': option_group,
        'related': related_options,
        'timestamp': timezone.now()
    }

@pytest.fixture
def sync_data(populated_database):
    """Creates test data for sync endpoint testing"""
    # Create some data before the sync point
    old_group = OptionGroupFactory(last_updated=timezone.now() - timedelta(hours=2))
    old_options = [OptionFactory(group=old_group) for _ in range(3)]
    
    sync_point = timezone.now() - timedelta(hours=1)
    
    # Create some data after the sync point
    new_group = OptionGroupFactory(last_updated=timezone.now())
    new_options = [OptionFactory(group=new_group) for _ in range(2)]
    
    # Soft delete one old option
    old_options[0].delete()
    
    return {
        'sync_point': sync_point,
        'old_group': old_group,
        'new_group': new_group,
        'old_options': old_options,
        'new_options': new_options,
        'deleted_option': old_options[0]
    } 