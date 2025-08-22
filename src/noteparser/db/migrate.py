#!/usr/bin/env python3
"""
Database migration system for noteparser
Handles schema evolution and data migration for AI services integration
"""

import hashlib
import json
import logging
import os
import sqlite3
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import yaml

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Migration:
    """Migration definition."""

    id: str
    name: str
    description: str
    version: str
    up_sql: str
    down_sql: str
    dependencies: List[str] = None
    created_at: str = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class MigrationRunner:
    """Database migration runner and manager."""

    def __init__(self, db_path: str = None, migrations_dir: str = None):
        """Initialize migration runner.

        Args:
            db_path: Path to SQLite database file
            migrations_dir: Directory containing migration files
        """
        self.db_path = db_path or os.getenv("DATABASE_PATH", "noteparser.db")
        self.migrations_dir = Path(migrations_dir or Path(__file__).parent / "migrations")
        self.migrations_dir.mkdir(exist_ok=True)

        # Initialize database and migration table
        self._init_database()

    def _init_database(self):
        """Initialize database and create migration tracking table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    version TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checksum TEXT NOT NULL,
                    execution_time INTEGER
                )
            """,
            )
            conn.commit()

    def create_migration(self, name: str, description: str = "", version: str = None) -> str:
        """Create a new migration file.

        Args:
            name: Migration name
            description: Migration description
            version: Version string (auto-generated if not provided)

        Returns:
            Migration ID
        """
        if version is None:
            version = datetime.now().strftime("%Y%m%d_%H%M%S")

        migration_id = f"{version}_{name.lower().replace(' ', '_').replace('-', '_')}"

        migration = Migration(
            id=migration_id,
            name=name,
            description=description,
            version=version,
            up_sql="-- Add your migration SQL here",
            down_sql="-- Add your rollback SQL here",
        )

        # Create migration file
        migration_file = self.migrations_dir / f"{migration_id}.yaml"
        with open(migration_file, "w") as f:
            yaml.dump(asdict(migration), f, default_flow_style=False)

        logger.info(f"Created migration: {migration_file}")
        return migration_id

    def load_migrations(self) -> Dict[str, Migration]:
        """Load all migrations from the migrations directory."""
        migrations = {}

        for migration_file in sorted(self.migrations_dir.glob("*.yaml")):
            try:
                with open(migration_file) as f:
                    data = yaml.safe_load(f)

                migration = Migration(**data)
                migrations[migration.id] = migration

            except Exception as e:
                logger.error(f"Failed to load migration {migration_file}: {e}")

        return migrations

    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration IDs."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT id FROM schema_migrations ORDER BY applied_at")
            return [row[0] for row in cursor.fetchall()]

    def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations."""
        all_migrations = self.load_migrations()
        applied_migrations = set(self.get_applied_migrations())

        pending = []
        for migration_id, migration in all_migrations.items():
            if migration_id not in applied_migrations:
                # Check dependencies
                if self._dependencies_satisfied(migration, applied_migrations):
                    pending.append(migration)

        # Sort by version
        return sorted(pending, key=lambda m: m.version)

    def _dependencies_satisfied(self, migration: Migration, applied: set) -> bool:
        """Check if migration dependencies are satisfied."""
        for dep in migration.dependencies:
            if dep not in applied:
                return False
        return True

    def _calculate_checksum(self, sql: str) -> str:
        """Calculate checksum for SQL content."""
        return hashlib.md5(sql.encode()).hexdigest()

    def apply_migration(self, migration: Migration) -> bool:
        """Apply a single migration.

        Args:
            migration: Migration to apply

        Returns:
            True if successful
        """
        logger.info(f"Applying migration: {migration.id}")

        start_time = datetime.now()
        checksum = self._calculate_checksum(migration.up_sql)

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Execute migration SQL
                conn.executescript(migration.up_sql)

                # Record migration
                conn.execute(
                    """
                    INSERT INTO schema_migrations 
                    (id, name, description, version, checksum, execution_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        migration.id,
                        migration.name,
                        migration.description,
                        migration.version,
                        checksum,
                        int((datetime.now() - start_time).total_seconds() * 1000),
                    ),
                )

                conn.commit()

            logger.info(f"Migration {migration.id} applied successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to apply migration {migration.id}: {e}")
            return False

    def rollback_migration(self, migration_id: str) -> bool:
        """Rollback a specific migration.

        Args:
            migration_id: ID of migration to rollback

        Returns:
            True if successful
        """
        migrations = self.load_migrations()

        if migration_id not in migrations:
            logger.error(f"Migration {migration_id} not found")
            return False

        migration = migrations[migration_id]
        logger.info(f"Rolling back migration: {migration_id}")

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Execute rollback SQL
                conn.executescript(migration.down_sql)

                # Remove migration record
                conn.execute("DELETE FROM schema_migrations WHERE id = ?", (migration_id,))
                conn.commit()

            logger.info(f"Migration {migration_id} rolled back successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to rollback migration {migration_id}: {e}")
            return False

    def migrate_up(self, target: str = None) -> bool:
        """Run all pending migrations up to target.

        Args:
            target: Target migration ID (all pending if None)

        Returns:
            True if all migrations successful
        """
        pending = self.get_pending_migrations()

        if target:
            # Filter to target migration
            target_index = None
            for i, migration in enumerate(pending):
                if migration.id == target:
                    target_index = i
                    break

            if target_index is None:
                logger.error(f"Target migration {target} not found in pending list")
                return False

            pending = pending[: target_index + 1]

        if not pending:
            logger.info("No pending migrations")
            return True

        logger.info(f"Running {len(pending)} migrations")

        for migration in pending:
            if not self.apply_migration(migration):
                logger.error(f"Migration failed at: {migration.id}")
                return False

        logger.info("All migrations completed successfully")
        return True

    def migrate_down(self, target: str = None, steps: int = 1) -> bool:
        """Rollback migrations.

        Args:
            target: Target migration to rollback to
            steps: Number of migrations to rollback (if target not specified)

        Returns:
            True if successful
        """
        applied = self.get_applied_migrations()

        if not applied:
            logger.info("No migrations to rollback")
            return True

        if target:
            # Rollback to specific target
            try:
                target_index = applied.index(target)
                to_rollback = applied[target_index + 1 :]
            except ValueError:
                logger.error(f"Target migration {target} not found in applied list")
                return False
        else:
            # Rollback specified number of steps
            to_rollback = applied[-steps:] if steps <= len(applied) else applied

        # Rollback in reverse order
        for migration_id in reversed(to_rollback):
            if not self.rollback_migration(migration_id):
                logger.error(f"Rollback failed at: {migration_id}")
                return False

        logger.info(f"Rolled back {len(to_rollback)} migrations")
        return True

    def status(self) -> Dict[str, Any]:
        """Get migration status."""
        all_migrations = self.load_migrations()
        applied = set(self.get_applied_migrations())
        pending = self.get_pending_migrations()

        return {
            "database": self.db_path,
            "migrations_dir": str(self.migrations_dir),
            "total_migrations": len(all_migrations),
            "applied_count": len(applied),
            "pending_count": len(pending),
            "applied_migrations": list(applied),
            "pending_migrations": [m.id for m in pending],
        }

    def reset(self, confirm: bool = False) -> bool:
        """Reset database by rolling back all migrations.

        Args:
            confirm: Must be True to actually reset

        Returns:
            True if successful
        """
        if not confirm:
            logger.warning("Reset requires confirmation (confirm=True)")
            return False

        applied = self.get_applied_migrations()

        if not applied:
            logger.info("No migrations to reset")
            return True

        logger.warning(f"Resetting database: rolling back {len(applied)} migrations")

        return self.migrate_down(steps=len(applied))


def create_base_migrations(runner: MigrationRunner):
    """Create base migrations for noteparser AI integration."""

    # Base tables migration
    runner.create_migration(
        "create_base_tables",
        "Create base tables for document processing and AI integration",
    )

    base_migration_file = runner.migrations_dir / "20240101_000001_create_base_tables.yaml"
    base_migration = Migration(
        id="20240101_000001_create_base_tables",
        name="create_base_tables",
        description="Create base tables for document processing and AI integration",
        version="20240101_000001",
        up_sql="""
-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    original_path TEXT,
    content_hash TEXT UNIQUE,
    file_size INTEGER,
    mime_type TEXT,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_status TEXT DEFAULT 'pending',
    metadata TEXT, -- JSON metadata
    content TEXT,  -- Processed content
    ai_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI processing results table
CREATE TABLE IF NOT EXISTS ai_processing_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    service_name TEXT NOT NULL, -- ragflow, deepwiki, etc.
    processing_type TEXT, -- index, query, analyze
    request_data TEXT, -- JSON request
    response_data TEXT, -- JSON response
    processing_time REAL,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents (id)
);

-- Document relationships
CREATE TABLE IF NOT EXISTS document_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_document_id INTEGER,
    target_document_id INTEGER,
    relationship_type TEXT, -- similar, prerequisite, continuation
    confidence REAL DEFAULT 1.0,
    metadata TEXT, -- JSON metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_document_id) REFERENCES documents (id),
    FOREIGN KEY (target_document_id) REFERENCES documents (id)
);

-- Processing queue
CREATE TABLE IF NOT EXISTS processing_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    service_name TEXT,
    processing_type TEXT,
    priority INTEGER DEFAULT 5,
    status TEXT DEFAULT 'pending', -- pending, processing, completed, failed
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    scheduled_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents (id)
);

-- User sessions (for web interface)
CREATE TABLE IF NOT EXISTS user_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    session_data TEXT, -- JSON session data
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Configuration storage
CREATE TABLE IF NOT EXISTS config_store (
    key TEXT PRIMARY KEY,
    value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(content_hash);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_ai_results_document ON ai_processing_results(document_id);
CREATE INDEX IF NOT EXISTS idx_ai_results_service ON ai_processing_results(service_name);
CREATE INDEX IF NOT EXISTS idx_relationships_source ON document_relationships(source_document_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON document_relationships(target_document_id);
CREATE INDEX IF NOT EXISTS idx_queue_status ON processing_queue(status);
CREATE INDEX IF NOT EXISTS idx_queue_priority ON processing_queue(priority);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at);

-- Insert default configuration
INSERT OR IGNORE INTO config_store (key, value, description) VALUES
    ('ai_services_enabled', 'true', 'Enable AI services integration'),
    ('default_processing_timeout', '300', 'Default processing timeout in seconds'),
    ('max_file_size', '104857600', 'Maximum file size in bytes (100MB)'),
    ('supported_formats', '["pdf", "docx", "pptx", "txt", "md"]', 'Supported file formats'),
    ('auto_ai_processing', 'true', 'Automatically process documents with AI services'),
    ('similarity_threshold', '0.7', 'Similarity threshold for document relationships');
        """,
        down_sql="""
-- Drop indexes
DROP INDEX IF EXISTS idx_sessions_expires;
DROP INDEX IF EXISTS idx_queue_priority;
DROP INDEX IF EXISTS idx_queue_status;
DROP INDEX IF EXISTS idx_relationships_target;
DROP INDEX IF EXISTS idx_relationships_source;
DROP INDEX IF EXISTS idx_ai_results_service;
DROP INDEX IF EXISTS idx_ai_results_document;
DROP INDEX IF EXISTS idx_documents_status;
DROP INDEX IF EXISTS idx_documents_hash;

-- Drop tables
DROP TABLE IF EXISTS config_store;
DROP TABLE IF EXISTS user_sessions;
DROP TABLE IF EXISTS processing_queue;
DROP TABLE IF EXISTS document_relationships;
DROP TABLE IF EXISTS ai_processing_results;
DROP TABLE IF EXISTS documents;
        """,
    )

    with open(base_migration_file, "w") as f:
        yaml.dump(asdict(base_migration), f, default_flow_style=False)

    # AI services integration migration
    runner.create_migration(
        "add_ai_services_tables",
        "Add tables for enhanced AI services integration",
    )

    ai_migration_file = runner.migrations_dir / "20240102_000001_add_ai_services_tables.yaml"
    ai_migration = Migration(
        id="20240102_000001_add_ai_services_tables",
        name="add_ai_services_tables",
        description="Add tables for enhanced AI services integration",
        version="20240102_000001",
        dependencies=["20240101_000001_create_base_tables"],
        up_sql="""
-- Vector embeddings table
CREATE TABLE IF NOT EXISTS document_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    service_name TEXT NOT NULL, -- ragflow, deepwiki
    chunk_index INTEGER DEFAULT 0,
    chunk_text TEXT,
    embedding_vector BLOB, -- Serialized vector
    vector_dimension INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents (id)
);

-- Extracted entities
CREATE TABLE IF NOT EXISTS extracted_entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    entity_text TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    start_pos INTEGER,
    end_pos INTEGER,
    confidence REAL,
    source_service TEXT,
    metadata TEXT, -- JSON metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents (id)
);

-- Knowledge graph relationships
CREATE TABLE IF NOT EXISTS knowledge_graph (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_entity_id INTEGER,
    predicate TEXT NOT NULL,
    object_entity_id INTEGER,
    confidence REAL DEFAULT 1.0,
    source_document_id INTEGER,
    context_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_entity_id) REFERENCES extracted_entities (id),
    FOREIGN KEY (object_entity_id) REFERENCES extracted_entities (id),
    FOREIGN KEY (source_document_id) REFERENCES documents (id)
);

-- Query cache for AI services
CREATE TABLE IF NOT EXISTS query_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_hash TEXT UNIQUE,
    query_text TEXT,
    service_name TEXT,
    response_data TEXT, -- JSON response
    hit_count INTEGER DEFAULT 1,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Service health monitoring
CREATE TABLE IF NOT EXISTS service_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT NOT NULL,
    status TEXT NOT NULL, -- healthy, unhealthy, unknown
    response_time REAL,
    error_message TEXT,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create additional indexes
CREATE INDEX IF NOT EXISTS idx_embeddings_document ON document_embeddings(document_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_service ON document_embeddings(service_name);
CREATE INDEX IF NOT EXISTS idx_entities_document ON extracted_entities(document_id);
CREATE INDEX IF NOT EXISTS idx_entities_type ON extracted_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_subject ON knowledge_graph(subject_entity_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_object ON knowledge_graph(object_entity_id);
CREATE INDEX IF NOT EXISTS idx_cache_hash ON query_cache(query_hash);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON query_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_health_service ON service_health(service_name);
        """,
        down_sql="""
-- Drop indexes
DROP INDEX IF EXISTS idx_health_service;
DROP INDEX IF EXISTS idx_cache_expires;
DROP INDEX IF EXISTS idx_cache_hash;
DROP INDEX IF EXISTS idx_knowledge_object;
DROP INDEX IF EXISTS idx_knowledge_subject;
DROP INDEX IF EXISTS idx_entities_type;
DROP INDEX IF EXISTS idx_entities_document;
DROP INDEX IF EXISTS idx_embeddings_service;
DROP INDEX IF EXISTS idx_embeddings_document;

-- Drop tables
DROP TABLE IF EXISTS service_health;
DROP TABLE IF EXISTS query_cache;
DROP TABLE IF EXISTS knowledge_graph;
DROP TABLE IF EXISTS extracted_entities;
DROP TABLE IF EXISTS document_embeddings;
        """,
    )

    with open(ai_migration_file, "w") as f:
        yaml.dump(asdict(ai_migration), f, default_flow_style=False)


def main():
    """CLI interface for migration system."""
    import argparse

    parser = argparse.ArgumentParser(description="Database migration system")
    parser.add_argument("--db-path", default="noteparser.db", help="Database file path")
    parser.add_argument("--migrations-dir", help="Migrations directory")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create migration command
    create_parser = subparsers.add_parser("create", help="Create new migration")
    create_parser.add_argument("name", help="Migration name")
    create_parser.add_argument("--description", default="", help="Migration description")

    # Migrate up command
    up_parser = subparsers.add_parser("up", help="Run pending migrations")
    up_parser.add_argument("--target", help="Target migration ID")

    # Migrate down command
    down_parser = subparsers.add_parser("down", help="Rollback migrations")
    down_parser.add_argument("--target", help="Target migration ID")
    down_parser.add_argument(
        "--steps",
        type=int,
        default=1,
        help="Number of migrations to rollback",
    )

    # Status command
    subparsers.add_parser("status", help="Show migration status")

    # Reset command
    reset_parser = subparsers.add_parser("reset", help="Reset database")
    reset_parser.add_argument("--confirm", action="store_true", help="Confirm reset")

    # Init command
    subparsers.add_parser("init", help="Initialize with base migrations")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize migration runner
    runner = MigrationRunner(args.db_path, args.migrations_dir)

    if args.command == "create":
        migration_id = runner.create_migration(args.name, args.description)
        print(f"Created migration: {migration_id}")

    elif args.command == "up":
        success = runner.migrate_up(args.target)
        exit(0 if success else 1)

    elif args.command == "down":
        success = runner.migrate_down(args.target, args.steps)
        exit(0 if success else 1)

    elif args.command == "status":
        status = runner.status()
        print(json.dumps(status, indent=2))

    elif args.command == "reset":
        success = runner.reset(args.confirm)
        exit(0 if success else 1)

    elif args.command == "init":
        create_base_migrations(runner)
        success = runner.migrate_up()
        print("Database initialized with base migrations")
        exit(0 if success else 1)


if __name__ == "__main__":
    main()
