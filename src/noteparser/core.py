"""Core NoteParser implementation."""

import os
from pathlib import Path
from typing import Optional, Union, Dict, Any
from markitdown import MarkItDown
from .exceptions import UnsupportedFormatError, ConversionError
from .converters.latex import LatexConverter
from .utils.metadata import MetadataExtractor


class NoteParser:
    """Main parser class that orchestrates document conversion."""
    
    SUPPORTED_FORMATS = {
        '.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls',
        '.html', '.htm', '.md', '.txt', '.csv', '.json', '.xml',
        '.epub', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
        # Audio/video formats for transcription
        '.mp3', '.wav', '.m4a', '.mp4', '.mov', '.avi'
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, llm_client: Optional[Any] = None):
        """Initialize NoteParser with optional configuration.
        
        Args:
            config: Optional configuration dictionary for customizing behavior
            llm_client: Optional LLM client for image descriptions and AI features
        """
        self.config = config or {}
        # Updated MarkItDown integration with latest features
        self.markitdown = MarkItDown(
            enable_plugins=True,
            llm_client=llm_client
        )
        self.latex_converter = LatexConverter()
        self.metadata_extractor = MetadataExtractor()
        self.llm_client = llm_client
    
    def parse_to_markdown(
        self,
        file_path: Union[str, Path],
        extract_metadata: bool = True,
        preserve_formatting: bool = True
    ) -> Dict[str, Any]:
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
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        try:
            result = self.markitdown.convert(str(file_path))
            markdown_content = result.text_content
            
            output = {"content": markdown_content}
            
            if extract_metadata:
                metadata = self.metadata_extractor.extract(file_path, markdown_content)
                output["metadata"] = metadata
            
            if preserve_formatting:
                markdown_content = self._preserve_academic_formatting(markdown_content)
                output["content"] = markdown_content
            
            return output
            
        except Exception as e:
            raise ConversionError(f"Failed to convert {file_path}: {str(e)}")
    
    def parse_to_latex(
        self,
        file_path: Union[str, Path],
        template: Optional[str] = None,
        extract_metadata: bool = True
    ) -> Dict[str, Any]:
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
            template=template,
            metadata=markdown_result.get("metadata", {})
        )
        
        output = {"content": latex_content}
        if extract_metadata:
            output["metadata"] = markdown_result.get("metadata", {})
        
        return output
    
    def parse_batch(
        self,
        directory: Union[str, Path],
        output_format: str = "markdown",
        recursive: bool = True,
        pattern: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
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
        
        if recursive:
            files = directory.rglob(pattern or "*")
        else:
            files = directory.glob(pattern or "*")
        
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
        content = re.sub(r'\$\$(.*?)\$\$', r'$$\1$$', content, flags=re.DOTALL)
        content = re.sub(r'\$(.*?)\$', r'$\1$', content)
        
        # Chemical formulas (basic detection)
        content = re.sub(r'\b([A-Z][a-z]?\d*)+\b', lambda m: self._format_chemical_formula(m.group()), content)
        
        # Code blocks enhancement
        content = re.sub(r'```(\w+)?\n(.*?)```', lambda m: self._enhance_code_block(m.group(1), m.group(2)), content, flags=re.DOTALL)
        
        # Citations
        content = re.sub(r'\[(\d+)\]', r'[\1]', content)
        content = re.sub(r'\[([A-Za-z]+\d{4}[a-z]?)\]', r'[\1]', content)  # Author-year citations
        
        # Diagram markers
        content = re.sub(r'\b(Figure|Fig\.|Table|Diagram)\s+(\d+)', r'**\1 \2**', content)
        
        # Academic keywords highlighting
        keywords = ['theorem', 'lemma', 'proof', 'definition', 'corollary', 'proposition']
        for keyword in keywords:
            content = re.sub(rf'\b{keyword}\b', rf'**{keyword.title()}**', content, flags=re.IGNORECASE)
        
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
        if len(formula) > 10 or not re.match(r'^[A-Z][a-z]?(\d*[A-Z][a-z]?\d*)*$', formula):
            return formula
            
        # Convert numbers to subscripts
        formatted = re.sub(r'(\d+)', r'<sub>\1</sub>', formula)
        return formatted
        
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
        lines = enhanced_code.split('\n')
        if len(lines) > 5:
            numbered = []
            for i, line in enumerate(lines, 1):
                numbered.append(f"{i:2d}│ {line}")
            enhanced_code = '\n'.join(numbered)
            
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
            'python': [r'def\s+\w+\(', r'import\s+\w+', r'from\s+\w+\s+import', r'print\('],
            'javascript': [r'function\s+\w+\(', r'var\s+\w+', r'let\s+\w+', r'const\s+\w+'],
            'java': [r'public\s+class', r'public\s+static\s+void\s+main', r'System\.out\.println'],
            'cpp': [r'#include\s*<', r'int\s+main\(', r'std::'],
            'sql': [r'SELECT\s+', r'FROM\s+', r'WHERE\s+', r'INSERT\s+INTO'],
            'bash': [r'#!/bin/bash', r'\$\w+', r'echo\s+'],
            'css': [r'\.\w+\s*{', r'#\w+\s*{', r':\s*\w+;'],
            'html': [r'<html', r'<div', r'<span', r'</\w+>']
        }
        
        code_lower = code.lower()
        for lang, regex_list in patterns.items():
            for pattern in regex_list:
                if re.search(pattern, code_lower):
                    return lang
                    
        return ''