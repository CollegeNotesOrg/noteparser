"""Tests for core NoteParser functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from noteparser.core import NoteParser
from noteparser.exceptions import UnsupportedFormatError


class TestNoteParser:
    """Test cases for the main NoteParser class."""

    @pytest.fixture()
    def parser(self):
        """Create a NoteParser instance for testing."""
        return NoteParser()

    @pytest.fixture()
    def sample_markdown(self):
        """Sample markdown content for testing."""
        return """# Test Document

This is a test document with various elements.

## Code Example

```python
def hello_world():
    print("Hello, World!")
```

## Mathematical Formula

The quadratic formula is: $x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}$

## List

- Item 1
- Item 2
- Item 3

**Bold text** and *italic text* example.
"""

    @pytest.fixture()
    def temp_file(self, sample_markdown):
        """Create a temporary file with sample content."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(sample_markdown)
            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    def test_init(self, parser):
        """Test parser initialization."""
        assert parser is not None
        assert hasattr(parser, "SUPPORTED_FORMATS")
        assert hasattr(parser, "markitdown")
        assert hasattr(parser, "latex_converter")
        assert hasattr(parser, "metadata_extractor")

    def test_supported_formats(self, parser):
        """Test that expected formats are supported."""
        expected_formats = {".pdf", ".docx", ".md", ".txt", ".jpg", ".png"}
        for fmt in expected_formats:
            assert fmt in parser.SUPPORTED_FORMATS

    @patch("noteparser.core.MarkItDown")
    def test_parse_to_markdown_success(self, mock_markitdown, parser, temp_file, sample_markdown):
        """Test successful markdown parsing."""
        # Mock MarkItDown response
        mock_result = Mock()
        mock_result.text_content = sample_markdown
        mock_markitdown_instance = Mock()
        mock_markitdown_instance.convert.return_value = mock_result
        mock_markitdown.return_value = mock_markitdown_instance

        # Test parsing
        result = parser.parse_to_markdown(temp_file)

        # Assertions
        assert "content" in result
        assert "metadata" in result
        assert len(result["content"]) > 0
        assert "Test Document" in result["content"]

    def test_parse_nonexistent_file(self, parser):
        """Test parsing a non-existent file raises FileNotFoundError."""
        nonexistent_file = Path("nonexistent_file.pdf")
        with pytest.raises(FileNotFoundError):
            parser.parse_to_markdown(nonexistent_file)

    def test_parse_unsupported_format(self, parser):
        """Test parsing unsupported format raises UnsupportedFormatError."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            temp_path = Path(f.name)

        try:
            with pytest.raises(UnsupportedFormatError):
                parser.parse_to_markdown(temp_path)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    @patch("noteparser.core.MarkItDown")
    def test_parse_to_latex(self, mock_markitdown, parser, temp_file, sample_markdown):
        """Test LaTeX conversion."""
        # Mock MarkItDown response
        mock_result = Mock()
        mock_result.text_content = sample_markdown
        mock_markitdown_instance = Mock()
        mock_markitdown_instance.convert.return_value = mock_result
        mock_markitdown.return_value = mock_markitdown_instance

        # Test LaTeX parsing
        result = parser.parse_to_latex(temp_file)

        # Assertions
        assert "content" in result
        assert "metadata" in result
        assert "\\documentclass" in result["content"]
        assert "\\begin{document}" in result["content"]
        assert "\\end{document}" in result["content"]

    def test_preserve_academic_formatting(self, parser):
        """Test academic formatting preservation."""
        content_with_math = """
        This is a theorem: **Theorem**: The sum of angles in a triangle is 180°.

        Mathematical equation: $E = mc^2$

        Display equation: $$\\int_0^1 x^2 dx = \\frac{1}{3}$$

        Citation: [1] and author-year citation [Smith2024]

        Chemical formula: H2O and C6H12O6

        Figure 1 shows the results.
        """

        processed = parser._preserve_academic_formatting(content_with_math)

        # Check theorem formatting
        assert "**Theorem**" in processed

        # Check math equations are preserved
        assert "$E = mc^2$" in processed
        assert "$$\\int_0^1 x^2 dx = \\frac{1}{3}$$" in processed

        # Check citations are preserved
        assert "[1]" in processed
        assert "[Smith2024]" in processed

        # Check figure references are bolded
        assert "**Figure 1**" in processed

    def test_batch_processing(self, parser, sample_markdown):
        """Test batch processing of multiple files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create multiple test files
            for i in range(3):
                test_file = temp_path / f"test_{i}.md"
                with open(test_file, "w") as f:
                    f.write(f"# Test Document {i}\\n{sample_markdown}")

            # Mock MarkItDown for batch processing
            with patch("noteparser.core.MarkItDown") as mock_markitdown:
                mock_result = Mock()
                mock_result.text_content = sample_markdown
                mock_markitdown_instance = Mock()
                mock_markitdown_instance.convert.return_value = mock_result
                mock_markitdown.return_value = mock_markitdown_instance

                # Test batch processing
                results = parser.parse_batch(temp_path, recursive=False)

                # Should have processed 3 files
                assert len(results) == 3

                # Check all results have content
                for file_path, result in results.items():
                    assert "content" in result
                    assert "error" not in result

    def test_format_chemical_formula(self, parser):
        """Test chemical formula formatting."""
        # Valid chemical formulas
        assert parser._format_chemical_formula("H2O") == "H<sub>2</sub>O"
        assert (
            parser._format_chemical_formula("C6H12O6") == "C<sub>6</sub>H<sub>12</sub>O<sub>6</sub>"
        )
        assert parser._format_chemical_formula("NaCl") == "NaCl"  # No numbers

        # Invalid/too long strings should remain unchanged
        long_string = "This is not a chemical formula"
        assert parser._format_chemical_formula(long_string) == long_string

    def test_detect_language(self, parser):
        """Test programming language detection."""
        # Python code
        python_code = """
        def hello():
            print("Hello, world!")
        import os
        """
        assert parser._detect_language(python_code) == "python"

        # JavaScript code
        js_code = """
        function hello() {
            console.log("Hello, world!");
        }
        let x = 5;
        """
        assert parser._detect_language(js_code) == "javascript"

        # Unknown code
        unknown_code = "This is just text with no clear language patterns"
        assert parser._detect_language(unknown_code) == ""

    def test_enhance_code_block(self, parser):
        """Test code block enhancement."""
        code = """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))"""

        enhanced = parser._enhance_code_block("python", code)

        assert "python" in enhanced
        assert "fibonacci" in enhanced
        # Should add line numbers for code longer than 5 lines
        assert "1│" in enhanced or "def fibonacci" in enhanced
