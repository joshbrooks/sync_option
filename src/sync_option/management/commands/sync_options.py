from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from sync_option.models import Option, OptionGroup, OptionRelation
from sync_option.sync import sync_options
import json
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Synchronize options from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the JSON file containing options')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
        parser.add_argument('--force', action='store_true', help='Force sync even if the file has already been processed')

    def handle(self, *args, **options):
        file_path = options['file_path']
        dry_run = options['dry_run']
        force = options['force']

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'File not found: {file_path}'))
            return
        except json.JSONDecodeError:
            self.stderr.write(self.style.ERROR(f'Invalid JSON in file: {file_path}'))
            return

        try:
            with transaction.atomic():
                sync_options(data, dry_run=dry_run, force=force)
                
                if dry_run:
                    self.stdout.write(self.style.SUCCESS('Dry run completed successfully'))
                else:
                    self.stdout.write(self.style.SUCCESS('Sync completed successfully'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error during sync: {str(e)}'))
            logger.exception('Error during sync') 