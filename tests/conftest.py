import pytest
from datetime import timedelta
from django.utils import timezone
from factory import Faker, SubFactory, LazyAttribute
from factory.django import DjangoModelFactory
from ninja.testing import TestClient
from sync_option.models import OptionGroup, Option, OptionRelation
from sync_option.api import api
from faker import Faker as FakerLib
import os

faker = FakerLib()

# API Client Fixture
@pytest.fixture
def api_client():
    # Set environment variable to skip registry validation during tests
    os.environ["NINJA_SKIP_REGISTRY"] = "1"
    return TestClient(api)

# Factories
class OptionGroupFactory(DjangoModelFactory):
    class Meta:
        model = OptionGroup
    
    name = Faker('word')
    names = LazyAttribute(lambda _: {
        'en': faker.word(),
        'tet': faker.word()
    })
    descriptions = LazyAttribute(lambda _: {
        'en': faker.sentence(),
        'tet': faker.sentence()
    })

class OptionFactory(DjangoModelFactory):
    class Meta:
        model = Option
    
    group = SubFactory(OptionGroupFactory)
    value = Faker('pyint')
    value_type = 'integer'
    names = LazyAttribute(lambda _: {
        'en': faker.word(),
        'tet': faker.word()
    })
    descriptions = LazyAttribute(lambda _: {
        'en': faker.sentence(),
        'tet': faker.sentence()
    })
    is_active = True

class OptionRelationFactory(DjangoModelFactory):
    class Meta:
        model = OptionRelation
    
    from_option = SubFactory(OptionFactory)
    to_option = SubFactory(OptionFactory)
    relation_type = 'belongs_to'
    metadata = LazyAttribute(lambda _: {
        'created_by': faker.user_name(),
        'created_at': faker.date_time().isoformat()
    })

# Fixtures
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
def populated_database():
    """Creates a populated database with multiple groups and options"""
    groups = [OptionGroupFactory() for _ in range(3)]
    options = []
    for group in groups:
        options.extend([OptionFactory(group=group) for _ in range(5)])
    return {'groups': groups, 'options': options}

@pytest.fixture
def sync_data():
    """Creates test data for sync operations"""
    group = OptionGroupFactory()
    options = [OptionFactory(group=group) for _ in range(10)]
    # Create some relations between options
    for i in range(5):
        OptionRelationFactory(
            from_option=options[i],
            to_option=options[i+5],
            relation_type='belongs_to'
        )
    return {'group': group, 'options': options} 