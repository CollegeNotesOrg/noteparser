#!/usr/bin/env python3
"""
Automated changelog generation for NoteParser.
Generates changelog entries from git commits with conventional commit format.
"""

import argparse
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional


class ChangelogGenerator:
    """Generate changelog from git commits using conventional commit format."""

    COMMIT_TYPES = {
        "feat": "### ✨ New Features",
        "fix": "### 🐛 Bug Fixes",
        "docs": "### 📚 Documentation",
        "style": "### 🎨 Code Style",
        "refactor": "### ♻️ Code Refactoring",
        "perf": "### ⚡ Performance Improvements",
        "test": "### 🧪 Tests",
        "build": "### 🔨 Build System",
        "ci": "### 🔧 CI/CD",
        "chore": "### 🔧 Maintenance",
        "revert": "### ⏪ Reverts",
    }

    def __init__(self, repo_path: Path = None):
        self.repo_path = repo_path or Path.cwd()
        self.changelog_path = self.repo_path / "CHANGELOG.md"

    def get_git_tags(self) -> list[str]:
        """Get all git tags sorted by version."""
        try:
            result = subprocess.run(
                ["git", "tag", "--sort=-version:refname"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return [tag.strip() for tag in result.stdout.split("\n") if tag.strip()]
        except subprocess.CalledProcessError:
            return []

    def get_commits_between_tags(self, from_tag: Optional[str], to_tag: Optional[str]) -> list[str]:
        """Get commits between two tags."""
        if from_tag and to_tag:
            rev_range = f"{from_tag}..{to_tag}"
        elif from_tag:
            rev_range = f"{from_tag}..HEAD"
        elif to_tag:
            rev_range = to_tag
        else:
            rev_range = "HEAD"

        try:
            result = subprocess.run(
                ["git", "log", "--pretty=format:%H|%s|%an|%ad", "--date=short", rev_range],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return [line.strip() for line in result.stdout.split("\n") if line.strip()]
        except subprocess.CalledProcessError:
            return []

    def parse_conventional_commit(self, commit_message: str) -> tuple[str, str, str, bool]:
        """
        Parse conventional commit message.
        Returns: (type, scope, description, is_breaking)
        """
        # Conventional commit format: type(scope): description
        pattern = r"^(\w+)(?:\(([^)]+)\))?(!)?: (.+)$"
        match = re.match(pattern, commit_message)

        if match:
            commit_type = match.group(1)
            scope = match.group(2) or ""
            is_breaking = bool(match.group(3))
            description = match.group(4)
            return commit_type, scope, description, is_breaking

        # Fallback for non-conventional commits
        return "chore", "", commit_message, False

    def group_commits_by_type(self, commits: list[str]) -> dict[str, list[dict]]:
        """Group commits by their type."""
        grouped = {}
        breaking_changes = []

        for commit_line in commits:
            parts = commit_line.split("|", 3)
            if len(parts) < 4:
                continue

            commit_hash, message, author, date = parts
            commit_type, scope, description, is_breaking = self.parse_conventional_commit(message)

            commit_info = {
                "hash": commit_hash[:8],
                "message": description,
                "scope": scope,
                "author": author,
                "date": date,
                "is_breaking": is_breaking,
            }

            if is_breaking:
                breaking_changes.append(commit_info)

            if commit_type not in grouped:
                grouped[commit_type] = []
            grouped[commit_type].append(commit_info)

        if breaking_changes:
            grouped["BREAKING"] = breaking_changes

        return grouped

    def generate_version_entry(self, version: str, from_tag: Optional[str]) -> str:
        """Generate changelog entry for a specific version."""
        commits = self.get_commits_between_tags(from_tag, version)
        if not commits:
            return ""

        grouped_commits = self.group_commits_by_type(commits)

        # Get version date
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%ad", "--date=short", version],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            version_date = result.stdout.strip()
        except subprocess.CalledProcessError:
            version_date = datetime.now().strftime("%Y-%m-%d")

        # Build changelog entry
        lines = [
            f"## [{version}] - {version_date}",
            "",
        ]

        # Breaking changes first
        if "BREAKING" in grouped_commits:
            lines.extend(
                [
                    "### 💥 BREAKING CHANGES",
                    "",
                ],
            )
            for commit in grouped_commits["BREAKING"]:
                scope_str = f"**{commit['scope']}**: " if commit["scope"] else ""
                lines.append(f"- {scope_str}{commit['message']} ([{commit['hash']}])")
            lines.append("")

        # Other changes grouped by type
        for commit_type in [
            "feat",
            "fix",
            "docs",
            "perf",
            "refactor",
            "style",
            "test",
            "build",
            "ci",
            "chore",
        ]:
            if commit_type in grouped_commits and commit_type != "BREAKING":
                type_header = self.COMMIT_TYPES.get(commit_type, f"### {commit_type.title()}")
                lines.extend(
                    [
                        type_header,
                        "",
                    ],
                )

                for commit in grouped_commits[commit_type]:
                    scope_str = f"**{commit['scope']}**: " if commit["scope"] else ""
                    lines.append(f"- {scope_str}{commit['message']} ([{commit['hash']}])")
                lines.append("")

        # Add comparison link
        if from_tag:
            lines.append(
                f"[{version}]: https://github.com/CollegeNotesOrg/noteparser/compare/{from_tag}...{version}",
            )
        else:
            lines.append(
                f"[{version}]: https://github.com/CollegeNotesOrg/noteparser/releases/tag/{version}",
            )

        return "\n".join(lines)

    def update_changelog_for_version(self, version: str) -> None:
        """Update CHANGELOG.md with a new version entry."""
        tags = self.get_git_tags()

        # Find the previous tag
        current_tag_index = None
        if version in tags:
            current_tag_index = tags.index(version)

        from_tag = None
        if current_tag_index is not None and current_tag_index + 1 < len(tags):
            from_tag = tags[current_tag_index + 1]

        # Generate new entry
        new_entry = self.generate_version_entry(version, from_tag)
        if not new_entry:
            print(f"No commits found for version {version}")
            return

        # Read existing changelog
        if self.changelog_path.exists():
            content = self.changelog_path.read_text()
        else:
            content = """# Changelog

All notable changes to NoteParser will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"""

        # Insert new entry after header
        lines = content.split("\n")
        header_end = 0
        for i, line in enumerate(lines):
            if line.startswith("##"):
                header_end = i
                break

        if header_end == 0:
            # No existing versions, add after header
            for i, line in enumerate(lines):
                if line.strip() == "":
                    header_end = i + 1
                    break

        # Insert new entry
        lines.insert(header_end, new_entry)
        lines.insert(header_end + 1, "")

        # Write back to file
        self.changelog_path.write_text("\n".join(lines))
        print(f"✅ Updated CHANGELOG.md for version {version}")

    def generate_full_changelog(self) -> None:
        """Generate complete changelog from all git tags."""
        tags = self.get_git_tags()

        header = """# Changelog

All notable changes to NoteParser will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"""

        entries = []
        for i, tag in enumerate(tags):
            from_tag = tags[i + 1] if i + 1 < len(tags) else None
            entry = self.generate_version_entry(tag, from_tag)
            if entry:
                entries.append(entry)

        full_changelog = header + "\n\n".join(entries)
        self.changelog_path.write_text(full_changelog)
        print(f"✅ Generated complete changelog with {len(entries)} versions")


def main():
    parser = argparse.ArgumentParser(description="Generate automated changelog")
    parser.add_argument("--version", "-v", help="Generate changelog for specific version")
    parser.add_argument("--full", "-f", action="store_true", help="Regenerate full changelog")
    parser.add_argument(
        "--repo-path", "-r", type=Path, help="Repository path (default: current directory)",
    )

    args = parser.parse_args()

    generator = ChangelogGenerator(args.repo_path)

    if args.full:
        generator.generate_full_changelog()
    elif args.version:
        generator.update_changelog_for_version(args.version)
    else:
        # Default: generate for latest tag or HEAD
        tags = generator.get_git_tags()
        if tags:
            generator.update_changelog_for_version(tags[0])
        else:
            print(
                "No tags found. Use --version to specify a version or --full to generate complete changelog.",
            )


if __name__ == "__main__":
    main()
