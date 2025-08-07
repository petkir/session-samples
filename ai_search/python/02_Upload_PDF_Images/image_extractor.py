"""
Image extractor module for extracting images from PDF files.
Handles various PDF formats and saves images for further processing.
"""
import os
import hashlib
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import asyncio
from dataclasses import dataclass
from datetime import datetime
import base64
import io

import fitz  # PyMuPDF
from PIL import Image
import structlog

from config import settings

logger = structlog.get_logger(__name__)


@dataclass
class ExtractedImage:
    """Represents an image extracted from a PDF document."""
    id: str
    file_name: str
    page_number: int
    image_index: int
    image_path: str
    image_format: str
    image_size: Tuple[int, int]
    file_size: int
    created_at: datetime
    pdf_source: str


class ImageExtractor:
    """Handles image extraction from PDF files."""
    
    def __init__(self):
        self.output_dir = Path(settings.extracted_images_path)
        self.output_dir.mkdir(exist_ok=True)
        
    async def extract_images_from_pdf(self, pdf_path: Path) -> List[ExtractedImage]:
        """
        Extract all images from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of ExtractedImage objects
        """
        try:
            logger.info("Extracting images from PDF", pdf_path=str(pdf_path))
            
            # Run image extraction in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            extracted_images = await loop.run_in_executor(
                None, self._extract_images_sync, pdf_path
            )
            
            logger.info(
                "Image extraction completed",
                pdf_path=str(pdf_path),
                image_count=len(extracted_images)
            )
            
            return extracted_images
            
        except Exception as e:
            logger.error("Failed to extract images from PDF", pdf_path=str(pdf_path), error=str(e))
            return []
    
    def _extract_images_sync(self, pdf_path: Path) -> List[ExtractedImage]:
        """
        Synchronous image extraction from PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of ExtractedImage objects
        """
        extracted_images = []
        
        try:
            # Open PDF document
            doc = fitz.open(str(pdf_path))
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images(full=True)
                
                for img_index, img in enumerate(image_list):
                    try:
                        # Get image data
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        # Skip if image is too small
                        if pix.width < settings.image_min_size or pix.height < settings.image_min_size:
                            pix = None
                            continue
                        
                        # Convert to RGB if necessary
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            img_data = pix.tobytes("png")
                            img_format = "PNG"
                        else:  # CMYK: convert to RGB first
                            pix1 = fitz.Pixmap(fitz.csRGB, pix)
                            img_data = pix1.tobytes("png")
                            img_format = "PNG"
                            pix1 = None
                        
                        # Process image with PIL
                        pil_image = Image.open(io.BytesIO(img_data))
                        
                        # Resize if too large
                        if max(pil_image.size) > settings.image_max_size:
                            pil_image.thumbnail(
                                (settings.image_max_size, settings.image_max_size),
                                Image.Resampling.LANCZOS
                            )
                        
                        # Generate unique filename
                        image_hash = hashlib.md5(img_data).hexdigest()[:8]
                        filename = f"{pdf_path.stem}_page{page_num + 1}_img{img_index + 1}_{image_hash}.{img_format.lower()}"
                        image_path = self.output_dir / filename
                        
                        # Save image
                        if img_format.upper() == "JPEG":
                            pil_image.save(image_path, format="JPEG", quality=settings.image_quality)
                        else:
                            pil_image.save(image_path, format=img_format)
                        
                        # Create ExtractedImage object
                        extracted_image = ExtractedImage(
                            id=f"{pdf_path.stem}_page{page_num + 1}_img{img_index + 1}",
                            file_name=filename,
                            page_number=page_num + 1,
                            image_index=img_index + 1,
                            image_path=str(image_path),
                            image_format=img_format,
                            image_size=pil_image.size,
                            file_size=image_path.stat().st_size,
                            created_at=datetime.now(),
                            pdf_source=str(pdf_path)
                        )
                        
                        extracted_images.append(extracted_image)
                        
                        logger.debug(
                            "Image extracted",
                            pdf_path=str(pdf_path),
                            page_num=page_num + 1,
                            image_index=img_index + 1,
                            image_size=pil_image.size,
                            file_size=extracted_image.file_size
                        )
                        
                        # Clean up
                        pix = None
                        
                    except Exception as e:
                        logger.warning(
                            "Failed to extract image",
                            pdf_path=str(pdf_path),
                            page_num=page_num + 1,
                            image_index=img_index + 1,
                            error=str(e)
                        )
                        continue
            
            doc.close()
            
        except Exception as e:
            logger.error("Error processing PDF for image extraction", pdf_path=str(pdf_path), error=str(e))
            
        return extracted_images
    
    def get_image_as_base64(self, image_path: str) -> Optional[str]:
        """
        Convert image to base64 string for API calls.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string or None if failed
        """
        try:
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                return base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            logger.error("Failed to convert image to base64", image_path=image_path, error=str(e))
            return None
    
    def cleanup_extracted_images(self, max_age_days: int = 7) -> None:
        """
        Clean up old extracted images.
        
        Args:
            max_age_days: Maximum age in days for keeping images
        """
        try:
            current_time = datetime.now()
            
            for image_file in self.output_dir.glob("*"):
                if image_file.is_file():
                    file_age = current_time - datetime.fromtimestamp(image_file.stat().st_mtime)
                    
                    if file_age.days > max_age_days:
                        image_file.unlink()
                        logger.debug("Cleaned up old image", image_path=str(image_file))
                        
        except Exception as e:
            logger.warning("Failed to cleanup extracted images", error=str(e))
