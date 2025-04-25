from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q, OuterRef, Subquery, Max
from uuid import UUID
from typing import Iterable
from django.urls import reverse
from uuid_utils import uuid7 as uuid7_

# The uuid7 from `uuid_utils` is not compatible with the uuid7 from `uuid`
# so we need to cast to the normal python
def uuid7():
    return UUID(uuid7_().hex)

class SyncModel(models.Model):
    """Abstract base model that adds sync functionality using UUIDv7"""
    sync_id = models.UUIDField(default=uuid7, editable=False, help_text="UUIDv7 for sync tracking")

    @classmethod
    def max_sync_id(cls, objects: models.Manager['SyncModel'] | models.QuerySet['SyncModel']):
        return (objects or cls.objects).aggregate(Max('sync_id'))['sync_id__max']

    def save(self, *args, **kwargs):
        sync_id = uuid7()
        if self.sync_id:
            # Keep everything except last 12 chars from new UUID, and last 12 from existing
            self.sync_id = UUID(hex=uuid7().hex[:-12] + self.sync_id.hex[-12:])
        else:
            self.sync_id = sync_id
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


from pydantic import BaseModel
class ManifestEntry(BaseModel):
    url: str
    etag: UUID | None = None


class OptionGroup(SyncModel):
    """
    A group of related options (e.g., 'sectors', 'countries', etc.)
    """
    name = models.CharField(max_length=100, unique=True)
    names = models.JSONField(default=dict)  # Translatable display names
    descriptions = models.JSONField(default=dict)  # Translatable descriptions

    def __str__(self):
        return self.name

    @property
    def options_url(self):
        return reverse("api-1.0.0:get_group_options", kwargs={"group_name": self.name})

    @property
    def relations_url(self):
        return reverse("api-1.0.0:get_relations", kwargs={"group_name": self.name})   

    @classmethod
    def with_latest_changes(cls):
        """
        Returns a queryset of OptionGroups annotated with their latest change sync_ids.
        This is more efficient than calling latest_change on each group individually.
        """
        # Subquery for latest option change
        latest_option_change = Option.objects.filter(
            group=OuterRef('pk'),
            is_active=True
        ).order_by('-sync_id').values('sync_id')[:1]

        # Subquery for latest relation change
        latest_relation_change = OptionRelation.objects.filter(
            Q(from_option__group=OuterRef('pk')) | 
            Q(to_option__group=OuterRef('pk'))
        ).order_by('-sync_id').values('sync_id')[:1]

        # Return annotated queryset
        return cls.objects.annotate(
            latest_option_change=Subquery(latest_option_change),
            latest_relation_change=Subquery(latest_relation_change)
        )

    @classmethod
    def get_manifest(cls) -> list[ManifestEntry]:
        """
        Get the manifest of the options URL
        """
        groups = cls.with_latest_changes()
        returns = []
        returns.append(ManifestEntry(url=reverse("api-1.0.0:list_groups"), etag=groups.aggregate(Max('sync_id'))['sync_id__max']))
        for group in groups:
            returns.append(ManifestEntry(url=group.options_url, etag=group.latest_option_change))
            returns.append(ManifestEntry(url=group.relations_url, etag=group.latest_relation_change))
        returns.append(ManifestEntry(url=reverse("api-1.0.0:get_relations"), etag=GroupRelationType.max_sync_id(GroupRelationType.objects.all())))
        return returns


class GroupRelationType(SyncModel):
    """
    Defines the types of relationships that can exist between options in different groups.
    For example: 'belongs_to', 'contains', 'references', etc.
    
    Cardinality is controlled by two boolean fields:
    - from_many: If True, multiple options from from_group can relate to the same to_group option
    - to_many: If True, one from_group option can relate to multiple to_group options
    
    Examples:
    - Suku belongs to Subdistrict: from_many=True, to_many=False
      (many sukus belong to one subdistrict)
    - Activity has Outputs: from_many=True, to_many=True
      (many activities can have many outputs)
    """
    name = models.CharField(max_length=50)
    from_group = models.ForeignKey(OptionGroup, on_delete=models.CASCADE, related_name='relation_types_from')
    to_group = models.ForeignKey(OptionGroup, on_delete=models.CASCADE, related_name='relation_types_to')
    from_many = models.BooleanField(
        default=False,
        help_text="If True, multiple options from from_group can relate to the same to_group option"
    )
    to_many = models.BooleanField(
        default=False,
        help_text="If True, one from_group option can relate to multiple to_group options"
    )
    names = models.JSONField(default=dict)  # Translatable display names
    descriptions = models.JSONField(default=dict, null=True, blank=True)  # Translatable descriptions
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['from_group', 'to_group', 'name'],
                name='unique_group_relation_type'
            )
        ]

    def __str__(self):
        cardinality = f"{'many' if self.from_many else 'one'}-to-{'many' if self.to_many else 'one'}"
        return f"{self.from_group.name} -> {self.name} ({cardinality}) -> {self.to_group.name}"

    def clean(self):
        """Validate that we don't have conflicting relationship types between the same groups"""
        existing = GroupRelationType.objects.filter(
            from_group=self.from_group,
            to_group=self.to_group,
            is_active=True
        ).exclude(pk=self.pk)

        if existing.exists() and not (self.from_many and self.to_many):
            # If this is not a many-to-many relationship, we can't have multiple active relation types
            # between the same groups unless all of them are many-to-many
            conflicting = existing.exclude(from_many=True, to_many=True)
            if conflicting.exists():
                raise ValidationError(
                    f'Cannot have multiple restricted cardinality relations from {self.from_group.name} to {self.to_group.name}'
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Option(SyncModel):
    """
    An individual option within a group
    """
    VALUE_TYPES = [
        ('string', 'String'),
        ('integer', 'Integer'),
    ]

    group = models.ForeignKey(OptionGroup, on_delete=models.CASCADE, related_name='options')
    value = models.CharField(max_length=255)
    value_type = models.CharField(max_length=10, choices=VALUE_TYPES)
    names = models.JSONField(default=dict)  # Translatable display names
    descriptions = models.JSONField(default=dict, null=True, blank=True)  # Translatable descriptions
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['group', 'value'],
                name='unique_option_value_per_group'
            )
        ]

    @property
    def name_display(self, codes: list[str] = ['en', 'tet']):
        names = [self.names.get(code) for code in codes if code in self.names]
        if len(names) == 1:
            return names[0]
        return ' / '.join(names)

    def __str__(self):
        return f"{self.group.name} {self.value} {self.name_display}"

    @property
    def typed_value(self):
        """Returns the value converted to its appropriate type"""
        if self.value_type == 'integer':
            return int(self.value)
        return self.value

    def clean(self):
        """Validate the value matches the specified type"""
        if self.value_type == 'integer':
            try:
                int(self.value)
            except (TypeError, ValueError):
                raise ValidationError({'value': 'Value must be a valid integer'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Implement soft delete"""
        self.is_active = False
        self.save()  # This will also update the group's sync_id


class OptionRelation(SyncModel):
    """
    Defines relationships between options based on the relationship types defined between their groups
    """
    from_option = models.ForeignKey(
        Option,
        on_delete=models.CASCADE,
        related_name='relations_from',
    )
    to_option = models.ForeignKey(
        Option,
        on_delete=models.CASCADE,
        related_name='relations_to'
    )
    relation_type = models.ForeignKey(
        GroupRelationType,
        on_delete=models.CASCADE,
        related_name='option_relations',
    )
    metadata = models.JSONField(default=dict, null=True, blank=True)


    def clean(self):
        """Validate the relation"""
        if self.from_option == self.to_option:
            raise ValidationError('An option cannot be related to itself')
        
        # Check for circular relationships
        if OptionRelation.objects.filter(
            from_option=self.to_option,
            to_option=self.from_option,
            relation_type=self.relation_type
        ).exists():
            raise ValidationError('Circular relationships are not allowed')

        # Validate that the relation type matches the groups of the options
        if self.relation_type.from_group_id != self.from_option.group_id:
            raise ValidationError('The relation type\'s from_group must match the from_option\'s group')
        if self.relation_type.to_group_id != self.to_option.group_id:
            raise ValidationError('The relation type\'s to_group must match the to_option\'s group')

        # Validate cardinality constraints
        if not self.relation_type.from_many:
            # If from_many is False, each to_option can only be related to one from_option
            if OptionRelation.objects.filter(
                to_option=self.to_option,
                relation_type=self.relation_type
            ).exclude(pk=self.pk).exists():
                raise ValidationError(
                    f'This {self.relation_type.name} relationship allows only one {self.relation_type.from_group.name} '
                    f'per {self.relation_type.to_group.name}'
                )

        if not self.relation_type.to_many:
            # If to_many is False, each from_option can only be related to one to_option
            if OptionRelation.objects.filter(
                from_option=self.from_option,
                relation_type=self.relation_type
            ).exclude(pk=self.pk).exists():
                raise ValidationError(
                    f'This {self.relation_type.name} relationship allows only one {self.relation_type.to_group.name} '
                    f'per {self.relation_type.from_group.name}'
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
