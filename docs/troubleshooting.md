# Troubleshooting Guide

This guide helps resolve common issues encountered when using NoteParser.

## Installation Issues

### Python Version Compatibility

**Problem:** Installation fails with Python version errors.

**Solution:**
```bash
# Check Python version
python --version

# NoteParser requires Python 3.8+
# Upgrade if necessary
python -m pip install --upgrade python
```

### Dependencies Not Installing

**Problem:** `pip install noteparser` fails with dependency errors.

**Solution:**
```bash
# Update pip first
python -m pip install --upgrade pip

# Install with verbose output to see specific errors
pip install -v noteparser

# Alternative: Use conda
conda install -c conda-forge noteparser
```

### Permission Errors on macOS/Linux

**Problem:** Permission denied errors during installation.

**Solution:**
```bash
# Install for current user only
pip install --user noteparser

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install noteparser
```

## Parsing Issues

### PDF Files Not Processing

**Problem:** PDF files fail to parse or produce empty output.

**Symptoms:**
- Empty Markdown output
- "Unable to extract text" errors
- OCR not working

**Solutions:**

1. **Check PDF format:**
```bash
# Test with a simple text-based PDF first
noteparser parse simple_text.pdf
```

2. **Enable OCR for image-based PDFs:**
```bash
# Install OCR dependencies
pip install noteparser[ocr]

# Parse with OCR enabled
noteparser parse --ocr scanned_document.pdf
```

3. **Handle password-protected PDFs:**
```bash
# Remove password first or use PDF tools
noteparser parse --password your_password protected.pdf
```

### Memory Errors with Large Files

**Problem:** Out of memory errors when processing large documents.

**Solution:**
```bash
# Process in chunks
noteparser parse --chunk-size 1000 large_file.pdf

# Or increase system memory allocation
export NOTEPARSER_MAX_MEMORY=8G
noteparser parse large_file.pdf
```

### Encoding Issues

**Problem:** Special characters not displaying correctly.

**Solution:**
```bash
# Specify encoding explicitly
noteparser parse --encoding utf-8 document.txt

# For Windows files
noteparser parse --encoding cp1252 windows_doc.txt
```

## AI Integration Issues

### API Key Problems

**Problem:** AI features not working, authentication errors.

**Solution:**
```bash
# Set API keys in environment
export OPENAI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"

# Or in config file
noteparser config set openai_api_key "your-key-here"
```

### AI Services Timeout

**Problem:** AI processing takes too long or times out.

**Solution:**
```bash
# Increase timeout
noteparser parse --ai-timeout 300 document.pdf

# Or disable AI features for faster processing
noteparser parse --no-ai document.pdf
```

### Image Description Failures

**Problem:** Images not being described by AI.

**Solution:**
```bash
# Check image formats are supported
noteparser parse --image-formats jpg,png,gif document.pdf

# Enable verbose logging to see AI requests
noteparser parse --verbose --ai-images document.pdf
```

## Output Quality Issues

### Poor Markdown Formatting

**Problem:** Output Markdown is poorly formatted.

**Solutions:**

1. **Enable academic formatting:**
```bash
noteparser parse --academic-format document.pdf
```

2. **Use specific templates:**
```bash
noteparser parse --template lecture_notes document.pdf
```

3. **Preserve original structure:**
```bash
noteparser parse --preserve-structure document.pdf
```

### Missing Mathematical Equations

**Problem:** Math formulas not converted properly.

**Solution:**
```bash
# Enable LaTeX math processing
noteparser parse --math-mode latex document.pdf

# Or use MathJax format
noteparser parse --math-mode mathjax document.pdf
```

### Code Blocks Not Detected

**Problem:** Source code not properly formatted.

**Solution:**
```bash
# Enable code detection
noteparser parse --detect-code document.pdf

# Specify programming languages to look for
noteparser parse --code-languages python,java,javascript document.pdf
```

## Plugin Issues

### Plugin Not Loading

**Problem:** Custom plugins not being recognized.

**Solution:**
```bash
# List available plugins
noteparser plugins list

# Install plugin
noteparser plugins install plugin_name

# Check plugin path
echo $NOTEPARSER_PLUGINS_PATH
```

### Plugin Compatibility

**Problem:** Plugin works with some files but not others.

**Solution:**
```bash
# Check plugin compatibility
noteparser plugins info plugin_name

# Run with specific plugin
noteparser parse --plugin specific_plugin document.pdf
```

## Performance Issues

### Slow Processing

**Problem:** Document processing takes too long.

**Solutions:**

1. **Disable unnecessary features:**
```bash
# Basic conversion only
noteparser parse --no-ai --no-ocr document.pdf
```

2. **Use parallel processing:**
```bash
# Process multiple files in parallel
noteparser batch --parallel 4 documents/
```

3. **Optimize for specific file types:**
```bash
# Skip image processing for text-only PDFs
noteparser parse --no-images document.pdf
```

### High Memory Usage

**Problem:** NoteParser uses too much memory.

**Solution:**
```bash
# Limit memory usage
noteparser parse --max-memory 2G document.pdf

# Process in streaming mode
noteparser parse --streaming document.pdf
```

## CLI Issues

### Command Not Found

**Problem:** `noteparser` command not recognized.

**Solution:**
```bash
# Check if installed correctly
pip show noteparser

# Add to PATH if necessary
export PATH="$PATH:$HOME/.local/bin"

# Or run as module
python -m noteparser parse document.pdf
```

### Configuration File Issues

**Problem:** Config file not being read.

**Solution:**
```bash
# Check config location
noteparser config show-path

# Create default config
noteparser config init

# Validate config file
noteparser config validate
```

## Web Interface Issues

### Web Server Not Starting

**Problem:** `noteparser serve` command fails.

**Solution:**
```bash
# Check port availability
noteparser serve --port 8080

# Run in debug mode
noteparser serve --debug

# Check firewall settings
sudo ufw allow 5000
```

### File Upload Failures

**Problem:** Cannot upload files through web interface.

**Solution:**
```bash
# Increase upload size limit
noteparser serve --max-file-size 100MB

# Check file permissions
chmod 644 document.pdf
```

## Getting Help

### Enable Debug Logging

For any issue, enable verbose logging to get more information:

```bash
# Enable debug output
noteparser --verbose parse document.pdf

# Save log to file
noteparser --log-file debug.log parse document.pdf
```

### Check System Requirements

```bash
# Check system info
noteparser system-info

# Test installation
noteparser test
```

### Report Issues

If you encounter a bug:

1. Enable verbose logging
2. Collect system information
3. Create a minimal example
4. Report at: [GitHub Issues](https://github.com/CollegeNotesOrg/noteparser/issues)

Include in your report:
- NoteParser version: `noteparser --version`
- Python version: `python --version`
- Operating system
- Complete error message
- Steps to reproduce

### Community Support

- **Documentation**: [https://collegenotesorg.github.io/noteparser/](https://collegenotesorg.github.io/noteparser/)
- **GitHub Issues**: [https://github.com/CollegeNotesOrg/noteparser/issues](https://github.com/CollegeNotesOrg/noteparser/issues)
- **Email Support**: Contact maintainers for complex issues

## Common Error Messages

### "Unable to parse file format"

**Cause:** Unsupported file format or corrupted file.

**Solution:**
```bash
# Check supported formats
noteparser formats

# Convert file format first
noteparser convert document.docx --to pdf
```

### "AI service unavailable"

**Cause:** AI services are down or API keys are invalid.

**Solution:**
```bash
# Check service status
noteparser ai status

# Test with different provider
noteparser parse --ai-provider anthropic document.pdf
```

### "Insufficient permissions"

**Cause:** Cannot read input file or write to output directory.

**Solution:**
```bash
# Fix file permissions
chmod 644 input_file.pdf
chmod 755 output_directory/

# Run with different user
sudo -u username noteparser parse document.pdf
```

This troubleshooting guide covers the most common issues. For specific problems not covered here, please check the [GitHub Issues](https://github.com/CollegeNotesOrg/noteparser/issues) or create a new issue with detailed information.