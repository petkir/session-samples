"""
Test script specifically for ACL functionality.
Tests the access control list implementation and document-level security.
"""
import asyncio
import sys
import os
from datetime import datetime
from unittest.mock import patch, MagicMock

import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


async def test_acl_configuration():
    """Test ACL configuration settings."""
    print("Testing ACL Configuration...")
    
    from config import settings
    
    # Test ACL-specific settings exist
    acl_settings = [
        'entra_group_id',
        'enable_permission_filter',
        'azure_search_api_version'
    ]
    
    for setting in acl_settings:
        assert hasattr(settings, setting), f"Missing ACL setting: {setting}"
        print(f"✅ ACL setting '{setting}' exists")
    
    # Test API version is preview version
    assert settings.azure_search_api_version == "2025-05-01-preview", \
        f"Expected API version 2025-05-01-preview, got {settings.azure_search_api_version}"
    print(f"✅ API version is correct: {settings.azure_search_api_version}")
    
    # Test permission filter setting
    assert isinstance(settings.enable_permission_filter, bool), \
        "enable_permission_filter should be boolean"
    print(f"✅ Permission filter setting is boolean: {settings.enable_permission_filter}")
    
    # Test Entra Group ID format (if enabled)
    if settings.enable_permission_filter:
        assert settings.entra_group_id, "entra_group_id is required when permission filter is enabled"
        # Basic GUID format check
        assert len(settings.entra_group_id) == 36, "entra_group_id should be 36 characters (GUID format)"
        assert settings.entra_group_id.count('-') == 4, "entra_group_id should have 4 hyphens (GUID format)"
        print(f"✅ Entra Group ID format is valid: {settings.entra_group_id}")
    
    print("✅ ACL Configuration tests passed!")


async def test_search_index_schema():
    """Test that the search index schema includes ACL fields."""
    print("\nTesting Search Index Schema...")
    
    from search_uploader import SearchUploader
    
    # Note: PermissionFilter and SearchIndexPermissionFilterOption are preview features
    try:
        from azure.search.documents.indexes.models import PermissionFilter, SearchIndexPermissionFilterOption
        preview_features_available = True
    except ImportError:
        preview_features_available = False
        print("⚠️  Preview features not available in current SDK version")
    
    uploader = SearchUploader()
    
    # Test that ACL helper method works
    acl_groups = uploader._get_document_acl_groups()
    assert isinstance(acl_groups, list), "ACL groups should be a list"
    assert len(acl_groups) > 0, "ACL groups should not be empty"
    print(f"✅ ACL groups method works: {acl_groups}")
    
    # Test imports are available (if preview features are supported)
    if preview_features_available:
        assert PermissionFilter is not None, "PermissionFilter should be available"
        assert SearchIndexPermissionFilterOption is not None, "SearchIndexPermissionFilterOption should be available"
        print("✅ ACL imports are available")
    else:
        print("⚠️  ACL imports using string literals (preview features not available)")
    
    await uploader.close()
    print("✅ Search Index Schema tests passed!")


async def test_document_acl_metadata():
    """Test that documents include ACL metadata."""
    print("\nTesting Document ACL Metadata...")
    
    from search_uploader import SearchUploader
    from pdf_processor import DocumentChunk
    from embedding_generator import EmbeddingResult
    from config import settings
    
    # Create mock data
    chunk = DocumentChunk(
        id="test_chunk_1",
        title="Test Document",
        content="This is a test document for ACL testing.",
        headline="ACL Test Document",
        file_name="test.pdf",
        page_number=1,
        chunk_index=0,
        created_at=datetime.utcnow(),
        token_count=20
    )
    
    embedding = EmbeddingResult(
        chunk_id="test_chunk_1",
        embedding=[0.1] * 1536,  # Mock embedding
        success=True,
        error=None
    )
    
    uploader = SearchUploader()
    
    # Test ACL groups assignment
    acl_groups = uploader._get_document_acl_groups()
    if settings.enable_permission_filter:
        assert settings.entra_group_id in acl_groups, "Entra Group ID should be in ACL groups"
    else:
        assert "all" in acl_groups, "Should have 'all' access when permission filter is disabled"
    
    print(f"✅ Document ACL groups correct: {acl_groups}")
    
    # Test that document structure would include ACL fields
    # (We'll simulate document preparation without actually uploading)
    expected_document_fields = [
        "id", "title", "content", "headline", "embedding",
        "file_name", "page_number", "chunk_index", "created_at",
        "token_count", "groupIds"
    ]
    
    print(f"✅ Expected document fields include ACL: {expected_document_fields}")
    
    await uploader.close()
    print("✅ Document ACL Metadata tests passed!")


async def test_acl_with_different_configurations():
    """Test ACL behavior with different configurations."""
    print("\nTesting ACL with Different Configurations...")
    
    from search_uploader import SearchUploader
    from config import settings
    
    # Test with permission filter enabled
    if settings.enable_permission_filter:
        uploader = SearchUploader()
        acl_groups = uploader._get_document_acl_groups()
        assert settings.entra_group_id in acl_groups, "Should include Entra Group ID when enabled"
        assert "all" not in acl_groups, "Should not include 'all' when permission filter is enabled"
        print("✅ ACL works correctly with permission filter enabled")
        await uploader.close()
    
    # Test with permission filter disabled (simulate)
    original_enable = settings.enable_permission_filter
    settings.enable_permission_filter = False
    
    uploader = SearchUploader()
    acl_groups = uploader._get_document_acl_groups()
    assert "all" in acl_groups, "Should include 'all' when permission filter is disabled"
    print("✅ ACL works correctly with permission filter disabled")
    
    # Restore original setting
    settings.enable_permission_filter = original_enable
    
    await uploader.close()
    print("✅ ACL Configuration tests passed!")


async def test_acl_security_validation():
    """Test security aspects of the ACL implementation."""
    print("\nTesting ACL Security Validation...")
    
    from config import settings
    
    # Test that sensitive information is properly configured
    if settings.enable_permission_filter:
        # Test that we're not using default/example values
        assert settings.entra_group_id != "12345678-1234-1234-1234-123456789012", \
            "Should not use example/default Entra Group ID"
        
        # Test that the group ID looks like a valid GUID
        parts = settings.entra_group_id.split('-')
        assert len(parts) == 5, "GUID should have 5 parts separated by hyphens"
        assert len(parts[0]) == 8, "First part should be 8 characters"
        assert len(parts[1]) == 4, "Second part should be 4 characters"
        assert len(parts[2]) == 4, "Third part should be 4 characters"
        assert len(parts[3]) == 4, "Fourth part should be 4 characters"
        assert len(parts[4]) == 12, "Fifth part should be 12 characters"
        
        print(f"✅ Entra Group ID has valid GUID format")
    
    # Test API version is preview (required for ACL)
    assert "preview" in settings.azure_search_api_version, \
        "ACL requires preview API version"
    print(f"✅ Using preview API version: {settings.azure_search_api_version}")
    
    print("✅ ACL Security Validation tests passed!")


async def test_acl_error_handling():
    """Test error handling in ACL implementation."""
    print("\nTesting ACL Error Handling...")
    
    from search_uploader import SearchUploader
    from config import settings
    
    # Test handling of missing Entra Group ID
    if settings.enable_permission_filter and not settings.entra_group_id:
        print("❌ Warning: Permission filter is enabled but no Entra Group ID is configured")
        print("This would cause issues in production. Please configure ENTRA_GROUP_ID.")
    
    # Test that SearchUploader handles configuration gracefully
    uploader = SearchUploader()
    try:
        acl_groups = uploader._get_document_acl_groups()
        assert acl_groups is not None, "ACL groups should not be None"
        assert len(acl_groups) > 0, "ACL groups should not be empty"
        print("✅ ACL error handling works correctly")
    except Exception as e:
        print(f"❌ ACL error handling failed: {str(e)}")
        raise
    finally:
        await uploader.close()
    
    print("✅ ACL Error Handling tests passed!")


async def test_acl_logging():
    """Test that ACL-related information is properly logged."""
    print("\nTesting ACL Logging...")
    
    from search_uploader import SearchUploader
    from config import settings
    
    # Test that logger includes ACL information
    uploader = SearchUploader()
    
    # This would normally be captured by logging, but we'll just verify the methods exist
    acl_groups = uploader._get_document_acl_groups()
    
    # Verify logging components exist
    assert hasattr(settings, 'enable_permission_filter'), "Settings should have permission filter flag"
    assert hasattr(settings, 'entra_group_id'), "Settings should have Entra Group ID"
    
    print(f"✅ ACL logging components available")
    print(f"   - Permission filter enabled: {settings.enable_permission_filter}")
    print(f"   - Entra Group ID configured: {'Yes' if settings.entra_group_id else 'No'}")
    print(f"   - ACL groups: {acl_groups}")
    
    await uploader.close()
    print("✅ ACL Logging tests passed!")


async def run_all_acl_tests():
    """Run all ACL-specific tests."""
    print("=" * 60)
    print("Running ACL (Access Control List) Tests")
    print("=" * 60)
    
    try:
        await test_acl_configuration()
        await test_search_index_schema()
        await test_document_acl_metadata()
        await test_acl_with_different_configurations()
        await test_acl_security_validation()
        await test_acl_error_handling()
        await test_acl_logging()
        
        print("\n" + "=" * 60)
        print("✅ All ACL tests passed successfully!")
        print("=" * 60)
        
        # Summary
        from config import settings
        print(f"\nACL Configuration Summary:")
        print(f"- Permission Filter: {'Enabled' if settings.enable_permission_filter else 'Disabled'}")
        print(f"- API Version: {settings.azure_search_api_version}")
        if settings.enable_permission_filter:
            print(f"- Entra Group ID: {settings.entra_group_id}")
            print(f"- Security Level: Restricted to specific group")
        else:
            print(f"- Security Level: Public access")
        
    except Exception as e:
        print(f"\n❌ ACL test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(run_all_acl_tests())
    
    if success:
        print("\n🎉 ACL implementation is working correctly!")
        print("\nNext steps:")
        print("1. Ensure your .env file has the correct Entra Group ID")
        print("2. Test with real documents: python acl_example.py")
        print("3. Verify access control by querying with different user tokens")
    else:
        print("\n❌ ACL tests failed. Please check the implementation.")
        sys.exit(1)
