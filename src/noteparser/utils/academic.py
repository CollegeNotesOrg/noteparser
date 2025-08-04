"""Academic document processing utilities."""

import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Citation:
    """Represents a citation found in the document."""
    id: str
    type: str  # 'numeric', 'author-year', 'footnote'
    text: str
    page_number: Optional[int] = None


@dataclass
class TableOfContents:
    """Represents the table of contents structure."""
    sections: List[Dict[str, Any]]
    total_sections: int
    max_depth: int


class AcademicProcessor:
    """Processes academic documents for bibliography, citations, and structure."""
    
    def __init__(self):
        """Initialize the academic processor."""
        self.citation_patterns = {
            'numeric': r'\[(\d+)\]',
            'author_year': r'\[([A-Za-z]+(?:\s+(?:et\s+al\.?|&\s+[A-Za-z]+))*,?\s*\d{4}[a-z]?)\]',
            'footnote': r'\^(\d+)',
            'inline': r'\(([A-Za-z]+(?:\s+(?:et\s+al\.?|&\s+[A-Za-z]+))*,?\s*\d{4}[a-z]?)\)'
        }
        
        self.bibliography_markers = [
            'references', 'bibliography', 'works cited', 'literature cited',
            'citations', 'sources', 'further reading'
        ]
        
    def extract_citations(self, content: str) -> List[Citation]:
        """Extract citations from document content.
        
        Args:
            content: Document content as string
            
        Returns:
            List of Citation objects found in the document
        """
        citations = []
        
        for citation_type, pattern in self.citation_patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                citation = Citation(
                    id=match.group(1),
                    type=citation_type,
                    text=match.group(0),
                    page_number=self._estimate_page_number(content, match.start())
                )
                citations.append(citation)
                
        # Remove duplicates based on ID and type
        unique_citations = []
        seen = set()
        for citation in citations:
            key = (citation.id, citation.type)
            if key not in seen:
                seen.add(key)
                unique_citations.append(citation)
                
        return unique_citations
        
    def extract_bibliography(self, content: str) -> Dict[str, Any]:
        """Extract bibliography section from document.
        
        Args:
            content: Document content as string
            
        Returns:
            Dictionary containing bibliography information
        """
        lines = content.split('\n')
        bibliography_start = -1
        
        # Find bibliography section
        for i, line in enumerate(lines):
            line_clean = line.strip().lower()
            if any(marker in line_clean for marker in self.bibliography_markers):
                if len(line_clean) < 50:  # Likely a section header
                    bibliography_start = i
                    break
                    
        if bibliography_start == -1:
            return {
                'found': False,
                'entries': [],
                'section_title': None
            }
            
        # Extract bibliography entries
        entries = []
        current_entry = []
        
        for i in range(bibliography_start + 1, len(lines)):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                if current_entry:
                    entries.append(' '.join(current_entry))
                    current_entry = []
                continue
                
            # Check if this looks like a new entry
            if self._is_new_bibliography_entry(line):
                if current_entry:
                    entries.append(' '.join(current_entry))
                current_entry = [line]
            else:
                if current_entry:  # Continuation of previous entry
                    current_entry.append(line)
                    
        # Add the last entry if exists
        if current_entry:
            entries.append(' '.join(current_entry))
            
        return {
            'found': True,
            'entries': entries[:50],  # Limit to prevent huge outputs
            'section_title': lines[bibliography_start].strip(),
            'entry_count': len(entries)
        }
        
    def generate_table_of_contents(self, content: str) -> TableOfContents:
        """Generate table of contents from document headers.
        
        Args:
            content: Document content as string
            
        Returns:
            TableOfContents object with document structure
        """
        lines = content.split('\n')
        sections = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Detect markdown headers
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                title = line.lstrip('#').strip()
                
                if title:  # Don't include empty headers
                    sections.append({
                        'level': level,
                        'title': title,
                        'line_number': i + 1,
                        'anchor': self._create_anchor(title)
                    })
                    
            # Detect underlined headers (alternative markdown style)
            elif i < len(lines) - 1:
                next_line = lines[i + 1].strip()
                if line and next_line:
                    if all(c == '=' for c in next_line) and len(next_line) >= len(line) // 2:
                        sections.append({
                            'level': 1,
                            'title': line,
                            'line_number': i + 1,
                            'anchor': self._create_anchor(line)
                        })
                    elif all(c == '-' for c in next_line) and len(next_line) >= len(line) // 2:
                        sections.append({
                            'level': 2,
                            'title': line,
                            'line_number': i + 1,
                            'anchor': self._create_anchor(line)
                        })
                        
        max_depth = max([s['level'] for s in sections]) if sections else 0
        
        return TableOfContents(
            sections=sections,
            total_sections=len(sections),
            max_depth=max_depth
        )
        
    def format_citations_section(self, citations: List[Citation]) -> str:
        """Format citations as a markdown section.
        
        Args:
            citations: List of Citation objects
            
        Returns:
            Formatted markdown string
        """
        if not citations:
            return ""
            
        lines = ["## Citations Found", ""]
        
        # Group by type
        by_type = {}
        for citation in citations:
            if citation.type not in by_type:
                by_type[citation.type] = []
            by_type[citation.type].append(citation)
            
        for citation_type, cites in by_type.items():
            lines.append(f"### {citation_type.replace('_', ' ').title()} Citations")
            lines.append("")
            
            for cite in cites[:20]:  # Limit display
                page_info = f" (page ~{cite.page_number})" if cite.page_number else ""
                lines.append(f"- `{cite.text}` - ID: {cite.id}{page_info}")
                
            lines.append("")
            
        return '\n'.join(lines)
        
    def format_toc_markdown(self, toc: TableOfContents) -> str:
        """Format table of contents as markdown.
        
        Args:
            toc: TableOfContents object
            
        Returns:
            Formatted markdown table of contents
        """
        if not toc.sections:
            return ""
            
        lines = ["## Table of Contents", ""]
        
        for section in toc.sections:
            indent = "  " * (section['level'] - 1)
            anchor_link = f"#{section['anchor']}"
            lines.append(f"{indent}- [{section['title']}]({anchor_link})")
            
        lines.append("")
        lines.append(f"*Total sections: {toc.total_sections}, Max depth: {toc.max_depth}*")
        lines.append("")
        
        return '\n'.join(lines)
        
    def _estimate_page_number(self, content: str, position: int) -> Optional[int]:
        """Estimate page number based on position in content.
        
        Args:
            content: Full document content
            position: Character position of citation
            
        Returns:
            Estimated page number or None
        """
        # Rough estimate: 500 words per page, 5 chars per word
        chars_per_page = 2500
        return max(1, position // chars_per_page + 1)
        
    def _is_new_bibliography_entry(self, line: str) -> bool:
        """Check if a line starts a new bibliography entry.
        
        Args:
            line: Line to check
            
        Returns:
            True if this looks like a new bibliography entry
        """
        # Check for numbered entries
        if re.match(r'^\d+\.?\s+', line):
            return True
            
        # Check for author-year pattern at start
        if re.match(r'^[A-Za-z]+,?\s+[A-Z]\.', line):
            return True
            
        # Check for bracketed numbers
        if re.match(r'^\[\d+\]\s+', line):
            return True
            
        return False
        
    def _create_anchor(self, title: str) -> str:
        """Create URL-safe anchor from title.
        
        Args:
            title: Section title
            
        Returns:
            URL-safe anchor string
        """
        # Convert to lowercase, replace spaces with hyphens, remove special chars
        anchor = re.sub(r'[^\w\s-]', '', title.lower())
        anchor = re.sub(r'[-\s]+', '-', anchor)
        return anchor.strip('-')