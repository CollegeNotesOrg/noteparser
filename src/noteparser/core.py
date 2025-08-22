"""Core NoteParser implementation."""

from pathlib import Path
from typing import Any, ClassVar

from markitdown import MarkItDown

from .converters.latex import LatexConverter
from .exceptions import ConversionError, UnsupportedFormatError
from .integration.ai_services import AIServicesIntegration
from .utils.metadata import MetadataExtractor


class NoteParser:
    """Main parser class that orchestrates document conversion."""

    SUPPORTED_FORMATS: ClassVar = {
        ".pdf",
        ".docx",
        ".doc",
        ".pptx",
        ".ppt",
        ".xlsx",
        ".xls",
        ".html",
        ".htm",
        ".md",
        ".txt",
        ".csv",
        ".json",
        ".xml",
        ".epub",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".tiff",
        # Audio/video formats for transcription
        ".mp3",
        ".wav",
        ".m4a",
        ".mp4",
        ".mov",
        ".avi",
    }

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        llm_client: Any | None = None,
        enable_ai: bool = False,
    ):
        """Initialize NoteParser with optional configuration.

        Args:
            config: Optional configuration dictionary for customizing behavior
            llm_client: Optional LLM client for image descriptions and AI features
            enable_ai: Whether to enable AI services integration
        """
        self.config = config or {}
        self.enable_ai = enable_ai

        # Updated MarkItDown integration with latest features
        self.markitdown = MarkItDown(enable_plugins=True, llm_client=llm_client)
        self.latex_converter = LatexConverter()
        self.metadata_extractor = MetadataExtractor()
        self.llm_client = llm_client

        # Initialize AI services if enabled
        self.ai_integration = None
        if enable_ai:
            try:
                self.ai_integration = AIServicesIntegration(config)
            except ImportError as e:
                print(f"Warning: AI services not available: {e}")
                self.enable_ai = False

    def parse_to_markdown(
        self,
        file_path: str | Path,
        extract_metadata: bool = True,
        preserve_formatting: bool = True,
    ) -> dict[str, Any]:
        """Parse document to Markdown format.

        Args:
            file_path: Path to the input file
            extract_metadata: Whether to extract document metadata
            preserve_formatting: Whether to preserve special formatting

        Returns:
            Dictionary containing markdown content and metadata
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise UnsupportedFormatError(
                f"Unsupported format: {file_path.suffix}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}",
            )

        try:
            result = self.markitdown.convert(str(file_path))
            markdown_content = result.text_content

            output: dict[str, Any] = {"content": markdown_content}

            if extract_metadata:
                metadata = self.metadata_extractor.extract(file_path, markdown_content)
                output["metadata"] = metadata

            if preserve_formatting:
                markdown_content = self._preserve_academic_formatting(markdown_content)
                output["content"] = markdown_content

            return output

        except Exception as e:
            raise ConversionError(f"Failed to convert {file_path}: {e!s}")

    def parse_to_latex(
        self,
        file_path: str | Path,
        template: str | None = None,
        extract_metadata: bool = True,
    ) -> dict[str, Any]:
        """Parse document to LaTeX format.

        Args:
            file_path: Path to the input file
            template: Optional LaTeX template to use
            extract_metadata: Whether to extract document metadata

        Returns:
            Dictionary containing LaTeX content and metadata
        """
        markdown_result = self.parse_to_markdown(file_path, extract_metadata)

        latex_content = self.latex_converter.convert(
            markdown_result["content"],
            template=template or "default",
            metadata=markdown_result.get("metadata", {}),
        )

        output = {"content": latex_content}
        if extract_metadata:
            output["metadata"] = markdown_result.get("metadata", {})

        return output

    def parse_batch(
        self,
        directory: str | Path,
        output_format: str = "markdown",
        recursive: bool = True,
        pattern: str | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Parse multiple documents in a directory.

        Args:
            directory: Directory containing documents
            output_format: Target format ('markdown' or 'latex')
            recursive: Whether to search recursively
            pattern: Optional file pattern to match

        Returns:
            Dictionary mapping file paths to parsed results
        """
        directory = Path(directory)
        results = {}

        files = directory.rglob(pattern or "*") if recursive else directory.glob(pattern or "*")

        for file_path in files:
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_FORMATS:
                try:
                    if output_format == "latex":
                        result = self.parse_to_latex(file_path)
                    else:
                        result = self.parse_to_markdown(file_path)
                    results[str(file_path)] = result
                except Exception as e:
                    results[str(file_path)] = {"error": str(e)}

        return results

    def _preserve_academic_formatting(self, content: str) -> str:
        """Preserve academic-specific formatting like equations and citations.

        Args:
            content: Markdown content to process

        Returns:
            Processed markdown with preserved formatting
        """
        import re

        # Mathematical equations
        content = re.sub(r"\$\$(.*?)\$\$", r"$$\1$$", content, flags=re.DOTALL)
        content = re.sub(r"\$(.*?)\$", r"$\1$", content)

        # Chemical formulas (basic detection)
        content = re.sub(
            r"\b([A-Z][a-z]?\d*)+\b",
            lambda m: self._format_chemical_formula(m.group()),
            content,
        )

        # Code blocks enhancement
        content = re.sub(
            r"```(\w+)?\n(.*?)```",
            lambda m: self._enhance_code_block(m.group(1), m.group(2)),
            content,
            flags=re.DOTALL,
        )

        # Citations
        content = re.sub(r"\[(\d+)\]", r"[\1]", content)
        content = re.sub(r"\[([A-Za-z]+\d{4}[a-z]?)\]", r"[\1]", content)  # Author-year citations

        # Diagram markers
        content = re.sub(r"\b(Figure|Fig\.|Table|Diagram)\s+(\d+)", r"**\1 \2**", content)

        # Academic keywords highlighting
        keywords = ["theorem", "lemma", "proof", "definition", "corollary", "proposition"]
        for keyword in keywords:
            content = re.sub(
                rf"\b{keyword}\b",
                rf"**{keyword.title()}**",
                content,
                flags=re.IGNORECASE,
            )

        return content

    def _format_chemical_formula(self, formula: str) -> str:
        """Format chemical formulas with proper subscripts.

        Args:
            formula: Raw chemical formula string

        Returns:
            Formatted formula with markdown subscripts
        """
        import re

        # Only process if it looks like a chemical formula
        if len(formula) > 10 or not re.match(r"^[A-Z][a-z]?(\d*[A-Z][a-z]?\d*)*$", formula):
            return formula

        # Convert numbers to subscripts
        return re.sub(r"(\d+)", r"<sub>\1</sub>", formula)

    def _enhance_code_block(self, language: str, code: str) -> str:
        """Enhance code blocks with better formatting.

        Args:
            language: Programming language identifier
            code: Code content

        Returns:
            Enhanced code block
        """
        if not language:
            language = self._detect_language(code)

        # Add language-specific enhancements
        enhanced_code = code.strip()

        # Add line numbers for longer code blocks
        lines = enhanced_code.split("\n")
        if len(lines) > 5:
            numbered = []
            for i, line in enumerate(lines, 1):
                numbered.append(f"{i:2d}│ {line}")
            enhanced_code = "\n".join(numbered)

        return f"```{language or ''}\n{enhanced_code}\n```"

    def _detect_language(self, code: str) -> str:
        """Detect programming language from code content.

        Args:
            code: Code content

        Returns:
            Detected language identifier
        """
        import re

        # Simple language detection patterns
        patterns = {
            "python": [r"def\s+\w+\(", r"import\s+\w+", r"from\s+\w+\s+import", r"print\("],
            "javascript": [r"function\s+\w+\(", r"var\s+\w+", r"let\s+\w+", r"const\s+\w+"],
            "java": [r"public\s+class", r"public\s+static\s+void\s+main", r"System\.out\.println"],
            "cpp": [r"#include\s*<", r"int\s+main\(", r"std::"],
            "sql": [r"SELECT\s+", r"FROM\s+", r"WHERE\s+", r"INSERT\s+INTO"],
            "bash": [r"#!/bin/bash", r"\$\w+", r"echo\s+"],
            "css": [r"\.\w+\s*{", r"#\w+\s*{", r":\s*\w+;"],
            "html": [r"<html", r"<div", r"<span", r"</\w+>"],
        }

        code_lower = code.lower()
        for lang, regex_list in patterns.items():
            for pattern in regex_list:
                if re.search(pattern, code_lower):
                    return lang

        return ""

    async def parse_to_markdown_with_ai(
        self,
        file_path: str | Path,
        extract_metadata: bool = True,
        preserve_formatting: bool = True,
    ) -> dict[str, Any]:
        """Parse document to Markdown with AI enhancement.

        Args:
            file_path: Path to the input file
            extract_metadata: Whether to extract document metadata
            preserve_formatting: Whether to preserve academic formatting

        Returns:
            Dictionary containing enhanced markdown content, metadata, and AI processing results
        """
        # Standard parsing first
        result = self.parse_to_markdown(file_path, extract_metadata, preserve_formatting)

        # Add AI processing if enabled
        if self.enable_ai and self.ai_integration:
            try:
                await self.ai_integration.initialize()

                # Process through AI services
                ai_result = await self.ai_integration.process_document(
                    {
                        "content": result["content"],
                        "metadata": {
                            "title": Path(file_path).stem,
                            "file_path": str(file_path),
                            **result.get("metadata", {}),
                        },
                    },
                )
                result["ai_processing"] = ai_result

            except Exception as e:
                print(f"Warning: AI processing failed: {e}")
                result["ai_processing"] = {"error": str(e)}

        return result

    async def query_knowledge(self, query: str, filters: dict | None = None) -> dict[str, Any]:
        """Query the AI knowledge base.

        Args:
            query: Natural language query
            filters: Optional filters for search

        Returns:
            Query results from AI services
        """
        if not self.enable_ai or not self.ai_integration:
            return {"error": "AI services not enabled"}

        try:
            await self.ai_integration.initialize()
            return await self.ai_integration.query_knowledge(query, filters)
        except Exception as e:
            return {"error": str(e)}
