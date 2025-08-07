"""
PDF processor module for extracting text and creating intelligent chunks.
Handles various PDF formats and creates meaningful chunks with headlines.
"""
import os
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import asyncio
from dataclasses import dataclass
from datetime import datetime

import PyPDF2
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken
import structlog

from config import settings

logger = structlog.get_logger(__name__)


@dataclass
class DocumentChunk:
    """Represents a chunk of text from a PDF document."""
    id: str
    title: str
    content: str
    headline: str
    file_name: str
    page_number: int
    chunk_index: int
    created_at: datetime
    token_count: int
    # Permission fields for group-based access control
    document_groups: List[str]
    default_group: str
    permission_level: str = "read"


class PDFProcessor:
    """Handles PDF text extraction and intelligent chunking."""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    
    async def process_pdf_directory(self, directory_path: str) -> List[DocumentChunk]:
        """
        Process all PDF files in a directory.
        
        Args:
            directory_path: Path to directory containing PDF files
            
        Returns:
            List of DocumentChunk objects
        """
        pdf_files = self._get_pdf_files(directory_path)
        
        if not pdf_files:
            logger.warning("No PDF files found in directory", directory=directory_path)
            return []
        
        logger.info("Processing PDF files", count=len(pdf_files), directory=directory_path)
        
        # Process PDFs concurrently with controlled concurrency
        semaphore = asyncio.Semaphore(settings.max_concurrent_pdfs)
        tasks = [self._process_single_pdf(pdf_file, semaphore) for pdf_file in pdf_files]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results and filter out exceptions
        all_chunks = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("PDF processing failed", error=str(result))
                continue
            all_chunks.extend(result)
        
        logger.info("PDF processing completed", total_chunks=len(all_chunks))
        return all_chunks
    
    async def _process_single_pdf(self, pdf_path: Path, semaphore: asyncio.Semaphore) -> List[DocumentChunk]:
        """
        Process a single PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            semaphore: Semaphore for concurrency control
            
        Returns:
            List of DocumentChunk objects
        """
        async with semaphore:
            try:
                logger.info("Processing PDF", file=str(pdf_path))
                
                # Extract text from PDF
                pages_text = await self._extract_text_from_pdf(pdf_path)
                
                if not pages_text:
                    logger.warning("No text extracted from PDF", file=str(pdf_path))
                    return []
                
                # Create chunks from extracted text
                chunks = await self._create_chunks_from_pages(pages_text, pdf_path)
                
                logger.info("PDF processing completed", file=str(pdf_path), chunks=len(chunks))
                return chunks
                
            except Exception as e:
                logger.error("Failed to process PDF", file=str(pdf_path), error=str(e))
                raise
    
    async def _extract_text_from_pdf(self, pdf_path: Path) -> List[Tuple[int, str]]:
        """
        Extract text from PDF using multiple methods for better reliability.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of tuples (page_number, text)
        """
        pages_text = []
        
        try:
            # Try pdfplumber first (better for complex layouts)
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        # Clean and normalize text
                        text = self._clean_text(text)
                        pages_text.append((page_num, text))
                        
        except Exception as e:
            logger.warning("pdfplumber failed, trying PyPDF2", error=str(e))
            
            # Fallback to PyPDF2
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page_num, page in enumerate(pdf_reader.pages, 1):
                        text = page.extract_text()
                        if text:
                            text = self._clean_text(text)
                            pages_text.append((page_num, text))
                            
            except Exception as e2:
                logger.error("Both PDF extraction methods failed", 
                           pdfplumber_error=str(e), pypdf2_error=str(e2))
                raise
        
        return pages_text
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.
        
        Args:
            text: Raw text from PDF
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers/footers (simple heuristic)
        text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
        
        # Remove special characters that might interfere with processing
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\']+', '', text)
        
        # Normalize quotes
        text = re.sub(r'["""]', '"', text)
       # text = re.sub(r'[''']', "'", text)
        
        return text.strip()
    
    async def _create_chunks_from_pages(self, pages_text: List[Tuple[int, str]], pdf_path: Path) -> List[DocumentChunk]:
        """
        Create intelligent chunks from extracted text.
        
        Args:
            pages_text: List of (page_number, text) tuples
            pdf_path: Path to the PDF file
            
        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        file_name = pdf_path.name
        title = self._extract_title_from_filename(file_name)
        
        for page_num, text in pages_text:
            if not text.strip():
                continue
                
            # Split text into chunks
            page_chunks = self.text_splitter.split_text(text)
            
            for chunk_index, chunk_text in enumerate(page_chunks):
                if not chunk_text.strip():
                    continue
                
                # Generate unique ID for chunk (sanitize filename for Azure AI Search)
                sanitized_filename = self._sanitize_filename_for_key(file_name)
                chunk_id = f"{sanitized_filename}_{page_num}_{chunk_index}"
                
                # Generate headline for chunk
                headline = self._generate_headline(chunk_text)
                
                # Count tokens
                token_count = len(self.encoding.encode(chunk_text))
                
                chunk = DocumentChunk(
                    id=chunk_id,
                    title=title,
                    content=chunk_text,
                    headline=headline,
                    file_name=file_name,
                    page_number=page_num,
                    chunk_index=chunk_index,
                    created_at=datetime.utcnow(),
                    token_count=token_count,
                    # Permission fields - can be overridden by caller
                    document_groups=self._get_document_groups(pdf_path),
                    default_group=settings.default_document_group,
                    permission_level="read"
                )
                
                chunks.append(chunk)
        
        return chunks
    
    def _extract_title_from_filename(self, filename: str) -> str:
        """
        Extract a readable title from filename.
        
        Args:
            filename: PDF filename
            
        Returns:
            Human-readable title
        """
        # Remove extension and replace separators
        title = Path(filename).stem
        title = re.sub(r'[_-]', ' ', title)
        title = re.sub(r'\s+', ' ', title)
        
        # Capitalize words
        title = ' '.join(word.capitalize() for word in title.split())
        
        return title
    
    def _generate_headline(self, text: str) -> str:
        """
        Generate a descriptive headline for a text chunk.
        
        Args:
            text: Text chunk
            
        Returns:
            Generated headline
        """
        # Take first sentence or first 100 characters
        sentences = re.split(r'[.!?]+', text)
        
        if sentences and len(sentences[0]) > 10:
            headline = sentences[0].strip()
        else:
            headline = text[:100].strip()
        
        # Clean up headline
        headline = re.sub(r'\s+', ' ', headline)
        
        # Ensure it ends properly
        if not headline.endswith(('.', '!', '?', ':')):
            headline += '...'
        
        return headline
    
    def _sanitize_filename_for_key(self, filename: str) -> str:
        """
        Sanitize filename for use as Azure AI Search document key.
        
        Azure AI Search keys can only contain letters, digits, underscore (_), 
        dash (-), or equal sign (=).
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for use as document key
        """
        import re
        
        # Replace periods and other invalid characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_\-=]', '_', filename)
        
        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        
        return sanitized
    
    def _get_pdf_files(self, directory_path: str) -> List[Path]:
        """
        Get all PDF files from directory.
        
        Args:
            directory_path: Directory path
            
        Returns:
            List of PDF file paths
        """
        directory = Path(directory_path)
        
        if not directory.exists():
            logger.error("Directory does not exist", directory=directory_path)
            return []
        
        pdf_files = list(directory.glob("*.pdf")) + list(directory.glob("*.PDF"))
        
        # Filter out empty files
        valid_files = []
        for pdf_file in pdf_files:
            if pdf_file.stat().st_size > 0:
                valid_files.append(pdf_file)
            else:
                logger.warning("Skipping empty PDF file", file=str(pdf_file))
        
        return valid_files
    
    def _get_document_groups(self, pdf_path: Path) -> List[str]:
        """
        Determine which groups should have access to a document.
        This is a placeholder implementation - in practice, you might:
        - Parse filename patterns to determine groups
        - Use metadata files to specify permissions
        - Have a mapping configuration
        - Use default groups from settings
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of group IDs that should have access to this document
        """
        # Default implementation: use all configured document access groups
        # In practice, you might want to implement custom logic here
        document_groups = settings.document_access_groups_list
        
        if not document_groups:
            # If no groups are configured, use the default group
            if settings.default_document_group:
                return [settings.default_document_group]
            else:
                # No groups configured - this means open access
                return []
        
        # For now, return all configured groups
        # TODO: Implement custom logic based on filename, metadata, etc.
        return document_groups
    
    def update_chunk_permissions(self, chunk: DocumentChunk, groups: List[str], default_group: str = None):
        """
        Update permission information for a document chunk.
        
        Args:
            chunk: DocumentChunk to update
            groups: List of group IDs that should have access
            default_group: Default group ID (optional)
        """
        chunk.document_groups = groups
        if default_group:
            chunk.default_group = default_group
        
        logger.debug("Updated chunk permissions", 
                    chunk_id=chunk.id,
                    groups=groups,
                    default_group=default_group)
