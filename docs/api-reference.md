# API Reference

This document provides comprehensive API documentation for the NoteParser system, including Python API, REST API, and CLI interfaces.

## API Overview

1. [Python API](#python-api)
2. [REST API](#rest-api)
3. [CLI Interface](#cli-interface)
4. [Plugin Development API](#plugin-development-api)
5. [Configuration API](#configuration-api)

## Python API

### Core Parser

#### `NoteParser`

The main parsing class that orchestrates document conversion.

```python
from noteparser import NoteParser

parser = NoteParser(config=None, llm_client=None)
```

**Parameters:**
- `config` (dict, optional): Configuration dictionary
- `llm_client` (optional): LLM client for image descriptions

**Methods:**

##### parse_to_markdown()

Parse a document to Markdown format.

```python
def parse_to_markdown(
    file_path: Union[str, Path],
    extract_metadata: bool = True,
    preserve_formatting: bool = True
) -> ParseResult
```

**Parameters:**
- `file_path` (str|Path): Path to input file
- `extract_metadata` (bool, optional): Whether to extract metadata. Defaults to True.
- `preserve_formatting` (bool, optional): Whether to preserve academic formatting. Defaults to True.

**Example:**
```python
result = parser.parse_to_markdown(
    "lecture.pdf",
    extract_metadata=True,
    preserve_formatting=True
)
```

**Returns:**
```python
{
    "content": "# Parsed markdown content...",
    "metadata": {
        "course": "CS101",
        "topic": "Data Structures",
        "word_count": 1500,
        "author": "Prof. Smith",
        # ... other metadata
    }
}
```

##### parse_to_latex()

Parse a document to LaTeX format.

```python
result = parser.parse_to_latex(
    "notes.pdf",
    template="article",
    extract_metadata=True
)
```

**Parameters:**
- `file_path` (str|Path): Path to input file
- `template` (str): LaTeX template ("article", "report", "beamer")
- `extract_metadata` (bool): Whether to extract metadata

**Returns:**
```python
{
    "content": "\\documentclass{article}...",
    "metadata": { /* metadata dictionary */ }
}
```

##### parse_batch()

Parse multiple documents in a directory.

```python
results = parser.parse_batch(
    "input/",
    output_format="markdown",
    recursive=True,
    pattern="*.pdf"
)
```

**Parameters:**
- `directory` (str|Path): Directory containing documents
- `output_format` (str): "markdown" or "latex"
- `recursive` (bool): Search recursively
- `pattern` (str, optional): File pattern to match

**Returns:**
```python
{
    "/path/to/file1.pdf": {
        "content": "...",
        "metadata": {...}
    },
    "/path/to/file2.pdf": {
        "error": "Conversion failed"
    }
}
```

### Organization Integration

#### `OrganizationSync`

Manages synchronization across multiple repositories.

```python
from noteparser.integration import OrganizationSync

org_sync = OrganizationSync(config_path=None)
```

**Methods:**

##### sync_parsed_notes()

Sync parsed notes to target repository.

```python
result = org_sync.sync_parsed_notes(
    source_files=["note1.md", "note2.md"],
    target_repo="study-notes",
    course="CS101"
)
```

**Returns:**
```python
{
    "synced_files": ["/path/to/synced/file1.md", ...],
    "errors": [],
    "target_repository": "study-notes",
    "timestamp": "2024-01-15T10:30:00"
}
```

##### generate_index()

Generate searchable index of all notes.

```python
index = org_sync.generate_index()
```

**Returns:**
```python
{
    "metadata": {
        "generated_at": "2024-01-15T10:30:00",
        "repositories": ["study-notes", "noteparser"],
        "total_files": 150
    },
    "courses": {
        "CS101": [...],
        "MATH201": [...]
    },
    "topics": {
        "algorithms": [...],
        "calculus": [...]
    },
    "files": [...]
}
```

##### create_cross_references()

Create cross-references between documents.

```python
cross_refs = org_sync.create_cross_references({
    "file1.md": "content...",
    "file2.md": "content..."
})
```

### Plugin System

#### `PluginManager`

Manages loading and execution of plugins.

```python
from noteparser.plugins import PluginManager

plugin_manager = PluginManager(plugin_dirs=None)
```

**Methods:**

##### get_plugins_for_file()

Get applicable plugins for a file.

```python
plugins = plugin_manager.get_plugins_for_file(
    Path("math_notes.pdf"),
    {"course": "MATH201"}
)
```

##### process_with_plugins()

Process content with all applicable plugins.

```python
result = plugin_manager.process_with_plugins(
    Path("cs_homework.pdf"),
    "content...",
    {"course": "CS101"}
)
```

## REST API

The web interface provides REST API endpoints for integration.

### Base URL
```
http://localhost:5000/api
```

### Authentication
Currently, no authentication is required for local development. For production deployments, implement appropriate authentication.

### Endpoints

#### POST `/api/parse`

Parse a document via REST API.

**Request:**
```json
{
  "source": "file://path/to/document.pdf",
  "output_formats": ["markdown", "latex"],
  "options": {
    "ocr": true,
    "preserve_formatting": true,
    "extract_metadata": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "results": {
    "markdown": {
      "content": "# Parsed content...",
      "metadata": {...}
    },
    "latex": {
      "content": "\\documentclass{article}...",
      "metadata": {...}
    }
  },
  "processing_time": 2.5
}
```

#### GET `/api/search`

Search across all notes.

**Request:**
```
GET /api/search?q=linear%20algebra&limit=20
```

**Response:**
```json
{
  "results": [
    {
      "path": "/path/to/note.md",
      "repository": "study-notes",
      "course": "MATH201",
      "topic": "Linear Algebra",
      "format": ".md",
      "relevance": 0.95
    }
  ],
  "total": 15,
  "query": "linear algebra"
}
```

#### GET `/api/plugins`

List all available plugins.

**Response:**
```json
{
  "plugins": [
    {
      "name": "math_processor",
      "version": "1.0.0",
      "description": "Enhanced processing for mathematics courses",
      "enabled": true,
      "course_types": ["math", "mathematics", "calculus"],
      "supported_formats": [".pdf", ".docx", ".md"]
    }
  ]
}
```

#### POST `/api/plugins/{plugin_name}/toggle`

Enable or disable a plugin.

**Request:**
```json
{
  "action": "enable"  // or "disable"
}
```

**Response:**
```json
{
  "success": true,
  "action": "enable"
}
```

#### POST `/api/sync`

Sync parsed notes to target repository.

**Request:**
```json
{
  "files": ["/path/to/note1.md", "/path/to/note2.md"],
  "target_repo": "study-notes",
  "course": "CS101"
}
```

**Response:**
```json
{
  "synced_files": ["/target/path/note1.md"],
  "errors": [],
  "target_repository": "study-notes",
  "timestamp": "2024-01-15T10:30:00"
}
```

#### POST `/api/index/refresh`

Refresh the organization index.

**Response:**
```json
{
  "success": true,
  "total_files": 150,
  "repositories": 3,
  "courses": 8,
  "generated_at": "2024-01-15T10:30:00"
}
```

## CLI Interface

The command-line interface provides full access to NoteParser functionality.

### Global Options

```bash
noteparser [--verbose] <command> [options]
```

- `--verbose, -v`: Enable verbose logging

### Commands

#### `parse`

Parse a single document.

```bash
noteparser parse input.pdf [options]
```

**Options:**
- `--output, -o PATH`: Output file path
- `--format, -f FORMAT`: Output format (markdown|latex)
- `--metadata/--no-metadata`: Extract metadata (default: true)
- `--preserve-formatting/--no-preserve-formatting`: Preserve formatting (default: true)

**Examples:**
```bash
# Basic parsing
noteparser parse lecture.pdf

# Parse to LaTeX with custom output
noteparser parse notes.docx -f latex -o output.tex

# Parse without metadata extraction
noteparser parse handout.pdf --no-metadata
```

#### `batch`

Parse multiple documents in a directory.

```bash
noteparser batch input_dir/ [options]
```

**Options:**
- `--output-dir, -o PATH`: Output directory
- `--format, -f FORMAT`: Output format (markdown|latex)
- `--recursive/--no-recursive`: Search recursively (default: true)
- `--pattern, -p PATTERN`: File pattern to match

**Examples:**
```bash
# Parse all files in directory
noteparser batch notes/

# Parse only PDFs recursively
noteparser batch documents/ -p "*.pdf" --recursive

# Parse to LaTeX in custom output directory
noteparser batch input/ -f latex -o latex_output/
```

#### `sync`

Sync parsed notes to target repository.

```bash
noteparser sync [files...] [options]
```

**Options:**
- `--target-repo, -t REPO`: Target repository name
- `--course, -c COURSE`: Course identifier

**Examples:**
```bash
# Sync specific files
noteparser sync output/*.md -t study-notes -c CS101

# Sync all markdown files
noteparser sync *.md
```

#### `index`

Generate organization-wide index.

```bash
noteparser index [options]
```

**Options:**
- `--format, -f FORMAT`: Output format (json|yaml)

**Examples:**
```bash
# Generate JSON index
noteparser index -f json

# Generate YAML index
noteparser index -f yaml > index.yaml
```

#### `plugins`

List and manage plugins.

```bash
noteparser plugins
```

#### `web`

Start the web dashboard.

```bash
noteparser web [options]
```

**Options:**
- `--host, -h HOST`: Host to bind to (default: 127.0.0.1)
- `--port, -p PORT`: Port to bind to (default: 5000)
- `--debug/--no-debug`: Enable debug mode (default: true)

#### `init`

Initialize noteparser configuration.

```bash
noteparser init [options]
```

**Options:**
- `--config-path, -c PATH`: Configuration file path

## Plugin Development API

### Base Plugin Class

Create custom plugins by extending `BasePlugin`.

```python
from noteparser.plugins import BasePlugin

class MyPlugin(BasePlugin):
    name = "my_plugin"
    version = "1.0.0"
    description = "My custom plugin"
    supported_formats = ['.pdf', '.md']
    course_types = ['physics', 'chemistry']
    
    def process_content(self, content: str, metadata: dict) -> dict:
        # Your processing logic here
        processed_content = self.enhance_content(content)
        
        return {
            'content': processed_content,
            'metadata': {
                **metadata,
                'processed_by': self.name,
                'custom_field': 'value'
            }
        }
    
    def can_handle(self, file_path, metadata):
        # Custom logic to determine if plugin should process file
        return super().can_handle(file_path, metadata)
```

### Plugin Methods

#### Required Methods

- `process_content(content, metadata)`: Main processing method
- `can_handle(file_path, metadata)`: Determine if plugin applies

#### Optional Methods

- `validate_config()`: Validate plugin configuration
- `get_info()`: Return plugin information

### Plugin Installation

1. Create your plugin file in `plugins/` directory
2. Restart the application or reload plugins
3. Enable through web interface or API

```python
# plugins/my_custom_plugin.py
from noteparser.plugins import BasePlugin

class MyCustomPlugin(BasePlugin):
    # Implementation here
    pass
```

## Configuration API

### Configuration File Format

Configuration uses YAML format (`.noteparser-org.yml`):

```yaml
organization:
  name: "my-notes"
  base_path: "."

repositories:
  study-notes:
    type: "notes"
    auto_sync: true

plugins:
  math_processor:
    enabled: true
    config:
      equation_numbering: true

# ... other settings
```

### Environment Variables

Override configuration with environment variables:

```bash
export NOTEPARSER_BASE_PATH="/path/to/notes"
export NOTEPARSER_AUTO_SYNC="true"
export NOTEPARSER_LOG_LEVEL="DEBUG"
```

### Configuration Loading Priority

1. Command-line arguments
2. Environment variables
3. Configuration file
4. Default values

## Error Handling

All APIs use consistent error handling:

### Python API Exceptions

```python
from noteparser.exceptions import (
    UnsupportedFormatError,
    ConversionError,
    PluginError
)

try:
    result = parser.parse_to_markdown("file.xyz")
except UnsupportedFormatError as e:
    print(f"Format not supported: {e}")
except ConversionError as e:
    print(f"Conversion failed: {e}")
```

### REST API Error Responses

```json
{
  "success": false,
  "error": "Unsupported file format: .xyz",
  "error_code": "UNSUPPORTED_FORMAT",
  "timestamp": "2024-01-15T10:30:00"
}
```

### CLI Exit Codes

- `0`: Success
- `1`: General error
- `2`: Invalid arguments
- `3`: File not found
- `4`: Unsupported format

## Rate Limits and Quotas

For production deployments, consider implementing:

- Request rate limiting
- File size limits
- Processing time limits
- Concurrent request limits

## Examples

See the `examples/` directory for complete usage examples:

- `examples/basic_usage.py`: Core API usage
- `examples/plugin_development.py`: Custom plugin creation
- `examples/batch_processing.py`: Large-scale processing
- `examples/web_integration.py`: REST API usage

## Support

For additional help:

- [GitHub Issues](https://github.com/CollegeNotesOrg/noteparser/issues)
- [Discussions](https://github.com/CollegeNotesOrg/noteparser/discussions)
- [Documentation](https://collegenotesorg.github.io/noteparser/)

---

**Author**: Suryansh Sijwali  
**Version**: 1.0.0  
**Last Updated**: January 15, 2024
