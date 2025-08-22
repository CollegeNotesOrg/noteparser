"""LaTeX conversion utilities."""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class LatexConverter:
    """Convert Markdown content to LaTeX format."""

    def __init__(self):
        """Initialize LaTeX converter."""
        self.templates = {
            "article": self._get_article_template(),
            "report": self._get_report_template(),
            "beamer": self._get_beamer_template(),
        }

        # Markdown to LaTeX conversion patterns
        self.conversion_patterns = [
            # Headers
            (r"^# (.*?)$", r"\\section{\1}"),
            (r"^## (.*?)$", r"\\subsection{\1}"),
            (r"^### (.*?)$", r"\\subsubsection{\1}"),
            (r"^#### (.*?)$", r"\\paragraph{\1}"),
            (r"^##### (.*?)$", r"\\subparagraph{\1}"),
            # Text formatting
            (r"\*\*(.*?)\*\*", r"\\textbf{\1}"),
            (r"\*(.*?)\*", r"\\textit{\1}"),
            (r"`(.*?)`", r"\\texttt{\1}"),
            # Lists
            (r"^\* (.*?)$", r"\\item \1"),
            (r"^\d+\. (.*?)$", r"\\item \1"),
            # Links
            (r"\[([^\]]+)\]\(([^)]+)\)", r"\\href{\2}{\1}"),
            # Images
            (r"!\[([^\]]*)\]\(([^)]+)\)", r"\\includegraphics[width=0.8\\textwidth]{\2}"),
        ]

    def convert(
        self,
        markdown_content: str,
        template: str = "article",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Convert markdown content to LaTeX.

        Args:
            markdown_content: Markdown content to convert
            template: LaTeX template to use ('article', 'report', 'beamer')
            metadata: Document metadata for template population

        Returns:
            LaTeX content string
        """
        if template not in self.templates:
            logger.warning(f"Unknown template '{template}', using 'article'")
            template = "article"

        # Convert markdown to LaTeX body
        latex_body = self._convert_markdown_to_latex(markdown_content)

        # Get template and populate with content
        template_content = self.templates[template]

        # Populate template variables
        template_vars = self._extract_template_variables(metadata or {})

        try:
            latex_document: str = template_content.format(content=latex_body, **template_vars)
        except KeyError as e:
            logger.warning(f"Missing template variable: {e}")
            # Use defaults for missing variables
            template_vars.update(
                {
                    "title": "Untitled Document",
                    "author": "Unknown Author",
                    "date": "\\today",
                },
            )
            latex_document = template_content.format(content=latex_body, **template_vars)

        return latex_document

    def _convert_markdown_to_latex(self, markdown: str) -> str:
        """Convert markdown content to LaTeX body.

        Args:
            markdown: Markdown content

        Returns:
            LaTeX body content
        """
        lines = markdown.split("\n")
        latex_lines = []
        in_code_block = False
        in_list = False
        list_type = None  # 'itemize' or 'enumerate'

        i = 0
        while i < len(lines):
            line = lines[i]
            original_line = line

            # Handle code blocks
            if line.strip().startswith("```"):
                if not in_code_block:
                    # Start code block
                    language = line.strip()[3:].strip()
                    latex_lines.append("\\begin{lstlisting}")
                    if language:
                        latex_lines[-1] = f"\\begin{{lstlisting}}[language={language}]"
                    in_code_block = True
                else:
                    # End code block
                    latex_lines.append("\\end{lstlisting}")
                    in_code_block = False
                i += 1
                continue

            # Inside code block - don't process
            if in_code_block:
                latex_lines.append(line)
                i += 1
                continue

            # Handle YAML frontmatter
            if i == 0 and line.strip() == "---":
                # Skip frontmatter
                i += 1
                while i < len(lines) and lines[i].strip() != "---":
                    i += 1
                i += 1  # Skip closing ---
                continue

            # Handle lists
            if re.match(r"^\s*[\*\-\+] ", line):
                if not in_list or list_type != "itemize":
                    if in_list:
                        latex_lines.append(f"\\end{{{list_type}}}")
                    latex_lines.append("\\begin{itemize}")
                    in_list = True
                    list_type = "itemize"
                # Convert list item
                line = re.sub(r"^\s*[\*\-\+] (.*)", r"\\item \1", line)
            elif re.match(r"^\s*\d+\. ", line):
                if not in_list or list_type != "enumerate":
                    if in_list:
                        latex_lines.append(f"\\end{{{list_type}}}")
                    latex_lines.append("\\begin{enumerate}")
                    in_list = True
                    list_type = "enumerate"
                # Convert list item
                line = re.sub(r"^\s*\d+\. (.*)", r"\\item \1", line)
            # Not a list item
            elif in_list:
                latex_lines.append(f"\\end{{{list_type}}}")
                in_list = False
                list_type = None

            # Apply conversion patterns
            for pattern, replacement in self.conversion_patterns:
                line = re.sub(pattern, replacement, line, flags=re.MULTILINE)

            # Handle equations (preserve LaTeX math)
            # Already in LaTeX format, so skip conversion

            # Handle tables
            if "|" in line and line.count("|") >= 2:
                table_lines = [line]
                # Collect table rows
                j = i + 1
                while j < len(lines) and "|" in lines[j]:
                    table_lines.append(lines[j])
                    j += 1

                # Convert table
                latex_table = self._convert_table_to_latex(table_lines)
                latex_lines.extend(latex_table)
                i = j - 1  # Skip processed table lines
            # Regular line processing
            elif line.strip() == "":
                latex_lines.append("")  # Preserve paragraph breaks
            else:
                latex_lines.append(line)

            i += 1

        # Close any remaining lists
        if in_list:
            latex_lines.append(f"\\end{{{list_type}}}")

        return "\n".join(latex_lines)

    def _convert_table_to_latex(self, table_lines: list[str]) -> list[str]:
        """Convert markdown table to LaTeX tabular.

        Args:
            table_lines: List of table row strings

        Returns:
            List of LaTeX table lines
        """
        if not table_lines:
            return []

        latex_lines = []

        # Parse first row to determine column count
        first_row = table_lines[0].strip()
        if first_row.startswith("|"):
            first_row = first_row[1:]
        if first_row.endswith("|"):
            first_row = first_row[:-1]

        columns = [col.strip() for col in first_row.split("|")]
        col_count = len(columns)

        # Start table
        latex_lines.append("\\begin{table}[h]")
        latex_lines.append("\\centering")
        latex_lines.append(f'\\begin{{tabular}}{{{"l" * col_count}}}')
        latex_lines.append("\\hline")

        # Process table rows
        for i, line in enumerate(table_lines):
            line = line.strip()
            if line.startswith("|"):
                line = line[1:]
            if line.endswith("|"):
                line = line[:-1]

            # Skip separator lines
            if re.match(r"^[\s\|\-:]+$", line):
                if i == 1:  # Header separator
                    latex_lines.append("\\hline")
                continue

            cells = [cell.strip() for cell in line.split("|")]
            latex_row = " & ".join(cells) + " \\\\"

            # Apply text formatting to cells
            for pattern, replacement in self.conversion_patterns[4:7]:  # Text formatting patterns
                latex_row = re.sub(pattern, replacement, latex_row)

            latex_lines.append(latex_row)

        # End table
        latex_lines.append("\\hline")
        latex_lines.append("\\end{tabular}")
        latex_lines.append("\\end{table}")

        return latex_lines

    def _extract_template_variables(self, metadata: dict[str, Any]) -> dict[str, str]:
        """Extract variables for template population.

        Args:
            metadata: Document metadata

        Returns:
            Dictionary of template variables
        """
        variables = {
            "title": metadata.get("title", "Document Title"),
            "author": metadata.get("author", "Author Name"),
            "date": metadata.get("date", "\\today"),
            "course": metadata.get("course", ""),
            "topic": metadata.get("topic", ""),
        }

        # Clean LaTeX special characters
        for key, value in variables.items():
            if isinstance(value, str):
                # Escape LaTeX special characters
                value = value.replace("&", "\\&")
                value = value.replace("%", "\\%")
                value = value.replace("$", "\\$")
                value = value.replace("#", "\\#")
                value = value.replace("_", "\\_")
                value = value.replace("{", "\\{")
                value = value.replace("}", "\\}")
                variables[key] = value

        return variables

    def _get_article_template(self) -> str:
        """Get LaTeX article template.

        Returns:
            LaTeX article template string
        """
        return """\\documentclass[11pt,a4paper]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{amsmath}}
\\usepackage{{amsfonts}}
\\usepackage{{amssymb}}
\\usepackage{{graphicx}}
\\usepackage{{hyperref}}
\\usepackage{{listings}}
\\usepackage{{xcolor}}
\\usepackage{{geometry}}
\\geometry{{margin=1in}}

% Configure listings for code highlighting
\\lstset{{
    basicstyle=\\ttfamily\\footnotesize,
    breaklines=true,
    frame=single,
    backgroundcolor=\\color{{gray!10}},
    keywordstyle=\\color{{blue}},
    commentstyle=\\color{{green!60!black}},
    stringstyle=\\color{{red}},
    showstringspaces=false,
    numbers=left,
    numberstyle=\\tiny\\color{{gray}}
}}

\\title{{{title}}}
\\author{{{author}}}
\\date{{{date}}}

\\begin{{document}}

\\maketitle

{content}

\\end{{document}}"""

    def _get_report_template(self) -> str:
        """Get LaTeX report template.

        Returns:
            LaTeX report template string
        """
        return """\\documentclass[11pt,a4paper]{{report}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{amsmath}}
\\usepackage{{amsfonts}}
\\usepackage{{amssymb}}
\\usepackage{{graphicx}}
\\usepackage{{hyperref}}
\\usepackage{{listings}}
\\usepackage{{xcolor}}
\\usepackage{{geometry}}
\\geometry{{margin=1in}}

% Configure listings for code highlighting
\\lstset{{
    basicstyle=\\ttfamily\\footnotesize,
    breaklines=true,
    frame=single,
    backgroundcolor=\\color{{gray!10}},
    keywordstyle=\\color{{blue}},
    commentstyle=\\color{{green!60!black}},
    stringstyle=\\color{{red}},
    showstringspaces=false,
    numbers=left,
    numberstyle=\\tiny\\color{{gray}}
}}

\\title{{{title}}}
\\author{{{author}}}
\\date{{{date}}}

\\begin{{document}}

\\maketitle
\\tableofcontents
\\newpage

{content}

\\end{{document}}"""

    def _get_beamer_template(self) -> str:
        """Get LaTeX beamer presentation template.

        Returns:
            LaTeX beamer template string
        """
        return """\\documentclass{{beamer}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{amsmath}}
\\usepackage{{amsfonts}}
\\usepackage{{amssymb}}
\\usepackage{{graphicx}}
\\usepackage{{hyperref}}
\\usepackage{{listings}}
\\usepackage{{xcolor}}

\\usetheme{{Madrid}}
\\usecolortheme{{default}}

% Configure listings for code highlighting
\\lstset{{
    basicstyle=\\ttfamily\\footnotesize,
    breaklines=true,
    backgroundcolor=\\color{{gray!10}},
    keywordstyle=\\color{{blue}},
    commentstyle=\\color{{green!60!black}},
    stringstyle=\\color{{red}},
    showstringspaces=false,
}}

\\title{{{title}}}
\\author{{{author}}}
\\date{{{date}}}

\\begin{{document}}

\\frame{{\\titlepage}}

{content}

\\end{{document}}"""
