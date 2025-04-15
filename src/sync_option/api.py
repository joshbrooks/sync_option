from datetime import datetime
from typing import List, Optional
from ninja import NinjaAPI, Schema, Router
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import OptionGroup, Option, OptionRelation

# Create a timezone-aware minimum datetime
MIN_DATETIME = timezone.make_aware(datetime.min)

# Create a router instead of a NinjaAPI instance
router = Router()

# Schemas
class OptionGroupSchema(Schema):
    name: str
    names: dict
    descriptions: dict
    last_updated: datetime

class OptionSchema(Schema):
    value: str
    value_type: str
    names: dict
    descriptions: dict
    is_active: bool
    last_updated: datetime
    typed_value: Optional[str] = None

    @staticmethod
    def resolve_typed_value(obj):
        return str(obj.typed_value)

class OptionRelationSchema(Schema):
    id: int
    from_option: OptionSchema
    to_option: OptionSchema
    relation_type: str
    metadata: dict
    last_updated: datetime

class SyncResponse(Schema):
    updated_groups: List[OptionGroupSchema]
    updated_options: List[OptionSchema]
    deleted_options: List[int]
    last_sync: datetime

# Endpoints
@router.get("/options/groups", response=List[OptionGroupSchema])
def list_groups(request):
    """Get all option groups"""
    return OptionGroup.objects.all()

@router.get("/options/groups/{group_name}", response=List[OptionSchema])
def get_group_options(request, group_name: str, last_sync: Optional[datetime] = None):
    """Get all options for a specific group"""
    group = get_object_or_404(OptionGroup, name=group_name)
    queryset = Option.objects.filter(group=group, is_active=True)
    
    if last_sync:
        queryset = queryset.filter(last_updated__gt=last_sync)
    
    return queryset

@router.get("/options/sync", response=SyncResponse)
def sync_options(
    request,
    last_sync: Optional[datetime] = None,
    groups: Optional[List[str]] = None
):
    """
    Incremental sync endpoint for options
    - Returns only items updated since last_sync
    - Can filter by specific groups
    """
    queryset = Option.objects.all()
    groups_queryset = OptionGroup.objects.all()
    
    if last_sync:
        queryset = queryset.filter(last_updated__gt=last_sync)
        groups_queryset = groups_queryset.filter(last_updated__gt=last_sync)
    
    if groups:
        queryset = queryset.filter(group__name__in=groups)
        groups_queryset = groups_queryset.filter(name__in=groups)
    
    deleted = Option.objects.filter(
        is_active=False,
        last_updated__gt=last_sync if last_sync else MIN_DATETIME
    ).values_list('id', flat=True)
    
    return {
        "updated_groups": groups_queryset,
        "updated_options": queryset.filter(is_active=True),
        "deleted_options": list(deleted),
        "last_sync": timezone.now()
    }

@router.get("/options/relations/{group_name}/{value}", response=List[OptionSchema])
def get_related_options(
    request,
    group_name: str,
    value: str,
    relation_type: Optional[str] = None
):
    """
    Get related options for a specific option
    Example: Get all subsectors for a sector
    """
    option = get_object_or_404(Option, group__name=group_name, value=value, is_active=True)
    relations = option.relations_from.all()
    
    if relation_type:
        relations = relations.filter(relation_type=relation_type)
    
    return [relation.to_option for relation in relations.select_related('to_option')]

@router.get("/options/relations/reverse/{group_name}/{value}", response=List[OptionSchema])
def get_reverse_relations(
    request,
    group_name: str,
    value: str,
    relation_type: Optional[str] = None
):
    """
    Get options that relate to this option
    Example: Get sector for a subsector
    """
    option = get_object_or_404(Option, group__name=group_name, value=value, is_active=True)
    relations = option.relations_to.all()
    
    if relation_type:
        relations = relations.filter(relation_type=relation_type)
    
    return [relation.from_option for relation in relations.select_related('from_option')]

@router.get("/options/relations", response=List[OptionRelationSchema])
def get_relations(request, last_sync: Optional[datetime] = None):
    """Get all option relations"""
    queryset = OptionRelation.objects.all()
    
    if last_sync:
        queryset = queryset.filter(last_updated__gt=last_sync)
    
    return queryset.select_related('from_option', 'to_option') 