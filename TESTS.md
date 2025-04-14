# Options System Test Strategy

## Overview

This document outlines the testing strategy for the options system backend, using pytest and factory-boy. We'll focus on:
- Model factories for test data generation
- Test fixtures for common scenarios
- Test cases for model validation and relationships
- Test cases for data integrity and constraints

## Test Setup

```python
import pytest
from factory import Factory, Faker, SubFactory, LazyAttribute
from factory.django import DjangoModelFactory

# Factories
class OptionGroupFactory(DjangoModelFactory):
    class Meta:
        model = 'sync_project.OptionGroup'
    
    name = Faker('word')
    names = LazyAttribute(lambda _: {'en': Faker('word'), 'tet': Faker('word')})
    descriptions = LazyAttribute(lambda _: {'en': Faker('sentence'), 'tet': Faker('sentence')})

class OptionFactory(DjangoModelFactory):
    class Meta:
        model = 'sync_project.Option'
    
    group = SubFactory(OptionGroupFactory)
    value = Faker('pyint')
    value_type = 'integer'
    names = LazyAttribute(lambda _: {'en': Faker('word'), 'tet': Faker('word')})
    descriptions = LazyAttribute(lambda _: {'en': Faker('sentence'), 'tet': Faker('sentence')})
    is_active = True

class OptionRelationFactory(DjangoModelFactory):
    class Meta:
        model = 'sync_project.OptionRelation'
    
    from_option = SubFactory(OptionFactory)
    to_option = SubFactory(OptionFactory)
    relation_type = 'belongs_to'
    metadata = LazyAttribute(lambda _: {})

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
```

## Test Cases

### Model Validation

```python
def test_option_value_type_validation():
    """Test that options validate their value types correctly"""
    # Test integer values
    option = OptionFactory(value_type='integer', value='123')
    assert option.typed_value == 123
    
    # Test string values
    option = OptionFactory(value_type='string', value='abc')
    assert option.typed_value == 'abc'
    
    # Test invalid integer
    with pytest.raises(ValidationError):
        OptionFactory(value_type='integer', value='not_an_int')
    
    # Test value type choices
    with pytest.raises(ValidationError):
        OptionFactory(value_type='invalid_type')

def test_option_unique_constraints():
    """Test that options maintain uniqueness constraints"""
    group = OptionGroupFactory()
    OptionFactory(group=group, value='1')
    
    # Test duplicate value in same group
    with pytest.raises(IntegrityError):
        OptionFactory(group=group, value='1')
    
    # Test same value in different group (should succeed)
    other_group = OptionGroupFactory()
    OptionFactory(group=other_group, value='1')

def test_option_translations():
    """Test option translation handling"""
    option = OptionFactory(
        names={'en': 'English', 'tet': 'Tetum'},
        descriptions={'en': 'English Desc', 'tet': 'Tetum Desc'}
    )
    
    assert option.names['en'] == 'English'
    assert option.names['tet'] == 'Tetum'
    assert option.descriptions['en'] == 'English Desc'
    assert option.descriptions['tet'] == 'Tetum Desc'
```

### Relationship Testing

```python
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
    with pytest.raises(ValidationError):
        OptionRelationFactory(
            from_option=option,
            to_option=option
        )
    
    # Test circular relationships
    opt1 = OptionFactory()
    opt2 = OptionFactory()
    OptionRelationFactory(from_option=opt1, to_option=opt2)
    
    with pytest.raises(ValidationError):
        OptionRelationFactory(from_option=opt2, to_option=opt1)
```

### Soft Delete Testing

```python
def test_option_soft_delete():
    """Test soft delete functionality"""
    option = OptionFactory()
    assert option.is_active
    
    # Test soft delete
    option.delete()
    option.refresh_from_db()
    assert not option.is_active
    
    # Test that soft-deleted options are excluded from default queryset
    assert not Option.objects.filter(id=option.id).exists()
    assert Option.objects.no_prefetch().filter(id=option.id).exists()

def test_cascade_soft_delete():
    """Test that relationships are maintained with soft deletes"""
    related = related_options()
    parent = related['parent']
    
    # Soft delete parent
    parent.delete()
    
    # Check that relationships are maintained
    for child in related['children']:
        assert child.relations_from.no_prefetch().exists()
        
    # Check that relationships are hidden in default queryset
    for child in related['children']:
        assert not child.relations_from.exists()
```

### Performance Testing

```python
@pytest.mark.django_db
def test_query_performance():
    """Test query performance with large datasets"""
    # Create test data
    groups = [OptionGroupFactory() for _ in range(10)]
    options = []
    for group in groups:
        options.extend([
            OptionFactory(group=group)
            for _ in range(100)
        ])
    
    # Test bulk operations
    with django.db.connection.execute_wrapper(QueryCountWrapper()) as wrapper:
        Option.objects.filter(group=groups[0]).update(is_active=False)
        assert wrapper.queries_count == 1
    
    # Test prefetch_related performance
    with django.db.connection.execute_wrapper(QueryCountWrapper()) as wrapper:
        list(Option.objects.prefetch_related('relations_from'))
        assert wrapper.queries_count <= 2
```

## Test Categories

1. **Unit Tests**
   - Model validation
   - Field constraints
   - Type conversion
   - Translation handling

2. **Integration Tests**
   - Relationship integrity
   - Cascading operations
   - Soft delete behavior
   - Query optimization

3. **Performance Tests**
   - Query count assertions
   - Bulk operation efficiency
   - Memory usage with large datasets
   - Index effectiveness

4. **Edge Cases**
   - Invalid data handling
   - Circular relationships
   - Concurrent modifications
   - Transaction rollbacks

## Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/test_models.py
pytest tests/test_relationships.py
pytest tests/test_performance.py

# Run with coverage
pytest --cov=sync_project tests/

# Generate coverage report
pytest --cov=sync_project --cov-report=html tests/
```

## CI Integration

```yaml
test:
  script:
    - pip install -r requirements-test.txt
    - pytest --cov=sync_project --cov-report=xml tests/
    - coverage report --fail-under=90
  artifacts:
    reports:
      coverage_report: coverage.xml
``` 