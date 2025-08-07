"""
Test script for the enhanced PDF upload with image extraction system.
Validates the implementation components and functionality.
"""
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import shutil

# Test imports
try:
    from config import settings
    from pdf_processor import PDFProcessor
    from image_extractor import ImageExtractor, ExtractedImage
    from image_analyzer import ImageAnalyzer, ImageAnalysis
    from embedding_generator import EmbeddingGenerator
    from search_uploader import SearchUploader
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


async def test_configuration():
    """Test configuration loading."""
    print("\n🧪 Testing Configuration...")
    
    try:
        # Test basic configuration
        assert settings.azure_search_service_name, "Search service name not configured"
        assert settings.azure_openai_endpoint, "OpenAI endpoint not configured"
        assert settings.pdf_directory_path, "PDF directory not configured"
        assert settings.extracted_images_path, "Images directory not configured"
        
        # Test image-specific configuration
        assert isinstance(settings.extract_images, bool), "extract_images should be boolean"
        assert settings.image_min_size > 0, "image_min_size should be positive"
        assert settings.image_max_size > 0, "image_max_size should be positive"
        assert 0 < settings.image_quality <= 100, "image_quality should be between 1-100"
        assert settings.vision_detail_level in ["low", "high"], "vision_detail_level should be 'low' or 'high'"
        
        print("✅ Configuration validation passed")
        return True
        
    except AssertionError as e:
        print(f"❌ Configuration error: {e}")
        return False
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


async def test_image_extractor():
    """Test image extraction functionality."""
    print("\n🧪 Testing Image Extractor...")
    
    try:
        extractor = ImageExtractor()
        
        # Test directory creation
        assert Path(settings.extracted_images_path).exists(), "Images directory should exist"
        
        # Test base64 conversion with a mock image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            # Create a simple test image
            from PIL import Image
            test_img = Image.new('RGB', (100, 100), color='red')
            test_img.save(tmp_file.name)
            
            # Test base64 conversion
            base64_result = extractor.get_image_as_base64(tmp_file.name)
            assert base64_result is not None, "Base64 conversion should work"
            assert len(base64_result) > 0, "Base64 result should not be empty"
            
            # Cleanup
            Path(tmp_file.name).unlink()
        
        print("✅ Image extractor tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Image extractor test failed: {e}")
        return False


async def test_pdf_processor():
    """Test PDF processor functionality."""
    print("\n🧪 Testing PDF Processor...")
    
    try:
        processor = PDFProcessor()
        
        # Test chunk creation from mock image analysis
        mock_analysis = ImageAnalysis(
            image_id="test_image_1",
            description="Test image description",
            extracted_text="Test extracted text",
            objects_detected=["chart", "text"],
            confidence_score=0.95,
            analysis_timestamp=processor.encoding.__class__.__name__,  # Using a datetime placeholder
            tokens_used=50,
            image_path="/test/path/image.jpg",
            pdf_source="/test/path/document.pdf",
            page_number=1
        )
        
        from datetime import datetime
        mock_analysis.analysis_timestamp = datetime.now()
        
        # Test chunk creation
        chunks = processor.create_chunks_from_image_analyses([mock_analysis])
        assert len(chunks) == 1, "Should create one chunk from one analysis"
        
        chunk = chunks[0]
        assert chunk.content_type == "image", "Chunk should be marked as image type"
        assert "Test image description" in chunk.content, "Should contain image description"
        assert "Test extracted text" in chunk.content, "Should contain extracted text"
        assert chunk.page_number == 1, "Should preserve page number"
        
        print("✅ PDF processor tests passed")
        return True
        
    except Exception as e:
        print(f"❌ PDF processor test failed: {e}")
        return False


async def test_embedding_generator():
    """Test embedding generator functionality."""
    print("\n🧪 Testing Embedding Generator...")
    
    try:
        generator = EmbeddingGenerator()
        
        # Test URL construction
        assert generator.endpoint_url.endswith('/embeddings'), "Endpoint URL should end with /embeddings"
        assert generator.api_key, "API key should be configured"
        
        # Test text preparation
        long_text = "This is a test text. " * 1000  # Make it long
        prepared_text = generator._prepare_text_for_embedding(long_text)
        assert len(prepared_text) <= 7000, "Text should be truncated if too long"
        
        # Test embedding validation
        valid_embedding = [0.1] * settings.vector_dimensions
        assert generator._validate_embedding(valid_embedding), "Valid embedding should pass validation"
        
        invalid_embedding = [0.1] * (settings.vector_dimensions - 1)
        assert not generator._validate_embedding(invalid_embedding), "Invalid embedding should fail validation"
        
        print("✅ Embedding generator tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Embedding generator test failed: {e}")
        return False


async def test_search_uploader():
    """Test search uploader functionality."""
    print("\n🧪 Testing Search Uploader...")
    
    try:
        uploader = SearchUploader()
        
        # Test endpoint construction
        assert uploader.endpoint == settings.azure_search_endpoint, "Endpoint should match settings"
        assert uploader.index_name == settings.search_index_name, "Index name should match settings"
        
        # Test that the uploader can be created without errors
        assert uploader.credential is not None, "Credential should be set"
        assert uploader.index_client is not None, "Index client should be initialized"
        assert uploader.search_client is not None, "Search client should be initialized"
        
        print("✅ Search uploader tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Search uploader test failed: {e}")
        return False


async def test_integration_components():
    """Test integration between components."""
    print("\n🧪 Testing Component Integration...")
    
    try:
        # Test that all components can be initialized together
        pdf_processor = PDFProcessor()
        embedding_generator = EmbeddingGenerator()
        search_uploader = SearchUploader()
        
        # Test that PDF processor has access to image components
        assert pdf_processor.image_extractor is not None, "PDF processor should have image extractor"
        assert pdf_processor.image_analyzer is not None, "PDF processor should have image analyzer"
        
        # Test that embedding generator can handle both text and images
        assert hasattr(embedding_generator, 'generate_embeddings_for_chunks'), "Should have text embedding method"
        assert hasattr(embedding_generator, 'generate_embeddings_for_images'), "Should have image embedding method"
        
        # Test that search uploader supports image fields
        assert hasattr(search_uploader, 'upload_image_analyses'), "Should have image upload method"
        
        print("✅ Component integration tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Component integration test failed: {e}")
        return False


async def test_directory_structure():
    """Test directory structure and file permissions."""
    print("\n🧪 Testing Directory Structure...")
    
    try:
        # Test PDF directory
        pdf_dir = Path(settings.pdf_directory_path)
        assert pdf_dir.exists(), f"PDF directory should exist: {pdf_dir}"
        assert pdf_dir.is_dir(), "PDF directory should be a directory"
        
        # Test images directory
        images_dir = Path(settings.extracted_images_path)
        assert images_dir.exists(), f"Images directory should exist: {images_dir}"
        assert images_dir.is_dir(), "Images directory should be a directory"
        
        # Test write permissions
        test_file = images_dir / "test_write.txt"
        test_file.write_text("test")
        assert test_file.exists(), "Should be able to write to images directory"
        test_file.unlink()  # Clean up
        
        print("✅ Directory structure tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Directory structure test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🧪 Enhanced PDF Upload with Image Extraction - Test Suite")
    print("=" * 60)
    
    tests = [
        test_configuration,
        test_directory_structure,
        test_image_extractor,
        test_pdf_processor,
        test_embedding_generator,
        test_search_uploader,
        test_integration_components,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! The system is ready to use.")
        return 0
    else:
        print("❌ Some tests failed. Please check the configuration and dependencies.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
