"""Enhanced OCR processing for handwritten and printed text."""

import logging
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


class OCRProcessor:
    """Enhanced OCR processor with preprocessing for better handwriting recognition."""

    def __init__(self, tesseract_path: str | None = None):
        """Initialize OCR processor.

        Args:
            tesseract_path: Optional path to tesseract executable
        """
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        self.supported_formats = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"}

    def process_image(
        self,
        image_path: Path,
        preprocess: bool = True,
        handwritten: bool = False,
    ) -> dict[str, Any]:
        """Process image with OCR to extract text.

        Args:
            image_path: Path to image file
            preprocess: Whether to apply image preprocessing
            handwritten: Whether to optimize for handwritten text

        Returns:
            Dictionary with OCR results and metadata
        """
        try:
            # Load image
            image = Image.open(image_path)

            # Apply preprocessing if requested
            if preprocess:
                image = self._preprocess_image(image, handwritten)

            # Configure OCR based on content type
            config = self._get_ocr_config(handwritten)

            # Extract text with confidence scores
            ocr_data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT,
                config=config,
            )

            # Process results
            text = self._extract_text_from_data(ocr_data)
            confidence = self._calculate_confidence(ocr_data)

            # Detect text structure
            structure = self._detect_text_structure(ocr_data)

            return {
                "text": text,
                "confidence": confidence,
                "structure": structure,
                "word_count": len(text.split()),
                "preprocessing_applied": preprocess,
                "handwritten_mode": handwritten,
                "image_size": image.size,
            }

        except Exception as e:
            logger.exception(f"OCR processing failed for {image_path}: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "error": str(e),
                "preprocessing_applied": preprocess,
                "handwritten_mode": handwritten,
            }

    def _preprocess_image(self, image: Image.Image, handwritten: bool) -> Image.Image:
        """Apply preprocessing to improve OCR accuracy.

        Args:
            image: PIL Image object
            handwritten: Whether optimizing for handwritten text

        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        if image.mode != "L":
            image = image.convert("L")

        # Convert to OpenCV format for advanced processing
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        if handwritten:
            # Preprocessing for handwritten text
            cv_image = self._preprocess_handwritten(cv_image)
        else:
            # Preprocessing for printed text
            cv_image = self._preprocess_printed(cv_image)

        # Convert back to PIL
        return Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))

    def _preprocess_handwritten(self, cv_image: np.ndarray) -> np.ndarray:
        """Preprocessing optimized for handwritten text.

        Args:
            cv_image: OpenCV image array

        Returns:
            Preprocessed image array
        """
        # Gaussian blur to smooth out rough edges
        cv_image = cv2.GaussianBlur(cv_image, (1, 1), 0)

        # Adaptive thresholding for varying lighting
        cv_image = cv2.adaptiveThreshold(
            cv_image,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2,
        )

        # Morphological operations to connect broken characters
        kernel = np.ones((1, 1), np.uint8)
        return cv2.morphologyEx(cv_image, cv2.MORPH_CLOSE, kernel)

    def _preprocess_printed(self, cv_image: np.ndarray) -> np.ndarray:
        """Preprocessing optimized for printed text.

        Args:
            cv_image: OpenCV image array

        Returns:
            Preprocessed image array
        """
        # Noise removal
        cv_image = cv2.medianBlur(cv_image, 3)

        # Thresholding
        _, cv_image = cv2.threshold(cv_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Dilation and erosion to remove noise
        kernel = np.ones((1, 1), np.uint8)
        cv_image = cv2.dilate(cv_image, kernel, iterations=1)
        return cv2.erode(cv_image, kernel, iterations=1)

    def _get_ocr_config(self, handwritten: bool) -> str:
        """Get Tesseract configuration based on content type.

        Args:
            handwritten: Whether optimizing for handwritten text

        Returns:
            Tesseract configuration string
        """
        if handwritten:
            # Configuration for handwritten text
            return "--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?;:()[]{}+-=*/<>@#$%^&_|~` "
        # Configuration for printed text
        return "--psm 6"

    def _extract_text_from_data(self, ocr_data: dict) -> str:
        """Extract clean text from OCR data.

        Args:
            ocr_data: Raw OCR data from pytesseract

        Returns:
            Cleaned text string
        """
        words = []
        for i, word in enumerate(ocr_data["text"]):
            if int(ocr_data["conf"][i]) > 30:  # Filter low-confidence words
                word = word.strip()
                if word:
                    words.append(word)

        return " ".join(words)

    def _calculate_confidence(self, ocr_data: dict) -> float:
        """Calculate overall confidence score.

        Args:
            ocr_data: Raw OCR data from pytesseract

        Returns:
            Average confidence score (0.0 to 1.0)
        """
        confidences = [int(conf) for conf in ocr_data["conf"] if int(conf) > 0]
        if confidences:
            return sum(confidences) / len(confidences) / 100.0
        return 0.0

    def _detect_text_structure(self, ocr_data: dict) -> dict[str, Any]:
        """Detect text structure like headers, paragraphs, lists.

        Args:
            ocr_data: Raw OCR data from pytesseract

        Returns:
            Dictionary describing text structure
        """
        # Group words by lines based on vertical position
        lines = {}
        for i, (top, text) in enumerate(zip(ocr_data["top"], ocr_data["text"], strict=False)):
            if text.strip() and int(ocr_data["conf"][i]) > 30:
                line_key = top // 10  # Group by approximate line
                if line_key not in lines:
                    lines[line_key] = []
                lines[line_key].append(text.strip())

        # Analyze structure
        line_texts = []
        for line_key in sorted(lines.keys()):
            line_text = " ".join(lines[line_key])
            line_texts.append(line_text)

        # Detect potential headers (short lines, possibly all caps)
        headers = []
        paragraphs = []

        for line in line_texts:
            if len(line) < 50 and (line.isupper() or line.istitle()):
                headers.append(line)
            elif len(line) > 20:
                paragraphs.append(line)

        return {
            "total_lines": len(line_texts),
            "potential_headers": headers,
            "paragraphs": paragraphs,
            "has_structure": len(headers) > 0 or len(paragraphs) > 1,
        }

    def format_ocr_markdown(self, ocr_result: dict[str, Any], title: str | None = None) -> str:
        """Format OCR results as structured markdown.

        Args:
            ocr_result: OCR processing results
            title: Optional title for the document

        Returns:
            Formatted markdown content
        """
        lines = []

        if title:
            lines.append(f"# {title}")
            lines.append("")

        # Add metadata
        lines.append("## OCR Metadata")
        lines.append(f"- **Confidence**: {ocr_result.get('confidence', 0.0):.1%}")
        lines.append(f"- **Word Count**: {ocr_result.get('word_count', 0)}")
        lines.append(f"- **Handwritten Mode**: {ocr_result.get('handwritten_mode', False)}")
        lines.append(
            f"- **Preprocessing Applied**: {ocr_result.get('preprocessing_applied', False)}",
        )

        if "image_size" in ocr_result:
            size = ocr_result["image_size"]
            lines.append(f"- **Image Size**: {size[0]}×{size[1]} pixels")

        if "error" in ocr_result:
            lines.append(f"- **Error**: {ocr_result['error']}")

        lines.append("")

        # Add extracted content
        lines.append("## Extracted Content")
        lines.append("")

        text = ocr_result.get("text", "")
        if text:
            # Try to preserve structure if detected
            structure = ocr_result.get("structure", {})
            if structure.get("has_structure"):
                # Add headers
                for header in structure.get("potential_headers", []):
                    lines.append(f"### {header}")
                    lines.append("")

                # Add paragraphs
                for paragraph in structure.get("paragraphs", []):
                    lines.append(paragraph)
                    lines.append("")
            else:
                # Just add the text as paragraphs
                paragraphs = text.split("\n\n")
                for paragraph in paragraphs:
                    if paragraph.strip():
                        lines.append(paragraph.strip())
                        lines.append("")
        else:
            lines.append("*No text extracted*")

        return "\n".join(lines)
