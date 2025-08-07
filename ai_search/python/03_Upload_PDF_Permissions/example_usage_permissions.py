"""
Example usage of the PDF upload to Azure AI Search with group-based permissions.
Demonstrates how to process PDFs, set permissions, and perform secure searches.
"""
import asyncio
from typing import List, Dict
import json
from datetime import datetime

from pdf_processor import PDFProcessor
from embedding_generator import EmbeddingGenerator
from search_uploader import SearchUploader
from secure_search import SecureSearchClient
from entraid_auth import auth_manager
from config import settings
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class PermissionAwarePDFProcessor:
    """PDF processor that handles group-based permissions."""
    
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.embedding_generator = EmbeddingGenerator()
        self.search_uploader = SearchUploader()
        self.secure_search = SecureSearchClient()
    
    async def process_and_upload_with_permissions(
        self,
        pdf_directory: str,
        document_groups: Dict[str, List[str]] = None
    ) -> Dict[str, any]:
        """
        Process PDFs and upload with specific group permissions.
        
        Args:
            pdf_directory: Directory containing PDF files
            document_groups: Optional mapping of filename to group IDs
            
        Returns:
            Dictionary with processing results
        """
        try:
            logger.info("Starting PDF processing with permissions", 
                       directory=pdf_directory)
            
            # Step 1: Process PDFs to extract text and create chunks
            logger.info("Processing PDF files...")
            chunks = await self.pdf_processor.process_pdf_directory(pdf_directory)
            
            if not chunks:
                logger.error("No chunks were created from PDFs")
                return {"success": False, "error": "No chunks created"}
            
            # Step 2: Apply custom permissions if provided
            if document_groups:
                for chunk in chunks:
                    filename = chunk.file_name
                    if filename in document_groups:
                        self.pdf_processor.update_chunk_permissions(
                            chunk, 
                            document_groups[filename]
                        )
            
            logger.info("Created chunks with permissions", 
                       chunk_count=len(chunks))
            
            # Step 3: Create or update search index
            logger.info("Creating/updating search index...")
            index_success = await self.search_uploader.create_or_update_index()
            
            if not index_success:
                logger.error("Failed to create/update search index")
                return {"success": False, "error": "Index creation failed"}
            
            # Step 4: Generate embeddings for chunks
            logger.info("Generating embeddings...")
            embeddings = await self.embedding_generator.generate_embeddings_batch(chunks)
            
            successful_embeddings = [e for e in embeddings if e.success]
            
            logger.info("Generated embeddings", 
                       total=len(embeddings),
                       successful=len(successful_embeddings))
            
            # Step 5: Upload documents to search index
            logger.info("Uploading documents to search index...")
            upload_result = await self.search_uploader.upload_documents(chunks, embeddings)
            
            logger.info("Upload completed", 
                       success=upload_result["success"],
                       failed=upload_result["failed"])
            
            return {
                "success": True,
                "chunks_processed": len(chunks),
                "embeddings_generated": len(successful_embeddings),
                "documents_uploaded": upload_result["success"],
                "upload_failures": upload_result["failed"],
                "errors": upload_result.get("errors", [])
            }
            
        except Exception as e:
            logger.error("Processing failed", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def demonstrate_secure_search(self, user_id: str, queries: List[str]):
        """
        Demonstrate secure search functionality with different queries.
        
        Args:
            user_id: User ID to search as
            queries: List of search queries to test
        """
        try:
            logger.info("Starting secure search demonstration", 
                       user_id=user_id, 
                       query_count=len(queries))
            
            # Get user statistics first
            stats = await self.secure_search.get_user_statistics(user_id)
            print(f"\\n=== User Statistics ===")
            print(f"User: {user_id}")
            print(f"Accessible documents: {stats['accessible_documents']}")
            print(f"Accessible groups: {stats['accessible_groups']}")
            print(f"File count: {stats['file_count']}")
            print(f"Groups: {stats['groups']}")
            
            # Test different search types
            search_types = ["text", "vector", "hybrid"]
            
            for query in queries:
                print(f"\\n=== Search Query: '{query}' ===")
                
                for search_type in search_types:
                    print(f"\\n--- {search_type.upper()} Search ---")
                    
                    results = await self.secure_search.search_with_permissions(
                        query=query,
                        user_id=user_id,
                        search_type=search_type,
                        top=3
                    )
                    
                    if results.get("error"):
                        print(f"Error: {results['error']}")
                        continue
                    
                    print(f"Found {len(results['results'])} results (Total: {results.get('count', 'N/A')})")
                    
                    for i, result in enumerate(results['results'], 1):
                        print(f"  {i}. {result['title']}")
                        print(f"     File: {result['file_name']} (Page {result['page_number']})")
                        print(f"     Score: {result.get('search_score', 'N/A')}")
                        print(f"     Preview: {result['content'][:100]}...")
                        print()
            
        except Exception as e:
            logger.error("Secure search demonstration failed", error=str(e))
            print(f"Error during search demonstration: {str(e)}")
    
    async def test_permission_validation(self, test_user_ids: List[str]):
        """
        Test permission validation for different users.
        
        Args:
            test_user_ids: List of user IDs to test
        """
        try:
            logger.info("Testing permission validation", user_count=len(test_user_ids))
            
            # Get configured document groups
            document_groups = settings.document_access_groups_list
            
            print(f"\\n=== Permission Validation Test ===")
            print(f"Configured document groups: {document_groups}")
            
            for user_id in test_user_ids:
                print(f"\\n--- Testing User: {user_id} ---")
                
                try:
                    # Get user's groups
                    user_groups = await auth_manager.get_user_groups(user_id)
                    print(f"User groups: {user_groups}")
                    
                    # Check access to each document group
                    for group_id in document_groups:
                        has_access = await auth_manager.validate_user_access(
                            user_id, [group_id]
                        )
                        print(f"  Access to {group_id}: {'✓' if has_access else '✗'}")
                    
                    # Get accessible groups
                    accessible_groups = await auth_manager.get_user_accessible_groups(user_id)
                    print(f"Accessible groups: {accessible_groups}")
                    
                    # Generate security filter
                    security_filter = auth_manager.generate_security_filter(accessible_groups)
                    print(f"Security filter: {security_filter}")
                    
                except Exception as e:
                    print(f"  Error testing user {user_id}: {str(e)}")
            
        except Exception as e:
            logger.error("Permission validation test failed", error=str(e))
            print(f"Error during permission validation test: {str(e)}")
    
    async def cleanup(self):
        """Clean up resources."""
        await self.secure_search.close()


async def main():
    """Main function to demonstrate the permission system."""
    
    # Initialize the permission-aware processor
    processor = PermissionAwarePDFProcessor()
    
    try:
        print("=== PDF Upload with Group-Based Permissions Demo ===\\n")
        
        # Step 1: Process and upload PDFs with permissions
        print("1. Processing and uploading PDFs...")
        
        # Example: Define specific groups for different documents
        document_groups = {
            "entire-lenzing-ar24.pdf": ["finance-team", "executives"],
            "page-11.pdf": ["finance-team"],
            "page-13.pdf": ["hr-team", "executives"],
            "page-15.pdf": ["marketing-team"]
        }
        
        result = await processor.process_and_upload_with_permissions(
            pdf_directory=settings.pdf_directory_path,
            document_groups=document_groups
        )
        
        if result["success"]:
            print(f"✓ Successfully processed {result['chunks_processed']} chunks")
            print(f"✓ Generated {result['embeddings_generated']} embeddings")
            print(f"✓ Uploaded {result['documents_uploaded']} documents")
            if result["upload_failures"]:
                print(f"⚠ {result['upload_failures']} upload failures")
        else:
            print(f"✗ Processing failed: {result['error']}")
            return
        
        # Step 2: Test permission validation
        print("\\n2. Testing permission validation...")
        
        # Example user IDs (replace with actual user IDs from your Entra ID)
        test_users = [
            "user1@example.com",
            "user2@example.com",
            "admin@example.com"
        ]
        
        await processor.test_permission_validation(test_users)
        
        # Step 3: Demonstrate secure search
        print("\\n3. Demonstrating secure search...")
        
        # Example queries to test
        test_queries = [
            "financial report",
            "annual revenue",
            "sustainability",
            "management team"
        ]
        
        # Test with first user
        if test_users:
            await processor.demonstrate_secure_search(test_users[0], test_queries)
        
        print("\\n=== Demo completed successfully! ===")
        
    except Exception as e:
        logger.error("Demo failed", error=str(e))
        print(f"\\nDemo failed: {str(e)}")
    
    finally:
        await processor.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
