"""
Azure AI Search uploader module for creating search indices and uploading documents.
Handles index creation, document upload, and error handling.
"""
import asyncio
from typing import List, Dict, Optional, Any
import json
from datetime import datetime

from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SearchField, SearchFieldDataType, SimpleField, 
    SearchableField, VectorSearch, VectorSearchProfile, 
    HnswAlgorithmConfiguration, VectorSearchAlgorithmConfiguration
)
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
import structlog

from config import settings
from pdf_processor import DocumentChunk
from embedding_generator import EmbeddingResult

logger = structlog.get_logger(__name__)


class SearchUploader:
    """Handles uploading documents to Azure AI Search."""
    
    def __init__(self):
        """Initialize the search uploader with Azure AI Search clients."""
        self.credential = AzureKeyCredential(settings.azure_search_admin_key)
        self.endpoint = settings.azure_search_endpoint
        self.index_name = settings.search_index_name
        
        # Initialize clients
        self.index_client = SearchIndexClient(
            endpoint=self.endpoint,
            credential=self.credential
        )
        
        self.search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=self.credential
        )
    
    async def create_or_update_index(self) -> bool:
        """
        Create or update the search index with proper schema.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Creating or updating search index", index_name=self.index_name)
            
            # Define vector search configuration
            vector_search = VectorSearch(
                algorithms=[
                    HnswAlgorithmConfiguration(name="hnsw-config")
                ],
                profiles=[
                    VectorSearchProfile(
                        name="vector-profile",
                        algorithm_configuration_name="hnsw-config"
                    )
                ]
            )
            
            # Define index fields
            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                SearchableField(name="title", type=SearchFieldDataType.String),
                SearchableField(name="content", type=SearchFieldDataType.String),
                SearchableField(name="headline", type=SearchFieldDataType.String),
                SearchField(
                    name="embedding",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    vector_search_dimensions=settings.vector_dimensions,
                    vector_search_profile_name="vector-profile"
                ),
                SimpleField(name="file_name", type=SearchFieldDataType.String, filterable=True),
                SimpleField(name="page_number", type=SearchFieldDataType.Int32, filterable=True),
                SimpleField(name="chunk_index", type=SearchFieldDataType.Int32, filterable=True),
                SimpleField(name="created_at", type=SearchFieldDataType.DateTimeOffset, filterable=True),
                SimpleField(name="token_count", type=SearchFieldDataType.Int32, filterable=True),
                # Permission fields for group-based access control
                SimpleField(
                    name="document_groups", 
                    type=SearchFieldDataType.Collection(SearchFieldDataType.String), 
                    filterable=True,
                    searchable=False
                ),
                SimpleField(name="default_group", type=SearchFieldDataType.String, filterable=True),
                SimpleField(name="permission_level", type=SearchFieldDataType.String, filterable=True)
            ]
            
            # Create index
            index = SearchIndex(
                name=self.index_name,
                fields=fields,
                vector_search=vector_search
            )
            
            # Create or update index
            result = await self.index_client.create_or_update_index(index)
            
            logger.info("Index created/updated successfully", 
                       index_name=self.index_name, 
                       field_count=len(fields))
            
            return True
            
        except Exception as e:
            logger.error("Failed to create/update index", 
                        index_name=self.index_name, 
                        error=str(e))
            return False
    
    async def upload_documents(self, chunks: List[DocumentChunk], embeddings: List[EmbeddingResult]) -> Dict[str, Any]:
        """
        Upload documents to the search index.
        
        Args:
            chunks: List of DocumentChunk objects
            embeddings: List of EmbeddingResult objects
            
        Returns:
            Dictionary with upload results
        """
        if not chunks or not embeddings:
            logger.warning("No documents to upload")
            return {"success": 0, "failed": 0, "errors": []}
        
        logger.info("Uploading documents to search index", 
                   chunk_count=len(chunks), 
                   embedding_count=len(embeddings))
        
        # Create mapping of chunk_id to embedding
        embedding_map = {result.chunk_id: result for result in embeddings}
        
        # Prepare documents for upload
        documents = []
        skipped_count = 0
        
        for chunk in chunks:
            embedding_result = embedding_map.get(chunk.id)
            
            if not embedding_result or not embedding_result.success:
                logger.warning("Skipping chunk due to missing/failed embedding", 
                             chunk_id=chunk.id)
                skipped_count += 1
                continue
            
            # Format datetime for Azure AI Search (ISO 8601 with timezone)
            if chunk.created_at.tzinfo is None:
                # Add UTC timezone if not present
                formatted_date = chunk.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            else:
                formatted_date = chunk.created_at.isoformat()
            
            document = {
                "id": chunk.id,
                "title": chunk.title,
                "content": chunk.content,
                "headline": chunk.headline,
                "embedding": embedding_result.embedding,
                "file_name": chunk.file_name,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "created_at": formatted_date,
                "token_count": chunk.token_count,
                # Permission fields
                "document_groups": chunk.document_groups,
                "default_group": chunk.default_group,
                "permission_level": chunk.permission_level
            }
            
            documents.append(document)
        
        if not documents:
            logger.error("No valid documents to upload")
            return {"success": 0, "failed": len(chunks), "errors": ["No valid documents"]}
        
        # Upload documents in batches
        batch_size = 100  # Azure AI Search recommended batch size
        results = {"success": 0, "failed": 0, "errors": []}
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_result = await self._upload_batch(batch, i // batch_size + 1)
            
            results["success"] += batch_result["success"]
            results["failed"] += batch_result["failed"]
            results["errors"].extend(batch_result["errors"])
        
        logger.info("Document upload completed", 
                   total_documents=len(documents), 
                   success=results["success"], 
                   failed=results["failed"], 
                   skipped=skipped_count)
        
        return results
    
    async def _upload_batch(self, documents: List[Dict], batch_number: int) -> Dict[str, Any]:
        """
        Upload a batch of documents to the search index.
        
        Args:
            documents: List of document dictionaries
            batch_number: Batch number for logging
            
        Returns:
            Dictionary with batch upload results
        """
        try:
            logger.info("Uploading document batch", 
                       batch_number=batch_number, 
                       document_count=len(documents))
            
            # Upload documents
            result = await self.search_client.upload_documents(documents)
            
            # Process results
            success_count = 0
            failed_count = 0
            errors = []
            
            for doc_result in result:
                if doc_result.succeeded:
                    success_count += 1
                else:
                    failed_count += 1
                    error_msg = f"Document {doc_result.key}: {doc_result.error_message}"
                    errors.append(error_msg)
                    logger.error("Document upload failed", 
                               document_id=doc_result.key, 
                               error=doc_result.error_message)
            
            logger.info("Batch upload completed", 
                       batch_number=batch_number, 
                       success=success_count, 
                       failed=failed_count)
            
            return {
                "success": success_count,
                "failed": failed_count,
                "errors": errors
            }
            
        except Exception as e:
            logger.error("Batch upload failed", 
                        batch_number=batch_number, 
                        error=str(e))
            
            return {
                "success": 0,
                "failed": len(documents),
                "errors": [f"Batch {batch_number}: {str(e)}"]
            }
    
    async def delete_index(self) -> bool:
        """
        Delete the search index.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Deleting search index", index_name=self.index_name)
            
            await self.index_client.delete_index(self.index_name)
            
            logger.info("Index deleted successfully", index_name=self.index_name)
            return True
            
        except ResourceNotFoundError:
            logger.warning("Index not found for deletion", index_name=self.index_name)
            return True
            
        except Exception as e:
            logger.error("Failed to delete index", 
                        index_name=self.index_name, 
                        error=str(e))
            return False
    
    async def get_index_statistics(self) -> Optional[Dict[str, Any]]:
        """
        Get statistics about the search index.
        
        Returns:
            Dictionary with index statistics or None if failed
        """
        try:
            # Get index statistics
            stats = await self.search_client.get_document_count()
            
            # Get index definition
            index = await self.index_client.get_index(self.index_name)
            
            return {
                "document_count": stats,
                "index_name": self.index_name,
                "field_count": len(index.fields),
                "created_at": index.created_date.isoformat() if index.created_date else None,
                "modified_at": index.modified_date.isoformat() if index.modified_date else None
            }
            
        except Exception as e:
            logger.error("Failed to get index statistics", 
                        index_name=self.index_name, 
                        error=str(e))
            return None
    
    async def search_documents(self, query: str, top: int = 10) -> List[Dict[str, Any]]:
        """
        Search documents in the index.
        
        Args:
            query: Search query
            top: Number of results to return
            
        Returns:
            List of search results
        """
        try:
            logger.info("Searching documents", query=query, top=top)
            
            results = await self.search_client.search(
                search_text=query,
                top=top,
                include_total_count=True
            )
            
            documents = []
            async for result in results:
                documents.append(dict(result))
            
            logger.info("Search completed", 
                       query=query, 
                       result_count=len(documents))
            
            return documents
            
        except Exception as e:
            logger.error("Search failed", query=query, error=str(e))
            return []
    
    async def close(self):
        """Close the search clients."""
        if hasattr(self.index_client, 'close'):
            await self.index_client.close()
        if hasattr(self.search_client, 'close'):
            await self.search_client.close()
