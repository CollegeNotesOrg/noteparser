#!/bin/bash

# NoteParser Release Script
# Usage: ./scripts/release.sh [version] [--dry-run]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VERSION="${1:-}"
DRY_RUN="${2:-}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')] $*${NC}"; }
warn() { echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARNING: $*${NC}" >&2; }
error() { echo -e "${RED}[$(date +'%H:%M:%S')] ERROR: $*${NC}" >&2; exit 1; }
success() { echo -e "${GREEN}[$(date +'%H:%M:%S')] SUCCESS: $*${NC}"; }

# Get current version from pyproject.toml
get_current_version() {
    grep '^version = ' "$PROJECT_DIR/pyproject.toml" | sed 's/version = "\(.*\)"/\1/'
}

# Validate version format
validate_version() {
    local version="$1"
    if [[ ! $version =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+)?$ ]]; then
        error "Invalid version format: $version. Use semantic versioning (e.g., 2.1.0)"
    fi
}

# Update version in pyproject.toml
update_version() {
    local new_version="$1"
    log "Updating version to $new_version..."
    
    if [[ "$DRY_RUN" == "--dry-run" ]]; then
        log "DRY RUN: Would update version in pyproject.toml"
        return
    fi
    
    sed -i.bak "s/^version = .*/version = \"$new_version\"/" "$PROJECT_DIR/pyproject.toml"
    rm -f "$PROJECT_DIR/pyproject.toml.bak"
}

# Update version in __init__.py
update_init_version() {
    local new_version="$1"
    local init_file="$PROJECT_DIR/src/noteparser/__init__.py"
    
    if [[ -f "$init_file" ]]; then
        log "Updating version in __init__.py..."
        
        if [[ "$DRY_RUN" == "--dry-run" ]]; then
            log "DRY RUN: Would update version in __init__.py"
            return
        fi
        
        # Create or update __version__
        if grep -q "__version__" "$init_file"; then
            sed -i.bak "s/__version__ = .*/__version__ = \"$new_version\"/" "$init_file"
        else
            echo "__version__ = \"$new_version\"" >> "$init_file"
        fi
        rm -f "$init_file.bak"
    fi
}

# Run tests
run_tests() {
    log "Running tests..."
    
    cd "$PROJECT_DIR"
    
    if [[ "$DRY_RUN" == "--dry-run" ]]; then
        log "DRY RUN: Would run tests"
        return
    fi
    
    # Install in development mode
    pip install -e ".[dev,all]"
    
    # Run linting
    log "Running linters..."
    ruff check src/ tests/ || error "Linting failed"
    black --check src/ tests/ || error "Code formatting check failed"
    
    # Run tests
    log "Running test suite..."
    pytest tests/ -v || error "Tests failed"
    
    success "All tests passed"
}

# Build package
build_package() {
    log "Building package..."
    
    cd "$PROJECT_DIR"
    
    if [[ "$DRY_RUN" == "--dry-run" ]]; then
        log "DRY RUN: Would build package"
        return
    fi
    
    # Clean previous builds
    rm -rf dist/ build/ *.egg-info/
    
    # Install build tools
    pip install --upgrade build twine
    
    # Build
    python -m build
    
    # Check package
    twine check dist/*
    
    success "Package built successfully"
}

# Create git tag
create_tag() {
    local version="$1"
    local tag_name="v$version"
    
    log "Creating git tag $tag_name..."
    
    if [[ "$DRY_RUN" == "--dry-run" ]]; then
        log "DRY RUN: Would create tag $tag_name and push to remote"
        return
    fi
    
    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        error "There are uncommitted changes. Please commit them first."
    fi
    
    # Create annotated tag
    git tag -a "$tag_name" -m "Release version $version

🚀 NoteParser $version

This release includes:
- AI-powered document processing and analysis
- Production-ready deployment configurations
- Comprehensive testing and monitoring
- Enhanced web interface with interactive AI features

See CHANGELOG.md for detailed changes."
    
    # Push tag
    git push origin "$tag_name"
    
    success "Tag $tag_name created and pushed"
}

# Upload to PyPI
upload_to_pypi() {
    local version="$1"
    
    log "Uploading to PyPI..."
    
    if [[ "$DRY_RUN" == "--dry-run" ]]; then
        log "DRY RUN: Would upload to PyPI"
        return
    fi
    
    cd "$PROJECT_DIR"
    
    # Upload to PyPI
    twine upload dist/*
    
    success "Package uploaded to PyPI"
    log "Package available at: https://pypi.org/project/noteparser/$version/"
}

# Generate changelog
generate_changelog() {
    local version="$1"
    
    log "Generating automated changelog for version $version..."
    
    if [[ "$DRY_RUN" == "--dry-run" ]]; then
        log "DRY RUN: Would generate changelog using automated script"
        return
    fi
    
    # Use the automated changelog generator
    python3 "$SCRIPT_DIR/generate-changelog.py" --version "v$version"
    
    if [[ $? -eq 0 ]]; then
        success "Changelog generated successfully"
    else
        warn "Changelog generation failed, continuing with release"
    fi
}

# Main release function
main() {
    log "Starting NoteParser release process..."
    
    cd "$PROJECT_DIR"
    
    # Get current version
    local current_version=$(get_current_version)
    log "Current version: $current_version"
    
    # Determine new version
    if [[ -z "$VERSION" ]]; then
        log "Available version bump options:"
        echo "  patch: $current_version -> $(echo $current_version | awk -F. '{$NF = $NF + 1;} 1' | sed 's/ /./g')"
        echo "  minor: $current_version -> $(echo $current_version | awk -F. '{$(NF-1) = $(NF-1) + 1; $NF = 0} 1' | sed 's/ /./g')"
        echo "  major: $current_version -> $(echo $current_version | awk -F. '{$1 = $1 + 1; $(NF-1) = 0; $NF = 0} 1' | sed 's/ /./g')"
        echo ""
        read -p "Enter new version (or patch/minor/major): " VERSION
    fi
    
    # Handle semantic shortcuts
    case "$VERSION" in
        "patch")
            VERSION=$(echo $current_version | awk -F. '{$NF = $NF + 1;} 1' | sed 's/ /./g')
            ;;
        "minor")
            VERSION=$(echo $current_version | awk -F. '{$(NF-1) = $(NF-1) + 1; $NF = 0} 1' | sed 's/ /./g')
            ;;
        "major")
            VERSION=$(echo $current_version | awk -F. '{$1 = $1 + 1; $(NF-1) = 0; $NF = 0} 1' | sed 's/ /./g')
            ;;
    esac
    
    validate_version "$VERSION"
    
    log "Releasing version: $VERSION"
    
    if [[ "$DRY_RUN" == "--dry-run" ]]; then
        warn "DRY RUN MODE - No changes will be made"
    else
        read -p "Continue with release? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Release cancelled"
            exit 0
        fi
    fi
    
    # Release steps
    run_tests
    update_version "$VERSION"
    update_init_version "$VERSION"
    build_package
    generate_changelog "$VERSION"
    
    if [[ "$DRY_RUN" != "--dry-run" ]]; then
        # Commit version changes
        git add pyproject.toml src/noteparser/__init__.py CHANGELOG.md
        git commit -m "chore: bump version to $VERSION

🔖 Release $VERSION

- Updated package version in pyproject.toml
- Updated __version__ in __init__.py
- Generated changelog for this release

Ready for PyPI publication and GitHub release."
    fi
    
    create_tag "$VERSION"
    
    # Note: PyPI upload will be handled by GitHub Actions
    log "🎉 Release $VERSION completed!"
    log ""
    log "Next steps:"
    log "  1. GitHub Actions will automatically:"
    log "     - Run tests across all platforms"
    log "     - Build and publish to PyPI"
    log "     - Create GitHub release with changelog"
    log "     - Build and push Docker images"
    log ""
    log "  2. Monitor the release:"
    log "     - GitHub: https://github.com/CollegeNotesOrg/noteparser/releases"
    log "     - PyPI: https://pypi.org/project/noteparser/"
    log "     - Docker: https://hub.docker.com/r/collegenotesorg/noteparser"
    log ""
    log "  3. Update documentation if needed"
    log "  4. Announce the release"
}

# Handle script arguments
if [[ $# -gt 0 && "$1" == "--help" ]]; then
    echo "NoteParser Release Script"
    echo ""
    echo "Usage: $0 [version] [--dry-run]"
    echo ""
    echo "Arguments:"
    echo "  version    Version number (e.g., 2.1.0) or 'patch', 'minor', 'major'"
    echo "  --dry-run  Preview changes without making them"
    echo ""
    echo "Examples:"
    echo "  $0                  # Interactive version selection"
    echo "  $0 2.1.0            # Release specific version"
    echo "  $0 minor            # Bump minor version"
    echo "  $0 2.1.0 --dry-run  # Preview release without changes"
    echo ""
    echo "The script will:"
    echo "  1. Run tests and linting"
    echo "  2. Update version in pyproject.toml and __init__.py"
    echo "  3. Build the package"
    echo "  4. Generate changelog"
    echo "  5. Create and push git tag"
    echo "  6. Trigger automated PyPI upload via GitHub Actions"
    exit 0
fi

main