"""
Enhanced embedding generator module for creating text embeddings using Azure OpenAI REST API.
Handles batch processing and rate limiting for efficient embedding generation.
Supports both text chunks and image analysis results.
Uses direct HTTP requests to the Azure OpenAI embeddings endpoint.
"""
import asyncio
from typing import List, Dict, Optional, Union
import time
import json
from dataclasses import dataclass

import aiohttp
import structlog
from asyncio_throttle import Throttler

from config import settings
from pdf_processor import DocumentChunk
from image_analyzer import ImageAnalysis

logger = structlog.get_logger(__name__)


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""
    chunk_id: str
    embedding: List[float]
    success: bool
    content_type: str = "text"  # "text" or "image"
    error: Optional[str] = None


class EmbeddingGenerator:
    """Generates embeddings for text chunks and image analyses using Azure OpenAI REST API."""
    
    def __init__(self):
        """Initialize the embedding generator with HTTP client."""
        self.endpoint_url = f"{settings.azure_openai_endpoint}/openai/deployments/{settings.azure_openai_embedding_deployment}/embeddings"
        self.api_key = settings.azure_openai_key
        self.api_version = "2023-05-15"
        
        # HTTP headers for Azure OpenAI API
        self.headers = {
            'Content-Type': 'application/json',
            'api-key': self.api_key
        }
        
        # Rate limiting: Azure OpenAI has rate limits
        # Adjust based on your tier (Standard: 240,000 tokens/minute)
        self.throttler = Throttler(rate_limit=100, period=60)  # 100 requests per minute
        
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        
        # HTTP session for connection pooling
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session for connection pooling."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout,
                connector=aiohttp.TCPConnector(limit=100)
            )
        return self.session
    
    async def generate_embeddings_for_chunks(self, chunks: List[DocumentChunk]) -> List[EmbeddingResult]:
        """
        Generate embeddings for text chunks.
        
        Args:
            chunks: List of DocumentChunk objects
            
        Returns:
            List of EmbeddingResult objects
        """
        if not chunks:
            return []
        
        logger.info("Generating embeddings for text chunks", chunk_count=len(chunks))
        
        # Create tasks for concurrent processing
        semaphore = asyncio.Semaphore(settings.max_concurrent_chunks)
        tasks = [
            self._generate_single_embedding(chunk.content, chunk.id, "text", semaphore) 
            for chunk in chunks
        ]
        
        results = await self._execute_embedding_tasks(tasks, chunks)
        return results
    
    async def generate_embeddings_for_images(self, image_analyses: List[ImageAnalysis]) -> List[EmbeddingResult]:
        """
        Generate embeddings for image analyses.
        
        Args:
            image_analyses: List of ImageAnalysis objects
            
        Returns:
            List of EmbeddingResult objects
        """
        if not image_analyses:
            return []
        
        logger.info("Generating embeddings for image analyses", image_count=len(image_analyses))
        
        # Create tasks for concurrent processing
        semaphore = asyncio.Semaphore(settings.max_concurrent_images)
        tasks = [
            self._generate_single_embedding(
                self._prepare_image_text_for_embedding(analysis), 
                analysis.image_id, 
                "image", 
                semaphore
            ) 
            for analysis in image_analyses
        ]
        
        results = await self._execute_embedding_tasks(tasks, image_analyses)
        return results
    
    async def _execute_embedding_tasks(self, tasks: List, source_objects: List) -> List[EmbeddingResult]:
        """
        Execute embedding tasks and collect results.
        
        Args:
            tasks: List of async tasks
            source_objects: List of source objects for error reporting
            
        Returns:
            List of EmbeddingResult objects
        """
        # Execute tasks and collect results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        embedding_results = []
        success_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                source_id = getattr(source_objects[i], 'id', getattr(source_objects[i], 'image_id', f'item_{i}'))
                logger.error("Embedding generation failed", 
                           source_id=source_id, error=str(result))
                embedding_results.append(EmbeddingResult(
                    chunk_id=source_id,
                    embedding=[],
                    success=False,
                    error=str(result)
                ))
            else:
                embedding_results.append(result)
                if result.success:
                    success_count += 1
        
        logger.info("Embedding generation completed", 
                   total=len(source_objects), success=success_count, 
                   failed=len(source_objects) - success_count)
        
        return embedding_results
    
    async def _generate_single_embedding(
        self, 
        text: str, 
        item_id: str, 
        content_type: str, 
        semaphore: asyncio.Semaphore
    ) -> EmbeddingResult:
        """
        Generate embedding for a single text with retry logic using direct HTTP requests.
        
        Args:
            text: Text to generate embedding for
            item_id: ID of the item
            content_type: Type of content ("text" or "image")
            semaphore: Semaphore for concurrency control
            
        Returns:
            EmbeddingResult object
        """
        async with semaphore:
            async with self.throttler:
                session = await self._get_session()
                
                for attempt in range(self.max_retries):
                    try:
                        # Prepare text for embedding
                        prepared_text = self._prepare_text_for_embedding(text)
                        
                        # Prepare request payload
                        payload = {
                            "input": prepared_text,
                            "model": settings.azure_openai_embedding_model
                        }
                        
                        # Add API version as query parameter
                        url = f"{self.endpoint_url}?api-version={self.api_version}"
                        
                        # Make HTTP request to Azure OpenAI API
                        async with session.post(url, json=payload) as response:
                            
                            if response.status == 200:
                                result = await response.json()
                                
                                if 'data' in result and len(result['data']) > 0:
                                    embedding = result['data'][0]['embedding']
                                    
                                    # Validate embedding
                                    if self._validate_embedding(embedding):
                                        logger.debug("Embedding generated successfully", 
                                                   item_id=item_id, 
                                                   content_type=content_type,
                                                   embedding_dim=len(embedding))
                                        
                                        return EmbeddingResult(
                                            chunk_id=item_id,
                                            embedding=embedding,
                                            success=True,
                                            content_type=content_type
                                        )
                                
                                # If we get here, something went wrong with the response
                                error_msg = f"Invalid response format: {result}"
                                logger.warning("Embedding generation failed", 
                                             item_id=item_id, 
                                             content_type=content_type,
                                             attempt=attempt + 1, 
                                             error=error_msg)
                            
                            elif response.status == 429:  # Rate limit
                                error_text = await response.text()
                                logger.warning("Rate limit exceeded", 
                                             item_id=item_id, 
                                             content_type=content_type,
                                             attempt=attempt + 1,
                                             status=response.status,
                                             error=error_text)
                                
                                if attempt < self.max_retries - 1:
                                    # Exponential backoff for rate limits
                                    delay = min(self.retry_delay * (2 ** attempt), 60)
                                    await asyncio.sleep(delay)
                                    continue
                                else:
                                    return EmbeddingResult(
                                        chunk_id=item_id,
                                        embedding=[],
                                        success=False,
                                        content_type=content_type,
                                        error=f"Rate limit exceeded: {error_text}"
                                    )
                            
                            else:  # Other HTTP errors
                                error_text = await response.text()
                                logger.error("HTTP error in embedding generation", 
                                           item_id=item_id, 
                                           content_type=content_type,
                                           attempt=attempt + 1,
                                           status=response.status,
                                           error=error_text)
                                
                                if attempt < self.max_retries - 1:
                                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                                    continue
                                else:
                                    return EmbeddingResult(
                                        chunk_id=item_id,
                                        embedding=[],
                                        success=False,
                                        content_type=content_type,
                                        error=f"HTTP {response.status}: {error_text}"
                                    )
                    
                    except aiohttp.ClientError as e:
                        logger.error("HTTP client error in embedding generation", 
                                   item_id=item_id, 
                                   content_type=content_type,
                                   attempt=attempt + 1, 
                                   error=str(e))
                        
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay * (2 ** attempt))
                        else:
                            return EmbeddingResult(
                                chunk_id=item_id,
                                embedding=[],
                                success=False,
                                content_type=content_type,
                                error=f"HTTP client error: {str(e)}"
                            )
                    
                    except Exception as e:
                        logger.error("Unexpected error in embedding generation", 
                                   item_id=item_id, 
                                   content_type=content_type,
                                   attempt=attempt + 1, 
                                   error=str(e))
                        
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay * (2 ** attempt))
                        else:
                            return EmbeddingResult(
                                chunk_id=item_id,
                                embedding=[],
                                success=False,
                                content_type=content_type,
                                error=f"Unexpected error: {str(e)}"
                            )
        
        # This should never be reached
        return EmbeddingResult(
            chunk_id=item_id,
            embedding=[],
            success=False,
            content_type=content_type,
            error="Unknown error"
        )
    
    def _prepare_text_for_embedding(self, text: str) -> str:
        """
        Prepare text for embedding generation.
        
        Args:
            text: Raw text
            
        Returns:
            Prepared text
        """
        # Clean and truncate text if necessary
        text = text.strip()
        
        # OpenAI embedding models have token limits
        # text-embedding-ada-002 has ~8000 token limit
        max_chars = 7000  # Conservative estimate
        
        if len(text) > max_chars:
            text = text[:max_chars]
            logger.warning("Text truncated for embedding", 
                         original_length=len(text), 
                         truncated_length=max_chars)
        
        return text
    
    def _prepare_image_text_for_embedding(self, analysis: ImageAnalysis) -> str:
        """
        Prepare image analysis text for embedding generation.
        
        Args:
            analysis: ImageAnalysis object
            
        Returns:
            Combined text for embedding
        """
        # Combine description and extracted text
        combined_text = f"Image Description: {analysis.description}"
        
        if analysis.extracted_text:
            combined_text += f"\n\nExtracted Text: {analysis.extracted_text}"
        
        if analysis.objects_detected:
            combined_text += f"\n\nObjects Detected: {', '.join(analysis.objects_detected)}"
        
        return combined_text
    
    def _validate_embedding(self, embedding: List[float]) -> bool:
        """
        Validate the generated embedding.
        
        Args:
            embedding: Generated embedding vector
            
        Returns:
            True if valid, False otherwise
        """
        if not embedding:
            return False
        
        # Check expected dimensions
        if len(embedding) != settings.vector_dimensions:
            logger.error("Invalid embedding dimensions", 
                        expected=settings.vector_dimensions, 
                        actual=len(embedding))
            return False
        
        # Check for NaN or infinite values
        if any(not isinstance(x, (int, float)) or x != x or abs(x) == float('inf') for x in embedding):
            logger.error("Embedding contains invalid values")
            return False
        
        return True
    
    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
