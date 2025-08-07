"""
Image analyzer module for analyzing images using Azure OpenAI GPT-4 Vision.
Generates descriptions and extracts text from images.
"""
import asyncio
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

import aiohttp
import structlog
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential

from config import settings
from image_extractor import ExtractedImage

logger = structlog.get_logger(__name__)


@dataclass
class ImageAnalysis:
    """Represents the analysis result of an image."""
    image_id: str
    description: str
    extracted_text: str
    objects_detected: List[str]
    confidence_score: float
    analysis_timestamp: datetime
    tokens_used: int
    image_path: str
    pdf_source: str
    page_number: int


class ImageAnalyzer:
    """Handles image analysis using Azure OpenAI GPT-4 Vision."""
    
    def __init__(self):
        self.endpoint = settings.azure_openai_endpoint
        self.api_key = settings.azure_openai_key
        self.deployment_name = settings.azure_openai_vision_deployment
        self.api_version = "2023-12-01-preview"
        self.max_concurrent = settings.max_concurrent_images
        
        # Setup authentication
        if self.api_key:
            self.credential = AzureKeyCredential(self.api_key)
        else:
            self.credential = DefaultAzureCredential()
    
    async def analyze_images(self, extracted_images: List[ExtractedImage]) -> List[ImageAnalysis]:
        """
        Analyze a list of extracted images.
        
        Args:
            extracted_images: List of ExtractedImage objects
            
        Returns:
            List of ImageAnalysis objects
        """
        if not extracted_images:
            return []
        
        logger.info("Starting image analysis", image_count=len(extracted_images))
        
        # Create semaphore for concurrent processing
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Create analysis tasks
        tasks = [
            self._analyze_single_image(image, semaphore)
            for image in extracted_images
        ]
        
        # Execute tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and collect successful results
        analyses = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("Image analysis failed", error=str(result))
                continue
            if result:
                analyses.append(result)
        
        logger.info("Image analysis completed", 
                   total_images=len(extracted_images),
                   successful_analyses=len(analyses))
        
        return analyses
    
    async def _analyze_single_image(
        self, 
        extracted_image: ExtractedImage, 
        semaphore: asyncio.Semaphore
    ) -> Optional[ImageAnalysis]:
        """
        Analyze a single image using GPT-4 Vision.
        
        Args:
            extracted_image: ExtractedImage object
            semaphore: Semaphore for concurrency control
            
        Returns:
            ImageAnalysis object or None if failed
        """
        async with semaphore:
            try:
                logger.debug("Analyzing image", image_id=extracted_image.id)
                
                # Read image file and convert to base64
                from image_extractor import ImageExtractor
                extractor = ImageExtractor()
                base64_image = extractor.get_image_as_base64(extracted_image.image_path)
                
                if not base64_image:
                    logger.error("Failed to convert image to base64", image_id=extracted_image.id)
                    return None
                
                # Prepare the request
                url = f"{self.endpoint}/openai/deployments/{self.deployment_name}/chat/completions"
                
                headers = {
                    "Content-Type": "application/json",
                    "api-key": self.api_key
                }
                
                payload = {
                    "model": settings.azure_openai_vision_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": self._get_analysis_prompt()
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}",
                                        "detail": settings.vision_detail_level
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": settings.vision_max_tokens,
                    "temperature": settings.vision_temperature
                }
                
                # Make the API call
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            return self._process_analysis_response(result, extracted_image)
                        else:
                            error_text = await response.text()
                            logger.error(
                                "Vision API call failed",
                                image_id=extracted_image.id,
                                status_code=response.status,
                                error=error_text
                            )
                            return None
                            
            except Exception as e:
                logger.error("Error analyzing image", image_id=extracted_image.id, error=str(e))
                return None
    
    def _get_analysis_prompt(self) -> str:
        """
        Get the prompt for image analysis.
        
        Returns:
            Analysis prompt string
        """
        return """
        Please analyze this image and provide a comprehensive description. 
        Return your response in JSON format with the following structure:
        {
            "description": "Detailed description of the image content, including objects, people, text, charts, diagrams, etc.",
            "extracted_text": "Any text visible in the image (OCR)",
            "objects_detected": ["list", "of", "objects", "or", "elements", "detected"],
            "confidence_score": 0.95
        }
        
        Focus on:
        1. Visual elements and their relationships
        2. Any text content (perform OCR)
        3. Charts, graphs, diagrams, or tables
        4. People, objects, and scenes
        5. Colors, layout, and composition
        6. Context and purpose of the image
        
        Make the description detailed and searchable, as it will be used for document search and retrieval.
        """
    
    def _process_analysis_response(
        self, 
        response: Dict, 
        extracted_image: ExtractedImage
    ) -> Optional[ImageAnalysis]:
        """
        Process the API response and create ImageAnalysis object.
        
        Args:
            response: API response dictionary
            extracted_image: Original ExtractedImage object
            
        Returns:
            ImageAnalysis object or None if failed
        """
        try:
            # Extract response content
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = response.get("usage", {})
            
            if not content:
                logger.warning("Empty response from vision API", image_id=extracted_image.id)
                return None
            
            # Try to parse JSON response
            try:
                # Find JSON content in the response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start != -1 and json_end != -1:
                    json_content = content[json_start:json_end]
                    analysis_data = json.loads(json_content)
                else:
                    # Fallback: create analysis from plain text
                    analysis_data = {
                        "description": content,
                        "extracted_text": "",
                        "objects_detected": [],
                        "confidence_score": 0.8
                    }
                    
            except json.JSONDecodeError:
                # Fallback: create analysis from plain text
                analysis_data = {
                    "description": content,
                    "extracted_text": "",
                    "objects_detected": [],
                    "confidence_score": 0.8
                }
            
            # Create ImageAnalysis object
            return ImageAnalysis(
                image_id=extracted_image.id,
                description=analysis_data.get("description", ""),
                extracted_text=analysis_data.get("extracted_text", ""),
                objects_detected=analysis_data.get("objects_detected", []),
                confidence_score=analysis_data.get("confidence_score", 0.8),
                analysis_timestamp=datetime.now(),
                tokens_used=usage.get("total_tokens", 0),
                image_path=extracted_image.image_path,
                pdf_source=extracted_image.pdf_source,
                page_number=extracted_image.page_number
            )
            
        except Exception as e:
            logger.error("Error processing analysis response", image_id=extracted_image.id, error=str(e))
            return None
    
    def create_search_chunk_from_analysis(self, analysis: ImageAnalysis) -> Dict:
        """
        Create a search chunk from image analysis for indexing.
        
        Args:
            analysis: ImageAnalysis object
            
        Returns:
            Dictionary representing a search chunk
        """
        # Combine description and extracted text
        combined_content = f"{analysis.description}\n\n"
        if analysis.extracted_text:
            combined_content += f"Text extracted from image: {analysis.extracted_text}"
        
        # Create headline
        headline = f"Image from page {analysis.page_number}"
        if analysis.objects_detected:
            headline += f" - Contains: {', '.join(analysis.objects_detected[:3])}"
        
        return {
            "id": f"image_{analysis.image_id}",
            "title": f"Image Analysis - {analysis.image_id}",
            "content": combined_content,
            "headline": headline,
            "content_type": "image",
            "file_name": Path(analysis.pdf_source).name,
            "page_number": analysis.page_number,
            "image_path": analysis.image_path,
            "objects_detected": analysis.objects_detected,
            "confidence_score": analysis.confidence_score,
            "analysis_timestamp": analysis.analysis_timestamp.isoformat(),
            "tokens_used": analysis.tokens_used,
            "chunk_index": 0,  # Images are single chunks
            "created_at": analysis.analysis_timestamp,
            "token_count": len(combined_content.split())  # Approximate token count
        }
