# Changelog

All notable changes to NoteParser will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**📝 Note**: This changelog is automatically generated from git commits using [Conventional Commits](https://conventionalcommits.org/) format.
Entries are created during the release process using `scripts/generate-changelog.py`.

## [v2.1.1] - 2025-08-22

### ✨ New Features

- complete AI services integration with database system and production config ([f4253b44])
- upgrade to v2.1.0 with complete release automation and AI documentation ([fe20d740])
- add production-ready AI integration with web interface and deployment ([3caf7f65])
- implement production-ready AI services integration ([d2da1861])
- bump version to 2.0.0 with AI integration features ([2aa70d0c])
- update dependencies for AI services integration ([2da637e9])
- add build system and automation scripts ([a562467f])
- add monitoring and observability infrastructure ([2544803f])
- add service configuration and API gateway ([4d4b31f6])
- add Docker infrastructure for development ([96b976fc])
- add AI services integration client library ([71224b3b])
- Add MkDocs documentation website and update organization name ([473e20d3])

### 🐛 Bug Fixes

- resolve plugin system test failures ([7f0003c1])
- resolve remaining mypy type errors and bandit security warnings ([2513518a])
- resolve Docker CI build failures and comprehensive code quality improvements ([6615bfc7])
- resolve Docker CI build failures and optimize image size ([8aee1231])
- update Python requirement to 3.10+ for markitdown compatibility ([3a9728ac])
- add type stubs and fix critical mypy errors ([5a4df828])
- resolve integration test failures for AI services ([bd9c030e])
- enable Docker image loading for testing in CI ([67ed8af4])
- improve pre-commit configuration for CI stability ([c233bd24])
- resolve asyncio event loop conflict in benchmark tests ([8372182c])
- resolve CI linting and configuration issues ([7cf3ea35])
- update deprecated GitHub Actions to restore CI functionality ([f114c56a])
- resolve CI pipeline issues and restore functionality ([72ff0c25])
- resolve broken links ([8605f641])
- Add enablement parameter to configure Pages automatically ([322b5211])
- Add workflow file to documentation build triggers ([fdb5d86e])
- Update GitHub Actions to use latest action versions ([fa320669])

### 📚 Documentation

- improve API reference and add troubleshooting guide ([fa31e82a])
- add footer navigation and analytics to mkdocs config ([63d90652])
- add comprehensive AI integration documentation ([00c93da7])

### ♻️ Code Refactoring

- add service integration patterns ([95b76fed])

### 🎨 Code Style

- modernize type annotations and fix linting errors ([c4490d2b])

### 🔨 Build System

- implement automated changelog system and fix CI dependencies ([955ad679])

### 🔧 Maintenance

- Re-enable Docker build now that DockerHub credentials are configured ([a6dcd6d0])
- Disable Docker build until DockerHub credentials are configured ([6236232b])
- Fix GitHub release workflow ([d233af98])
- Bump version to 2.1.1 ([2c0c903c])

[v2.1.1]: https://github.com/CollegeNotesOrg/noteparser/compare/v1.0.0...v2.1.1

## [v2.1.2] - 2025-08-22

### 🔧 Maintenance

- Bump version to 2.1.2 ([f07231ad])

[v2.1.2]: https://github.com/CollegeNotesOrg/noteparser/compare/v2.1.1...v2.1.2

## [1.0.0] - 2024-08-06

### Added
- Initial release of NoteParser
- Core document parsing functionality using Microsoft MarkItDown
- Support for PDF, DOCX, PPTX, XLSX, HTML, EPUB, and image formats
- Audio and video transcription capabilities
- Enhanced OCR processing for handwritten notes
- Markdown and LaTeX output formats
- Academic-specific formatting preservation
- Plugin system with built-in Math and Computer Science plugins
- Multi-repository organization support
- GitHub Actions integration
- Web dashboard with Flask
- Comprehensive CLI interface
- REST API endpoints
- Cross-reference detection
- Batch processing capabilities
- Metadata extraction
- Bibliography and citation detection

### Features
- 🔄 Multi-format document conversion
- 🎓 Academic-focused processing (equations, theorems, citations)
- 🔌 Extensible plugin architecture
- 🌐 Organization-wide integration
- 🖥️ Web interface for easy management
- 📊 Searchable document indexing

### Dependencies
- Python 3.10+ required
- Microsoft MarkItDown for core parsing
- Flask for web interface
- Various academic processing libraries

[1.0.0]: https://github.com/CollegeNotesOrg/noteparser/releases/tag/v1.0.0

---

**Maintained by**: Suryansh Sijwali ([@SuryanshSS1011](https://github.com/SuryanshSS1011))
**Organization**: [CollegeNotesOrg](https://github.com/CollegeNotesOrg)
