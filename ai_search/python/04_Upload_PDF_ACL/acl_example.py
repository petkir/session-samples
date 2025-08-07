"""
Example usage of the PDF upload system with ACL support.

This example shows how to:
1. Configure the system for ACL-based access control
2. Upload documents that are restricted to specific Entra groups
3. Understand the security implications
"""

import asyncio
import os
from config import settings
from main import PDFUploadOrchestrator
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


async def main():
    """
    Example of using the PDF upload system with ACL support.
    
    This will:
    1. Process PDFs in the configured directory
    2. Upload them to Azure AI Search with ACL restrictions
    3. Only users in the specified Entra group can access the documents
    """
    
    logger.info("Starting PDF upload with ACL example")
    
    # Log current configuration
    logger.info("ACL Configuration", 
               enable_permission_filter=settings.enable_permission_filter,
               entra_group_id=settings.entra_group_id if settings.enable_permission_filter else "Not configured",
               api_version=settings.azure_search_api_version)
    
    # Check if ACL is properly configured
    if settings.enable_permission_filter:
        if not settings.entra_group_id:
            logger.error("ACL is enabled but no Entra Group ID is configured. Please set ENTRA_GROUP_ID in your .env file")
            return
        
        logger.info("ACL is enabled - documents will be restricted to Entra Group", 
                   group_id=settings.entra_group_id)
    else:
        logger.warning("ACL is disabled - documents will be publicly accessible")
    
    # Initialize the processor
    processor = PDFUploadOrchestrator()
    
    try:
        # Process and upload PDFs
        success = await processor.run()
        
        if success:
            logger.info("Processing completed successfully")
            results = {"success": "Processing completed", "total_documents": "Unknown"}
        else:
            logger.error("Processing failed")
            results = {"success": 0, "failed": 1, "total_documents": 0}
        
        logger.info("Upload completed", 
                   success=success,
                   total_documents=results.get("total_documents", "Unknown"))
        
        if settings.enable_permission_filter:
            logger.info("ACL Security Note", 
                       message="Documents uploaded with ACL restrictions",
                       access_group=settings.entra_group_id,
                       security_note="Only users in the specified Entra group can access these documents")
        else:
            logger.warning("Security Note", 
                          message="Documents uploaded without ACL restrictions",
                          access_level="PUBLIC",
                          security_note="All users can access these documents")
        
    except Exception as e:
        logger.error("Error during processing", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(main())
