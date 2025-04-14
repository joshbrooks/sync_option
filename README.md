# Sync Option

A Django application for managing hierarchical options with synchronization capabilities.

## Features

- Hierarchical option management
- Multilingual support
- Option relationships
- Synchronization with external data sources
- RESTful API endpoints
- Django admin interface

## Installation

1. Install the package:
```bash
pip install sync-option
```

2. Add to your Django settings:
```python
INSTALLED_APPS = [
    ...
    'sync_option',
    ...
]
```

3. Run migrations:
```bash
python manage.py migrate
```

## Management Commands

The application provides two management commands for different purposes:

### sync_options

This command is used for synchronizing options from a JSON file in production environments.

```bash
# Basic usage
python manage.py sync_options path/to/options.json

# Dry run to see what would be done without making changes
python manage.py sync_options path/to/options.json --dry-run

# Force sync even if file was already processed
python manage.py sync_options path/to/options.json --force
```

Features:
- Reads and validates JSON data
- Uses database transactions for atomic operations
- Provides dry-run capability for testing
- Includes force sync option for reprocessing files
- Detailed error logging and reporting

### load_demo_data

This command is used for development and testing purposes to load a realistic dataset.

```bash
# Load demo data
python manage.py load_demo_data

# Remove existing data and load fresh demo data
python manage.py load_demo_data --remove-existing
```

The demo data includes:
- Economic sectors and subsectors
- Districts and subdistricts
- Relationships between entities
- Multilingual names and descriptions
- Realistic metadata

## API Endpoints

// ... existing code ...
