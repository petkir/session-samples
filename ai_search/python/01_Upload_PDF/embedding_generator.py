"""
Embedding generator module for creating text embeddings using Azure OpenAI REST API.
Handles batch processing and rate limiting for efficient embedding generation.
Uses direct HTTP requests to the Azure OpenAI embeddings endpoint.
"""
import asyncio
from typing import List, Dict, Optional
import time
import json
from dataclasses import dataclass

import aiohttp
import structlog
from asyncio_throttle import Throttler

from config import settings
from pdf_processor import DocumentChunk

logger = structlog.get_logger(__name__)


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""
    chunk_id: str
    embedding: List[float]
    success: bool
    error: Optional[str] = None


class EmbeddingGenerator:
    """Generates embeddings for text chunks using Azure OpenAI REST API."""
    
    def __init__(self):
        """Initialize the embedding generator with HTTP client."""
        self.endpoint_url = settings.azure_openai_endpoint
        self.api_key = settings.azure_openai_key
        
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
    
    async def generate_embeddings(self, chunks: List[DocumentChunk]) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple text chunks.
        
        Args:
            chunks: List of DocumentChunk objects
            
        Returns:
            List of EmbeddingResult objects
        """
        if not chunks:
            return []
        
        logger.info("Generating embeddings", chunk_count=len(chunks))
        
        # Create tasks for concurrent processing
        semaphore = asyncio.Semaphore(settings.max_concurrent_chunks)
        tasks = [
            self._generate_single_embedding(chunk, semaphore) 
            for chunk in chunks
        ]
        
        # Execute tasks and collect results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        embedding_results = []
        success_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Embedding generation failed", 
                           chunk_id=chunks[i].id, error=str(result))
                embedding_results.append(EmbeddingResult(
                    chunk_id=chunks[i].id,
                    embedding=[],
                    success=False,
                    error=str(result)
                ))
            else:
                embedding_results.append(result)
                if result.success:
                    success_count += 1
        
        logger.info("Embedding generation completed", 
                   total=len(chunks), success=success_count, 
                   failed=len(chunks) - success_count)
        
        return embedding_results
    
    async def _generate_single_embedding(self, chunk: DocumentChunk, semaphore: asyncio.Semaphore) -> EmbeddingResult:
        """
        Generate embedding for a single text chunk with retry logic using direct HTTP requests.
        
        Args:
            chunk: DocumentChunk to generate embedding for
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
                        text = self._prepare_text_for_embedding(chunk.content)
                        
                        # Prepare request payload
                        payload = {
                            "input": text
                        }
                        
                        # Make HTTP request to Azure OpenAI API
                        async with session.post(
                            self.endpoint_url,
                            json=payload
                        ) as response:
                            
                            if response.status == 200:
                                result = await response.json()
                                
                                if 'data' in result and len(result['data']) > 0:
                                    embedding = result['data'][0]['embedding']
                                    
                                    # Validate embedding
                                    if self._validate_embedding(embedding):
                                        logger.debug("Embedding generated successfully", 
                                                   chunk_id=chunk.id, 
                                                   embedding_dim=len(embedding))
                                        
                                        return EmbeddingResult(
                                            chunk_id=chunk.id,
                                            embedding=embedding,
                                            success=True
                                        )
                                
                                # If we get here, something went wrong with the response
                                error_msg = f"Invalid response format: {result}"
                                logger.warning("Embedding generation failed", 
                                             chunk_id=chunk.id, 
                                             attempt=attempt + 1, 
                                             error=error_msg)
                            
                            elif response.status == 429:  # Rate limit
                                error_text = await response.text()
                                logger.warning("Rate limit exceeded", 
                                             chunk_id=chunk.id, 
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
                                        chunk_id=chunk.id,
                                        embedding=[],
                                        success=False,
                                        error=f"Rate limit exceeded: {error_text}"
                                    )
                            
                            else:  # Other HTTP errors
                                error_text = await response.text()
                                logger.error("HTTP error in embedding generation", 
                                           chunk_id=chunk.id, 
                                           attempt=attempt + 1,
                                           status=response.status,
                                           error=error_text)
                                
                                if attempt < self.max_retries - 1:
                                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                                    continue
                                else:
                                    return EmbeddingResult(
                                        chunk_id=chunk.id,
                                        embedding=[],
                                        success=False,
                                        error=f"HTTP {response.status}: {error_text}"
                                    )
                    
                    except aiohttp.ClientError as e:
                        logger.error("HTTP client error in embedding generation", 
                                   chunk_id=chunk.id, 
                                   attempt=attempt + 1, 
                                   error=str(e))
                        
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay * (2 ** attempt))
                        else:
                            return EmbeddingResult(
                                chunk_id=chunk.id,
                                embedding=[],
                                success=False,
                                error=f"HTTP client error: {str(e)}"
                            )
                    
                    except Exception as e:
                        logger.error("Unexpected error in embedding generation", 
                                   chunk_id=chunk.id, 
                                   attempt=attempt + 1, 
                                   error=str(e))
                        
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay * (2 ** attempt))
                        else:
                            return EmbeddingResult(
                                chunk_id=chunk.id,
                                embedding=[],
                                success=False,
                                error=f"Unexpected error: {str(e)}"
                            )
        
        # This should never be reached
        return EmbeddingResult(
            chunk_id=chunk.id,
            embedding=[],
            success=False,
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
      #  if len(embedding) != settings.vector_dimensions:
      #      logger.error("Invalid embedding dimensions", 
      #                  expected=settings.vector_dimensions, 
      #                  actual=len(embedding))
      #      return False
        
        # Check for NaN or infinite values
       # if any(not isinstance(x, (int, float)) or x != x or abs(x) == float('inf') for x in embedding):
       #     logger.error("Embedding contains invalid values")
       #     return False
        
        return True
    
    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
