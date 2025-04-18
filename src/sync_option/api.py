from typing import List, Optional
from ninja import ModelSchema, Router, Field
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import HttpRequest, HttpResponse

from .models import OptionGroup, Option, OptionRelation, ManifestEntry

router = Router()



@router.get("/manifest", response=list[ManifestEntry])
def get_manifest(request: HttpRequest, response: HttpResponse):
    """
    Get the manifest of the options URL
    """
    return OptionGroup.get_manifest()


class OptionGroupSchema(ModelSchema):

    class Meta:
        model = OptionGroup
        fields = ['name', 'names', 'descriptions', "sync_id"]

class OptionSchema(ModelSchema):
    typed_value: Optional[str] = None

    class Meta:
        model = Option
        fields = ['value', 'value_type', 'names', 'descriptions', 'is_active', "sync_id"]

    @staticmethod
    def resolve_typed_value(obj):
        return str(obj.typed_value)

class OptionRelationSchema(ModelSchema):
    from_node: str = Field(None)
    from_group: str = Field(None)
    to_node: str = Field(None)
    to_group: str = Field(None)

    class Meta:
        model = OptionRelation
        fields = ['relation_type', 'sync_id']

    @staticmethod
    def resolve_from_group(obj: OptionRelation) -> str:
        return obj.from_option.group.name

    @staticmethod
    def resolve_from_node(obj: OptionRelation) -> str:
        return obj.from_option.sync_id.hex[-12:]

    @staticmethod
    def resolve_to_node(obj: OptionRelation) -> str:
        return obj.to_option.sync_id.hex[-12:]

    @staticmethod
    def resolve_to_group(obj: OptionRelation) -> str:
        return obj.to_option.group.name


@router.get("/options/groups", response=List[OptionGroupSchema])
def list_groups(request, response:HttpResponse):
    """Get all option groups"""
    queryset = OptionGroup.objects.all()
    response.headers["Etag"] = OptionGroup.max_sync_id(queryset)
    return queryset

@router.get("/options/groups/{group_name}", response=List[OptionSchema])
def get_group_options(request: HttpRequest, response: HttpResponse, group_name: str):
    """Get all options for a specific group"""
    queryset = Option.objects.filter(group=get_object_or_404(OptionGroup, name=group_name))
    response.headers["Etag"] = Option.max_sync_id(queryset)
    return queryset

@router.get("/options/relations/{group_name}", response=List[OptionRelationSchema])
def get_relations(request: HttpRequest, response: HttpResponse, group_name: str):
    """Get all option relations"""
    group = get_object_or_404(OptionGroup, name=group_name)

    queryset = OptionRelation.objects.filter(
        Q(to_option__group=group) | Q(from_option__group=group)
    ).select_related('from_option', 'to_option', 'from_option__group', 'to_option__group')
    response.headers["Etag"] = OptionRelation.max_sync_id(
        queryset
    )
    return queryset