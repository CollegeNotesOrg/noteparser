"""Mathematics course plugin for enhanced equation processing."""

import re
from typing import Any

from noteparser.plugins.base import BasePlugin


class MathPlugin(BasePlugin):
    """Plugin for processing mathematics course content."""

    name = "math_processor"
    version = "1.0.0"
    description = "Enhanced processing for mathematics courses"
    supported_formats = [".pdf", ".docx", ".md", ".tex"]
    course_types = ["math", "mathematics", "calculus", "algebra", "statistics", "geometry"]

    def process_content(self, content: str, metadata: dict[str, Any]) -> dict[str, Any]:
        """Process mathematical content with enhanced formatting.

        Args:
            content: Document content
            metadata: Document metadata

        Returns:
            Processed content with mathematical enhancements
        """
        processed_content = content
        processing_log = []

        # Enhanced equation detection
        processed_content, eq_count = self._enhance_equations(processed_content)
        if eq_count > 0:
            processing_log.append(f"Enhanced {eq_count} mathematical equations")

        # Theorem and proof formatting
        processed_content, thm_count = self._format_theorems(processed_content)
        if thm_count > 0:
            processing_log.append(f"Formatted {thm_count} theorems/proofs")

        # Mathematical symbols standardization
        processed_content = self._standardize_symbols(processed_content)
        processing_log.append("Standardized mathematical symbols")

        # Add mathematical metadata
        math_metadata = self._extract_math_metadata(processed_content)

        return {
            "content": processed_content,
            "metadata": {
                **metadata,
                "math_equations": math_metadata["equation_count"],
                "math_theorems": math_metadata["theorem_count"],
                "math_symbols": math_metadata["symbols_used"],
                "processing_log": processing_log,
            },
        }

    def _enhance_equations(self, content: str) -> tuple[str, int]:
        """Enhance mathematical equations with better formatting.

        Args:
            content: Content to process

        Returns:
            Tuple of (processed_content, equations_count)
        """
        equation_count = 0

        # Display equations ($$...$$)
        def replace_display_equation(match):
            nonlocal equation_count
            equation_count += 1
            equation = match.group(1).strip()

            # Add equation numbering if not present
            if not re.search(r"\\tag\{.*\}", equation):
                equation = f"{equation} \\tag{{{equation_count}}}"

            return f"$$\n{equation}\n$$"

        content = re.sub(r"\$\$(.*?)\$\$", replace_display_equation, content, flags=re.DOTALL)

        # Inline equations - ensure proper spacing
        content = re.sub(r"\$([^$]+)\$", r" $\1$ ", content)
        content = re.sub(r"\s+", " ", content)  # Clean up extra spaces

        return content, equation_count

    def _format_theorems(self, content: str) -> tuple[str, int]:
        """Format theorems, lemmas, and proofs.

        Args:
            content: Content to process

        Returns:
            Tuple of (processed_content, theorem_count)
        """
        theorem_count = 0

        theorem_patterns = [
            (r"\b(theorem|lemma|corollary|proposition)\b\s*:?\s*(.*)", r"**\1**:\2"),
            (r"\b(proof)\b\s*:?\s*", r"**Proof**: "),
            (r"\b(definition)\b\s*:?\s*(.*)", r"**Definition**: \2"),
            (r"(Q\.E\.D\.|QED|∎)", r"*\1* ∎"),
        ]

        for pattern, replacement in theorem_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            theorem_count += len(matches)
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

        return content, theorem_count

    def _standardize_symbols(self, content: str) -> str:
        """Standardize mathematical symbols and notation.

        Args:
            content: Content to process

        Returns:
            Content with standardized symbols
        """
        symbol_replacements = {
            # Greek letters
            "alpha": "α",
            "beta": "β",
            "gamma": "γ",
            "delta": "δ",
            "epsilon": "ε",
            "theta": "θ",
            "lambda": "λ",
            "mu": "μ",
            "pi": "π",
            "sigma": "σ",
            "phi": "φ",
            "omega": "ω",
            # Mathematical operators
            "infinity": "∞",
            "integral": "∫",
            "sum": "∑",
            "product": "∏",
            "partial": "∂",
            "nabla": "∇",
            "therefore": "∴",
            "because": "∵",
            # Set theory
            "subset": "⊂",
            "superset": "⊃",
            "union": "∪",
            "intersection": "∩",
            "element": "∈",
            "not element": "∉",
            "empty set": "∅",
            # Logic
            "and": "∧",
            "or": "∨",
            "not": "¬",
            "implies": "⇒",
            "iff": "⇔",
            # Arrows
            "rightarrow": "→",
            "leftarrow": "←",
            "uparrow": "↑",
            "downarrow": "↓",
        }

        # Only replace whole words to avoid partial matches
        for word, symbol in symbol_replacements.items():
            pattern = rf"\b{re.escape(word)}\b"
            content = re.sub(pattern, symbol, content, flags=re.IGNORECASE)

        return content

    def _extract_math_metadata(self, content: str) -> dict[str, Any]:
        """Extract mathematical metadata from content.

        Args:
            content: Processed content

        Returns:
            Dictionary with mathematical metadata
        """
        # Count equations
        display_equations = len(re.findall(r"\$\$.*?\$\$", content, re.DOTALL))
        inline_equations = len(re.findall(r"\$[^$]+\$", content))

        # Count theorems/proofs
        theorem_count = len(
            re.findall(
                r"\*\*(theorem|lemma|corollary|proposition|proof|definition)\*\*",
                content,
                re.IGNORECASE,
            ),
        )

        # Find mathematical symbols used
        math_symbols = set()
        symbol_pattern = r"[α-ωΑ-Ω∞∫∑∏∂∇∴∵⊂⊃∪∩∈∉∅∧∨¬⇒⇔→←↑↓]"
        symbols_found = re.findall(symbol_pattern, content)
        math_symbols.update(symbols_found)

        return {
            "equation_count": display_equations + inline_equations,
            "display_equations": display_equations,
            "inline_equations": inline_equations,
            "theorem_count": theorem_count,
            "symbols_used": list(math_symbols),
        }
