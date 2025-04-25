from django.core.management.base import BaseCommand
import yaml
from sync_option.models import Option, OptionGroup, OptionRelation, GroupRelationType
from django.utils import timezone
from typing import Dict, List, Tuple, Optional, TypedDict, Generator
from datetime import datetime


class YAMLFields(TypedDict, total=False):
    """Fields that can appear in the YAML data structure.
    Marked as total=False since not all fields are required in every record."""
    content_type: int
    object_id: int
    last_updated: datetime
    value: int
    change_id: int
    is_active: bool
    # Foreign key fields
    subsector: int
    sector: int
    suku: int
    munisipiu: int
    postu_administrativu: int  # For suku
    type: int  # For program activity type
    level: int  # For program activity level
    # Many-to-many fields
    activity: int  # For outputactivity
    output: int   # For outputactivity/outputobjective
    objective: int  # For outputobjective
    # Label-specific fields
    label: str
    lang: str
    option: int


class YAMLLabelFields(TypedDict):
    label: str
    lang: str
    option: int


class YAMLItem(TypedDict):
    """Represents a single item in the YAML data structure."""
    model: str
    pk: int
    fields: YAMLFields


def get_or_create_groups(yaml_data: List[YAMLItem]) -> Generator[OptionGroup, None, None]:
    """Create OptionGroups for each unique model in the YAML data."""
    groups: set[str] = set()
    for item in yaml_data:
        model_name = item['model'].split('.')[-1]
        if model_name.endswith('label'):
            continue
        if model_name in groups:
            continue
        groups.add(model_name)
        group, _ = OptionGroup.objects.get_or_create(
            name=model_name,
        )
        yield group


def create_relation_types() -> Dict[Tuple[str, str], GroupRelationType]:
    """
    Create or get GroupRelationType instances for all known relationships.
    Returns a dictionary mapping (from_group, to_group) tuples to GroupRelationType instances.
    """
    # Define all our relationships
    relationships = [
        {'from_group': 'subsector', 'to_group': 'sector', 'name': 'belongs_to', 'from_many': True, 'to_many': False},
        {'from_group': 'output', 'to_group': 'activity', 'name': 'belongs_to', 'from_many': True, 'to_many': True},
        {'from_group': 'output', 'to_group': 'subsector', 'name': 'belongs_to', 'from_many': True, 'to_many': False},
        {'from_group': 'output', 'to_group': 'objective', 'name': 'belongs_to', 'from_many': True, 'to_many': True},
        {'from_group': 'programactivity', 'to_group': 'programactivitylevel', 'name': 'belongs_to', 'from_many': True, 'to_many': False},
        {'from_group': 'programactivity', 'to_group': 'programactivitytype', 'name': 'belongs_to', 'from_many': True, 'to_many': False},
        {'from_group': 'postuadministrativu', 'to_group': 'munisipiu', 'name': 'belongs_to', 'from_many': True, 'to_many': False},
        {'from_group': 'suku', 'to_group': 'postuadministrativu', 'name': 'belongs_to', 'from_many': True, 'to_many': False},
        {'from_group': 'aldeia', 'to_group': 'suku', 'name': 'belongs_to', 'from_many': True, 'to_many': False},
    ]

    # Get all groups
    groups = {group.name: group for group in OptionGroup.objects.all()}
    relation_types = {}

    # Create or update each relationship type
    for rel in relationships:
        from_group = groups[rel['from_group']]
        to_group = groups[rel['to_group']]

        
        relation_type, _ = GroupRelationType.objects.get_or_create(
            name=rel['name'] ,
            from_group=from_group,
            to_group=to_group,
            defaults={
                'from_many': rel['from_many'],
                'to_many': rel['to_many'],
                'names': {'en': rel['name'].replace('_', ' ').title()},
            }
        )
        relation_types[(from_group.name, to_group.name)] = relation_type

    return relation_types


def get_or_create_relations(yaml_data: List[YAMLItem]) -> Generator[OptionRelation, None, None]:
    """Create OptionRelations for each unique model in the YAML data."""
    # Get all our relation types
    relation_types = create_relation_types()

    for item in yaml_data:
        fields = item["fields"]
        model_name = item['model']

        # Handle belongs_to relations
        if model_name == "ida_options.aldeia":
            if suku := fields.get('suku'):
                rel, _ = OptionRelation.objects.get_or_create(
                    from_option=Option.objects.get(group__name='aldeia', value=str(item['pk'])),
                    to_option=Option.objects.get(group__name='suku', value=str(suku)),
                    relation_type=relation_types[('aldeia', 'suku')],
                )
                yield rel

        elif model_name == "ida_options.suku":
            if postu := fields.get('postu_administrativu'):
                rel, _ = OptionRelation.objects.get_or_create(
                    from_option=Option.objects.get(group__name='suku', value=str(item['pk'])),
                    to_option=Option.objects.get(group__name='postuadministrativu', value=str(postu)),
                    relation_type=relation_types[('suku', 'postuadministrativu')],
                )
                yield rel

        elif model_name == "ida_options.subsector":
            if sector := fields.get('sector'):
                rel, _ = OptionRelation.objects.get_or_create(
                    from_option=Option.objects.get(group__name='subsector', value=str(item['pk'])),
                    to_option=Option.objects.get(group__name='sector', value=str(sector)),
                    relation_type=relation_types[('subsector', 'sector')],
                )
                yield rel
        
        elif model_name == "ida_options.postuadministrativu":
            if munisipiu := fields.get('munisipiu'):
                rel, _ = OptionRelation.objects.get_or_create(
                    from_option=Option.objects.get(group__name='postuadministrativu', value=str(item['pk'])),
                    to_option=Option.objects.get(group__name='munisipiu', value=str(munisipiu)),
                    relation_type=relation_types[('postuadministrativu', 'munisipiu')],
                )
                yield rel
        
        elif model_name == "ida_options.output":
            # Output is related to subsector
            if subsector := fields.get('subsector'):
                rel, _ = OptionRelation.objects.get_or_create(
                    from_option=Option.objects.get(group__name='output', value=str(item['pk'])),
                    to_option=Option.objects.get(group__name='subsector', value=str(subsector)),
                    relation_type=relation_types[('output', 'subsector')],
                )
                yield rel

        elif model_name == "ida_options.programactivity":
            # Related to `ProgramActivityType` and `ProgramActivityLevel`
            if program_activity_type := fields.get('type'):
                rel, _ = OptionRelation.objects.get_or_create(
                    from_option=Option.objects.get(group__name='programactivity', value=str(item['pk'])),
                    to_option=Option.objects.get(group__name='programactivitytype', value=str(program_activity_type)),
                    relation_type=relation_types[('programactivity', 'programactivitytype')],
                )
                yield rel
            if program_activity_level := fields.get('level'):
                rel, _ = OptionRelation.objects.get_or_create(
                    from_option=Option.objects.get(group__name='programactivity', value=str(item['pk'])),
                    to_option=Option.objects.get(group__name='programactivitylevel', value=str(program_activity_level)),
                    relation_type=relation_types[('programactivity', 'programactivitylevel')],
                )
                yield rel

        # Handle many-to-many relations
        elif model_name == "ida_options.outputobjective":
            if objective := fields.get('objective'):
                if output := fields.get('output'):
                    rel, _ = OptionRelation.objects.get_or_create(
                        from_option=Option.objects.get(group__name='output', value=str(output)),
                        to_option=Option.objects.get(group__name='objective', value=str(objective)),
                        relation_type=relation_types[('output', 'objective')],
                    )
                    yield rel

        elif model_name == "ida_options.outputactivity":
            if activity := fields.get('activity'):
                if output := fields.get('output'):
                    rel, _ = OptionRelation.objects.get_or_create(
                        from_option=Option.objects.get(group__name='output', value=str(output)),
                        to_option=Option.objects.get(group__name='activity', value=str(activity)),
                        relation_type=relation_types[('output', 'activity')],
                    )
                    yield rel


class Command(BaseCommand):
    help = 'Import options from YAML file generated by Django dumpdata'

    def add_arguments(self, parser):
        parser.add_argument('yaml_file', type=str, help='Path to the YAML file')

    def handle(self, *args, **options):
        yaml_file = options['yaml_file']
        # OptionGroup.objects.all().delete()
        # Option.objects.all().delete()
        # Read YAML file
        with open(yaml_file, 'r') as f:
            data: List[YAMLItem] = yaml.safe_load(f)
            groups = get_or_create_groups(data)
            # for group in groups:
            #     self.stdout.write(f"{'Created' if group else 'Updated'} OptionGroup: {group.name}")
        
            # options = get_or_create_options(data)
            # for option in options:
            #     self.stdout.write(f"{'Created' if option else 'Updated'} Option: {option.value} in {option.group.name}")
        
            relations = get_or_create_relations(data)
            for relation in relations:
                self.stdout.write(f"{'Created' if relation else 'Updated'} OptionRelation: {relation.from_option.value} -> {relation.to_option.value} ({relation.relation_type})")

        # # Group data by model
        # model_groups: Dict[str, List[YAMLItem]] = {}

        # for item in data:
        #     model_name = item['model'].split('.')[-1]  # Get last part of model name
        #     if model_name not in model_groups:
        #         model_groups[model_name] = []
        #     model_groups[model_name].append(item)
        
        # # Process each model type
        # for model_name, items in model_groups.items():
        #     if not model_name.endswith('label'):  # Skip label models
        #         group, results = process_model_group(model_name, items, model_groups)
                
        #         # Output results
        #         self.stdout.write(f"{'Created' if group else 'Updated'} OptionGroup: {model_name}")
        #         for option, created in results:
        #             self.stdout.write(f"{'Created' if created else 'Updated'} Option: {option.value} in {model_name}")
        
        # self.stdout.write(self.style.SUCCESS('Successfully imported options from YAML')) 