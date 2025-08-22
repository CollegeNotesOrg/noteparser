# Quick Start

Get up and running with NoteParser in just a few minutes!

## 1. Installation

First, install NoteParser:

```bash
pip install noteparser
```

For all features (recommended):

```bash
pip install noteparser[all]
```

!!! tip "System Dependencies"
    For OCR and media processing, install system dependencies:
    
    === "Ubuntu/Debian"
        ```bash
        sudo apt-get install tesseract-ocr ffmpeg poppler-utils
        ```
    === "macOS"
        ```bash
        brew install tesseract ffmpeg poppler
        ```
    === "Windows"
        ```bash
        choco install tesseract ffmpeg poppler
        ```

## 2. Your First Parse

Let's convert a document to Markdown:

```bash
# Parse a PDF to Markdown
noteparser parse lecture.pdf

# Parse with specific output format
noteparser parse notes.docx --format latex --output notes.tex

# Parse with metadata extraction
noteparser parse handout.pdf --metadata
```

## 3. Initialize Your Project

Set up NoteParser in your study directory:

```bash
# Navigate to your notes directory
cd /path/to/your/notes

# Initialize configuration
noteparser init

# This creates .noteparser-org.yml with default settings
```

## 4. Batch Processing

Process multiple documents at once:

```bash
# Process all files in a directory
noteparser batch documents/

# Process only PDFs recursively
noteparser batch semester-notes/ --pattern "*.pdf" --recursive

# Process to LaTeX format
noteparser batch input/ --format latex --output-dir latex-output/
```

## 5. Web Dashboard

Start the web interface for easy management:

```bash
noteparser web
```

Then open your browser to `http://localhost:5000` to:

- Browse your documents
- Parse files through the web interface
- Search across all notes
- Manage plugins and settings

## 6. Organization Sync

Sync your parsed notes to a study repository:

```bash
# Sync specific files
noteparser sync output/*.md --target-repo study-notes --course CS101

# Sync all markdown files
noteparser sync *.md
```

## Common Workflows

### 📖 **Daily Student Workflow**

```bash
# 1. Convert today's lecture slides
noteparser parse "CS101_Lecture_15.pdf"

# 2. Sync to your study repository
noteparser sync output/cs101-lecture-15.md --course CS101

# 3. View in web dashboard
noteparser web
```

### 🏫 **Course Setup**

```bash
# 1. Initialize in course directory
cd ~/courses/fall2024/cs101
noteparser init

# 2. Process all existing materials
noteparser batch course-materials/ --recursive

# 3. Generate course index
noteparser index --format json > course-index.json
```

### 👥 **Study Group Collaboration**

```bash
# 1. Process shared materials
noteparser parse "Group_Study_Notes.docx"

# 2. Commit to shared repository
git add output/group-study-notes.md
git commit -m "Add processed study notes"
git push
```

## Python API Quick Start

Use NoteParser programmatically:

```python
from noteparser import NoteParser
from noteparser.integration import OrganizationSync

# Initialize parser
parser = NoteParser()

# Parse a document
result = parser.parse_to_markdown("lecture.pdf")
print(result['content'])
print(result['metadata'])

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

## Configuration Basics

Create `.noteparser-org.yml` in your project root:

```yaml
organization:
  name: "my-study-notes"
  base_path: "."

repositories:
  study-notes:
    type: "notes"
    auto_sync: true
    formats: ["markdown", "latex"]

plugins:
  math_processor:
    enabled: true
    config:
      equation_numbering: true
  
  cs_processor:
    enabled: true
    config:
      code_line_numbers: true
```

## Plugin System

Enable course-specific processing:

```bash
# List available plugins
noteparser plugins

# Plugins are automatically applied based on:
# - File content
# - Course metadata
# - File extensions
```

Built-in plugins include:

- **Math Processor**: Enhanced equation handling
- **CS Processor**: Code block improvements  
- **Chemistry Processor**: Chemical formula formatting

## GitHub Actions Integration

Automate processing with GitHub Actions:

```yaml
# .github/workflows/parse-notes.yml
name: Parse Notes
on:
  push:
    paths: ['input/**']

jobs:
  parse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install NoteParser
        run: pip install noteparser[all]
      - name: Parse documents
        run: noteparser batch input/ --format markdown
      - name: Sync to study repo
        run: noteparser sync output/*.md --target-repo study-notes
```

## Tips for Success

!!! tip "File Organization"
    Organize your files with clear naming:
    ```
    semester-notes/
    ├── CS101/
    │   ├── lectures/
    │   ├── assignments/
    │   └── exams/
    ├── MATH201/
    └── output/
    ```

!!! tip "Metadata Enhancement"
    Include course info in filenames:
    - `CS101_Lecture_05_DataStructures.pdf`
    - `MATH201_Assignment_03_Calculus.docx`

!!! tip "Regular Syncing"
    Set up automatic syncing to keep your notes organized across repositories.

## What's Next?

Now that you're up and running:

- [📖 Learn the CLI](cli.md) - Master the command-line interface
- [📚 API Reference](api-reference.md) - Complete API documentation
- [⚙️ Advanced Configuration](configuration.md) - Customize your workflow

## Need Help?

- **📚 [Troubleshooting Guide](troubleshooting.md)** - Common solutions
- **🐛 [Issues](https://github.com/CollegeNotesOrg/noteparser/issues)** - Report problems