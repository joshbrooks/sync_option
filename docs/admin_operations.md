# Admin Interface Operations Guide

This guide explains how to perform common operations in the Django admin interface for the Sync Option application.

## Creating New Options

### 1. Creating a New Option Group

1. Navigate to "Option groups" in the admin interface
2. Click "Add option group"
3. Fill in the required fields:
   - Name: A unique identifier for the group
   - Names: JSON object with language codes as keys
     ```json
     {
       "en": "English Name",
       "tet": "Tetum Name"
     }
     ```
   - Descriptions: JSON object with language codes as keys
     ```json
     {
       "en": "English Description",
       "tet": "Tetum Description"
     }
     ```
4. Click "Save"

### 2. Creating a New Option

1. Navigate to "Options" in the admin interface
2. Click "Add option"
3. Fill in the required fields:
   - Value: A unique identifier within the group
   - Group: Select the group this option belongs to
   - Value type: Choose the type (string, integer, etc.)
   - Names: JSON object with language codes as keys
   - Descriptions: JSON object with language codes as keys
   - Is active: Check to make the option available
4. Click "Save"

### 3. Creating Option Relationships

1. Navigate to "Option relations" in the admin interface
2. Click "Add option relation"
3. Fill in the required fields:
   - From option: Select the child option
   - To option: Select the parent option
   - Relation type: Choose "belongs_to" for hierarchical relationships
   - Metadata: Optional JSON object for additional information
4. Click "Save"

## Modifying Existing Data

### 1. Editing an Option Group

1. Navigate to "Option groups"
2. Click on the group you want to edit
3. Modify any fields as needed
4. Click "Save"

### 2. Editing an Option

1. Navigate to "Options"
2. Click on the option you want to edit
3. Modify any fields as needed
4. Click "Save"

### 3. Editing a Relationship

1. Navigate to "Option relations"
2. Click on the relationship you want to edit
3. Modify any fields as needed
4. Click "Save"

## Common Use Cases

### 1. Adding a New District and Subdistricts

1. Create the district:
   - Group: "districts"
   - Value: "new_district"
   - Names: {"en": "New District", "tet": "Distritu Foun"}

2. Create subdistricts:
   - Group: "subdistricts"
   - Value: "new_subdistrict"
   - Names: {"en": "New Subdistrict", "tet": "Sub-distritu Foun"}

3. Create relationships:
   - From option: new_subdistrict
   - To option: new_district
   - Relation type: belongs_to

### 2. Adding a New Economic Sector and Subsectors

1. Create the sector:
   - Group: "sectors"
   - Value: "new_sector"
   - Names: {"en": "New Sector", "tet": "Setór Foun"}

2. Create subsectors:
   - Group: "subsectors"
   - Value: "new_subsector"
   - Names: {"en": "New Subsector", "tet": "Sub-setór Foun"}

3. Create relationships:
   - From option: new_subsector
   - To option: new_sector
   - Relation type: belongs_to

## Best Practices

1. **Naming Conventions**
   - Use lowercase for values
   - Use underscores for spaces
   - Keep names consistent across languages

2. **Relationship Management**
   - Always create parent options before child options
   - Use the "belongs_to" relation type for hierarchies
   - Verify relationships after creation

3. **Data Integrity**
   - Keep options active unless explicitly deactivating
   - Maintain consistent value types within groups

4. **Multilingual Support**
   - Always provide both English and Tetum translations
   - Keep translations consistent across related options
   - Use proper Unicode characters for Tetum text

## Troubleshooting

1. **Cannot Create Option**
   - Verify the value is unique within the group
   - Check that the group exists
   - Ensure all required fields are filled

2. **Cannot Create Relationship**
   - Verify both options exist
   - Check that the relationship doesn't already exist
   - Ensure the relationship type is valid

3. **Options Not Showing**
   - Check if the option is active
   - Verify the group is correct
   - Check for any filters that might be hiding the option

4. **Relationships Not Showing**
   - Verify both options exist
   - Check the relationship type
   - Look for any filters that might be hiding the relationship 