# Automated Changelog Generation

NoteParser uses an automated changelog generation system that creates entries from git commits using the [Conventional Commits](https://conventionalcommits.org/) specification.

## How It Works

1. **Commits are parsed** using conventional commit format
2. **Entries are grouped** by type (feat, fix, docs, etc.)
3. **Changelog is generated** automatically during releases
4. **GitHub releases** include extracted release notes

## Commit Format

Use conventional commits format for all commits:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Commit Types

- `feat`: ✨ New features
- `fix`: 🐛 Bug fixes
- `docs`: 📚 Documentation changes
- `style`: 🎨 Code style changes (formatting, etc.)
- `refactor`: ♻️ Code refactoring
- `perf`: ⚡ Performance improvements
- `test`: 🧪 Test additions or modifications
- `build`: 🔨 Build system or dependencies
- `ci`: 🔧 CI/CD configuration changes
- `chore`: 🔧 Maintenance tasks

### Examples

```bash
# New feature
git commit -m "feat(parser): add PDF OCR support with tesseract integration"

# Bug fix
git commit -m "fix(cli): resolve argument parsing error with --output flag"

# Breaking change
git commit -m "feat(api)!: redesign REST API endpoints for v2.0"

# With scope and body
git commit -m "perf(core): optimize document processing pipeline

Reduce memory usage by 40% through streaming processing
and improved garbage collection in large document parsing."
```

## Manual Generation

You can manually generate or update the changelog:

```bash
# Generate changelog for specific version
python3 scripts/generate-changelog.py --version v2.1.0

# Regenerate complete changelog from all tags
python3 scripts/generate-changelog.py --full

# Generate for latest tag
python3 scripts/generate-changelog.py
```

## Automated Integration

### Release Script

The `scripts/release.sh` automatically:
1. Generates changelog for the new version
2. Commits the updated CHANGELOG.md
3. Creates git tags with release notes

```bash
./scripts/release.sh 2.1.0
```

### GitHub Actions

The publish workflow (`.github/workflows/publish.yml`):
1. Runs the changelog generator on new tags
2. Creates GitHub releases with formatted notes
3. Updates the repository CHANGELOG.md

### Pre-commit Hooks

Consider adding a pre-commit hook to validate commit messages:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.0.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
```

## Benefits

### ✅ **Automated**
- No manual changelog maintenance
- Consistent formatting across releases
- Automatic GitHub release notes

### ✅ **Structured**
- Clear categorization by change type
- Breaking changes highlighted
- Links to commits and comparisons

### ✅ **Developer Friendly**
- Encourages better commit messages
- Clear project history
- Easier code review and debugging

## Migration Guide

If you have existing commits that don't follow conventional format:

1. **New commits**: Use conventional format going forward
2. **Old commits**: The generator handles non-conventional commits as "chore" type
3. **Manual entries**: Can be added directly to CHANGELOG.md if needed

## Customization

The changelog generator can be customized by editing `scripts/generate-changelog.py`:

- **Commit types**: Modify `COMMIT_TYPES` dictionary
- **Grouping logic**: Adjust `group_commits_by_type()` method
- **Output format**: Customize `generate_version_entry()` method
- **Parsing rules**: Update `parse_conventional_commit()` regex

## Best Practices

### Commit Messages
- Use imperative mood ("add feature" not "added feature")
- Keep first line under 72 characters
- Reference issues: "fix(parser): resolve PDF parsing issue (#123)"
- Use scopes consistently: "feat(api)", "fix(cli)", "docs(readme)"

### Breaking Changes
- Mark with `!`: `feat(api)!: redesign authentication`
- Explain migration in commit body
- Update major version number

### Release Process
- Run `./scripts/release.sh` for all releases
- Review generated changelog before pushing
- Ensure all PRs use conventional commits

This system ensures consistent, informative changelogs with minimal manual effort while encouraging better development practices through structured commit messages.
