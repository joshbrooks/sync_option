# Exploring Demo Data Tutorial

This tutorial will guide you through exploring the demo data that was loaded using the `load_demo_data` management command. We'll use the Django admin interface to examine the hierarchical structure of options and their relationships.

## Prerequisites

- Demo data loaded (using `python manage.py load_demo_data`)
- Superuser account created (username: josh, password: joshjosh)
- Django development server running
- Cypress installed (for generating screenshots)

### Installing Cypress

To install Cypress and its dependencies:

1. Install Cypress using npm:
   ```bash
   npm install cypress --save-dev
   ```

2. Initialize Cypress in your project:
   ```bash
   npx cypress open
   ```

This will:
- Install Cypress and its dependencies
- Create a `cypress` directory in your project
- Set up the basic configuration

![Admin Login](docs/screenshots/01_admin_login.png)

## Accessing the Admin Interface

1. Start the Django development server:
   ```bash
   python manage.py runserver
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8000/admin/
   ```

3. Log in using the superuser credentials:
   - Username: josh
   - Password: joshjosh

## Exploring the Data Structure

### 1. Option Groups

The demo data includes four main option groups:
- Sectors (Economic Sectors)
- Subsectors (Economic Subsectors)
- Districts
- Subdistricts

![Option Groups](docs/screenshots/02_option_groups.png)

To view these:
1. Click on "Option groups" in the admin interface
2. You'll see a list of all groups with their names in both English and Tetum
3. Use the search box to find specific groups
4. Click on any group to view its details

![Option Group Detail](docs/screenshots/05_option_group_detail.png)

### 2. Options

Each group contains multiple options. To explore them:
1. Click on "Options" in the admin interface
2. Use the filters on the right to view options by:
   - Group (Sectors, Subsectors, etc.)
   - Value type
   - Active status

![Options List](docs/screenshots/03_options_list.png)

3. The list shows:
   - Option value
   - Group it belongs to
   - Names in English and Tetum
   - Value type
   - Active status
   - Last updated timestamp

![Option Detail](docs/screenshots/06_option_detail.png)

### 3. Option Relations

The relationships between options form a hierarchy:
1. Click on "Option relations" in the admin interface
2. You'll see how options are connected:
   - Subdistricts belong to districts
   - Subsectors belong to main sectors

![Option Relations](docs/screenshots/04_option_relations.png)

3. Use the filters to view specific types of relationships
4. The list shows:
   - From option (child)
   - To option (parent)
   - Relation type
   - Last updated timestamp

![Option Relation Detail](docs/screenshots/07_option_relation_detail.png)

## Example Hierarchies

### District Hierarchy
- Dili (District)
  - Dom Aleixo (Subdistrict)
  - Nain Feto (Subdistrict)
  - Vera Cruz (Subdistrict)

### Economic Sector Hierarchy
- Agriculture (Sector)
  - Crop Production (Subsector)
  - Fisheries (Subsector)
  - Livestock (Subsector)

## Tips for Exploration

1. **Search Functionality**
   - Use the search box to find specific options
   - Search works on names, values, and descriptions

2. **Filtering**
   - Use the filters on the right to narrow down options
   - Filter by group, value type, or active status

3. **Viewing Details**
   - Click on any option to see its full details
   - View all relationships for an option
   - See multilingual names and descriptions

4. **Understanding Relationships**
   - The "belongs_to" relationship type indicates hierarchy
   - Child options (from_option) belong to parent options (to_option)

## Next Steps

After exploring the demo data, you can:
1. Create new options and groups
2. Modify existing options
3. Create new relationships
4. Use the API endpoints to interact with the data programmatically

Would you like to explore any specific aspect of the demo data in more detail? 