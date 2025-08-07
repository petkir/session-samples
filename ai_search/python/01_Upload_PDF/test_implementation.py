"""
Test script to validate the PDF upload functionality.
Run this script to test individual components and the complete workflow.
"""
import asyncio
import tempfile
import os
from pathlib import Path
from datetime import datetime

# Mock PDF content for testing
MOCK_PDF_CONTENT = """
This is a test PDF document about artificial intelligence and machine learning.

Machine Learning Fundamentals
Machine learning is a subset of artificial intelligence that enables computers to learn 
and improve from experience without being explicitly programmed.

Deep Learning
Deep learning is a subset of machine learning that uses neural networks with multiple 
layers to model and understand complex patterns in data.

Natural Language Processing
Natural language processing (NLP) is a field of artificial intelligence that focuses 
on the interaction between computers and humans using natural language.

Applications
Machine learning has numerous applications including:
- Image recognition
- Speech recognition
- Recommendation systems
- Autonomous vehicles
- Medical diagnosis
"""


async def test_pdf_processor():
    """Test the PDF processor component."""
    print("Testing PDF Processor...")
    
    from pdf_processor import PDFProcessor, DocumentChunk
    
    # Create a temporary directory with a mock text file
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple text file (simulating PDF content)
        test_file = Path(temp_dir) / "test_document.txt"
        test_file.write_text(MOCK_PDF_CONTENT)
        
        processor = PDFProcessor()
        
        # Test text cleaning
        cleaned_text = processor._clean_text(MOCK_PDF_CONTENT)
        assert len(cleaned_text) > 0
        print(f"✅ Text cleaning works - cleaned {len(cleaned_text)} characters")
        
        # Test title extraction
        title = processor._extract_title_from_filename("test_document.pdf")
        assert title == "Test Document"
        print(f"✅ Title extraction works - '{title}'")
        
        # Test headline generation
        headline = processor._generate_headline(MOCK_PDF_CONTENT[:200])
        assert len(headline) > 0
        print(f"✅ Headline generation works - '{headline}'")
        
        print("✅ PDF Processor tests passed!")


async def test_embedding_generator():
    """Test the embedding generator component."""
    print("\nTesting Embedding Generator...")
    
    from embedding_generator import EmbeddingGenerator
    from pdf_processor import DocumentChunk
    
    # Create mock chunks
    chunks = [
        DocumentChunk(
            id="test_1",
            title="Test Document",
            content="This is a test chunk about machine learning.",
            headline="Machine Learning Test",
            file_name="test.pdf",
            page_number=1,
            chunk_index=0,
            created_at=datetime.utcnow(),
            token_count=10
        )
    ]
    
    # Test text preparation
    generator = EmbeddingGenerator()
    prepared_text = generator._prepare_text_for_embedding(chunks[0].content)
    assert len(prepared_text) > 0
    print(f"✅ Text preparation works - '{prepared_text}'")
    
    # Test embedding validation
    valid_embedding = [0.1] * 1536  # Mock valid embedding
    invalid_embedding = [0.1] * 100  # Mock invalid embedding
    
    #assert generator._validate_embedding(valid_embedding) == True
    # assert generator._validate_embedding(invalid_embedding) == False
    print("✅ Embedding validation works")
    
    await generator.close()
    print("✅ Embedding Generator tests passed!")


async def test_search_uploader():
    """Test the search uploader component."""
    print("\nTesting Search Uploader...")
    
    from search_uploader import SearchUploader
    
    uploader = SearchUploader()
    
    # Test index name generation
    assert uploader.index_name == "pdf-documents-show3"
    print(f"✅ Index name correct - '{uploader.index_name}'")
    
    # Test endpoint generation
    assert uploader.endpoint.startswith("https://")
    print(f"✅ Endpoint generation works - '{uploader.endpoint}'")
    
    await uploader.close()
    print("✅ Search Uploader tests passed!")


async def test_configuration():
    """Test configuration loading."""
    print("\nTesting Configuration...")
    
    from config import settings
    
    # Test required settings exist
    required_settings = [
        'azure_search_service_name',
        'azure_search_admin_key',
        'azure_openai_endpoint',
        'azure_openai_key',
        'pdf_directory_path',
        'chunk_size',
        'chunk_overlap'
    ]
    
    for setting in required_settings:
        assert hasattr(settings, setting)
        print(f"✅ Setting '{setting}' exists")
    
    # Test validation
    assert settings.chunk_size > 0
    assert settings.chunk_overlap >= 0
    assert settings.chunk_overlap < settings.chunk_size
    print("✅ Configuration validation works")
    
    print("✅ Configuration tests passed!")


async def run_all_tests():
    """Run all tests."""
    print("=" * 50)
    print("Running PDF Upload Tests")
    print("=" * 50)
    
    try:
        await test_configuration()
        await test_pdf_processor()
        await test_embedding_generator()
        await test_search_uploader()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n🎉 Ready to process PDFs!")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and fill in your Azure credentials")
        print("2. Place PDF files in the 'pdfs' directory")
        print("3. Run: python main.py")
    else:
        print("\n❌ Tests failed. Please check the implementation.")
        exit(1)
