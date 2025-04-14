from django.contrib import admin
from .models import OptionGroup, Option, OptionRelation

@admin.register(OptionGroup)
class OptionGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_names', 'get_descriptions', 'last_updated')
    search_fields = ('name', 'names', 'descriptions')
    readonly_fields = ('last_updated',)

    def get_names(self, obj):
        return f"{obj.names.get('en', '')} / {obj.names.get('tet', '')}"
    get_names.short_description = 'Names'

    def get_descriptions(self, obj):
        return f"{obj.descriptions.get('en', '')} / {obj.descriptions.get('tet', '')}"
    get_descriptions.short_description = 'Descriptions'

@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('value', 'group', 'get_names', 'value_type', 'is_active', 'last_updated')
    list_filter = ('group', 'value_type', 'is_active')
    search_fields = ('value', 'names', 'descriptions')
    readonly_fields = ('last_updated',)

    def get_names(self, obj):
        return f"{obj.names.get('en', '')} / {obj.names.get('tet', '')}"
    get_names.short_description = 'Names'

@admin.register(OptionRelation)
class OptionRelationAdmin(admin.ModelAdmin):
    list_display = ('from_option', 'to_option', 'relation_type', 'last_updated')
    list_filter = ('relation_type',)
    search_fields = ('from_option__value', 'to_option__value')
    readonly_fields = ('last_updated',)
