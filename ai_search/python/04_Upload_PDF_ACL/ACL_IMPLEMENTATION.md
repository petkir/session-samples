# ACL Implementation Summary

## Overview

This implementation adds Access Control Lists (ACL) support to the PDF upload system, allowing documents to be restricted to specific Microsoft Entra groups. This feature enables document-level security and integrates with existing organizational security structures.

## Key Changes Made

### 1. Configuration Updates (`config.py`)

- **Updated API version**: Changed from `2023-11-01` to `2025-05-01-preview` to support ACL features
- **Added ACL settings**:
  - `entra_group_id`: The Object ID of the Entra group that should have access to documents
  - `enable_permission_filter`: Boolean flag to enable/disable permission-based filtering

### 2. Search Index Schema (`search_uploader.py`)

- **Added ACL field**: Added `groupIds` field with `PermissionFilter.GROUP_IDS` type
- **Enabled permission filtering**: Set `permission_filter_option = SearchIndexPermissionFilterOption.ENABLED`
- **Updated imports**: Added `PermissionFilter` and `SearchIndexPermissionFilterOption` imports

### 3. Document Upload Process

- **ACL metadata**: Each document now includes a `groupIds` field with the specified Entra Group ID
- **Helper method**: Added `_get_document_acl_groups()` method to determine which groups should have access
- **Enhanced logging**: Added ACL-related logging information

### 4. Documentation and Examples

- **Updated README**: Added comprehensive ACL documentation
- **Created ACL example**: New `acl_example.py` file demonstrating ACL usage
- **Updated .env.example**: Added ACL configuration variables

## Implementation Details

### ACL Field Structure

```python
# In the search index schema
SearchField(
    name="groupIds", 
    type=SearchFieldDataType.Collection(SearchFieldDataType.String),
    filterable=True,
    permission_filter=PermissionFilter.GROUP_IDS
)
```

### Document Structure

```python
# Each uploaded document now includes:
{
    "id": "document-id",
    "content": "document content",
    "embedding": [0.1, 0.2, ...],
    # ... other fields ...
    "groupIds": ["12345678-1234-1234-1234-123456789012"]  # Entra Group ID
}
```

### Index Configuration

```python
# Index created with permission filtering enabled
index = SearchIndex(
    name=index_name,
    fields=fields,
    vector_search=vector_search,
    permission_filter_option=SearchIndexPermissionFilterOption.ENABLED
)
```

## Security Benefits

1. **Document-Level Security**: Each document can be restricted to specific groups
2. **Automatic Filtering**: Search results are automatically filtered based on user permissions
3. **Organizational Integration**: Leverages existing Entra ID group structures
4. **Query-Time Enforcement**: Permissions are enforced at query time, not just upload time

## Usage Instructions

### 1. Configure ACL Settings

Add to your `.env` file:

```env
# Use the preview API version
AZURE_SEARCH_API_VERSION=2025-05-01-preview

# Enable permission filtering
ENABLE_PERMISSION_FILTER=true

# Set your Entra Group ID
ENTRA_GROUP_ID=12345678-1234-1234-1234-123456789012
```

### 2. Get Your Entra Group ID

1. Go to Azure Portal → Microsoft Entra ID → Groups
2. Find your desired group
3. Copy the Object ID
4. Use this ID in the `ENTRA_GROUP_ID` setting

### 3. Upload Documents

```bash
# Upload with ACL restrictions
python main.py

# Or use the ACL example
python acl_example.py
```

### 4. Query with ACL (for application integration)

```http
POST https://your-search-service.search.windows.net/indexes/pdf-documents-acl/docs/search?api-version=2025-05-01-preview
Content-Type: application/json
x-ms-query-source-authorization: Bearer <user-token>

{
  "search": "your query here",
  "top": 10
}
```

## Important Notes

### API Version Requirement

- **Must use**: `2025-05-01-preview` API version
- **Feature Status**: Preview feature, not recommended for production

### Limitations

- Maximum 32 group IDs per document
- Maximum 5 unique `rbacScope` values across all documents
- Existing fields cannot be converted to permission filter fields
- Preview feature limitations apply

### Token Requirements

When querying with ACL enabled, you must:
1. Provide a valid Entra ID authentication token
2. Use the `x-ms-query-source-authorization` header
3. Ensure the user is a member of the appropriate group

## Testing ACL Functionality

1. **Upload documents** with ACL enabled
2. **Query as authorized user** - should see documents
3. **Query as unauthorized user** - should see no results
4. **Check logs** for ACL-related information

## Security Considerations

- **Group Management**: Regularly review group memberships
- **Principle of Least Privilege**: Only grant access to users who need it
- **Audit Trail**: Monitor document access patterns
- **Token Security**: Ensure proper handling of authentication tokens
- **Test Thoroughly**: Verify ACL restrictions work as expected

## Migration from Non-ACL Version

If you have existing documents without ACL:
1. **Create new index** with ACL fields
2. **Re-upload documents** with ACL metadata
3. **Update application** to use new API version
4. **Test permissions** thoroughly

## Support and Resources

- [Azure AI Search ACL Documentation](https://learn.microsoft.com/en-us/azure/search/search-index-access-control-lists-and-rbac-push-api)
- [Azure AI Search Python SDK](https://docs.microsoft.com/en-us/python/api/overview/azure/search-documents-readme)
- [Microsoft Entra ID Groups](https://learn.microsoft.com/en-us/azure/active-directory/fundamentals/active-directory-groups-create-azure-portal)

## Example Implementation

See `acl_example.py` for a complete example of using the ACL feature, including:
- Configuration validation
- Document upload with ACL
- Logging and monitoring
- Security best practices
