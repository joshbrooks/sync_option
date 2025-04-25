# Options API Design

## Overview

This API design document outlines the endpoints for managing the generic options system. The API is built using Django Ninja, leveraging Pydantic for schema validation and OpenAPI documentation.

## Schemas

```python
from datetime import datetime
from typing import Dict, List, Optional, Union
from ninja import ModelSchema, Schema

class OptionGroupSchema(ModelSchema):
    class Meta:
        model = OptionGroup
        fields = ['name', 'names', 'descriptions', 'last_updated']

class OptionSchema(ModelSchema):
    typed_value: Union[str, int]
    
    class Meta:
        model = Option
        fields = ['value', 'value_type', 'names', 'descriptions', 'is_active', 'last_updated']
    
    @staticmethod
    def resolve_typed_value(obj):
        return obj.typed_value

class OptionRelationSchema(ModelSchema):
    class Meta:
        model = OptionRelation
        fields = ['from_option', 'to_option', 'metadata']

class SyncResponse(Schema):
    """Response for incremental sync requests"""
    updated_groups: List[OptionGroupSchema]
    updated_options: List[OptionSchema]
    deleted_options: List[int]  # List of option IDs that were deleted
    last_sync: datetime
```

## Endpoints

### Groups and Options

```python
@api.get("/options/groups")
def list_groups(request):
    """Get all option groups"""
    return OptionGroup.objects.all()

@api.get("/options/groups/{group_name}")
def get_group_options(request, group_name: str):
    """Get all options for a specific group"""
    return Option.objects.filter(group__name=group_name)

@api.get("/options/sync")
def sync_options(
    request,
    last_sync: datetime = None,
    groups: List[str] = Query(None)
):
    """
    Incremental sync endpoint for options
    - Returns only items updated since last_sync
    - Can filter by specific groups
    """
    queryset = Option.objects.all()
    groups_queryset = OptionGroup.objects.all()
    
    if groups:
        queryset = queryset.filter(group__name__in=groups)
        groups_queryset = groups_queryset.filter(name__in=groups)
    
    deleted = Option.objects.filter(
        is_active=False,
    ).values_list('id', flat=True)
    
    return SyncResponse(
        updated_groups=groups_queryset,
        updated_options=queryset.filter(is_active=True),
        deleted_options=list(deleted)
    )
```

### Relationships

```python
@api.get("/options/relations/{group_name}/{value}")
def get_related_options(
    request,
    group_name: str,
    value: str,
    relation_type: str = Query(None)
):
    """
    Get related options for a specific option
    Example: Get all subsectors for a sector
    """
    option = Option.objects.get(group__name=group_name, value=value)
    relations = option.relations_from
    
    if relation_type:
        relations = relations.filter(relation_type=relation_type)
    
    return relations.select_related('to_option')

@api.get("/options/relations/reverse/{group_name}/{value}")
def get_reverse_relations(
    request,
    group_name: str,
    value: str,
    relation_type: str = Query(None)
):
    """
    Get options that relate to this option
    Example: Get sector for a subsector
    """
    option = Option.objects.get(group__name=group_name, value=value)
    relations = option.relations_to
    
    if relation_type:
        relations = relations.filter(relation_type=relation_type)
    
    return relations.select_related('from_option')
```

## Performance Considerations

1. **Database Indexing**
   - Index on `last_updated` for efficient sync queries
   - Compound index on `group` and `value` for option lookups
   - Indexes on relationship fields for fast relation queries

2. **Query Optimization**
   - Use `select_related` for relationship queries
   - Batch updates in sync endpoint
   - Filter by `is_active` before returning results

3. **Response Size**
   - Incremental updates reduce payload size
   - Optional group filtering for selective sync
   - Pagination for large result sets (if needed)
