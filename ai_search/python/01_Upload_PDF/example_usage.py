"""
Example usage script demonstrating how to use the PDF upload functionality.
This script shows various ways to use the PDF upload components.
"""
import asyncio
import os
from pathlib import Path

from config import settings
from pdf_processor import PDFProcessor
from embedding_generator import EmbeddingGenerator
from search_uploader import SearchUploader
from main import PDFUploadOrchestrator


async def example_basic_usage():
    """Basic usage example."""
    print("=== Basic PDF Upload Example ===")
    
    # Create orchestrator
    orchestrator = PDFUploadOrchestrator()
    
    # Run the complete process
    success = await orchestrator.run()
    
    if success:
        print("✅ PDF upload completed successfully!")
        
        # Test search functionality
        print("\n=== Testing Search ===")
        await orchestrator.search_test("machine learning", top=3)
    else:
        print("❌ PDF upload failed!")


async def example_component_usage():
    """Example using individual components."""
    print("\n=== Component Usage Example ===")
    
    # Initialize components
    pdf_processor = PDFProcessor()
    embedding_generator = EmbeddingGenerator()
    search_uploader = SearchUploader()
    
    try:
        # Step 1: Process PDFs
        print("Processing PDFs...")
        chunks = await pdf_processor.process_pdf_directory(settings.pdf_directory_path)
        print(f"Created {len(chunks)} chunks")
        
        # Step 2: Generate embeddings
        print("Generating embeddings...")
        embeddings = await embedding_generator.generate_embeddings(chunks)
        successful_embeddings = sum(1 for e in embeddings if e.success)
        print(f"Generated {successful_embeddings} embeddings")
        
        # Step 3: Create index
        print("Creating search index...")
        index_success = await search_uploader.create_or_update_index()
        
        if index_success:
            # Step 4: Upload documents
            print("Uploading documents...")
            results = await search_uploader.upload_documents(chunks, embeddings)
            print(f"Uploaded {results['success']} documents")
        
    finally:
        # Cleanup
        await embedding_generator.close()
        await search_uploader.close()


async def example_custom_directory():
    """Example with custom PDF directory."""
    print("\n=== Custom Directory Example ===")
    
    custom_dir = "./custom_pdfs"
    
    # Create custom directory if it doesn't exist
    Path(custom_dir).mkdir(exist_ok=True)
    
    orchestrator = PDFUploadOrchestrator()
    
    # Run with custom directory
    success = await orchestrator.run(pdf_directory=custom_dir)
    
    if success:
        print(f"✅ Custom directory processing completed!")
    else:
        print(f"❌ Custom directory processing failed!")


async def example_search_operations():
    """Example of search operations."""
    print("\n=== Search Operations Example ===")
    
    search_uploader = SearchUploader()
    
    try:
        # Get index statistics
        stats = await search_uploader.get_index_statistics()
        if stats:
            print(f"Index contains {stats['document_count']} documents")
        
        # Perform searches
        queries = ["artificial intelligence", "machine learning", "data science"]
        
        for query in queries:
            print(f"\nSearching for: {query}")
            results = await search_uploader.search_documents(query, top=3)
            
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.get('title', 'N/A')} - {result.get('headline', 'N/A')[:50]}...")
    
    finally:
        await search_uploader.close()


if __name__ == "__main__":
    # Run examples
    asyncio.run(example_basic_usage())
    asyncio.run(example_component_usage())
    asyncio.run(example_custom_directory())
    asyncio.run(example_search_operations())
