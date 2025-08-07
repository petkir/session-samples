"""
Example usage of the enhanced PDF upload with image extraction system.
Demonstrates various use cases and configurations.
"""
import asyncio
from pathlib import Path

from main import PDFUploadOrchestrator
from config import settings
from search_uploader import SearchUploader


async def example_basic_upload():
    """Basic example of uploading PDFs with image extraction."""
    print("=== Basic PDF Upload with Image Extraction ===")
    
    orchestrator = PDFUploadOrchestrator()
    
    # Run the complete process
    success = await orchestrator.run()
    
    if success:
        print("✓ Upload completed successfully!")
    else:
        print("✗ Upload failed!")
    
    return success


async def example_search_functionality():
    """Example of searching the uploaded content."""
    print("\n=== Search Functionality Examples ===")
    
    uploader = SearchUploader()
    
    try:
        # Search for text content
        print("\n1. Searching for text content...")
        text_results = await uploader.search_documents("financial report", top=5, content_type="text")
        print(f"Found {len(text_results)} text results")
        
        for i, result in enumerate(text_results[:3]):
            print(f"  {i+1}. {result.get('title', 'No title')} (Page {result.get('page_number', 'N/A')})")
            print(f"     {result.get('headline', 'No headline')[:100]}...")
        
        # Search for image content
        print("\n2. Searching for image content...")
        image_results = await uploader.search_documents("chart diagram", top=5, content_type="image")
        print(f"Found {len(image_results)} image results")
        
        for i, result in enumerate(image_results[:3]):
            print(f"  {i+1}. {result.get('title', 'No title')} (Page {result.get('page_number', 'N/A')})")
            print(f"     Objects: {result.get('objects_detected', [])}")
            print(f"     Confidence: {result.get('confidence_score', 0.0):.2f}")
        
        # Search all content types
        print("\n3. Searching all content types...")
        all_results = await uploader.search_documents("data analysis", top=10)
        print(f"Found {len(all_results)} total results")
        
        text_count = sum(1 for r in all_results if r.get('content_type') == 'text')
        image_count = sum(1 for r in all_results if r.get('content_type') == 'image')
        print(f"  - Text results: {text_count}")
        print(f"  - Image results: {image_count}")
        
    except Exception as e:
        print(f"Search failed: {e}")
    finally:
        await uploader.close()


async def example_index_management():
    """Example of index management operations."""
    print("\n=== Index Management Examples ===")
    
    uploader = SearchUploader()
    
    try:
        # Get index statistics
        stats = await uploader.get_index_statistics()
        if stats:
            print(f"Index Name: {stats['index_name']}")
            print(f"Total Documents: {stats['document_count']}")
            print(f"Field Count: {stats['field_count']}")
            print(f"Created: {stats.get('created_at', 'Unknown')}")
            print(f"Modified: {stats.get('modified_at', 'Unknown')}")
        
        # Note: Uncomment the following lines to recreate the index
        # print("\nRecreating index...")
        # await uploader.delete_index()
        # await uploader.create_or_update_index()
        # print("Index recreated successfully!")
        
    except Exception as e:
        print(f"Index management failed: {e}")
    finally:
        await uploader.close()


async def example_image_analysis_details():
    """Example of detailed image analysis workflow."""
    print("\n=== Image Analysis Details ===")
    
    from image_extractor import ImageExtractor
    from image_analyzer import ImageAnalyzer
    
    # Get first PDF file for demonstration
    pdf_dir = Path(settings.pdf_directory_path)
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found for image analysis example")
        return
    
    pdf_file = pdf_files[0]
    print(f"Analyzing images from: {pdf_file.name}")
    
    # Extract images
    extractor = ImageExtractor()
    extracted_images = await extractor.extract_images_from_pdf(pdf_file)
    
    print(f"Extracted {len(extracted_images)} images")
    
    if extracted_images:
        # Analyze first image
        analyzer = ImageAnalyzer()
        analyses = await analyzer.analyze_images(extracted_images[:1])  # Analyze first image only
        
        if analyses:
            analysis = analyses[0]
            print(f"\nImage Analysis Results:")
            print(f"  Image ID: {analysis.image_id}")
            print(f"  Description: {analysis.description[:200]}...")
            print(f"  Extracted Text: {analysis.extracted_text[:100]}...")
            print(f"  Objects Detected: {analysis.objects_detected}")
            print(f"  Confidence Score: {analysis.confidence_score:.2f}")
            print(f"  Tokens Used: {analysis.tokens_used}")


async def example_configuration_options():
    """Example of different configuration options."""
    print("\n=== Configuration Options ===")
    
    print(f"PDF Directory: {settings.pdf_directory_path}")
    print(f"Images Directory: {settings.extracted_images_path}")
    print(f"Extract Images: {settings.extract_images}")
    print(f"Image Min Size: {settings.image_min_size}px")
    print(f"Image Max Size: {settings.image_max_size}px")
    print(f"Image Quality: {settings.image_quality}%")
    print(f"Supported Formats: {settings.supported_image_formats}")
    print(f"Vision Model: {settings.azure_openai_vision_model}")
    print(f"Vision Detail Level: {settings.vision_detail_level}")
    print(f"Max Concurrent Images: {settings.max_concurrent_images}")
    print(f"Chunk Size: {settings.chunk_size}")
    print(f"Chunk Overlap: {settings.chunk_overlap}")
    print(f"Search Index: {settings.search_index_name}")


async def main():
    """Run all examples."""
    print("🚀 Enhanced PDF Upload with Image Extraction - Examples")
    print("=" * 60)
    
    # Show configuration
    await example_configuration_options()
    
    # Run basic upload
    success = await example_basic_upload()
    
    if success:
        # Run search examples
        await example_search_functionality()
        
        # Show index management
        await example_index_management()
        
        # Show image analysis details
        await example_image_analysis_details()
    
    print("\n" + "=" * 60)
    print("✓ All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
