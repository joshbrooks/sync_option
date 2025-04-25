from django.contrib import admin
from .models import OptionGroup, Option, OptionRelation, GroupRelationType
from django.db.models import Count

class FromOptionRelationInline(admin.TabularInline):
    model = OptionRelation
    fk_name = 'from_option'
    extra = 0
    readonly_fields = ('sync_id', 'to_option', 'relation_type', 'metadata')
    verbose_name = "Relation From This Option"
    verbose_name_plural = "Relations From This Option"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('to_option', 'to_option__group')


class ToOptionRelationInline(admin.TabularInline):
    model = OptionRelation
    fk_name = 'to_option'
    extra = 0
    readonly_fields = ('sync_id', 'from_option', 'relation_type', 'metadata')
    verbose_name = "Relation To This Option"
    verbose_name_plural = "Relations To This Option"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('from_option', 'from_option__group')


class OptionInline(admin.TabularInline):
    model = Option
    extra = 0
    readonly_fields = ('sync_id', 'names', 'descriptions', 'value', 'value_type', 'is_active')
    can_delete = False
    verbose_name = "Option in this group"
    verbose_name_plural = "Options in this group"

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        # Optimize the inline queryset with any foreign keys used in __str__ or display
        return super().get_queryset(request).select_related('group')


@admin.register(OptionGroup)
class OptionGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_names', 'get_descriptions', 'sync_id', 'get_options_count')
    search_fields = ('name', 'names', 'descriptions')
    inlines = [OptionInline]

    def get_names(self, obj):
        return f"{obj.names.get('en', '')} / {obj.names.get('tet', '')}"
    get_names.short_description = 'Names'

    def get_descriptions(self, obj):
        return f"{obj.descriptions.get('en', '')} / {obj.descriptions.get('tet', '')}"
    get_descriptions.short_description = 'Descriptions'

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('options', 'options__group').annotate(options_count=Count('options'))

    def get_options_count(self, obj):
        """Return the annotated options_count"""
        return obj.options_count
    get_options_count.short_description = 'Number of Options'

@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('value', 'group', 'get_names', 'value_type', 'is_active', 'sync_id')
    list_filter = ('group', 'value_type', 'is_active')
    search_fields = ('value', 'names', 'descriptions')
    inlines = [FromOptionRelationInline, ToOptionRelationInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('group').prefetch_related('relations_from', 'relations_to')

    def get_names(self, obj):
        return f"{obj.names.get('en', '')} / {obj.names.get('tet', '')}"
    get_names.short_description = 'Names'


@admin.register(OptionRelation)
class OptionRelationAdmin(admin.ModelAdmin):
    list_display = ('from_option', 'relation_type', 'to_option')
    list_filter = ('relation_type', 'from_option__group')
    search_fields = ('from_option__value', 'to_option__value')
    readonly_fields = ('sync_id','from_option','to_option','relation_type', 'metadata')


    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'from_option', 'from_option__group',
            'to_option', 'to_option__group'
        )

@admin.register(GroupRelationType)
class GroupRelationTypeAdmin(admin.ModelAdmin):
    list_display = ('from_group', 'name', 'to_group', 'from_many', 'to_many')

