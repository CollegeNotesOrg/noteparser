#!/usr/bin/env python3
"""
Database seeding system for noteparser
Provides sample data and test fixtures for development and testing
"""

import hashlib
import json
import logging
import os
import random
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseSeeder:
    """Database seeder for noteparser development and testing."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database seeder.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or os.getenv("DATABASE_PATH", "noteparser.db")

        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found: {self.db_path}")

    def clear_data(self, confirm: bool = False) -> bool:
        """Clear all seeded data from database.

        Args:
            confirm: Must be True to actually clear data

        Returns:
            True if successful
        """
        if not confirm:
            logger.warning("Clear data requires confirmation (confirm=True)")
            return False

        logger.warning("Clearing all data from database")

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Clear data in dependency order
                tables = [
                    "service_health",
                    "query_cache",
                    "knowledge_graph",
                    "extracted_entities",
                    "document_embeddings",
                    "processing_queue",
                    "document_relationships",
                    "ai_processing_results",
                    "user_sessions",
                    "documents",
                ]

                for table in tables:
                    conn.execute(f"DELETE FROM {table}")

                conn.commit()

            logger.info("Data cleared successfully")
            return True

        except Exception as e:
            logger.exception(f"Failed to clear data: {e}")
            return False

    def seed_sample_documents(self, count: int = 10) -> list[int]:
        """Seed sample documents.

        Args:
            count: Number of documents to create

        Returns:
            List of document IDs
        """
        logger.info(f"Seeding {count} sample documents")

        document_types = [
            {
                "filename": "calculus_notes.pdf",
                "mime_type": "application/pdf",
                "content": """# Calculus I - Limits and Derivatives

## Chapter 1: Limits
The concept of limit is fundamental to calculus. A limit describes the behavior of a function as the input approaches a particular value.

### Definition
Let f(x) be a function. We say that the limit of f(x) as x approaches a is L, written as:
lim(x→a) f(x) = L

### Properties of Limits
1. Limit of a sum: lim(x→a) [f(x) + g(x)] = lim(x→a) f(x) + lim(x→a) g(x)
2. Limit of a product: lim(x→a) [f(x) · g(x)] = lim(x→a) f(x) · lim(x→a) g(x)

## Chapter 2: Derivatives
The derivative measures the rate of change of a function.

### Definition
The derivative of f(x) is defined as:
f'(x) = lim(h→0) [f(x+h) - f(x)] / h

### Common Derivatives
- d/dx(x^n) = nx^(n-1)
- d/dx(sin x) = cos x
- d/dx(cos x) = -sin x
- d/dx(e^x) = e^x
                """,
                "metadata": json.dumps(
                    {
                        "subject": "mathematics",
                        "course": "MATH 101",
                        "chapter": 1,
                        "keywords": ["calculus", "limits", "derivatives", "mathematics"],
                    },
                ),
            },
            {
                "filename": "data_structures_algorithms.md",
                "mime_type": "text/markdown",
                "content": """# Data Structures and Algorithms

## Binary Trees
A binary tree is a hierarchical data structure where each node has at most two children.

### Properties
- Each node contains data and references to left and right children
- Maximum number of nodes at level k is 2^k
- Time complexity for search, insert, delete: O(log n) for balanced trees

### Implementation
```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def inorder_traversal(root):
    if root:
        inorder_traversal(root.left)
        print(root.val)
        inorder_traversal(root.right)
```

## Hash Tables
Hash tables provide O(1) average case for insert, delete, and search operations.

### Collision Resolution
1. Separate Chaining: Use linked lists to handle collisions
2. Open Addressing: Find next available slot using probing

### Load Factor
Load factor = Number of elements / Table size
Optimal load factor is typically 0.75
                """,
                "metadata": json.dumps(
                    {
                        "subject": "computer_science",
                        "course": "CS 301",
                        "topic": "data_structures",
                        "keywords": ["algorithms", "binary_tree", "hash_table", "computer_science"],
                    },
                ),
            },
            {
                "filename": "organic_chemistry_reactions.pdf",
                "mime_type": "application/pdf",
                "content": """# Organic Chemistry - Reaction Mechanisms

## Nucleophilic Substitution Reactions

### SN1 Mechanism
Unimolecular nucleophilic substitution proceeds through a carbocation intermediate.

#### Characteristics:
- Rate depends only on substrate concentration
- Stereochemistry: Racemization occurs
- Favored by tertiary substrates
- Protic solvents stabilize carbocation

#### Mechanism Steps:
1. Ionization: R-X → R+ + X-
2. Nucleophilic attack: R+ + Nu- → R-Nu

### SN2 Mechanism
Bimolecular nucleophilic substitution occurs in a single concerted step.

#### Characteristics:
- Rate depends on both substrate and nucleophile concentrations
- Stereochemistry: Complete inversion (Walden inversion)
- Favored by primary substrates
- Aprotic solvents increase nucleophilicity

#### Energy Profile:
The reaction proceeds through a single transition state with partial bonds to both leaving group and nucleophile.
                """,
                "metadata": json.dumps(
                    {
                        "subject": "chemistry",
                        "course": "CHEM 201",
                        "topic": "organic_reactions",
                        "keywords": [
                            "chemistry",
                            "organic",
                            "nucleophilic_substitution",
                            "mechanisms",
                        ],
                    },
                ),
            },
            {
                "filename": "quantum_mechanics_intro.tex",
                "mime_type": "application/x-latex",
                "content": """# Introduction to Quantum Mechanics

## Wave-Particle Duality
Quantum objects exhibit both wave-like and particle-like properties depending on the experimental setup.

### De Broglie Wavelength
Every particle has an associated wavelength:
λ = h/p
where h is Planck's constant and p is momentum.

### Heisenberg Uncertainty Principle
The position and momentum of a particle cannot be simultaneously known with perfect precision:
Δx · Δp ≥ ℏ/2

## Schrödinger Equation
The time-dependent Schrödinger equation describes the evolution of quantum systems:
iℏ ∂ψ/∂t = Ĥψ

### Time-Independent Case
For stationary states:
Ĥψ = Eψ
This is an eigenvalue equation where E represents energy eigenvalues.

## Applications
1. Particle in a box
2. Harmonic oscillator
3. Hydrogen atom
                """,
                "metadata": json.dumps(
                    {
                        "subject": "physics",
                        "course": "PHYS 302",
                        "topic": "quantum_mechanics",
                        "keywords": ["quantum", "physics", "schrodinger", "wave_function"],
                    },
                ),
            },
        ]

        document_ids = []
        base_time = datetime.now() - timedelta(days=30)

        with sqlite3.connect(self.db_path) as conn:
            for i in range(count):
                doc_template = random.choice(document_types)

                # Generate unique filename and content
                filename = f"{i:03d}_{doc_template['filename']}"
                content = doc_template["content"] + f"\n\n<!-- Document ID: {i} -->"
                content_hash = hashlib.md5(content.encode()).hexdigest()

                # Random processing status
                statuses = ["completed", "pending", "processing", "failed"]
                status = random.choice(statuses)

                # Random timestamps
                created_at = base_time + timedelta(days=random.randint(0, 30))
                processed_at = created_at + timedelta(minutes=random.randint(1, 60))

                cursor = conn.execute(
                    """
                    INSERT INTO documents
                    (filename, content_hash, file_size, mime_type, processing_status,
                     metadata, content, ai_processed, created_at, processed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        filename,
                        content_hash,
                        len(content),
                        doc_template["mime_type"],
                        status,
                        doc_template["metadata"],
                        content,
                        status == "completed",
                        created_at.isoformat(),
                        processed_at.isoformat(),
                    ),
                )

                document_ids.append(cursor.lastrowid)

            conn.commit()

        logger.info(f"Created {len(document_ids)} sample documents")
        return document_ids

    def seed_ai_processing_results(
        self,
        document_ids: list[int],
        count: Optional[int] = None,
    ) -> int:
        """Seed AI processing results.

        Args:
            document_ids: List of document IDs to create results for
            count: Number of results to create (default: 2-5 per document)

        Returns:
            Number of results created
        """
        if not document_ids:
            return 0

        count = count or len(document_ids) * 3
        logger.info(f"Seeding {count} AI processing results")

        services = ["ragflow", "deepwiki", "langextract", "dolphin"]
        processing_types = ["index", "query", "analyze", "extract"]

        results_created = 0

        with sqlite3.connect(self.db_path) as conn:
            for i in range(count):
                document_id = random.choice(document_ids)
                service = random.choice(services)
                proc_type = random.choice(processing_types)

                # Generate sample request/response data
                request_data = json.dumps(
                    {
                        "document_id": document_id,
                        "options": {"extract_entities": True, "generate_summary": True},
                    },
                )

                response_data = json.dumps(
                    {
                        "status": "success",
                        "entities_count": random.randint(5, 50),
                        "processing_time": random.uniform(0.5, 10.0),
                        "confidence": random.uniform(0.7, 0.99),
                    },
                )

                success = random.choice([True, True, True, False])  # 75% success rate
                error_msg = None if success else "Connection timeout"

                conn.execute(
                    """
                    INSERT INTO ai_processing_results
                    (document_id, service_name, processing_type, request_data,
                     response_data, processing_time, success, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        document_id,
                        service,
                        proc_type,
                        request_data,
                        response_data,
                        random.uniform(0.1, 5.0),
                        success,
                        error_msg,
                    ),
                )

                results_created += 1

            conn.commit()

        logger.info(f"Created {results_created} AI processing results")
        return results_created

    def seed_document_relationships(
        self,
        document_ids: list[int],
        count: Optional[int] = None,
    ) -> int:
        """Seed document relationships.

        Args:
            document_ids: List of document IDs
            count: Number of relationships to create

        Returns:
            Number of relationships created
        """
        if len(document_ids) < 2:
            return 0

        count = count or min(20, len(document_ids) * 2)
        logger.info(f"Seeding {count} document relationships")

        relationship_types = ["similar", "prerequisite", "continuation", "related", "references"]
        relationships_created = 0

        with sqlite3.connect(self.db_path) as conn:
            for i in range(count):
                # Ensure different documents
                source_id = random.choice(document_ids)
                target_id = random.choice(
                    [doc_id for doc_id in document_ids if doc_id != source_id],
                )

                rel_type = random.choice(relationship_types)
                confidence = random.uniform(0.6, 0.95)

                metadata = json.dumps(
                    {
                        "detection_method": "content_similarity",
                        "common_keywords": random.randint(3, 15),
                        "semantic_score": confidence,
                    },
                )

                try:
                    conn.execute(
                        """
                        INSERT INTO document_relationships
                        (source_document_id, target_document_id, relationship_type,
                         confidence, metadata)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (source_id, target_id, rel_type, confidence, metadata),
                    )

                    relationships_created += 1

                except sqlite3.IntegrityError:
                    # Skip if relationship already exists
                    pass

            conn.commit()

        logger.info(f"Created {relationships_created} document relationships")
        return relationships_created

    def seed_processing_queue(self, document_ids: list[int], count: Optional[int] = None) -> int:
        """Seed processing queue entries.

        Args:
            document_ids: List of document IDs
            count: Number of queue entries to create

        Returns:
            Number of queue entries created
        """
        if not document_ids:
            return 0

        count = count or len(document_ids) // 2
        logger.info(f"Seeding {count} processing queue entries")

        services = ["ragflow", "deepwiki", "langextract", "dolphin"]
        processing_types = ["index", "analyze", "extract", "summarize"]
        statuses = ["pending", "processing", "completed", "failed"]

        queue_entries = 0

        with sqlite3.connect(self.db_path) as conn:
            for i in range(count):
                document_id = random.choice(document_ids)
                service = random.choice(services)
                proc_type = random.choice(processing_types)
                status = random.choice(statuses)
                priority = random.randint(1, 10)

                # Generate timestamps based on status
                now = datetime.now()
                scheduled_at = now - timedelta(minutes=random.randint(1, 1440))

                started_at = None
                completed_at = None
                error_message = None

                if status in ["processing", "completed", "failed"]:
                    started_at = scheduled_at + timedelta(minutes=random.randint(1, 30))

                    if status in ["completed", "failed"]:
                        completed_at = started_at + timedelta(minutes=random.randint(1, 60))

                        if status == "failed":
                            error_message = "Processing timeout occurred"

                conn.execute(
                    """
                    INSERT INTO processing_queue
                    (document_id, service_name, processing_type, priority, status,
                     attempts, scheduled_at, started_at, completed_at, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        document_id,
                        service,
                        proc_type,
                        priority,
                        status,
                        random.randint(1, 3),
                        scheduled_at.isoformat(),
                        started_at.isoformat() if started_at else None,
                        completed_at.isoformat() if completed_at else None,
                        error_message,
                    ),
                )

                queue_entries += 1

            conn.commit()

        logger.info(f"Created {queue_entries} processing queue entries")
        return queue_entries

    def seed_service_health(self) -> int:
        """Seed service health data.

        Returns:
            Number of health records created
        """
        logger.info("Seeding service health data")

        services = [
            {"name": "ragflow", "base_response_time": 0.5},
            {"name": "deepwiki", "base_response_time": 0.8},
            {"name": "langextract", "base_response_time": 1.2},
            {"name": "dolphin", "base_response_time": 2.0},
        ]

        statuses = ["healthy", "healthy", "healthy", "unhealthy"]  # 75% healthy
        records_created = 0

        with sqlite3.connect(self.db_path) as conn:
            # Create health records for the last 24 hours
            for hour in range(24):
                check_time = datetime.now() - timedelta(hours=hour)

                for service in services:
                    status = random.choice(statuses)

                    if status == "healthy":
                        response_time = service["base_response_time"] * random.uniform(0.8, 1.5)
                        error_message = None
                    else:
                        response_time = service["base_response_time"] * random.uniform(5, 20)
                        error_message = random.choice(
                            [
                                "Connection refused",
                                "Request timeout",
                                "Service unavailable",
                                "Internal server error",
                            ],
                        )

                    conn.execute(
                        """
                        INSERT INTO service_health
                        (service_name, status, response_time, error_message, checked_at)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            service["name"],
                            status,
                            response_time,
                            error_message,
                            check_time.isoformat(),
                        ),
                    )

                    records_created += 1

            conn.commit()

        logger.info(f"Created {records_created} service health records")
        return records_created

    def seed_all(self, document_count: int = 20) -> dict[str, int]:
        """Seed all data types.

        Args:
            document_count: Number of documents to create

        Returns:
            Dictionary with counts of each data type created
        """
        logger.info(f"Seeding complete dataset with {document_count} documents")

        results = {}

        # Seed documents first
        document_ids = self.seed_sample_documents(document_count)
        results["documents"] = len(document_ids)

        # Seed related data
        results["ai_results"] = self.seed_ai_processing_results(document_ids)
        results["relationships"] = self.seed_document_relationships(document_ids)
        results["queue_entries"] = self.seed_processing_queue(document_ids)
        results["health_records"] = self.seed_service_health()

        logger.info(f"Seeding completed: {results}")
        return results

    def get_stats(self) -> dict[str, int]:
        """Get current database statistics.

        Returns:
            Dictionary with table row counts
        """
        stats = {}

        tables = [
            "documents",
            "ai_processing_results",
            "document_relationships",
            "processing_queue",
            "service_health",
            "user_sessions",
            "config_store",
        ]

        with sqlite3.connect(self.db_path) as conn:
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]

        return stats


def main():
    """CLI interface for database seeding."""
    import argparse

    parser = argparse.ArgumentParser(description="Database seeding system")
    parser.add_argument("--db-path", default="noteparser.db", help="Database file path")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Seed all command
    seed_all_parser = subparsers.add_parser("seed-all", help="Seed all data types")
    seed_all_parser.add_argument("--count", type=int, default=20, help="Number of documents")

    # Clear data command
    clear_parser = subparsers.add_parser("clear", help="Clear all seeded data")
    clear_parser.add_argument("--confirm", action="store_true", help="Confirm clear operation")

    # Statistics command
    subparsers.add_parser("stats", help="Show database statistics")

    # Individual seed commands
    seed_docs_parser = subparsers.add_parser("seed-docs", help="Seed sample documents")
    seed_docs_parser.add_argument("--count", type=int, default=10, help="Number of documents")

    subparsers.add_parser("seed-health", help="Seed service health data")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize seeder
    try:
        seeder = DatabaseSeeder(args.db_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Run migrations first: python migrate.py init")
        sys.exit(1)

    if args.command == "seed-all":
        results = seeder.seed_all(args.count)
        print(f"Seeding completed: {json.dumps(results, indent=2)}")

    elif args.command == "clear":
        success = seeder.clear_data(args.confirm)
        sys.exit(0 if success else 1)

    elif args.command == "stats":
        stats = seeder.get_stats()
        print(json.dumps(stats, indent=2))

    elif args.command == "seed-docs":
        document_ids = seeder.seed_sample_documents(args.count)
        print(f"Created {len(document_ids)} documents")

    elif args.command == "seed-health":
        count = seeder.seed_service_health()
        print(f"Created {count} health records")


if __name__ == "__main__":
    main()
