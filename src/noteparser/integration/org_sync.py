"""Organization-wide synchronization and integration."""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
import subprocess
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class RepositoryConfig:
    """Configuration for a repository in the organization."""
    name: str
    path: Path
    type: str  # 'notes', 'parser', 'templates', 'dashboard'
    auto_sync: bool = True
    formats: List[str] = None
    
    def __post_init__(self):
        if self.formats is None:
            self.formats = ['markdown']


@dataclass
class CrossReference:
    """Cross-reference between documents across repositories."""
    source_repo: str
    source_file: str
    target_repo: str
    target_file: str
    relationship: str  # 'related', 'prerequisite', 'continuation'
    confidence: float = 1.0


class OrganizationSync:
    """Manages synchronization across multiple repositories in the organization."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize organization sync.
        
        Args:
            config_path: Path to organization configuration file
        """
        self.config_path = config_path or Path('.noteparser-org.yml')
        self.config = self._load_config()
        self.repositories = self._discover_repositories()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load organization configuration."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        
        # Default configuration
        default_config = {
            'organization': {
                'name': 'study-notes-org',
                'base_path': '.',
                'auto_discovery': True
            },
            'repositories': {
                'study-notes': {
                    'type': 'notes',
                    'auto_sync': True,
                    'formats': ['markdown', 'latex']
                },
                'noteparser': {
                    'type': 'parser',
                    'auto_sync': False,
                    'formats': ['markdown']
                }
            },
            'sync_settings': {
                'auto_commit': True,
                'commit_message_template': 'Auto-sync: {timestamp} - {file_count} files updated',
                'branch': 'main',
                'push_on_sync': False
            },
            'cross_references': {
                'enabled': True,
                'similarity_threshold': 0.7,
                'max_suggestions': 5
            }
        }
        
        # Save default config
        with open(self.config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
            
        return default_config
        
    def _discover_repositories(self) -> Dict[str, RepositoryConfig]:
        """Discover repositories in the organization."""
        repositories = {}
        base_path = Path(self.config['organization']['base_path'])
        
        # Load from config
        for repo_name, repo_config in self.config['repositories'].items():
            repo_path = base_path / repo_name
            if repo_path.exists():
                repositories[repo_name] = RepositoryConfig(
                    name=repo_name,
                    path=repo_path,
                    type=repo_config['type'],
                    auto_sync=repo_config.get('auto_sync', True),
                    formats=repo_config.get('formats', ['markdown'])
                )
                
        # Auto-discovery if enabled
        if self.config['organization'].get('auto_discovery', True):
            for item in base_path.iterdir():
                if item.is_dir() and (item / '.git').exists():
                    repo_name = item.name
                    if repo_name not in repositories:
                        # Try to determine type from structure
                        repo_type = self._detect_repository_type(item)
                        repositories[repo_name] = RepositoryConfig(
                            name=repo_name,
                            path=item,
                            type=repo_type,
                            auto_sync=False  # Conservative default
                        )
                        
        return repositories
        
    def _detect_repository_type(self, repo_path: Path) -> str:
        """Detect repository type from its structure."""
        # Check for common patterns
        if (repo_path / 'src' / 'noteparser').exists():
            return 'parser'
        elif (repo_path / 'courses').exists() or (repo_path / 'notes').exists():
            return 'notes'
        elif (repo_path / 'templates').exists():
            return 'templates'
        elif (repo_path / 'dashboard').exists() or (repo_path / 'web').exists():
            return 'dashboard'
        else:
            return 'unknown'
            
    def sync_parsed_notes(
        self, 
        source_files: List[Path], 
        target_repo: str = 'study-notes',
        course: Optional[str] = None
    ) -> Dict[str, Any]:
        """Sync parsed notes to the target repository.
        
        Args:
            source_files: List of parsed note files
            target_repo: Target repository name
            course: Optional course identifier for organization
            
        Returns:
            Sync results and statistics
        """
        if target_repo not in self.repositories:
            raise ValueError(f"Repository '{target_repo}' not found in organization")
            
        target_path = self.repositories[target_repo].path
        synced_files = []
        errors = []
        
        for source_file in source_files:
            try:
                # Determine target location
                if course:
                    target_dir = target_path / 'courses' / course
                else:
                    target_dir = target_path / 'parsed'
                    
                target_dir.mkdir(parents=True, exist_ok=True)
                target_file = target_dir / source_file.name
                
                # Copy file
                import shutil
                shutil.copy2(source_file, target_file)
                synced_files.append(str(target_file))
                
                logger.info(f"Synced {source_file} to {target_file}")
                
            except Exception as e:
                errors.append(f"Failed to sync {source_file}: {e}")
                logger.error(f"Sync error: {e}")
                
        # Auto-commit if enabled
        if self.config['sync_settings'].get('auto_commit', True):
            self._auto_commit(target_repo, synced_files)
            
        return {
            'synced_files': synced_files,
            'errors': errors,
            'target_repository': target_repo,
            'timestamp': datetime.now().isoformat()
        }
        
    def create_cross_references(self, content_map: Dict[str, str]) -> List[CrossReference]:
        """Create cross-references between documents.
        
        Args:
            content_map: Map of file paths to content
            
        Returns:
            List of cross-references found
        """
        if not self.config['cross_references'].get('enabled', True):
            return []
            
        cross_refs = []
        files = list(content_map.keys())
        threshold = self.config['cross_references'].get('similarity_threshold', 0.7)
        
        for i, file1 in enumerate(files):
            for file2 in files[i+1:]:
                similarity = self._calculate_similarity(
                    content_map[file1], 
                    content_map[file2]
                )
                
                if similarity > threshold:
                    # Determine repositories
                    repo1 = self._get_repository_for_file(Path(file1))
                    repo2 = self._get_repository_for_file(Path(file2))
                    
                    if repo1 and repo2:
                        cross_ref = CrossReference(
                            source_repo=repo1,
                            source_file=file1,
                            target_repo=repo2,
                            target_file=file2,
                            relationship='related',
                            confidence=similarity
                        )
                        cross_refs.append(cross_ref)
                        
        # Limit results
        max_suggestions = self.config['cross_references'].get('max_suggestions', 5)
        cross_refs.sort(key=lambda x: x.confidence, reverse=True)
        return cross_refs[:max_suggestions]
        
    def generate_index(self) -> Dict[str, Any]:
        """Generate searchable index of all notes across repositories.
        
        Returns:
            Comprehensive index structure
        """
        index = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'repositories': list(self.repositories.keys()),
                'total_files': 0
            },
            'courses': {},
            'topics': {},
            'files': []
        }
        
        for repo_name, repo_config in self.repositories.items():
            if repo_config.type != 'notes':
                continue
                
            repo_files = self._scan_repository_files(repo_config.path)
            
            for file_info in repo_files:
                # Add to index
                index['files'].append({
                    'repository': repo_name,
                    'path': str(file_info['path']),
                    'course': file_info.get('course'),
                    'topic': file_info.get('topic'),
                    'format': file_info['format'],
                    'size': file_info['size'],
                    'modified': file_info['modified']
                })
                
                # Organize by course
                course = file_info.get('course', 'uncategorized')
                if course not in index['courses']:
                    index['courses'][course] = []
                index['courses'][course].append(file_info)
                
                # Organize by topic
                topic = file_info.get('topic', 'general')
                if topic not in index['topics']:
                    index['topics'][topic] = []
                index['topics'][topic].append(file_info)
                
        index['metadata']['total_files'] = len(index['files'])
        
        # Save index
        index_path = Path('.noteparser-index.json')
        with open(index_path, 'w') as f:
            json.dump(index, f, indent=2, default=str)
            
        return index
        
    def _auto_commit(self, repo_name: str, files: List[str]) -> bool:
        """Auto-commit synced files.
        
        Args:
            repo_name: Repository name
            files: List of file paths to commit
            
        Returns:
            True if commit was successful
        """
        repo_path = self.repositories[repo_name].path
        
        try:
            # Add files
            subprocess.run(['git', 'add'] + files, cwd=repo_path, check=True)
            
            # Create commit message
            template = self.config['sync_settings'].get(
                'commit_message_template',
                'Auto-sync: {timestamp} - {file_count} files updated'
            )
            commit_message = template.format(
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                file_count=len(files)
            )
            
            # Commit
            subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=repo_path,
                check=True
            )
            
            logger.info(f"Auto-committed {len(files)} files to {repo_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Auto-commit failed for {repo_name}: {e}")
            return False
            
    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between two pieces of content.
        
        Args:
            content1: First content string
            content2: Second content string
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Simple word-based similarity
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
        
    def _get_repository_for_file(self, file_path: Path) -> Optional[str]:
        """Get repository name for a given file path.
        
        Args:
            file_path: File path to check
            
        Returns:
            Repository name or None if not found
        """
        for repo_name, repo_config in self.repositories.items():
            try:
                file_path.relative_to(repo_config.path)
                return repo_name
            except ValueError:
                continue
        return None
        
    def _scan_repository_files(self, repo_path: Path) -> List[Dict[str, Any]]:
        """Scan repository for note files.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            List of file information dictionaries
        """
        files = []
        supported_extensions = {'.md', '.tex', '.pdf', '.docx', '.txt'}
        
        for file_path in repo_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in supported_extensions:
                # Extract metadata from path
                parts = file_path.relative_to(repo_path).parts
                course = parts[1] if len(parts) > 2 and parts[0] == 'courses' else None
                
                files.append({
                    'path': file_path,
                    'course': course,
                    'topic': file_path.stem,
                    'format': file_path.suffix,
                    'size': file_path.stat().st_size,
                    'modified': file_path.stat().st_mtime
                })
                
        return files