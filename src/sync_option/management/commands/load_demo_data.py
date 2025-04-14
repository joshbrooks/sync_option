from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
from sync_option.models import OptionGroup, Option, OptionRelation

class Command(BaseCommand):
    help = 'Loads demonstration data with realistic options and relationships'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before loading demo data',
        )

    def handle(self, *args, **options):
        faker = Faker()
        
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            OptionRelation.objects.all().delete()
            Option.objects.all().delete()
            OptionGroup.objects.all().delete()
        
        # Create core option groups
        self.stdout.write('Creating option groups...')
        groups = {
            'sectors': OptionGroup.objects.create(
                name='sectors',
                names={'en': 'Economic Sectors', 'tet': 'Setór Ekonomiku'},
                descriptions={'en': 'Main economic sectors', 'tet': 'Setór ekonomiku prinsipál'}
            ),
            'subsectors': OptionGroup.objects.create(
                name='subsectors',
                names={'en': 'Economic Subsectors', 'tet': 'Sub-setór Ekonomiku'},
                descriptions={'en': 'Economic subsectors', 'tet': 'Sub-setór ekonomiku'}
            ),
            'districts': OptionGroup.objects.create(
                name='districts',
                names={'en': 'Districts', 'tet': 'Distritu'},
                descriptions={'en': 'Administrative districts', 'tet': 'Distritu administrativu'}
            ),
            'subdistricts': OptionGroup.objects.create(
                name='subdistricts',
                names={'en': 'Subdistricts', 'tet': 'Sub-distritu'},
                descriptions={'en': 'Administrative subdistricts', 'tet': 'Sub-distritu administrativu'}
            )
        }

        # Create sectors
        self.stdout.write('Creating sectors...')
        sectors = []
        sector_names = [
            ('Agriculture', 'Agrikultura'),
            ('Manufacturing', 'Industria'),
            ('Services', 'Servisu'),
            ('Construction', 'Konstrusaun'),
            ('Mining', 'Minerasaun')
        ]
        for en_name, tet_name in sector_names:
            sector = Option.objects.create(
                group=groups['sectors'],
                value=en_name.lower().replace(' ', '_'),
                value_type='string',
                names={'en': en_name, 'tet': tet_name},
                descriptions={'en': f'{en_name} sector', 'tet': f'Setór {tet_name.lower()}'},
                is_active=True
            )
            sectors.append(sector)

        # Create subsectors
        self.stdout.write('Creating subsectors...')
        subsectors = []
        subsector_data = [
            ('Agriculture', [
                ('Crop Production', 'Produksaun Ai-han'),
                ('Livestock', 'Hakiak'),
                ('Fisheries', 'Peskas')
            ]),
            ('Manufacturing', [
                ('Food Processing', 'Prosesamentu Ai-han'),
                ('Textiles', 'Téxtil'),
                ('Electronics', 'Eletrónika')
            ]),
            ('Services', [
                ('Education', 'Edukasaun'),
                ('Healthcare', 'Saúde'),
                ('Tourism', 'Turizmu')
            ]),
            ('Construction', [
                ('Residential', 'Rezidensial'),
                ('Commercial', 'Komersial'),
                ('Infrastructure', 'Infraestrutura')
            ]),
            ('Mining', [
                ('Oil & Gas', 'Minyak no Gas'),
                ('Minerals', 'Minerál'),
                ('Quarrying', 'Pedreira')
            ])
        ]

        for sector_name, subsector_list in subsector_data:
            sector = next(s for s in sectors if s.names['en'] == sector_name)
            for en_name, tet_name in subsector_list:
                subsector = Option.objects.create(
                    group=groups['subsectors'],
                    value=en_name.lower().replace(' ', '_'),
                    value_type='string',
                    names={'en': en_name, 'tet': tet_name},
                    descriptions={'en': f'{en_name} subsector', 'tet': f'Sub-setór {tet_name.lower()}'},
                    is_active=True
                )
                subsectors.append(subsector)
                # Create relationship
                OptionRelation.objects.create(
                    from_option=subsector,
                    to_option=sector,
                    relation_type='belongs_to',
                    metadata={'created_by': 'demo', 'created_at': timezone.now().isoformat()}
                )

        # Create districts
        self.stdout.write('Creating districts...')
        districts = []
        district_names = [
            ('Dili', 'Dili'),
            ('Baucau', 'Baukau'),
            ('Ermera', 'Ermera'),
            ('Liquica', 'Likisá'),
            ('Manatuto', 'Manatutu')
        ]
        for en_name, tet_name in district_names:
            district = Option.objects.create(
                group=groups['districts'],
                value=en_name.lower(),
                value_type='string',
                names={'en': en_name, 'tet': tet_name},
                descriptions={'en': f'{en_name} District', 'tet': f'Distritu {tet_name}'},
                is_active=True
            )
            districts.append(district)

        # Create subdistricts
        self.stdout.write('Creating subdistricts...')
        subdistrict_data = [
            ('Dili', [
                ('Nain Feto', 'Nain Feto'),
                ('Vera Cruz', 'Vera Cruz'),
                ('Dom Aleixo', 'Dom Aleixo')
            ]),
            ('Baucau', [
                ('Baucau Vila', 'Baukau Vila'),
                ('Vemasse', 'Vemasse'),
                ('Laga', 'Laga')
            ]),
            ('Ermera', [
                ('Ermera Vila', 'Ermera Vila'),
                ('Railaco', 'Railako'),
                ('Letefoho', 'Letefoho')
            ]),
            ('Liquica', [
                ('Liquica Vila', 'Likisá Vila'),
                ('Bazartete', 'Bazartete'),
                ('Maubara', 'Maubara')
            ]),
            ('Manatuto', [
                ('Manatuto Vila', 'Manatutu Vila'),
                ('Laclo', 'Laklo'),
                ('Laclubar', 'Laklubar')
            ])
        ]

        for district_name, subdistrict_list in subdistrict_data:
            district = next(d for d in districts if d.names['en'] == district_name)
            for en_name, tet_name in subdistrict_list:
                subdistrict = Option.objects.create(
                    group=groups['subdistricts'],
                    value=en_name.lower().replace(' ', '_'),
                    value_type='string',
                    names={'en': en_name, 'tet': tet_name},
                    descriptions={'en': f'{en_name} Subdistrict', 'tet': f'Sub-distritu {tet_name}'},
                    is_active=True
                )
                # Create relationship
                OptionRelation.objects.create(
                    from_option=subdistrict,
                    to_option=district,
                    relation_type='belongs_to',
                    metadata={'created_by': 'demo', 'created_at': timezone.now().isoformat()}
                )

        self.stdout.write(self.style.SUCCESS('Successfully loaded demonstration data')) 