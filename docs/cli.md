# Command Line Interface

NoteParser provides a comprehensive command-line interface for all document processing operations.

## Global Options

```bash
noteparser [--verbose] [--config PATH] <command> [options]
```

**Global Options:**
- `--verbose, -v`: Enable verbose logging
- `--config, -c PATH`: Path to configuration file
- `--help, -h`: Show help message

## Commands Overview

| Command | Description |
|---------|-------------|
| `parse` | Parse a single document |
| `batch` | Process multiple documents |
| `sync` | Sync notes to repositories |
| `web` | Start web dashboard |
| `init` | Initialize configuration |
| `index` | Generate organization index |
| `plugins` | Manage plugins |
| `config` | Configuration management |

## Core Commands

### `parse` - Parse Single Document

Convert a single document to your desired format:

```bash
noteparser parse input.pdf [options]
```

**Options:**
- `--output, -o PATH`: Output file path
- `--format, -f FORMAT`: Output format (`markdown` or `latex`)
- `--metadata/--no-metadata`: Extract metadata (default: true)
- `--preserve-formatting/--no-preserve-formatting`: Preserve formatting (default: true)

=== "Basic Usage"
    ```bash
    # Parse PDF to markdown
    noteparser parse lecture.pdf

    # Parse with specific output file
    noteparser parse notes.docx -o processed-notes.md
    ```

=== "Format Options"
    ```bash
    # Parse to LaTeX
    noteparser parse slides.pptx -f latex

    # Parse without metadata
    noteparser parse handout.pdf --no-metadata
    ```

=== "Advanced Options"
    ```bash
    # Custom output with preserved formatting
    noteparser parse complex-doc.pdf -o output.md --preserve-formatting

    # Parse with verbose logging
    noteparser -v parse document.pdf
    ```

### `batch` - Process Multiple Documents

Process entire directories of documents:

```bash
noteparser batch input_directory/ [options]
```

**Options:**
- `--output-dir, -o PATH`: Output directory
- `--format, -f FORMAT`: Output format (`markdown` or `latex`)
- `--recursive/--no-recursive`: Search recursively (default: true)
- `--pattern, -p PATTERN`: File pattern to match
- `--parallel/--no-parallel`: Enable parallel processing (default: true)

=== "Directory Processing"
    ```bash
    # Process all files in directory
    noteparser batch documents/

    # Process with custom output directory
    noteparser batch input/ -o processed/
    ```

=== "Pattern Matching"
    ```bash
    # Process only PDFs
    noteparser batch docs/ -p "*.pdf"

    # Process multiple file types
    noteparser batch notes/ -p "*.{pdf,docx,pptx}"
    ```

=== "Advanced Batch Processing"
    ```bash
    # Non-recursive processing
    noteparser batch semester-notes/ --no-recursive

    # LaTeX output with custom directory
    noteparser batch input/ -f latex -o latex-output/
    ```

### `sync` - Synchronize Notes

Sync processed notes to target repositories:

```bash
noteparser sync [files...] [options]
```

**Options:**
- `--target-repo, -t REPO`: Target repository name
- `--course, -c COURSE`: Course identifier
- `--branch, -b BRANCH`: Target branch
- `--commit-message, -m MESSAGE`: Custom commit message

=== "File Syncing"
    ```bash
    # Sync specific files
    noteparser sync output/*.md -t study-notes

    # Sync with course specification
    noteparser sync notes.md -t study-notes -c CS101
    ```

=== "Repository Management"
    ```bash
    # Sync to specific branch
    noteparser sync *.md -t study-notes -b develop

    # Sync with custom commit message
    noteparser sync notes.md -m "Add lecture notes for Week 5"
    ```

## Utility Commands

### `web` - Web Dashboard

Start the interactive web interface:

```bash
noteparser web [options]
```

**Options:**
- `--host, -h HOST`: Host to bind to (default: 127.0.0.1)
- `--port, -p PORT`: Port to bind to (default: 5000)
- `--debug/--no-debug`: Enable debug mode
- `--open/--no-open`: Open browser automatically

```bash
# Start on default port
noteparser web

# Start on custom host/port
noteparser web -h 0.0.0.0 -p 8080

# Start with debug mode
noteparser web --debug
```

### `init` - Initialize Configuration

Set up NoteParser in your project:

```bash
noteparser init [options]
```

**Options:**
- `--config-path, -c PATH`: Configuration file path
- `--interactive/--no-interactive`: Interactive setup
- `--template TEMPLATE`: Configuration template

```bash
# Basic initialization
noteparser init

# Interactive setup
noteparser init --interactive

# Custom config path
noteparser init -c custom-config.yml
```

### `index` - Generate Index

Create searchable indexes of your notes:

```bash
noteparser index [options]
```

**Options:**
- `--format, -f FORMAT`: Output format (`json`, `yaml`, or `html`)
- `--output, -o PATH`: Output file path
- `--include-content/--no-include-content`: Include full content

```bash
# Generate JSON index
noteparser index -f json

# Generate HTML index with content
noteparser index -f html --include-content -o index.html
```

## Management Commands

### `plugins` - Plugin Management

List and manage available plugins:

```bash
noteparser plugins [subcommand]
```

**Subcommands:**
- `list`: List all plugins
- `enable PLUGIN`: Enable a plugin
- `disable PLUGIN`: Disable a plugin
- `info PLUGIN`: Show plugin information

```bash
# List all plugins
noteparser plugins list

# Enable math processor
noteparser plugins enable math_processor

# Get plugin information
noteparser plugins info cs_processor
```

### `config` - Configuration Management

Manage configuration settings:

```bash
noteparser config [subcommand]
```

**Subcommands:**
- `show`: Display current configuration
- `validate`: Validate configuration file
- `test SETTING`: Test specific setting
- `migrate`: Migrate configuration format

```bash
# Show current configuration
noteparser config show

# Validate configuration
noteparser config validate

# Test specific setting
noteparser config test plugins.math_processor.enabled
```

## Advanced Usage

### Environment Variables

Set configuration via environment variables:

```bash
export NOTEPARSER_LOG_LEVEL=DEBUG
export NOTEPARSER_AUTO_SYNC=true
noteparser parse document.pdf
```

### Configuration Files

Use custom configuration files:

```bash
noteparser --config my-config.yml parse document.pdf
```

### Piping and Automation

Chain commands together:

```bash
# Parse and immediately sync
noteparser parse lecture.pdf && noteparser sync output/*.md

# Batch process and generate index
noteparser batch docs/ && noteparser index -f json > course-index.json
```

## Error Handling and Debugging

### Verbose Output

Enable detailed logging:

```bash
noteparser -v parse document.pdf
```

### Common Issues

#### File Not Found
```bash
noteparser parse nonexistent.pdf
# Error: File 'nonexistent.pdf' not found
```

#### Permission Errors
```bash
# Fix with proper permissions
chmod +r document.pdf
noteparser parse document.pdf
```

#### Configuration Issues
```bash
# Validate configuration
noteparser config validate

# Show current settings
noteparser config show
```

### Exit Codes

- `0`: Success
- `1`: General error
- `2`: Invalid arguments
- `3`: File not found
- `4`: Unsupported format
- `5`: Configuration error

## Automation Examples

### Shell Scripts

Create automation scripts:

```bash
#!/bin/bash
# daily-processing.sh

# Process today's lecture materials
noteparser batch daily-notes/ -p "*.pdf"

# Sync to study repository
noteparser sync output/*.md -t study-notes -c CS101

# Generate updated index
noteparser index -f json > daily-index.json
```

### Cron Jobs

Schedule regular processing:

```bash
# Add to crontab
0 18 * * * cd /path/to/notes && noteparser batch input/ && noteparser sync output/*.md
```

### Git Hooks

Integrate with Git workflows:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Process any new documents before commit
if [ -d "input" ]; then
    noteparser batch input/ -o processed/
    git add processed/
fi
```

## Performance Tips

### Parallel Processing

Enable parallel processing for large batches:

```bash
noteparser batch large-directory/ --parallel
```

### Memory Usage

For large files, process individually:

```bash
# Instead of batch processing large files
for file in *.pdf; do
    noteparser parse "$file"
done
```

### Caching

Use caching for repeated operations:

```bash
export NOTEPARSER_CACHE_ENABLED=true
noteparser batch documents/
```

## What's Next?

- [API Reference](api-reference.md) - Complete API documentation
- [Configuration](configuration.md) - Customize your setup
- [Quick Start](quickstart.md) - Get up and running quickly
