# Installation

This guide will help you install NoteParser and all its dependencies.

## Requirements

- **Python 3.8+** (Python 3.11+ recommended)
- **System dependencies** for OCR and media processing (optional)

## Installation Methods

### Option 1: Using pip (Recommended)

=== "Basic Installation"

    Install the core package from PyPI:

    ```bash
    pip install noteparser
    ```

=== "From Source"

    Install the latest development version:

    ```bash
    git clone https://github.com/CollegeNotesOrg/noteparser.git
    cd noteparser
    pip install -e .
    ```

=== "Development"

    Install with development tools:

    ```bash
    git clone https://github.com/CollegeNotesOrg/noteparser.git
    cd noteparser
    pip install -e .[dev]
    ```

=== "All Features"

    Install with all optional dependencies:

    ```bash
    pip install -e .[all]
    ```

### Option 2: Using requirements.txt

If you prefer managing dependencies explicitly:

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

## Optional Dependencies

NoteParser supports additional features through optional dependencies:

### PDF Processing
```bash
pip install noteparser[pdf]
```
Includes: `pymupdf`, `pdfplumber`

### Office Documents
```bash
pip install noteparser[office]
```
Includes: `python-docx`, `python-pptx`, `openpyxl`

### OCR Capabilities
```bash
pip install noteparser[ocr]
```
Includes: `pytesseract`, `pillow`

### Everything
```bash
pip install noteparser[all]
```
Includes all optional dependencies.

## System Dependencies

Some features require system packages to be installed:

=== "Ubuntu/Debian"

    ```bash
    sudo apt-get update
    sudo apt-get install -y \
        tesseract-ocr \
        tesseract-ocr-eng \
        ffmpeg \
        poppler-utils \
        libreoffice
    ```

=== "macOS"

    Using [Homebrew](https://brew.sh/):

    ```bash
    brew install tesseract ffmpeg poppler
    ```

    Using [MacPorts](https://www.macports.org/):

    ```bash
    sudo port install tesseract ffmpeg poppler
    ```

=== "Windows"

    Using [Chocolatey](https://chocolatey.org/):

    ```bash
    choco install tesseract ffmpeg poppler
    ```

    Using [Scoop](https://scoop.sh/):

    ```bash
    scoop install tesseract ffmpeg poppler
    ```

### What These Dependencies Provide

- **Tesseract OCR**: Text extraction from images and scanned documents
- **FFmpeg**: Audio and video transcription
- **Poppler**: Enhanced PDF processing
- **LibreOffice**: Better Office document conversion

## Verification

Verify your installation:

```bash
# Check if NoteParser is installed
noteparser --version

# Test basic functionality
noteparser --help

# Test with a simple file (if you have one)
noteparser parse sample.pdf
```

## Virtual Environment Setup

We strongly recommend using a virtual environment:

=== "venv"

    ```bash
    # Create virtual environment
    python -m venv noteparser-env

    # Activate (Linux/macOS)
    source noteparser-env/bin/activate

    # Activate (Windows)
    noteparser-env\Scripts\activate

    # Install NoteParser
    pip install noteparser[all]
    ```

=== "conda"

    ```bash
    # Create conda environment
    conda create -n noteparser python=3.11

    # Activate environment
    conda activate noteparser

    # Install NoteParser
    pip install noteparser[all]
    ```

=== "pipenv"

    ```bash
    # Install pipenv if not already installed
    pip install pipenv

    # Create Pipfile and install
    pipenv install noteparser[all]

    # Activate shell
    pipenv shell
    ```

## Docker Installation

For containerized deployment:

```bash
# Pull the official image (when available)
docker pull collegenotesorg/noteparser:latest

# Or build from source
git clone https://github.com/CollegeNotesOrg/noteparser.git
cd noteparser
docker build -t noteparser .

# Run container
docker run -it --rm -v $(pwd):/workspace noteparser
```

## Development Setup

For contributing to NoteParser:

```bash
# Clone the repository
git clone https://github.com/CollegeNotesOrg/noteparser.git
cd noteparser

# Create development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies including dev tools
pip install -r requirements-dev.txt

# Install in development mode
pip install -e .[all,dev]

# Install pre-commit hooks
pre-commit install

# Verify installation
pytest tests/ -v
```

## Troubleshooting

### Common Issues

#### Python Version
Ensure you're using Python 3.8 or newer:
```bash
python --version
```

#### Permission Errors
On Unix systems, you might need to use `--user`:
```bash
pip install --user noteparser
```

#### System Dependencies Missing
If OCR or media processing fails:

1. Verify system dependencies are installed
2. Check that executables are in your PATH:
   ```bash
   tesseract --version
   ffmpeg -version
   ```

#### Import Errors
If you get import errors, ensure the virtual environment is activated:
```bash
which python
which pip
```

### Getting Help

If you encounter issues:

1. Check the [troubleshooting guide](https://github.com/CollegeNotesOrg/noteparser#troubleshooting)
2. Search [existing issues](https://github.com/CollegeNotesOrg/noteparser/issues)
3. Create a [new issue](https://github.com/CollegeNotesOrg/noteparser/issues/new) with:
   - Your Python version
   - Operating system
   - Complete error message
   - Steps to reproduce

## What's Next?

Once installed, check out:

- [Quick Start Guide](quickstart.md) - Get up and running in 5 minutes
- [Configuration](configuration.md) - Customize NoteParser for your workflow
- [Command Line Interface](cli.md) - Learn the CLI commands
