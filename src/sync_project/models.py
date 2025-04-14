from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class OptionGroup(models.Model):
    """
    A group of related options (e.g., 'sectors', 'countries', etc.)
    """
    name = models.CharField(max_length=100, unique=True)
    names = models.JSONField(default=dict)  # Translatable display names
    descriptions = models.JSONField(default=dict)  # Translatable descriptions
    last_updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.last_updated = timezone.now()
        super().save(*args, **kwargs)


class Option(models.Model):
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
    last_updated = models.DateTimeField(default=timezone.now)

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
        self.last_updated = timezone.now()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Implement soft delete"""
        self.is_active = False
        self.last_updated = timezone.now()
        self.save()


class OptionRelation(models.Model):
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
    last_updated = models.DateTimeField(default=timezone.now)

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
        self.last_updated = timezone.now()
        super().save(*args, **kwargs)
