"""Metadata extraction utilities."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extract metadata from documents and file paths."""

    def __init__(self):
        """Initialize metadata extractor."""
        self.course_patterns = [
            r"([A-Z]{2,4}\s?\d{3,4})",  # CS101, MATH 201
            r"([A-Z][a-z]+\s?\d{3,4})",  # Math101, Physics201
        ]

        self.date_patterns = [
            r"(\d{4}-\d{2}-\d{2})",  # 2024-01-15
            r"(\d{2}/\d{2}/\d{4})",  # 01/15/2024
            r"(\d{1,2}-\d{1,2}-\d{4})",  # 1-15-2024
        ]

    def extract(self, file_path: Path, content: str) -> dict[str, Any]:
        """Extract metadata from file path and content.

        Args:
            file_path: Path to the source file
            content: Document content as string

        Returns:
            Dictionary containing extracted metadata
        """
        metadata = {
            "source_file": str(file_path),
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size if file_path.exists() else 0,
            "file_type": file_path.suffix.lower(),
            "extracted_at": datetime.now().isoformat(),
        }

        # Extract from file path
        path_metadata = self._extract_from_path(file_path)
        metadata.update(path_metadata)

        # Extract from content
        content_metadata = self._extract_from_content(content)
        metadata.update(content_metadata)

        # Post-process and validate
        return self._validate_and_clean(metadata)

    def _extract_from_path(self, file_path: Path) -> dict[str, Any]:
        """Extract metadata from file path structure.

        Args:
            file_path: File path to analyze

        Returns:
            Dictionary with path-based metadata
        """
        metadata = {}

        # Get path parts
        parts = file_path.parts
        stem = file_path.stem

        # Try to identify course from path
        for part in parts:
            course = self._extract_course_code(part)
            if course:
                metadata["course"] = course
                break

        # Try to extract course from filename
        if "course" not in metadata:
            course = self._extract_course_code(stem)
            if course:
                metadata["course"] = course

        # Extract topic/subject from filename
        topic = self._extract_topic(stem)
        if topic:
            metadata["topic"] = topic

        # Extract date from filename or path
        date = self._extract_date_from_string(" ".join(parts))
        if date:
            metadata["date"] = date

        # Identify document type from filename patterns
        doc_type = self._identify_document_type(stem.lower())
        if doc_type:
            metadata["document_type"] = doc_type

        return metadata

    def _extract_from_content(self, content: str) -> dict[str, Any]:
        """Extract metadata from document content.

        Args:
            content: Document content

        Returns:
            Dictionary with content-based metadata
        """
        metadata = {}

        # Basic statistics
        lines = content.split("\n")
        words = content.split()

        metadata.update(
            {
                "word_count": len(words),
                "line_count": len(lines),
                "char_count": len(content),
            },
        )

        # Extract title from content (first heading or significant line)
        title = self._extract_title(content)
        if title:
            metadata["title"] = title

        # Extract author if mentioned
        author = self._extract_author(content)
        if author:
            metadata["author"] = author

        # Extract date from content
        content_date = self._extract_date_from_string(content)
        if content_date and "date" not in metadata:
            metadata["date"] = content_date

        # Count equations, code blocks, etc.
        metadata["math_equations"] = len(re.findall(r"\$.*?\$", content))
        metadata["code_blocks"] = len(re.findall(r"```.*?```", content, re.DOTALL))
        metadata["images_referenced"] = len(re.findall(r"!\[.*?\]\(.*?\)", content))

        # Extract tags from content
        tags = self._extract_tags(content)
        if tags:
            metadata["tags"] = tags

        return metadata

    def _extract_course_code(self, text: str) -> Optional[str]:
        """Extract course code from text.

        Args:
            text: Text to search for course codes

        Returns:
            Course code if found, None otherwise
        """
        for pattern in self.course_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].upper().replace(" ", "")
        return None

    def _extract_topic(self, filename: str) -> Optional[str]:
        """Extract topic/subject from filename.

        Args:
            filename: Filename to analyze

        Returns:
            Topic if identified, None otherwise
        """
        # Remove course codes, dates, and common prefixes/suffixes
        clean_name = filename

        # Remove course codes
        for pattern in self.course_patterns:
            clean_name = re.sub(pattern, "", clean_name, flags=re.IGNORECASE)

        # Remove dates
        for pattern in self.date_patterns:
            clean_name = re.sub(pattern, "", clean_name)

        # Remove common prefixes
        prefixes = ["lecture", "lab", "hw", "homework", "assignment", "exam", "quiz", "notes"]
        for prefix in prefixes:
            clean_name = re.sub(rf"^{prefix}[_\-\s]*", "", clean_name, flags=re.IGNORECASE)

        # Remove numbers and separators, clean up
        clean_name = re.sub(r"[_\-\s]+", " ", clean_name)
        clean_name = re.sub(r"^\d+[_\-\s]*", "", clean_name)
        clean_name = clean_name.strip()

        return clean_name if clean_name and len(clean_name) > 2 else None

    def _extract_date_from_string(self, text: str) -> Optional[str]:
        """Extract date from text.

        Args:
            text: Text to search for dates

        Returns:
            ISO format date string if found, None otherwise
        """
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                date_str = matches[0]
                # Try to parse and normalize
                try:
                    if "-" in date_str and len(date_str.split("-")[0]) == 4:
                        # Already in YYYY-MM-DD format
                        return date_str
                    if "/" in date_str:
                        # MM/DD/YYYY format
                        parts = date_str.split("/")
                        if len(parts) == 3:
                            return f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                except:
                    continue
        return None

    def _extract_title(self, content: str) -> Optional[str]:
        """Extract document title from content.

        Args:
            content: Document content

        Returns:
            Title if found, None otherwise
        """
        lines = content.split("\n")

        # Look for markdown headers
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line.startswith("#"):
                title = line.lstrip("#").strip()
                if len(title) > 3 and len(title) < 100:
                    return title

        # Look for lines that might be titles (short, at the beginning)
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) > 5 and len(line) < 80 and not line.startswith(("http", "www")):
                # Check if it looks like a title (not too many special characters)
                if len(re.findall(r"[a-zA-Z\s]", line)) / len(line) > 0.7:
                    return line

        return None

    def _extract_author(self, content: str) -> Optional[str]:
        """Extract author from content.

        Args:
            content: Document content

        Returns:
            Author if found, None otherwise
        """
        # Look for author patterns
        author_patterns = [
            r"author:\s*([^\n]+)",
            r"by\s+([A-Z][a-z]+\s+[A-Z][a-z]+)",
            r"prof(?:essor)?\s+([A-Z][a-z]+\s+[A-Z][a-z]+)",
        ]

        for pattern in author_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                return matches[0].strip()

        return None

    def _extract_tags(self, content: str) -> list[str]:
        """Extract tags from content.

        Args:
            content: Document content

        Returns:
            List of tags found
        """
        tags = []

        # Look for hashtags
        hashtags = re.findall(r"#([a-zA-Z][a-zA-Z0-9_]+)", content)
        tags.extend(hashtags)

        # Look for YAML frontmatter tags
        yaml_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        if yaml_match:
            try:
                import yaml

                frontmatter = yaml.safe_load(yaml_match.group(1))
                if isinstance(frontmatter, dict) and "tags" in frontmatter:
                    if isinstance(frontmatter["tags"], list):
                        tags.extend(frontmatter["tags"])
                    elif isinstance(frontmatter["tags"], str):
                        tags.extend(frontmatter["tags"].split(","))
            except:
                pass

        return list({tag.strip() for tag in tags if tag.strip()})

    def _identify_document_type(self, filename: str) -> Optional[str]:
        """Identify document type from filename.

        Args:
            filename: Filename to analyze

        Returns:
            Document type if identified
        """
        type_patterns = {
            "lecture": r"\b(lecture|class|session)\b",
            "homework": r"\b(hw|homework|assignment|problem[_ ]?set)\b",
            "exam": r"\b(exam|test|midterm|final|quiz)\b",
            "lab": r"\b(lab|laboratory|experiment)\b",
            "notes": r"\b(notes?|summary|review)\b",
            "syllabus": r"\b(syllabus|outline|schedule)\b",
            "presentation": r"\b(presentation|slides?|ppt)\b",
        }

        for doc_type, pattern in type_patterns.items():
            if re.search(pattern, filename, re.IGNORECASE):
                return doc_type

        return None

    def _validate_and_clean(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Validate and clean extracted metadata.

        Args:
            metadata: Raw metadata dictionary

        Returns:
            Cleaned and validated metadata
        """
        # Remove None values
        clean_metadata = {k: v for k, v in metadata.items() if v is not None}

        # Ensure course codes are properly formatted
        if "course" in clean_metadata:
            course = clean_metadata["course"]
            # Standardize format: DEPT123 or DEPT 123
            course = re.sub(r"([A-Z]+)(\d+)", r"\1\2", course.upper())
            clean_metadata["course"] = course

        # Clean title
        if "title" in clean_metadata:
            title = clean_metadata["title"]
            # Remove excessive whitespace and special characters
            title = re.sub(r"\s+", " ", title).strip()
            if len(title) < 3:
                del clean_metadata["title"]
            else:
                clean_metadata["title"] = title

        # Ensure tags is a list
        if "tags" in clean_metadata and not isinstance(clean_metadata["tags"], list):
            clean_metadata["tags"] = [clean_metadata["tags"]]

        return clean_metadata
