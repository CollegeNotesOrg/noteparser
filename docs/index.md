# NoteParser 📚

**A comprehensive document parser for converting academic materials to Markdown and LaTeX**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/CollegeNotesOrg/noteparser)](https://github.com/CollegeNotesOrg/noteparser)

NoteParser is a powerful academic document processing system built on top of Microsoft's [MarkItDown](https://github.com/microsoft/markitdown) library. It's designed specifically for university students and educators who need to convert various document formats into structured, searchable, and cross-referenced academic notes.

---

## ✨ Key Features

### 🔄 **Multi-Format Support**
Convert between various academic document formats:

- **Input**: PDF, DOCX, PPTX, XLSX, HTML, EPUB, Images, Audio, Video
- **Output**: Markdown, LaTeX, HTML

### 🎓 **Academic-Focused Processing**
Specialized processing for academic content:

- **Mathematical equations** preservation and enhancement
- **Code blocks** with syntax highlighting and language detection
- **Bibliography** and citation extraction
- **Chemical formulas** with proper subscript formatting
- **Academic keyword highlighting** (theorem, proof, definition, etc.)

### 🔌 **Extensible Plugin System**
Customize processing for different subjects:

- **Course-specific processors** (Math, Computer Science, Chemistry)
- **Custom parser plugins** for specialized content
- **Easy plugin development** with base classes

### 🌐 **Organization Integration**
Perfect for course and study group organization:

- **Multi-repository synchronization** for course organization
- **Cross-reference detection** between related documents
- **Automated GitHub Actions** for continuous processing
- **Searchable indexing** across all notes

### 🤖 **AI-Powered Intelligence**
Advanced AI services for enhanced learning:

- **RagFlow**: Semantic search and document insights using RAG
- **DeepWiki**: AI-powered knowledge graphs and wiki organization
- **Natural language queries** across your entire document collection
- **Automatic concept linking** and knowledge organization

### 🖥️ **Multiple Interfaces**
Use NoteParser your way:

- **Command-line interface** for batch processing
- **Web dashboard** for browsing and managing notes
- **Python API** for programmatic access
- **REST API** endpoints for integration

---

## 🚀 Quick Start

Get started in minutes:

```bash
# Install NoteParser
pip install noteparser

# Parse your first document
noteparser parse lecture.pdf --format markdown

# Start the web dashboard
noteparser web
```

[Get Started →](quickstart.md){ .md-button .md-button--primary }
[View on GitHub →](https://github.com/CollegeNotesOrg/noteparser){ .md-button }

---

## 📊 Use Cases

=== "👨‍🎓 Individual Student"

    **Daily workflow for personal note-taking:**

    ```bash
    # Convert lecture slides to markdown
    noteparser parse "Today's Lecture.pdf"
    noteparser sync output/todays-lecture.md --course CS101
    ```

    Perfect for:
    - Converting professor slides to searchable notes
    - OCR handwritten notes from photos
    - Organizing semester materials

=== "🏫 Course Organization"

    **Semester setup and batch processing:**

    ```bash
    # Process entire semester at once
    noteparser init
    noteparser batch course-materials/ --recursive
    noteparser index --format json > course-index.json
    ```

    Perfect for:
    - Organizing multiple courses
    - Batch processing assignments
    - Creating searchable course indexes

=== "👥 Study Group"

    **Collaborative note sharing:**

    ```bash
    # Process shared materials
    noteparser parse shared-notes.docx --format markdown
    git add . && git commit -m "Add processed notes"
    git push origin main  # Triggers auto-sync
    ```

    Perfect for:
    - Sharing processed notes with teammates
    - Automated GitHub Actions integration
    - Consistent formatting across contributors

=== "🔬 Research Lab"

    **Academic research processing:**

    ```bash
    # Convert research papers
    noteparser parse "Research Paper.pdf" --format latex
    noteparser web  # Browse and cross-reference
    ```

    Perfect for:
    - Literature review processing
    - Cross-referencing related papers
    - Extracting citations and references

---

## 🛠️ Advanced Features

### **Smart Content Detection**
- Mathematical equations with LaTeX formatting preservation
- Code blocks with automatic language detection
- Citations in APA, MLA, IEEE formats
- Figures and tables with structured conversion

### **Metadata Extraction**
- Course identification from file names and paths
- Topic extraction and automatic categorization
- Author and date detection
- Academic keywords and tagging

### **Cross-References**
- Similar content detection across documents
- Prerequisite tracking between topics
- Citation network visualization
- Knowledge graph construction

---

## 🤝 Community

Join our growing community of students and educators:

- **💬 [GitHub Discussions](https://github.com/CollegeNotesOrg/noteparser/discussions)** - Ask questions and share ideas
- **🐛 [Report Issues](https://github.com/CollegeNotesOrg/noteparser/issues)** - Help us improve
- **📚 [API Reference](api-reference.md)** - Complete API documentation
- **⚙️ [Configuration](configuration.md)** - Customize your setup

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/CollegeNotesOrg/noteparser/blob/master/LICENSE) file for details.

---

**Made with ❤️ for students, by a student**

*Transform your study materials into a searchable, interconnected knowledge base*
