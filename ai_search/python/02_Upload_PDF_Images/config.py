"""
Configuration settings for the PDF upload with image extraction to Azure AI Search application.
Uses Pydantic for validation and type safety.
"""
from typing import Optional, List
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application settings with validation."""
    
    model_config = ConfigDict(env_file=".env", case_sensitive=False)
    
    # Azure AI Search Configuration
    azure_search_service_name: str = Field(..., description="Azure AI Search service name")
    azure_search_admin_key: str = Field(..., description="Azure AI Search admin key")
    azure_search_api_version: str = Field(default="2023-11-01", description="Azure AI Search API version")
    
    # Azure OpenAI Configuration
    azure_openai_endpoint: str = Field(..., description="Azure OpenAI endpoint URL")
    azure_openai_key: str = Field(..., description="Azure OpenAI API key")
    azure_openai_embedding_model: str = Field(default="text-embedding-ada-002", description="Embedding model name")
    azure_openai_embedding_deployment: str = Field(default="text-embedding-ada-002", description="Azure OpenAI embedding deployment name")
    
    # Azure OpenAI Vision Configuration (NEW)
    azure_openai_vision_model: str = Field(default="gpt-4-vision-preview", description="Vision model name")
    azure_openai_vision_deployment: str = Field(default="gpt-4-vision-preview", description="Azure OpenAI vision deployment name")
    
    # PDF Processing Configuration
    pdf_directory_path: str = Field(default="./pdfs", description="Directory containing PDF files")
    extracted_images_path: str = Field(default="./extracted_images", description="Directory for extracted images")
    chunk_size: int = Field(default=1000, ge=100, le=8000, description="Text chunk size in characters")
    chunk_overlap: int = Field(default=200, ge=0, le=1000, description="Overlap between chunks")
    max_concurrent_pdfs: int = Field(default=5, ge=1, le=20, description="Maximum concurrent PDF processing")
    max_concurrent_chunks: int = Field(default=10, ge=1, le=50, description="Maximum concurrent chunk processing")
    max_concurrent_images: int = Field(default=3, ge=1, le=10, description="Maximum concurrent image processing")
    
    # Image Processing Configuration (NEW)
    extract_images: bool = Field(default=True, description="Enable image extraction from PDFs")
    image_min_size: int = Field(default=100, description="Minimum image size in pixels")
    image_max_size: int = Field(default=2048, description="Maximum image size in pixels")
    image_quality: int = Field(default=85, ge=1, le=100, description="Image quality for JPEG compression")
    supported_image_formats: str = Field(default="JPEG,PNG,TIFF", description="Supported image formats")
    
    # Vision Analysis Configuration (NEW)
    vision_max_tokens: int = Field(default=1000, description="Maximum tokens for vision analysis")
    vision_temperature: float = Field(default=0.1, ge=0.0, le=1.0, description="Temperature for vision analysis")
    vision_detail_level: str = Field(default="high", description="Vision analysis detail level (low/high)")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")
    
    # Search Index Configuration
    search_index_name: str = Field(default="pdf-documents-with-images", description="Azure AI Search index name")
    vector_dimensions: int = Field(default=1536, description="Vector embedding dimensions")
    
    @field_validator('pdf_directory_path')
    @classmethod
    def validate_pdf_directory(cls, v):
        """Validate that PDF directory exists."""
        if not os.path.exists(v):
            os.makedirs(v, exist_ok=True)
        return v
    
    @field_validator('extracted_images_path')
    @classmethod
    def validate_images_directory(cls, v):
        """Validate that images directory exists."""
        if not os.path.exists(v):
            os.makedirs(v, exist_ok=True)
        return v
    
    @field_validator('chunk_overlap')
    @classmethod
    def validate_chunk_overlap(cls, v, info):
        """Validate that chunk overlap is less than chunk size."""
        if info.data and 'chunk_size' in info.data and v >= info.data['chunk_size']:
            raise ValueError("Chunk overlap must be less than chunk size")
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    @field_validator('vision_detail_level')
    @classmethod
    def validate_vision_detail_level(cls, v):
        """Validate vision detail level."""
        valid_levels = ['low', 'high']
        if v.lower() not in valid_levels:
            raise ValueError(f"Vision detail level must be one of {valid_levels}")
        return v.lower()
    
    @property
    def azure_search_endpoint(self) -> str:
        """Generate Azure AI Search endpoint URL."""
        return f"https://{self.azure_search_service_name}.search.windows.net"
    
    @property
    def supported_image_formats_list(self) -> List[str]:
        """Get list of supported image formats."""
        return [fmt.strip().upper() for fmt in self.supported_image_formats.split(',')]


# Global settings instance
settings = Settings()
