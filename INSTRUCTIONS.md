# Generic Options System Design

## Overview

This document outlines a more generic approach to handling options with translations, replacing the current system of many specific option models with a more flexible and maintainable solution.

## Database Schema

### OptionGroup Model

```python
class OptionGroup(models.Model):
    """
    Defines a category/type of options (e.g. 'sectors', 'activities', 'locations')
    """
    name = models.CharField(max_length=100, unique=True)  # Internal reference name
    names = models.JSONField(
        null=True, blank=True,
        help_text="Dictionary of language codes to display names, e.g. {'en': 'Sectors', 'tet': 'Setór'}"
    )
    descriptions = models.JSONField(
        null=True, blank=True,
        help_text="Dictionary of language codes to descriptions"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'option_groups'
        verbose_name = 'Option Group'
        verbose_name_plural = 'Option Groups'

    def __str__(self):
        return f"{self.name} ({self.names.get('en', 'Unnamed')})"
```

### Option Model

```python
class Option(models.Model):
    """
    Generic option entry that can belong to any group
    """
    VALUE_TYPES = [
        ('string', 'String'),
        ('integer', 'Integer'),
    ]

    group = models.ForeignKey(OptionGroup, on_delete=models.CASCADE)
    value = models.CharField(
        max_length=100,
        help_text="The value for this option - can be either string or integer based on value_type"
    )
    value_type = models.CharField(
        max_length=10,
        choices=VALUE_TYPES,
        help_text="Indicates whether the value should be treated as string or integer"
    )
    names = models.JSONField(
        null=True, blank=True,
        help_text="Dictionary of language codes to names, e.g. {'en': 'Name', 'tet': 'Naran'}"
    )
    descriptions = models.JSONField(
        null=True, blank=True,
        help_text="Optional dictionary of language codes to descriptions"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'options'
        constraints = [
            models.UniqueConstraint(
                fields=['group', 'value'],
                name='unique_option_value_per_group'
            )
        ]
        indexes = [
            models.Index(fields=['group', 'value']),
            models.Index(fields=['group', 'is_active'])
        ]

    def clean(self):
        """
        Validate that integer values are actually integers when value_type is 'integer'
        """
        if self.value_type == 'integer':
            try:
                int(self.value)
            except ValueError:
                raise ValidationError('Value must be a valid integer when value_type is "integer"')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def typed_value(self):
        """
        Return the value converted to its proper type
        """
        if self.value_type == 'integer':
            return int(self.value)
        return self.value
```

### OptionRelation Model

```python
class OptionRelation(models.Model):
    """
    Defines relationships between options, such as hierarchies or dependencies
    """
    from_option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='relations_from')
    to_option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='relations_to')
    relation_type = models.CharField(
        max_length=50,
        help_text="Type of relationship (e.g. 'parent', 'requires', 'belongs_to')"
    )
    metadata = models.JSONField(
        null=True, blank=True,
        help_text="Additional metadata about the relationship"
    )

    class Meta:
        db_table = 'option_relations'
        constraints = [
            models.UniqueConstraint(
                fields=['from_option', 'to_option', 'relation_type'],
                name='unique_option_relation'
            )
        ]
        indexes = [
            models.Index(fields=['from_option', 'relation_type']),
            models.Index(fields=['to_option', 'relation_type'])
        ]
```

## Example Usage

```python
# Creating an option group
sectors = OptionGroup.objects.create(
    name='sectors',
    names={'en': 'Sectors', 'tet': 'Setór'}
)

# Creating options with different value types
health_sector = Option.objects.create(
    group=sectors,
    value='1',
    value_type='integer',
    names={'en': 'Health', 'tet': 'Saúde'}
)

special_program = Option.objects.create(
    group=sectors,
    value='SP-001',
    value_type='string',
    names={'en': 'Special Program', 'tet': 'Programa Espesiál'}
)

# Creating relationships
OptionRelation.objects.create(
    from_option=special_program,
    to_option=health_sector,
    relation_type='belongs_to'
)

# Querying options
integer_options = Option.objects.filter(value_type='integer')
string_options = Option.objects.filter(value_type='string')

# Get typed value
print(health_sector.typed_value)  # Returns int(1)
print(special_program.typed_value)  # Returns "SP-001"
```

## Key Features

1. **Simplified Schema**
   - Single value field with type indicator
   - JSON fields for translations
   - Clean relationship model

2. **Flexible Value Types**
   - Support for both string and integer values
   - Type validation and conversion
   - Unique constraints per group

3. **Translation Support**
   - JSON fields store translations for all supported languages
   - No need for separate translation tables

## Migration Strategy

1. Create new tables
2. For each existing model:
   - Create appropriate OptionGroup
   - Migrate options with correct value type
   - Establish relationships
3. Validate data integrity
4. Update application code
5. Archive old tables

## Next Steps

1. Review and approve design
2. Create migration plan
3. Implement models
4. Write migration scripts
5. Update application code
6. Test thoroughly
7. Deploy changes
