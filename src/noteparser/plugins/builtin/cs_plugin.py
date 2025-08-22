"""Computer Science course plugin for code processing."""

import re
from typing import Any

from noteparser.plugins.base import BasePlugin


class ComputerSciencePlugin(BasePlugin):
    """Plugin for processing computer science course content."""

    name = "cs_processor"
    version = "1.0.0"
    description = "Enhanced processing for computer science courses"
    supported_formats = [".pdf", ".docx", ".md", ".txt"]
    course_types = [
        "cs",
        "computer science",
        "programming",
        "software",
        "algorithms",
        "data structures",
    ]

    def process_content(self, content: str, metadata: dict[str, Any]) -> dict[str, Any]:
        """Process CS content with enhanced code formatting.

        Args:
            content: Document content
            metadata: Document metadata

        Returns:
            Processed content with CS enhancements
        """
        processed_content = content
        processing_log = []

        # Enhanced code block detection
        processed_content, code_blocks = self._enhance_code_blocks(processed_content)
        if code_blocks:
            processing_log.append(f"Enhanced {len(code_blocks)} code blocks")

        # Algorithm formatting
        processed_content, algo_count = self._format_algorithms(processed_content)
        if algo_count > 0:
            processing_log.append(f"Formatted {algo_count} algorithms")

        # Complexity notation
        processed_content = self._enhance_complexity_notation(processed_content)
        processing_log.append("Enhanced complexity notation")

        # Technical terms highlighting
        processed_content = self._highlight_technical_terms(processed_content)
        processing_log.append("Highlighted technical terms")

        # Extract CS metadata
        cs_metadata = self._extract_cs_metadata(processed_content, code_blocks)

        return {
            "content": processed_content,
            "metadata": {
                **metadata,
                "code_blocks": len(code_blocks),
                "languages_detected": cs_metadata["languages"],
                "algorithms_count": cs_metadata["algorithms_count"],
                "complexity_notations": cs_metadata["complexity_notations"],
                "processing_log": processing_log,
            },
        }

    def _enhance_code_blocks(self, content: str) -> tuple[str, list[dict[str, Any]]]:
        """Enhance code blocks with better formatting and language detection.

        Args:
            content: Content to process

        Returns:
            Tuple of (processed_content, list_of_code_blocks)
        """
        code_blocks = []

        def process_code_block(match):
            language = match.group(1) or ""
            code = match.group(2).strip()

            # Detect language if not specified
            if not language:
                language = self._detect_programming_language(code)

            # Add syntax highlighting hints
            enhanced_code = self._add_syntax_hints(code, language)

            # Store code block info
            code_blocks.append(
                {
                    "language": language,
                    "code": code,
                    "line_count": len(code.split("\n")),
                    "has_comments": "//" in code or "#" in code or "/*" in code,
                },
            )

            return f"```{language}\n{enhanced_code}\n```"

        # Process existing code blocks
        content = re.sub(r"```(\w*)\n(.*?)```", process_code_block, content, flags=re.DOTALL)

        # Detect inline code that should be blocks
        lines = content.split("\n")
        enhanced_lines = []
        in_potential_code = False
        potential_code_lines = []

        for line in lines:
            # Check if line looks like code
            if self._looks_like_code_line(line):
                if not in_potential_code:
                    in_potential_code = True
                    potential_code_lines = [line]
                else:
                    potential_code_lines.append(line)
            else:
                # End of potential code block
                if in_potential_code and len(potential_code_lines) >= 3:
                    # Convert to code block
                    code_content = "\n".join(potential_code_lines)
                    language = self._detect_programming_language(code_content)

                    enhanced_lines.append(f"```{language}")
                    enhanced_lines.extend(potential_code_lines)
                    enhanced_lines.append("```")

                    code_blocks.append(
                        {
                            "language": language,
                            "code": code_content,
                            "line_count": len(potential_code_lines),
                            "auto_detected": True,
                        },
                    )
                else:
                    # Not enough lines, keep as is
                    enhanced_lines.extend(potential_code_lines)

                enhanced_lines.append(line)
                in_potential_code = False
                potential_code_lines = []

        return "\n".join(enhanced_lines), code_blocks

    def _detect_programming_language(self, code: str) -> str:
        """Detect programming language from code content.

        Args:
            code: Code content

        Returns:
            Detected language or 'text' if unknown
        """
        code_lower = code.lower()

        # Language detection patterns
        patterns = {
            "python": [
                r"def\s+\w+\(",
                r"import\s+\w+",
                r"from\s+\w+\s+import",
                r"print\(",
                r'if\s+__name__\s*==\s*["\']__main__["\']',
            ],
            "java": [
                r"public\s+class",
                r"public\s+static\s+void\s+main",
                r"System\.out\.println",
                r"import\s+java\.",
            ],
            "cpp": [r"#include\s*<", r"int\s+main\(", r"std::", r"cout\s*<<", r"cin\s*>>"],
            "c": [r"#include\s*<stdio\.h>", r"printf\(", r"scanf\(", r"int\s+main\("],
            "javascript": [
                r"function\s+\w+\(",
                r"var\s+\w+",
                r"let\s+\w+",
                r"const\s+\w+",
                r"console\.log\(",
                r"document\.",
            ],
            "html": [r"<html", r"<div", r"<span", r"</\w+>", r"<!DOCTYPE"],
            "css": [r"\.\w+\s*{", r"#\w+\s*{", r":\s*\w+;", r"@media"],
            "sql": [
                r"SELECT\s+",
                r"FROM\s+",
                r"WHERE\s+",
                r"INSERT\s+INTO",
                r"CREATE\s+TABLE",
                r"UPDATE\s+",
                r"DELETE\s+FROM",
            ],
            "bash": [r"#!/bin/bash", r"\$\w+", r"echo\s+", r"grep\s+", r"awk\s+"],
        }

        language_scores = {}
        for lang, regex_list in patterns.items():
            score = 0
            for pattern in regex_list:
                matches = len(re.findall(pattern, code_lower))
                score += matches
            if score > 0:
                language_scores[lang] = score

        if language_scores:
            return max(language_scores, key=language_scores.get)
        return "text"

    def _looks_like_code_line(self, line: str) -> bool:
        """Check if a line looks like code.

        Args:
            line: Line to check

        Returns:
            True if line looks like code
        """
        stripped = line.strip()

        # Skip empty lines and markdown
        if not stripped or stripped.startswith(("#", "*")):
            return False

        # Code indicators
        code_indicators = [
            r"^\s*[a-zA-Z_]\w*\s*\(",  # Function calls
            r"^\s*[a-zA-Z_]\w*\s*=",  # Variable assignments
            r"^\s*(if|for|while|def|class|function)\b",  # Keywords
            r"[{}();]",  # Common code punctuation
            r"^\s*//",  # Comments
            r"^\s*#",  # Python comments
            r"^\s*/\*",  # C-style comments
        ]

        return any(re.search(pattern, stripped) for pattern in code_indicators)

    def _add_syntax_hints(self, code: str, language: str) -> str:
        """Add syntax highlighting hints to code.

        Args:
            code: Code content
            language: Programming language

        Returns:
            Code with syntax hints
        """
        # Add line numbers for longer code blocks
        lines = code.split("\n")
        if len(lines) > 5:
            numbered_lines = []
            for i, line in enumerate(lines, 1):
                numbered_lines.append(f"{i:3d} | {line}")
            return "\n".join(numbered_lines)

        return code

    def _format_algorithms(self, content: str) -> tuple[str, int]:
        """Format algorithms with proper structure.

        Args:
            content: Content to process

        Returns:
            Tuple of (processed_content, algorithm_count)
        """
        algorithm_count = 0

        # Algorithm block patterns
        algorithm_patterns = [
            (
                r"\b(algorithm)\s*:?\s*(.*?)(?=\n\n|\Z)",
                r"## Algorithm: \2\n\n```pseudocode\n\2\n```",
            ),
            (r"\b(pseudocode)\s*:?\s*", r"**Pseudocode:**\n```pseudocode\n"),
        ]

        for pattern, replacement in algorithm_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            algorithm_count += len(matches)
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE | re.DOTALL)

        return content, algorithm_count

    def _enhance_complexity_notation(self, content: str) -> str:
        """Enhance Big O and complexity notation.

        Args:
            content: Content to process

        Returns:
            Content with enhanced complexity notation
        """
        # Big O notation
        content = re.sub(r"O\(([^)]+)\)", r"**O(\1)**", content)
        content = re.sub(r"Θ\(([^)]+)\)", r"**Θ(\1)**", content)
        content = re.sub(r"Ω\(([^)]+)\)", r"**Ω(\1)**", content)

        # Common complexity classes
        complexity_classes = {
            "O(1)": "O(1) - Constant time",
            "O(log n)": "O(log n) - Logarithmic time",
            "O(n)": "O(n) - Linear time",
            "O(n log n)": "O(n log n) - Linearithmic time",
            "O(n²)": "O(n²) - Quadratic time",
            "O(2^n)": "O(2^n) - Exponential time",
        }

        return content

    def _highlight_technical_terms(self, content: str) -> str:
        """Highlight important CS technical terms.

        Args:
            content: Content to process

        Returns:
            Content with highlighted terms
        """
        technical_terms = [
            "algorithm",
            "data structure",
            "binary tree",
            "hash table",
            "linked list",
            "array",
            "stack",
            "queue",
            "heap",
            "graph",
            "recursion",
            "iteration",
            "sorting",
            "searching",
            "dynamic programming",
            "greedy algorithm",
            "divide and conquer",
            "backtracking",
            "time complexity",
            "space complexity",
            "asymptotic analysis",
        ]

        for term in technical_terms:
            pattern = rf"\b{re.escape(term)}\b"
            content = re.sub(pattern, rf"**{term}**", content, flags=re.IGNORECASE)

        return content

    def _extract_cs_metadata(
        self,
        content: str,
        code_blocks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Extract CS-specific metadata.

        Args:
            content: Processed content
            code_blocks: List of detected code blocks

        Returns:
            Dictionary with CS metadata
        """
        # Languages used
        languages = set()
        for block in code_blocks:
            if block["language"] != "text":
                languages.add(block["language"])

        # Count algorithms
        algorithm_count = len(re.findall(r"\*\*Algorithm\*\*", content, re.IGNORECASE))

        # Find complexity notations
        complexity_notations = re.findall(r"\*\*[OΘΩ]\([^)]+\)\*\*", content)

        return {
            "languages": list(languages),
            "algorithms_count": algorithm_count,
            "complexity_notations": list(set(complexity_notations)),
            "total_code_lines": sum(block["line_count"] for block in code_blocks),
        }
