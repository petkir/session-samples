"""
Configuration settings for the PDF upload to Azure AI Search application.
Uses Pydantic for validation and type safety.
"""
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # Azure AI Search Configuration
    azure_search_service_name: str = Field(..., description="Azure AI Search service name")
    azure_search_admin_key: str = Field(..., description="Azure AI Search admin key")
    azure_search_api_version: str = Field(default="2023-11-01", description="Azure AI Search API version")
    
    # Azure OpenAI Configuration
    azure_openai_endpoint: str = Field(..., description="Azure OpenAI endpoint URL")
    azure_openai_key: str = Field(..., description="Azure OpenAI API key")
    azure_openai_embedding_model: str = Field(default="text-embedding-ada-002", description="Embedding model name")
    azure_openai_deployment_name: str = Field(default="text-embedding-ada-002", description="Azure OpenAI deployment name")
    
    # Entra ID Configuration for Group-Based Permissions
    azure_tenant_id: str = Field(..., description="Azure tenant ID")
    azure_client_id: str = Field(..., description="Azure application client ID")
    azure_client_secret: str = Field(..., description="Azure application client secret")
    azure_authority: str = Field(..., description="Azure authority URL")
    
    # Document Permission Configuration
    document_access_groups: str = Field(default="", description="Comma-separated list of group IDs that can access documents")
    default_document_group: str = Field(default="", description="Default group ID for documents without specific group assignment")
    
    # PDF Processing Configuration
    pdf_directory_path: str = Field(default="./pdfs", description="Directory containing PDF files")
    chunk_size: int = Field(default=1000, ge=100, le=8000, description="Text chunk size in characters")
    chunk_overlap: int = Field(default=200, ge=0, le=1000, description="Overlap between chunks")
    max_concurrent_pdfs: int = Field(default=5, ge=1, le=20, description="Maximum concurrent PDF processing")
    max_concurrent_chunks: int = Field(default=10, ge=1, le=50, description="Maximum concurrent chunk processing")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")
    
    # Search Index Configuration
    search_index_name: str = Field(default="pdf-documents", description="Azure AI Search index name")
    vector_dimensions: int = Field(default=1536, description="Vector embedding dimensions")
    
    @validator('pdf_directory_path')
    def validate_pdf_directory(cls, v):
        """Validate that PDF directory exists."""
        if not os.path.exists(v):
            os.makedirs(v, exist_ok=True)
        return v
    
    @validator('chunk_overlap')
    def validate_chunk_overlap(cls, v, values):
        """Validate that chunk overlap is less than chunk size."""
        if 'chunk_size' in values and v >= values['chunk_size']:
            raise ValueError("Chunk overlap must be less than chunk size")
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    @property
    def azure_search_endpoint(self) -> str:
        """Generate Azure AI Search endpoint URL."""
        return f"https://{self.azure_search_service_name}.search.windows.net"
    
    @property
    def document_access_groups_list(self) -> List[str]:
        """Get document access groups as a list."""
        if not self.document_access_groups:
            return []
        return [group.strip() for group in self.document_access_groups.split(',') if group.strip()]
    
    @property
    def graph_scopes(self) -> List[str]:
        """Get required Microsoft Graph scopes."""
        return [
            "https://graph.microsoft.com/User.Read",
            "https://graph.microsoft.com/Group.Read.All",
            "https://graph.microsoft.com/GroupMember.Read.All"
        ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
