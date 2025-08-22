# NoteParser 📚

**A comprehensive AI-powered document parser for converting and analyzing academic materials**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/noteparser.svg)](https://badge.fury.io/py/noteparser)
[![CI](https://github.com/CollegeNotesOrg/noteparser/workflows/CI/badge.svg)](https://github.com/CollegeNotesOrg/noteparser/actions)
[![codecov](https://codecov.io/gh/CollegeNotesOrg/noteparser/branch/master/graph/badge.svg)](https://codecov.io/gh/CollegeNotesOrg/noteparser)

NoteParser is a powerful AI-enhanced academic document processing system built on Microsoft's [MarkItDown](https://github.com/microsoft/markitdown) library. It combines traditional document parsing with cutting-edge AI services to provide intelligent document analysis, semantic search, and knowledge extraction for university students and educators.

## ✨ Key Features

### 🔄 **Multi-Format Support**
- **Documents**: PDF, DOCX, PPTX, XLSX, HTML, EPUB
- **Media**: Images with OCR, Audio/Video with transcription
- **Output**: Markdown, LaTeX, HTML

### 🎓 **Academic-Focused Processing**
- **Mathematical equations** preservation and enhancement
- **Code blocks** with syntax highlighting and language detection
- **Bibliography** and citation extraction
- **Chemical formulas** with proper subscript formatting
- **Academic keyword highlighting** (theorem, proof, definition, etc.)

### 🔌 **Extensible Plugin System**
- **Course-specific processors** (Math, Computer Science, Chemistry)
- **Custom parser plugins** for specialized content
- **Easy plugin development** with base classes

### 🌐 **Organization Integration**
- **Multi-repository synchronization** for course organization
- **Cross-reference detection** between related documents
- **Automated GitHub Actions** for continuous processing
- **Searchable indexing** across all notes

### 🤖 **AI-Powered Intelligence**
- **Semantic document analysis** with keyword and topic extraction
- **Natural language Q&A** over your document library
- **Intelligent summarization** and insight generation
- **Knowledge graph** construction and navigation
- **AI-enhanced search** with relevance ranking

### 🖥️ **Multiple Interfaces**
- **AI-enhanced CLI** with natural language commands
- **Interactive web dashboard** with AI features
- **Python API** with async AI integration
- **REST API** endpoints with AI processing

## 🚀 Quick Start

### Installation

#### Option 1: Using pip (Recommended)

```bash
# Install from PyPI with all features (recommended)
pip install noteparser[all]

# Install with AI features only
pip install noteparser[ai]

# Install basic version
pip install noteparser

# Install from source with AI features
git clone https://github.com/CollegeNotesOrg/noteparser.git
cd noteparser
pip install -e .[ai,dev]
```

#### Option 2: Using requirements.txt

```bash
# Clone the repository
git clone https://github.com/CollegeNotesOrg/noteparser.git
cd noteparser

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt

# Install the package
pip install -e .
```

#### System Dependencies

Some features require system packages:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    ffmpeg \
    poppler-utils

# macOS
brew install tesseract ffmpeg poppler

# Windows (using Chocolatey)
choco install tesseract ffmpeg poppler
```

### Basic Usage

```bash
# Initialize in your project directory
noteparser init

# Parse a single document
noteparser parse lecture.pdf --format markdown

# Parse with AI enhancement
noteparser ai analyze lecture.pdf --output enhanced-lecture.md

# Query your knowledge base
noteparser ai query "What is machine learning?" --filters '{"course": "CS101"}'

# Batch process a directory
noteparser batch input/ --recursive --format latex

# Start the AI-enhanced web dashboard
noteparser web --host 0.0.0.0 --port 5000

# Check AI services health
noteparser ai health --detailed

# Sync to organization repository
noteparser sync output/*.md --target-repo study-notes --course CS101
```

### Python API

```python
import asyncio
from noteparser import NoteParser
from noteparser.integration import OrganizationSync

# Initialize parser with AI capabilities
parser = NoteParser(enable_ai=True, llm_client=your_llm_client)

# Parse single document
result = parser.parse_to_markdown("lecture.pdf")
print(result['content'])

# Parse with AI enhancement
async def ai_parse():
    result = await parser.parse_to_markdown_with_ai("lecture.pdf")
    print(f"Content: {result['content']}")
    print(f"AI Insights: {result['ai_processing']}")

asyncio.run(ai_parse())

# Query knowledge base
async def query_knowledge():
    result = await parser.query_knowledge(
        "What are the key concepts in machine learning?",
        filters={"course": "CS101"}
    )
    print(f"Answer: {result['answer']}")
    for doc in result['documents']:
        print(f"- {doc['title']} (relevance: {doc['score']:.2f})")

asyncio.run(query_knowledge())

# Batch processing
results = parser.parse_batch("notes/", output_format="markdown")

# Organization sync
org_sync = OrganizationSync()
sync_result = org_sync.sync_parsed_notes(
    source_files=["note1.md", "note2.md"],
    target_repo="study-notes",
    course="CS101"
)
```

## 📁 Project Structure

```
your-study-organization/
├── noteparser/                  # This repository - AI-powered parsing engine
├── noteparser-ai-services/     # AI microservices (RagFlow, DeepWiki)
├── study-notes/                # Main notes repository
│   ├── courses/
│   │   ├── CS101/
│   │   ├── MATH201/
│   │   └── PHYS301/
│   └── .noteparser.yml         # Organization configuration
├── note-templates/             # Shared LaTeX/Markdown templates
├── note-extensions/            # Custom plugins
└── note-dashboard/             # Optional: separate web interface
```

## 🤖 AI Services Setup

NoteParser can operate in two modes:

### Standalone Mode (Basic)
Works without external AI services - provides core document parsing functionality.

### AI-Enhanced Mode (Recommended)
Requires the `noteparser-ai-services` repository for full AI capabilities.

```bash
# Clone and start AI services
git clone https://github.com/CollegeNotesOrg/noteparser-ai-services.git
cd noteparser-ai-services
docker-compose up -d

# Verify services are running
curl http://localhost:8010/health  # RagFlow
curl http://localhost:8011/health  # DeepWiki

# Test AI integration
noteparser ai health
```

**AI Services Documentation**: [https://collegenotesorg.github.io/noteparser-ai-services/](https://collegenotesorg.github.io/noteparser-ai-services/)

## ⚙️ Configuration

### AI Services Configuration (`config/services.yml`)

```yaml
services:
  ragflow:
    host: localhost
    port: 8010
    enabled: true
    config:
      embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
      vector_db_type: "faiss"
      chunk_size: 512
      top_k: 5

  deepwiki:
    host: localhost
    port: 8011
    enabled: true
    config:
      ai_model: "gpt-3.5-turbo"
      auto_link: true
      similarity_threshold: 0.7

features:
  enable_rag: true
  enable_wiki: true
  enable_ai_suggestions: true
```

### Organization Configuration (`.noteparser-org.yml`)

```yaml
organization:
  name: "my-study-notes"
  base_path: "."
  auto_discovery: true

repositories:
  study-notes:
    type: "notes"
    auto_sync: true
    formats: ["markdown", "latex"]
  noteparser:
    type: "parser"
    auto_sync: false

sync_settings:
  auto_commit: true
  commit_message_template: "Auto-sync: {timestamp} - {file_count} files updated"
  branch: "main"
  push_on_sync: false

cross_references:
  enabled: true
  similarity_threshold: 0.7
  max_suggestions: 5
```

### Plugin Configuration

```yaml
plugins:
  math_processor:
    enabled: true
    config:
      equation_numbering: true
      symbol_standardization: true
  
  cs_processor:
    enabled: true
    config:
      code_line_numbers: true
      auto_language_detection: true
```

## 🔌 Plugin Development

Create custom plugins for specialized course content:

```python
from noteparser.plugins import BasePlugin

class ChemistryPlugin(BasePlugin):
    name = "chemistry_processor"
    version = "1.0.0"
    description = "Enhanced processing for chemistry courses"
    course_types = ['chemistry', 'organic', 'biochemistry']
    
    def process_content(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        # Your custom processing logic here
        processed_content = self.enhance_chemical_formulas(content)
        
        return {
            'content': processed_content,
            'metadata': {**metadata, 'chemical_formulas_found': count}
        }
```

## 🌊 GitHub Actions Integration

Automatic processing when you push new documents:

```yaml
# .github/workflows/parse-notes.yml
name: Parse and Sync Notes
on:
  push:
    paths: ['input/**', 'raw-notes/**']

jobs:
  parse-notes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install noteparser[all]
      - name: Parse documents
        run: noteparser batch input/ --format markdown
      - name: Sync to study-notes
        run: noteparser sync output/*.md --target-repo study-notes
```

## 🖥️ AI-Enhanced Web Dashboard

Access the AI-powered web interface at `http://localhost:5000`:

```bash
noteparser web
```

### Core Features:
- **Browse** all repositories and courses
- **Search** across all notes with semantic similarity
- **View** documents with syntax highlighting
- **Parse** new documents through the web interface
- **Manage** plugins and configuration
- **Monitor** sync status and cross-references

### AI Features (`/ai` dashboard):
- **🤖 AI Document Analysis**: Upload and analyze documents with AI insights
- **🔍 Knowledge Querying**: Natural language Q&A over your document library
- **📊 Text Analysis**: Extract keywords, topics, and summaries from content
- **🚀 Enhanced Search**: Semantic search with relevance ranking and AI answers
- **💡 Smart Insights**: Automatic topic detection and content relationships
- **📈 Service Health**: Real-time monitoring of AI service status

### Production Deployment:

```bash
# Using Docker Compose (recommended)
docker-compose -f docker-compose.prod.yml up -d

# Using deployment script
./scripts/deploy.sh production 2.1.0

# Access the application
open http://localhost:5000
open http://localhost:5000/ai  # AI Dashboard
```

## 📊 Use Cases

### 📖 **Individual Student**
```bash
# Daily workflow
noteparser parse "Today's Lecture.pdf" 
noteparser sync output/todays-lecture.md --course CS101
```

### 🏫 **Course Organization**
```bash
# Semester setup
noteparser init
noteparser batch course-materials/ --recursive
noteparser index --format json > course-index.json
```

### 👥 **Study Group**
```bash
# Collaborative notes
noteparser parse shared-notes.docx --format markdown
git add . && git commit -m "Add processed notes"
git push origin main  # Triggers auto-sync via GitHub Actions
```

### 🔬 **Research Lab**
```bash
# Research paper processing
noteparser parse "Research Paper.pdf" --format latex
noteparser web  # Browse and cross-reference with existing notes
```

## 📚 Advanced Features

### 🔍 **Smart Content Detection**
- **Mathematical equations**: Automatic LaTeX formatting preservation
- **Code blocks**: Language detection and syntax highlighting
- **Citations**: APA, MLA, IEEE format recognition
- **Figures and tables**: Structured conversion with captions

### 🏷️ **Metadata Extraction**
- **Course identification** from file names and paths
- **Topic extraction** and categorization
- **Author and date** detection
- **Academic keywords** and tagging

### 🔗 **Cross-References**
- **Similar content detection** across documents
- **Prerequisite tracking** between topics
- **Citation network** visualization
- **Knowledge graph** construction

## 🛠️ Development

### Setup Development Environment

```bash
git clone https://github.com/CollegeNotesOrg/noteparser.git
cd noteparser
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies including dev tools
pip install -r requirements-dev.txt

# Or using pip extras
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install
```

### Run Tests

```bash
pytest tests/ -v --cov=noteparser
```

### Code Quality

```bash
# Formatting
black src/
ruff check src/

# Type checking
mypy src/noteparser/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📦 Dependencies

### Core Dependencies
- **markitdown** - Microsoft's document parsing engine
- **Flask** - Web framework for dashboard
- **Click** - CLI interface
- **PyYAML** - Configuration management
- **Pillow** - Image processing
- **OpenCV** - Advanced image operations
- **pytesseract** - OCR capabilities
- **SpeechRecognition** - Audio transcription
- **moviepy** - Video processing

### Optional Dependencies
- **pdfplumber** - Enhanced PDF processing
- **python-docx/pptx** - Office document handling
- **BeautifulSoup4** - HTML parsing
- **pandas** - Table processing

See `requirements.txt` for the complete list with version specifications.

## 🙏 Acknowledgments

- **Microsoft MarkItDown** - The core parsing engine that powers format conversion
- **Academic Community** - For inspiration and requirements gathering
- **Open Source Libraries** - All the amazing Python packages that make this possible

## 📞 Support

- **Documentation**: [https://collegenotesorg.github.io/noteparser/](https://collegenotesorg.github.io/noteparser/)
- **Issues**: [GitHub Issues](https://github.com/CollegeNotesOrg/noteparser/issues)
- **Discussions**: [GitHub Discussions](https://github.com/CollegeNotesOrg/noteparser/discussions)

---

**Made with ❤️ for students, by a student**

*Transform your study materials into a searchable, interconnected knowledge base*

---

**Author**: Suryansh Sijwali  
**GitHub**: [@SuryanshSS1011](https://github.com/SuryanshSS1011)  
**Organization**: [CollegeNotesOrg](https://github.com/CollegeNotesOrg)
