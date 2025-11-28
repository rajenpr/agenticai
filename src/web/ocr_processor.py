"""
OCR Processing Module for Screenshot Text Extraction.
Extracts text from uploaded screenshot images using Tesseract OCR.
"""
import os
import io
from typing import Optional, Dict
from PIL import Image
import pytesseract
import logging

logger = logging.getLogger(__name__)


class OCRProcessor:
    """
    OCR processor for extracting text from screenshot images.
    """

    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize OCR processor.

        Args:
            tesseract_cmd: Path to tesseract executable (optional)
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        elif os.environ.get("TESSERACT_CMD"):
            pytesseract.pytesseract.tesseract_cmd = os.environ.get("TESSERACT_CMD")

        logger.info("OCR Processor initialized")

    def extract_text_from_image(
        self,
        image_data: bytes,
        lang: str = 'eng'
    ) -> Dict[str, any]:
        """
        Extract text from image bytes.

        Args:
            image_data: Image file bytes
            lang: Language for OCR (default: 'eng' for English)

        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(image_data))

            logger.info(f"Processing image: size={image.size}, mode={image.mode}")

            # Perform OCR
            text = pytesseract.image_to_string(image, lang=lang)

            # Get additional data (confidence, bounding boxes)
            data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)

            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if conf != '-1']
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            result = {
                'success': True,
                'text': text.strip(),
                'confidence': round(avg_confidence, 2),
                'image_size': image.size,
                'word_count': len(text.split()),
                'char_count': len(text)
            }

            logger.info(f"OCR successful: {result['word_count']} words extracted")
            return result

        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': ''
            }

    def extract_text_from_file(self, file_path: str, lang: str = 'eng') -> Dict[str, any]:
        """
        Extract text from image file path.

        Args:
            file_path: Path to image file
            lang: Language for OCR

        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            with open(file_path, 'rb') as f:
                image_data = f.read()

            return self.extract_text_from_image(image_data, lang)

        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': ''
            }

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results.

        Args:
            image: PIL Image object

        Returns:
            Preprocessed PIL Image
        """
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')

        # Increase contrast (optional, can improve accuracy)
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        return image

    def extract_text_with_preprocessing(
        self,
        image_data: bytes,
        lang: str = 'eng'
    ) -> Dict[str, any]:
        """
        Extract text with image preprocessing for better accuracy.

        Args:
            image_data: Image file bytes
            lang: Language for OCR

        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            # Open and preprocess image
            image = Image.open(io.BytesIO(image_data))
            processed_image = self.preprocess_image(image)

            logger.info("Performing OCR with preprocessing")

            # Perform OCR on processed image
            text = pytesseract.image_to_string(processed_image, lang=lang)

            result = {
                'success': True,
                'text': text.strip(),
                'preprocessed': True,
                'word_count': len(text.split()),
                'char_count': len(text)
            }

            logger.info(f"OCR with preprocessing successful: {result['word_count']} words")
            return result

        except Exception as e:
            logger.error(f"OCR preprocessing error: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': ''
            }


# Singleton instance
_ocr_processor = None


def get_ocr_processor() -> OCRProcessor:
    """Get or create OCR processor instance."""
    global _ocr_processor
    if _ocr_processor is None:
        _ocr_processor = OCRProcessor()
    return _ocr_processor
