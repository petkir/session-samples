"""
Main application entry point for PDF upload to Azure AI Search.
Orchestrates the entire process from PDF processing to search index upload.
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
    """Orchestrates the entire PDF upload process."""
    
    def __init__(self):
        """Initialize the orchestrator with all components."""
        self.pdf_processor = PDFProcessor()
        self.embedding_generator = EmbeddingGenerator()
        self.search_uploader = SearchUploader()
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
        Run the complete PDF upload process.
        
        Args:
            pdf_directory: Directory containing PDF files (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Starting PDF upload process")
            
            # Use provided directory or default from settings
            pdf_dir = pdf_directory or settings.pdf_directory_path
            
            # Validate directory
            if not Path(pdf_dir).exists():
                console.print(f"[red]Error: PDF directory '{pdf_dir}' does not exist[/red]")
                return False
            
            # Display configuration
            self._display_configuration(pdf_dir)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console,
                transient=True
            ) as progress:
                
                # Step 1: Create or update search index
                task1 = progress.add_task("Creating search index...", total=1)
                
                if self.shutdown_event.is_set():
                    return False
                
                index_success = await self.search_uploader.create_or_update_index()
                
                if not index_success:
                    console.print("[red]Failed to create search index[/red]")
                    return False
                
                progress.update(task1, completed=1)
                
                # Step 2: Process PDF files
                task2 = progress.add_task("Processing PDF files...", total=1)
                
                if self.shutdown_event.is_set():
                    return False
                
                chunks = await self.pdf_processor.process_pdf_directory(pdf_dir)
                
                if not chunks:
                    console.print("[yellow]No PDF files found or processed[/yellow]")
                    return False
                
                progress.update(task2, completed=1)
                
                # Step 3: Generate embeddings
                task3 = progress.add_task("Generating embeddings...", total=1)
                
                if self.shutdown_event.is_set():
                    return False
                
                embeddings = await self.embedding_generator.generate_embeddings(chunks)
                
                if not embeddings:
                    console.print("[red]Failed to generate embeddings[/red]")
                    return False
                
                progress.update(task3, completed=1)
                
                # Step 4: Upload to search index
                task4 = progress.add_task("Uploading to search index...", total=1)
                
                if self.shutdown_event.is_set():
                    return False
                
                upload_results = await self.search_uploader.upload_documents(chunks, embeddings)
                
                progress.update(task4, completed=1)
            
            # Display results
            self._display_results(chunks, embeddings, upload_results)
            
            logger.info("PDF upload process completed successfully")
            return True
            
        except Exception as e:
            logger.error("PDF upload process failed", error=str(e))
            console.print(f"[red]Error: {str(e)}[/red]")
            return False
        
        finally:
            # Cleanup resources
            await self._cleanup()
    
    def _display_configuration(self, pdf_directory: str):
        """Display current configuration."""
        table = Table(title="Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("PDF Directory", pdf_directory)
        table.add_row("Search Service", settings.azure_search_service_name)
        table.add_row("Index Name", settings.search_index_name)
        table.add_row("Embedding Model", settings.azure_openai_embedding_model)
        table.add_row("Chunk Size", str(settings.chunk_size))
        table.add_row("Chunk Overlap", str(settings.chunk_overlap))
        table.add_row("Max Concurrent PDFs", str(settings.max_concurrent_pdfs))
        table.add_row("Max Concurrent Chunks", str(settings.max_concurrent_chunks))
        
        console.print(table)
        console.print()
    
    def _display_results(self, chunks, embeddings, upload_results):
        """Display processing results."""
        table = Table(title="Processing Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")
        
        successful_embeddings = sum(1 for e in embeddings if e.success)
        failed_embeddings = len(embeddings) - successful_embeddings
        
        table.add_row("PDF Chunks Created", str(len(chunks)))
        table.add_row("Embeddings Generated", str(successful_embeddings))
        table.add_row("Embedding Failures", str(failed_embeddings))
        table.add_row("Documents Uploaded", str(upload_results["success"]))
        table.add_row("Upload Failures", str(upload_results["failed"]))
        
        console.print(table)
        
        # Display errors if any
        if upload_results["errors"]:
            console.print("\n[red]Upload Errors:[/red]")
            for error in upload_results["errors"][:5]:  # Show first 5 errors
                console.print(f"  • {error}")
            
            if len(upload_results["errors"]) > 5:
                console.print(f"  ... and {len(upload_results['errors']) - 5} more errors")
    
    async def _cleanup(self):
        """Cleanup resources."""
        try:
            await self.embedding_generator.close()
            await self.search_uploader.close()
            logger.info("Resources cleaned up successfully")
        except Exception as e:
            logger.error("Error during cleanup", error=str(e))
    
    async def search_test(self, query: str, top: int = 5):
        """
        Test search functionality.
        
        Args:
            query: Search query
            top: Number of results to return
        """
        try:
            console.print(f"[cyan]Searching for: {query}[/cyan]")
            
            results = await self.search_uploader.search_documents(query, top)
            
            if not results:
                console.print("[yellow]No results found[/yellow]")
                return
            
            table = Table(title="Search Results")
            table.add_column("Score", style="green")
            table.add_column("Title", style="cyan")
            table.add_column("Headline", style="yellow")
            table.add_column("File", style="blue")
            
            for result in results:
                score = f"{result.get('@search.score', 0):.2f}"
                title = result.get('title', 'N/A')[:30]
                headline = result.get('headline', 'N/A')[:50]
                file_name = result.get('file_name', 'N/A')
                
                table.add_row(score, title, headline, file_name)
            
            console.print(table)
            
        except Exception as e:
            logger.error("Search test failed", error=str(e))
            console.print(f"[red]Search failed: {str(e)}[/red]")
        
        finally:
            await self._cleanup()


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Upload PDF documents to Azure AI Search")
    parser.add_argument("--pdf-dir", type=str, help="Directory containing PDF files")
    parser.add_argument("--search", type=str, help="Test search with query")
    parser.add_argument("--delete-index", action="store_true", help="Delete the search index")
    parser.add_argument("--stats", action="store_true", help="Show index statistics")
    
    args = parser.parse_args()
    
    orchestrator = PDFUploadOrchestrator()
    
    try:
        if args.delete_index:
            console.print("[yellow]Deleting search index...[/yellow]")
            success = await orchestrator.search_uploader.delete_index()
            if success:
                console.print("[green]Index deleted successfully[/green]")
            else:
                console.print("[red]Failed to delete index[/red]")
                return 1
        
        elif args.stats:
            console.print("[cyan]Getting index statistics...[/cyan]")
            stats = await orchestrator.search_uploader.get_index_statistics()
            if stats:
                table = Table(title="Index Statistics")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                
                for key, value in stats.items():
                    table.add_row(key.replace('_', ' ').title(), str(value))
                
                console.print(table)
            else:
                console.print("[red]Failed to get index statistics[/red]")
                return 1
        
        elif args.search:
            await orchestrator.search_test(args.search)
        
        else:
            # Run the main upload process
            success = await orchestrator.run(args.pdf_dir)
            return 0 if success else 1
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Process interrupted by user[/yellow]")
        return 1
    
    except Exception as e:
        logger.error("Unexpected error in main", error=str(e))
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
        return 1
    
    finally:
        await orchestrator._cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
