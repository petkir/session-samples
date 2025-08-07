"""
Secure search module that implements group-based permissions for Azure AI Search.
Provides search functionality with automatic filtering based on user's group membership.
"""
import asyncio
from typing import List, Dict, Optional, Any
import json
from datetime import datetime

from azure.search.documents.aio import SearchClient
from azure.search.documents import SearchItemPaged
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
import structlog

from config import settings
from entraid_auth import auth_manager
from embedding_generator import EmbeddingGenerator

logger = structlog.get_logger(__name__)


class SecureSearchClient:
    """Secure search client that enforces group-based permissions."""
    
    def __init__(self):
        """Initialize the secure search client."""
        self.credential = AzureKeyCredential(settings.azure_search_admin_key)
        self.endpoint = settings.azure_search_endpoint
        self.index_name = settings.search_index_name
        
        # Initialize search client
        self.search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=self.credential
        )
        
        # Initialize embedding generator for semantic search
        self.embedding_generator = EmbeddingGenerator()
    
    async def search_with_permissions(
        self,
        query: str,
        user_id: str,
        search_type: str = "hybrid",
        top: int = 10,
        include_total_count: bool = False,
        facets: Optional[List[str]] = None,
        filter_expression: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform a search with automatic permission filtering.
        
        Args:
            query: Search query string
            user_id: User's object ID or UPN
            search_type: Type of search ("text", "vector", "hybrid")
            top: Number of results to return
            include_total_count: Whether to include total count
            facets: List of facet fields
            filter_expression: Additional filter expression
            
        Returns:
            Dictionary containing search results and metadata
        """
        try:
            logger.info("Performing secure search", 
                       query=query, 
                       user_id=user_id, 
                       search_type=search_type)
            
            # Get user's accessible groups
            user_groups = await auth_manager.get_user_accessible_groups(user_id)
            
            if not user_groups:
                logger.warning("User has no accessible groups", user_id=user_id)
                return {
                    "results": [],
                    "count": 0,
                    "facets": {},
                    "message": "No accessible documents found"
                }
            
            # Generate security filter based on user's groups
            security_filter = auth_manager.generate_security_filter(user_groups)
            
            # Combine with additional filter if provided
            if filter_expression:
                combined_filter = f"({security_filter}) and ({filter_expression})"
            else:
                combined_filter = security_filter
            
            # Perform search based on type
            if search_type == "vector":
                results = await self._vector_search(query, combined_filter, top, include_total_count, facets)
            elif search_type == "text":
                results = await self._text_search(query, combined_filter, top, include_total_count, facets)
            else:  # hybrid
                results = await self._hybrid_search(query, combined_filter, top, include_total_count, facets)
            
            logger.info("Search completed successfully", 
                       user_id=user_id,
                       results_count=len(results.get("results", [])),
                       total_count=results.get("count", 0))
            
            return results
            
        except Exception as e:
            logger.error("Search failed", user_id=user_id, error=str(e))
            return {
                "results": [],
                "count": 0,
                "facets": {},
                "error": str(e)
            }
    
    async def _text_search(
        self,
        query: str,
        filter_expression: str,
        top: int,
        include_total_count: bool,
        facets: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Perform text-based search."""
        try:
            search_results = await self.search_client.search(
                search_text=query,
                filter=filter_expression,
                top=top,
                include_total_count=include_total_count,
                facets=facets,
                select=["id", "title", "content", "headline", "file_name", "page_number", "chunk_index", "created_at"]
            )
            
            return await self._process_search_results(search_results)
            
        except HttpResponseError as e:
            logger.error("Text search failed", error=str(e))
            raise
    
    async def _vector_search(
        self,
        query: str,
        filter_expression: str,
        top: int,
        include_total_count: bool,
        facets: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Perform vector-based search."""
        try:
            # Generate embedding for the query
            embedding_result = await self.embedding_generator.generate_embedding(query)
            
            if not embedding_result.success:
                raise Exception(f"Failed to generate embedding: {embedding_result.error}")
            
            # Create vector query
            vector_query = VectorizedQuery(
                vector=embedding_result.embedding,
                k_nearest_neighbors=top,
                fields="embedding"
            )
            
            search_results = await self.search_client.search(
                search_text=None,
                vector_queries=[vector_query],
                filter=filter_expression,
                top=top,
                include_total_count=include_total_count,
                facets=facets,
                select=["id", "title", "content", "headline", "file_name", "page_number", "chunk_index", "created_at"]
            )
            
            return await self._process_search_results(search_results)
            
        except Exception as e:
            logger.error("Vector search failed", error=str(e))
            raise
    
    async def _hybrid_search(
        self,
        query: str,
        filter_expression: str,
        top: int,
        include_total_count: bool,
        facets: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Perform hybrid search (text + vector)."""
        try:
            # Generate embedding for the query
            embedding_result = await self.embedding_generator.generate_embedding(query)
            
            if not embedding_result.success:
                logger.warning("Failed to generate embedding, falling back to text search")
                return await self._text_search(query, filter_expression, top, include_total_count, facets)
            
            # Create vector query
            vector_query = VectorizedQuery(
                vector=embedding_result.embedding,
                k_nearest_neighbors=top,
                fields="embedding"
            )
            
            search_results = await self.search_client.search(
                search_text=query,
                vector_queries=[vector_query],
                filter=filter_expression,
                top=top,
                include_total_count=include_total_count,
                facets=facets,
                select=["id", "title", "content", "headline", "file_name", "page_number", "chunk_index", "created_at"]
            )
            
            return await self._process_search_results(search_results)
            
        except Exception as e:
            logger.error("Hybrid search failed", error=str(e))
            raise
    
    async def _process_search_results(self, search_results: SearchItemPaged) -> Dict[str, Any]:
        """Process search results and return structured data."""
        results = []
        facets = {}
        count = 0
        
        async for result in search_results:
            # Extract search score if available
            score = getattr(result, '@search.score', None)
            
            # Create result item
            result_item = {
                "id": result.get("id"),
                "title": result.get("title"),
                "content": result.get("content"),
                "headline": result.get("headline"),
                "file_name": result.get("file_name"),
                "page_number": result.get("page_number"),
                "chunk_index": result.get("chunk_index"),
                "created_at": result.get("created_at"),
                "search_score": score
            }
            
            results.append(result_item)
        
        # Get facets if available
        if hasattr(search_results, 'get_facets'):
            facets = search_results.get_facets() or {}
        
        # Get count if available
        if hasattr(search_results, 'get_count'):
            count = search_results.get_count() or len(results)
        
        return {
            "results": results,
            "count": count,
            "facets": facets
        }
    
    async def get_document_by_id(self, document_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific document by ID with permission checking.
        
        Args:
            document_id: Document ID to retrieve
            user_id: User's object ID or UPN
            
        Returns:
            Document data if accessible, None otherwise
        """
        try:
            # Get user's accessible groups
            user_groups = await auth_manager.get_user_accessible_groups(user_id)
            
            if not user_groups:
                logger.warning("User has no accessible groups", user_id=user_id)
                return None
            
            # Generate security filter
            security_filter = auth_manager.generate_security_filter(user_groups)
            
            # Search for the specific document with security filter
            search_results = await self.search_client.search(
                search_text="*",
                filter=f"id eq '{document_id}' and ({security_filter})",
                top=1
            )
            
            async for result in search_results:
                logger.info("Document retrieved successfully", 
                           document_id=document_id, 
                           user_id=user_id)
                return dict(result)
            
            logger.warning("Document not found or not accessible", 
                          document_id=document_id, 
                          user_id=user_id)
            return None
            
        except Exception as e:
            logger.error("Failed to get document", 
                        document_id=document_id, 
                        user_id=user_id, 
                        error=str(e))
            return None
    
    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get statistics about documents accessible to a user.
        
        Args:
            user_id: User's object ID or UPN
            
        Returns:
            Dictionary containing user-specific statistics
        """
        try:
            # Get user's accessible groups
            user_groups = await auth_manager.get_user_accessible_groups(user_id)
            
            if not user_groups:
                return {
                    "accessible_documents": 0,
                    "accessible_groups": 0,
                    "file_count": 0,
                    "groups": []
                }
            
            # Generate security filter
            security_filter = auth_manager.generate_security_filter(user_groups)
            
            # Get document count
            search_results = await self.search_client.search(
                search_text="*",
                filter=security_filter,
                top=0,
                include_total_count=True,
                facets=["file_name"]
            )
            
            document_count = search_results.get_count() or 0
            
            # Get file count from facets
            facets = search_results.get_facets() or {}
            file_facets = facets.get("file_name", [])
            file_count = len(file_facets)
            
            return {
                "accessible_documents": document_count,
                "accessible_groups": len(user_groups),
                "file_count": file_count,
                "groups": user_groups
            }
            
        except Exception as e:
            logger.error("Failed to get user statistics", user_id=user_id, error=str(e))
            return {
                "accessible_documents": 0,
                "accessible_groups": 0,
                "file_count": 0,
                "groups": [],
                "error": str(e)
            }
    
    async def close(self):
        """Close the search client."""
        await self.search_client.close()


# Example usage function
async def example_secure_search():
    """Example of how to use the secure search client."""
    client = SecureSearchClient()
    
    try:
        # Example user ID (in practice, get this from authentication)
        user_id = "user@example.com"
        
        # Perform a search
        results = await client.search_with_permissions(
            query="artificial intelligence",
            user_id=user_id,
            search_type="hybrid",
            top=5
        )
        
        print(f"Found {len(results['results'])} results")
        for result in results['results']:
            print(f"- {result['title']} (Score: {result['search_score']})")
        
        # Get user statistics
        stats = await client.get_user_statistics(user_id)
        print(f"User can access {stats['accessible_documents']} documents from {stats['file_count']} files")
        
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(example_secure_search())
