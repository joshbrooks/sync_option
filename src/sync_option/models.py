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
        return returns


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
    descriptions = models.JSONField(default=dict)  # Translatable descriptions
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['group', 'value'],
                name='unique_option_value_per_group'
            )
        ]

    def __str__(self):
        return f"{self.group.name}: {self.value}"

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
    Defines relationships between options (e.g., sector -> subsector)
    """
    from_option = models.ForeignKey(
        Option,
        on_delete=models.CASCADE,
        related_name='relations_from'
    )
    to_option = models.ForeignKey(
        Option,
        on_delete=models.CASCADE,
        related_name='relations_to'
    )
    relation_type = models.CharField(max_length=50)
    metadata = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['from_option', 'to_option', 'relation_type'],
                name='unique_option_relation'
            )
        ]

    def clean(self):
        """Validate the relation"""
        if self.from_option == self.to_option:
            raise ValidationError('An option cannot be related to itself')
        
        # Check for circular relationships
        if OptionRelation.objects.filter(
            from_option=self.to_option,
            to_option=self.from_option
        ).exists():
            raise ValidationError('Circular relationships are not allowed')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
