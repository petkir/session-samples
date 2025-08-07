"""
Enhanced PDF processor module for extracting text and creating intelligent chunks.
Handles various PDF formats and creates meaningful chunks with headlines.
Integrates with image extraction for complete document processing.
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
from image_extractor import ImageExtractor, ExtractedImage
from image_analyzer import ImageAnalyzer, ImageAnalysis

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
    content_type: str = "text"  # "text" or "image"


class PDFProcessor:
    """Handles PDF text extraction, image extraction, and intelligent chunking."""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        
        # Initialize image processing components
        self.image_extractor = ImageExtractor()
        self.image_analyzer = ImageAnalyzer()
    
    async def process_pdf_directory(self, directory_path: str) -> Tuple[List[DocumentChunk], List[ImageAnalysis]]:
        """
        Process all PDF files in a directory, extracting both text and images.
        
        Args:
            directory_path: Path to directory containing PDF files
            
        Returns:
            Tuple of (text_chunks, image_analyses)
        """
        pdf_files = self._get_pdf_files(directory_path)
        
        if not pdf_files:
            logger.warning("No PDF files found in directory", directory=directory_path)
            return [], []
        
        logger.info("Processing PDF files", count=len(pdf_files), directory=directory_path)
        
        # Process PDFs concurrently with controlled concurrency
        semaphore = asyncio.Semaphore(settings.max_concurrent_pdfs)
        tasks = [self._process_single_pdf(pdf_file, semaphore) for pdf_file in pdf_files]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results and filter out exceptions
        all_text_chunks = []
        all_image_analyses = []
        
        for result in results:
            if isinstance(result, Exception):
                logger.error("PDF processing failed", error=str(result))
                continue
            
            text_chunks, image_analyses = result
            all_text_chunks.extend(text_chunks)
            all_image_analyses.extend(image_analyses)
        
        logger.info("PDF processing completed", 
                   total_text_chunks=len(all_text_chunks),
                   total_image_analyses=len(all_image_analyses))
        
        return all_text_chunks, all_image_analyses
    
    async def _process_single_pdf(self, pdf_path: Path, semaphore: asyncio.Semaphore) -> Tuple[List[DocumentChunk], List[ImageAnalysis]]:
        """
        Process a single PDF file, extracting both text and images.
        
        Args:
            pdf_path: Path to the PDF file
            semaphore: Semaphore for concurrency control
            
        Returns:
            Tuple of (text_chunks, image_analyses)
        """
        async with semaphore:
            try:
                logger.info("Processing PDF", file=str(pdf_path))
                
                # Extract text from PDF
                text_chunks = await self._extract_text_and_create_chunks(pdf_path)
                
                # Extract and analyze images if enabled
                image_analyses = []
                if settings.extract_images:
                    # Extract images from PDF
                    extracted_images = await self.image_extractor.extract_images_from_pdf(pdf_path)
                    
                    # Analyze images if any were extracted
                    if extracted_images:
                        image_analyses = await self.image_analyzer.analyze_images(extracted_images)
                
                logger.info("PDF processing completed", 
                           file=str(pdf_path),
                           text_chunks=len(text_chunks),
                           image_analyses=len(image_analyses))
                
                return text_chunks, image_analyses
                
            except Exception as e:
                logger.error("Error processing PDF", file=str(pdf_path), error=str(e))
                return [], []
    
    async def _extract_text_and_create_chunks(self, pdf_path: Path) -> List[DocumentChunk]:
        """
        Extract text from PDF and create intelligent chunks.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of DocumentChunk objects
        """
        try:
            # Extract text using pdfplumber (better for layout preservation)
            text_content = await self._extract_text_with_pdfplumber(pdf_path)
            
            if not text_content:
                # Fallback to PyPDF2
                text_content = await self._extract_text_with_pypdf2(pdf_path)
            
            if not text_content:
                logger.warning("No text extracted from PDF", file=str(pdf_path))
                return []
            
            # Create chunks from extracted text
            chunks = await self._create_intelligent_chunks(text_content, pdf_path)
            
            return chunks
            
        except Exception as e:
            logger.error("Error extracting text from PDF", file=str(pdf_path), error=str(e))
            return []
    
    async def _extract_text_with_pdfplumber(self, pdf_path: Path) -> Dict[int, str]:
        """
        Extract text from PDF using pdfplumber.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary mapping page numbers to text content
        """
        try:
            text_content = {}
            
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        text_content[page_num + 1] = text
            
            return text_content
            
        except Exception as e:
            logger.warning("pdfplumber extraction failed", file=str(pdf_path), error=str(e))
            return {}
    
    async def _extract_text_with_pypdf2(self, pdf_path: Path) -> Dict[int, str]:
        """
        Extract text from PDF using PyPDF2 (fallback method).
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary mapping page numbers to text content
        """
        try:
            text_content = {}
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if text:
                        text_content[page_num + 1] = text
            
            return text_content
            
        except Exception as e:
            logger.warning("PyPDF2 extraction failed", file=str(pdf_path), error=str(e))
            return {}
    
    async def _create_intelligent_chunks(self, text_content: Dict[int, str], pdf_path: Path) -> List[DocumentChunk]:
        """
        Create intelligent chunks from extracted text.
        
        Args:
            text_content: Dictionary mapping page numbers to text
            pdf_path: Path to the PDF file
            
        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        
        for page_num, text in text_content.items():
            if not text.strip():
                continue
            
            # Split text into chunks
            text_chunks = self.text_splitter.split_text(text)
            
            for chunk_index, chunk_text in enumerate(text_chunks):
                if not chunk_text.strip():
                    continue
                
                # Generate headline for chunk
                headline = self._generate_headline(chunk_text, page_num, chunk_index)
                
                # Create chunk ID
                chunk_id = f"{pdf_path.stem}_page{page_num}_chunk{chunk_index}"
                
                # Count tokens
                token_count = len(self.encoding.encode(chunk_text))
                
                chunk = DocumentChunk(
                    id=chunk_id,
                    title=f"Page {page_num}, Chunk {chunk_index + 1}",
                    content=chunk_text,
                    headline=headline,
                    file_name=pdf_path.name,
                    page_number=page_num,
                    chunk_index=chunk_index,
                    created_at=datetime.now(),
                    token_count=token_count,
                    content_type="text"
                )
                
                chunks.append(chunk)
        
        return chunks
    
    def _generate_headline(self, text: str, page_num: int, chunk_index: int) -> str:
        """
        Generate a descriptive headline for a text chunk.
        
        Args:
            text: Text content
            page_num: Page number
            chunk_index: Chunk index
            
        Returns:
            Generated headline
        """
        # Extract first meaningful sentence or phrase
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10 and len(sentence) < 100:
                return f"Page {page_num}: {sentence}"
        
        # Fallback: use first words
        words = text.split()[:10]
        if words:
            return f"Page {page_num}: {' '.join(words)}..."
        
        return f"Page {page_num}, Chunk {chunk_index + 1}"
    
    def _get_pdf_files(self, directory_path: str) -> List[Path]:
        """
        Get all PDF files from a directory.
        
        Args:
            directory_path: Directory path
            
        Returns:
            List of PDF file paths
        """
        directory = Path(directory_path)
        
        if not directory.exists():
            logger.error("Directory does not exist", directory=directory_path)
            return []
        
        pdf_files = list(directory.glob("*.pdf"))
        pdf_files.extend(directory.glob("*.PDF"))
        
        return sorted(pdf_files)
    
    def create_chunks_from_image_analyses(self, image_analyses: List[ImageAnalysis]) -> List[DocumentChunk]:
        """
        Create DocumentChunk objects from image analyses.
        
        Args:
            image_analyses: List of ImageAnalysis objects
            
        Returns:
            List of DocumentChunk objects representing image content
        """
        chunks = []
        
        for analysis in image_analyses:
            # Combine description and extracted text
            combined_content = f"Image Description: {analysis.description}"
            
            if analysis.extracted_text:
                combined_content += f"\n\nExtracted Text: {analysis.extracted_text}"
            
            if analysis.objects_detected:
                combined_content += f"\n\nObjects Detected: {', '.join(analysis.objects_detected)}"
            
            # Generate headline
            headline = f"Image from page {analysis.page_number}"
            if analysis.objects_detected:
                headline += f" - Contains: {', '.join(analysis.objects_detected[:3])}"
            
            # Count tokens
            token_count = len(self.encoding.encode(combined_content))
            
            chunk = DocumentChunk(
                id=f"image_{analysis.image_id}",
                title=f"Image Analysis - {analysis.image_id}",
                content=combined_content,
                headline=headline,
                file_name=Path(analysis.pdf_source).name,
                page_number=analysis.page_number,
                chunk_index=0,  # Images are single chunks
                created_at=analysis.analysis_timestamp,
                token_count=token_count,
                content_type="image"
            )
            
            chunks.append(chunk)
        
        return chunks
