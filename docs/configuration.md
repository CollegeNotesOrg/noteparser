# Configuration

NoteParser is highly configurable to suit your academic workflow. This guide covers all configuration options and how to customize your setup.

## Configuration Files

### Organization Configuration (`.noteparser-org.yml`)

The main configuration file should be placed in your project root:

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

## Configuration Sections

### Organization Settings

Configure your study organization structure:

=== "Basic Setup"
    ```yaml
    organization:
      name: "my-study-notes"
      base_path: "."
      auto_discovery: true
    ```

=== "Advanced Setup"
    ```yaml
    organization:
      name: "university-notes"
      base_path: "/Users/student/notes"
      auto_discovery: true
      default_course: "CS101"
      academic_year: "2024-2025"
      semester: "Fall"
    ```

**Options:**
- `name`: Organization identifier
- `base_path`: Root directory for notes
- `auto_discovery`: Automatically detect courses from directory structure
- `default_course`: Default course for uncategorized notes
- `academic_year`: Current academic year
- `semester`: Current semester

### Repository Configuration

Define repositories in your organization:

```yaml
repositories:
  study-notes:
    type: "notes"                    # Repository type
    auto_sync: true                  # Enable automatic syncing
    formats: ["markdown", "latex"]   # Supported output formats
    branch: "main"                   # Target branch
    path: "../study-notes"           # Relative path

  shared-resources:
    type: "resources"
    auto_sync: false
    formats: ["markdown"]
    url: "https://github.com/team/shared-notes.git"
```

**Repository Types:**
- `notes`: Main notes repository
- `parser`: NoteParser repository
- `resources`: Shared resources
- `templates`: LaTeX/Markdown templates
- `plugins`: Custom plugins

### Sync Settings

Control how notes are synchronized:

```yaml
sync_settings:
  auto_commit: true
  commit_message_template: "Auto-sync: {timestamp} - {file_count} files updated"
  branch: "main"
  push_on_sync: false
  ignore_patterns:
    - "*.tmp"
    - ".DS_Store"
  conflict_resolution: "newest"  # newest, ask, skip
```

### Cross-Reference Settings

Configure intelligent cross-referencing:

```yaml
cross_references:
  enabled: true
  similarity_threshold: 0.7
  max_suggestions: 5
  algorithms:
    - "cosine_similarity"
    - "jaccard_similarity"
  excluded_words:
    - "the"
    - "and"
    - "or"
```

### Plugin Configuration

Configure course-specific plugins:

=== "Math Course"
    ```yaml
    plugins:
      math_processor:
        enabled: true
        config:
          equation_numbering: true
          symbol_standardization: true
          theorem_detection: true
          proof_formatting: true
    ```

=== "Computer Science"
    ```yaml
    plugins:
      cs_processor:
        enabled: true
        config:
          code_line_numbers: true
          auto_language_detection: true
          syntax_highlighting: true
          algorithm_detection: true
    ```

=== "Chemistry"
    ```yaml
    plugins:
      chemistry_processor:
        enabled: true
        config:
          formula_rendering: true
          reaction_equations: true
          molecular_structures: true
    ```

## Environment Variables

Override configuration with environment variables:

```bash
# Base configuration
export NOTEPARSER_BASE_PATH="/path/to/notes"
export NOTEPARSER_AUTO_SYNC="true"
export NOTEPARSER_LOG_LEVEL="DEBUG"

# Plugin settings
export NOTEPARSER_MATH_ENABLED="true"
export NOTEPARSER_CS_ENABLED="false"

# Sync settings
export NOTEPARSER_AUTO_COMMIT="false"
export NOTEPARSER_BRANCH="develop"
```

### Environment Variable Names

Variables follow the pattern: `NOTEPARSER_[SECTION]_[OPTION]`

- Configuration sections become prefixes
- Nested options use underscores
- Boolean values: `"true"` or `"false"`
- Arrays: comma-separated values

Examples:
```bash
NOTEPARSER_ORGANIZATION_NAME="my-notes"
NOTEPARSER_SYNC_SETTINGS_AUTO_COMMIT="true"
NOTEPARSER_PLUGINS_MATH_PROCESSOR_ENABLED="true"
```

## Configuration Priority

Configuration is loaded in this order (later overrides earlier):

1. **Default values**
2. **Configuration file** (`.noteparser-org.yml`)
3. **Environment variables**
4. **Command-line arguments**

## Course-Specific Configuration

Override settings for specific courses:

```yaml
course_overrides:
  CS101:
    plugins:
      cs_processor:
        enabled: true
        config:
          code_line_numbers: true
      math_processor:
        enabled: false

  MATH201:
    plugins:
      math_processor:
        enabled: true
        config:
          equation_numbering: true
      cs_processor:
        enabled: false
```

## Output Format Configuration

Customize output formats:

```yaml
output_formats:
  markdown:
    extension: ".md"
    template: "academic"
    front_matter: true
    toc: true

  latex:
    extension: ".tex"
    template: "article"
    packages:
      - "amsmath"
      - "amssymb"
      - "graphicx"
    geometry: "margin=1in"
```

## Web Dashboard Settings

Configure the web interface:

```yaml
web:
  host: "127.0.0.1"
  port: 5000
  debug: false
  auth:
    enabled: false
    username: "admin"
    password: "secure_password"
  theme:
    primary_color: "#1976d2"
    sidebar_width: "250px"
```

## Logging Configuration

Control logging behavior:

```yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "noteparser.log"
  max_size: "10MB"
  backup_count: 5
```

## Advanced Settings

### Performance Tuning

```yaml
performance:
  max_workers: 4
  chunk_size: 1000
  memory_limit: "512MB"
  cache_enabled: true
  cache_size: 100
```

### Security Settings

```yaml
security:
  allow_network_requests: true
  trusted_domains:
    - "github.com"
    - "*.edu"
  max_file_size: "50MB"
  allowed_extensions:
    - ".pdf"
    - ".docx"
    - ".pptx"
```

## Validation

Validate your configuration:

```bash
# Check configuration file
noteparser config validate

# Show current configuration
noteparser config show

# Test specific setting
noteparser config test plugins.math_processor.enabled
```

## Configuration Examples

### Individual Student Setup

```yaml
organization:
  name: "john-doe-notes"
  base_path: "~/Documents/Notes"

repositories:
  study-notes:
    type: "notes"
    auto_sync: true

plugins:
  math_processor:
    enabled: true
  cs_processor:
    enabled: true
```

### Study Group Setup

```yaml
organization:
  name: "cs-study-group"
  base_path: "."

repositories:
  shared-notes:
    type: "notes"
    url: "https://github.com/study-group/notes.git"
    auto_sync: true

sync_settings:
  auto_commit: true
  push_on_sync: true
```

### Research Lab Setup

```yaml
organization:
  name: "research-lab-notes"
  base_path: "/shared/research-notes"

repositories:
  literature-review:
    type: "notes"
    formats: ["latex"]
  paper-drafts:
    type: "drafts"
    formats: ["latex"]

cross_references:
  enabled: true
  similarity_threshold: 0.8
```

## Troubleshooting Configuration

### Common Issues

#### Configuration Not Found
```bash
# Check if file exists
ls -la .noteparser-org.yml

# Create default configuration
noteparser init
```

#### Invalid YAML Syntax
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('.noteparser-org.yml'))"
```

#### Plugin Not Loading
```bash
# List available plugins
noteparser plugins

# Check plugin configuration
noteparser config show plugins
```

## Migration

### Upgrading Configuration

When updating NoteParser, migrate configuration:

```bash
# Backup current configuration
cp .noteparser-org.yml .noteparser-org.yml.backup

# Migrate to new format
noteparser config migrate

# Validate new configuration
noteparser config validate
```

### Schema Changes

Check the changelog for configuration schema changes between versions.

## What's Next?

- [CLI Interface](cli.md) - Learn about command-line usage
- [API Reference](api-reference.md) - Complete API documentation
- [Quick Start](quickstart.md) - Get started quickly
