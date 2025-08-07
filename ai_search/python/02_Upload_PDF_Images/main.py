"""
Enhanced main application entry point for PDF upload with image extraction to Azure AI Search.
Orchestrates the entire process from PDF processing to search index upload, including image analysis.
"""
import asyncio
import sys
from pathlib import Path
from typing import Optional
import signal

import structlog
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from config import settings
from pdf_processor import PDFProcessor
from embedding_generator import EmbeddingGenerator
from search_uploader import SearchUploader
from image_extractor import ImageExtractor
from image_analyzer import ImageAnalyzer

# Setup logging
if settings.log_format == "json":
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
else:
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

logger = structlog.get_logger(__name__)
console = Console()


class PDFUploadOrchestrator:
    """Orchestrates the entire PDF upload process with image extraction and analysis."""
    
    def __init__(self):
        """Initialize the orchestrator with all components."""
        self.pdf_processor = PDFProcessor()
        self.embedding_generator = EmbeddingGenerator()
        self.search_uploader = SearchUploader()
        self.image_extractor = ImageExtractor()
        self.image_analyzer = ImageAnalyzer()
        self.shutdown_event = asyncio.Event()
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal", signal=signum)
            self.shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self, pdf_directory: Optional[str] = None) -> bool:
        """
        Run the complete PDF upload process with image extraction and analysis.
        
        Args:
            pdf_directory: Directory containing PDF files (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Starting PDF upload process with image extraction")
            
            # Use provided directory or default from settings
            pdf_dir = pdf_directory or settings.pdf_directory_path
            
            # Validate directory
            if not Path(pdf_dir).exists():
                logger.error("PDF directory does not exist", directory=pdf_dir)
                return False
            
            # Create progress display
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                
                # Step 1: Process PDFs (extract text and images)
                pdf_task = progress.add_task("Processing PDFs...", total=100)
                
                if self.shutdown_event.is_set():
                    return False
                
                text_chunks, image_analyses = await self.pdf_processor.process_pdf_directory(pdf_dir)
                
                if not text_chunks and not image_analyses:
                    logger.error("No content extracted from PDFs")
                    return False
                
                progress.update(pdf_task, completed=100)
                
                # Step 2: Create or update search index
                index_task = progress.add_task("Creating search index...", total=100)
                
                if self.shutdown_event.is_set():
                    return False
                
                index_success = await self.search_uploader.create_or_update_index()
                if not index_success:
                    logger.error("Failed to create search index")
                    return False
                
                progress.update(index_task, completed=100)
                
                # Step 3: Generate embeddings for text chunks
                embed_task = progress.add_task("Generating embeddings...", total=100)
                
                if self.shutdown_event.is_set():
                    return False
                
                # Generate embeddings for text chunks
                text_embeddings = []
                if text_chunks:
                    text_embeddings = await self.embedding_generator.generate_embeddings_for_chunks(text_chunks)
                
                # Generate embeddings for image analyses
                image_embeddings = []
                if image_analyses:
                    image_embeddings = await self.embedding_generator.generate_embeddings_for_images(image_analyses)
                
                progress.update(embed_task, completed=100)
                
                # Step 4: Upload documents to search index
                upload_task = progress.add_task("Uploading to search index...", total=100)
                
                if self.shutdown_event.is_set():
                    return False
                
                # Upload text documents
                text_upload_results = {"success": 0, "failed": 0, "errors": []}
                if text_chunks and text_embeddings:
                    text_upload_results = await self.search_uploader.upload_documents(text_chunks, text_embeddings)
                
                # Upload image analyses
                image_upload_results = {"success": 0, "failed": 0, "errors": []}
                if image_analyses and image_embeddings:
                    image_upload_results = await self.search_uploader.upload_image_analyses(image_analyses, image_embeddings)
                
                progress.update(upload_task, completed=100)
            
            # Display results
            await self._display_results(text_chunks, image_analyses, text_upload_results, image_upload_results)
            
            logger.info("PDF upload process completed successfully")
            return True
            
        except Exception as e:
            logger.error("PDF upload process failed", error=str(e))
            return False
        finally:
            # Cleanup
            await self._cleanup()
    
    async def _display_results(self, text_chunks, image_analyses, text_upload_results, image_upload_results):
        """Display processing results in a nice table format."""
        
        # Create summary table
        table = Table(title="PDF Upload Results", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="dim")
        table.add_column("Text Content", justify="right")
        table.add_column("Image Content", justify="right")
        table.add_column("Total", justify="right", style="bold")
        
        # Add rows
        table.add_row(
            "Items Processed",
            str(len(text_chunks)),
            str(len(image_analyses)),
            str(len(text_chunks) + len(image_analyses))
        )
        
        table.add_row(
            "Successfully Uploaded",
            str(text_upload_results["success"]),
            str(image_upload_results["success"]),
            str(text_upload_results["success"] + image_upload_results["success"])
        )
        
        table.add_row(
            "Failed Uploads",
            str(text_upload_results["failed"]),
            str(image_upload_results["failed"]),
            str(text_upload_results["failed"] + image_upload_results["failed"])
        )
        
        console.print(table)
        
        # Display errors if any
        all_errors = text_upload_results["errors"] + image_upload_results["errors"]
        if all_errors:
            console.print("\n[bold red]Errors:[/bold red]")
            for error in all_errors[:10]:  # Show first 10 errors
                console.print(f"  • {error}")
            if len(all_errors) > 10:
                console.print(f"  ... and {len(all_errors) - 10} more errors")
        
        # Display index statistics
        stats = await self.search_uploader.get_index_statistics()
        if stats:
            console.print(f"\n[bold green]Search Index:[/bold green] {stats['index_name']}")
            console.print(f"[dim]Total Documents:[/dim] {stats['document_count']}")
            console.print(f"[dim]Index Fields:[/dim] {stats['field_count']}")
    
    async def _cleanup(self):
        """Cleanup resources."""
        try:
            await self.embedding_generator.close()
            await self.search_uploader.close()
            
            # Cleanup old extracted images
            if settings.extract_images:
                self.image_extractor.cleanup_extracted_images()
                
        except Exception as e:
            logger.warning("Error during cleanup", error=str(e))


async def main():
    """Main entry point."""
    console.print("[bold blue]PDF Upload with Image Extraction to Azure AI Search[/bold blue]")
    console.print(f"[dim]Processing directory:[/dim] {settings.pdf_directory_path}")
    console.print(f"[dim]Extracted images directory:[/dim] {settings.extracted_images_path}")
    console.print(f"[dim]Search index:[/dim] {settings.search_index_name}")
    console.print(f"[dim]Image extraction enabled:[/dim] {settings.extract_images}")
    console.print()
    
    orchestrator = PDFUploadOrchestrator()
    
    success = await orchestrator.run()
    
    if success:
        console.print("[bold green]✓ Process completed successfully![/bold green]")
        return 0
    else:
        console.print("[bold red]✗ Process failed![/bold red]")
        return 1


if __name__ == "__main__":
    # Run the async main function
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
