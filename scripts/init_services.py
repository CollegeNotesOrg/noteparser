#!/usr/bin/env python3
"""
Initialize AI services and infrastructure for noteparser.

This script sets up the necessary databases, configurations, and
initial data for the AI-enhanced noteparser system.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any

import yaml

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.noteparser.integration.ai_services import AIServicesIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ServiceInitializer:
    """Initialize and configure all AI services."""

    def __init__(self):
        self.config = self.load_config()
        self.services = {}

    def load_config(self) -> dict[str, Any]:
        """Load configuration from file or environment."""
        config_path = Path(__file__).parent.parent / "config" / "services.yml"

        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f)
        else:
            # Default configuration
            config = {
                "services": {
                    "ragflow": {
                        "enabled": True,
                        "host": os.getenv("RAGFLOW_HOST", "localhost"),
                        "port": int(os.getenv("RAGFLOW_PORT", 8010)),
                    },
                    "deepwiki": {
                        "enabled": True,
                        "host": os.getenv("DEEPWIKI_HOST", "localhost"),
                        "port": int(os.getenv("DEEPWIKI_PORT", 8011)),
                    },
                    "dolphin": {
                        "enabled": False,
                        "host": os.getenv("DOLPHIN_HOST", "localhost"),
                        "port": int(os.getenv("DOLPHIN_PORT", 8012)),
                    },
                    "langextract": {
                        "enabled": False,
                        "host": os.getenv("LANGEXTRACT_HOST", "localhost"),
                        "port": int(os.getenv("LANGEXTRACT_PORT", 8013)),
                    },
                },
                "database": {
                    "postgres": {
                        "host": os.getenv("POSTGRES_HOST", "localhost"),
                        "port": int(os.getenv("POSTGRES_PORT", 5432)),
                        "database": os.getenv("POSTGRES_DB", "noteparser"),
                        "user": os.getenv("POSTGRES_USER", "noteparser"),
                        "password": os.getenv("POSTGRES_PASSWORD", "noteparser"),
                    },
                    "redis": {
                        "host": os.getenv("REDIS_HOST", "localhost"),
                        "port": int(os.getenv("REDIS_PORT", 6379)),
                        "db": int(os.getenv("REDIS_DB", 0)),
                    },
                    "elasticsearch": {
                        "host": os.getenv("ELASTICSEARCH_HOST", "localhost"),
                        "port": int(os.getenv("ELASTICSEARCH_PORT", 9200)),
                    },
                },
            }

        return config

    async def check_database_connections(self) -> bool:
        """Check if databases are accessible."""
        logger.info("Checking database connections...")

        # Check PostgreSQL
        try:
            import psycopg2

            conn = psycopg2.connect(
                host=self.config["database"]["postgres"]["host"],
                port=self.config["database"]["postgres"]["port"],
                database=self.config["database"]["postgres"]["database"],
                user=self.config["database"]["postgres"]["user"],
                password=self.config["database"]["postgres"]["password"],
            )
            conn.close()
            logger.info("✓ PostgreSQL connection successful")
        except Exception as e:
            logger.error(f"✗ PostgreSQL connection failed: {e}")
            return False

        # Check Redis
        try:
            import redis

            r = redis.Redis(
                host=self.config["database"]["redis"]["host"],
                port=self.config["database"]["redis"]["port"],
                db=self.config["database"]["redis"]["db"],
            )
            r.ping()
            logger.info("✓ Redis connection successful")
        except Exception as e:
            logger.error(f"✗ Redis connection failed: {e}")
            return False

        # Check Elasticsearch
        try:
            from elasticsearch import Elasticsearch

            es = Elasticsearch(
                [
                    f"{self.config['database']['elasticsearch']['host']}:"
                    f"{self.config['database']['elasticsearch']['port']}",
                ],
            )
            es.info()
            logger.info("✓ Elasticsearch connection successful")
        except Exception as e:
            logger.error(f"✗ Elasticsearch connection failed: {e}")
            return False

        return True

    async def initialize_database_schema(self):
        """Initialize database schema."""
        logger.info("Initializing database schema...")

        try:
            from sqlalchemy import create_engine
            from sqlalchemy.sql import text

            # Create database URL
            db_config = self.config["database"]["postgres"]
            db_url = (
                f"postgresql://{db_config['user']}:{db_config['password']}@"
                f"{db_config['host']}:{db_config['port']}/{db_config['database']}"
            )

            # Create engine
            engine = create_engine(db_url)

            # Create tables
            with engine.connect() as conn:
                # Documents table
                conn.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS documents (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(255),
                        content TEXT,
                        file_path VARCHAR(500),
                        file_type VARCHAR(50),
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                    ),
                )

                # Wiki articles table
                conn.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS wiki_articles (
                        id SERIAL PRIMARY KEY,
                        article_id VARCHAR(255) UNIQUE,
                        title VARCHAR(255),
                        content TEXT,
                        concepts JSONB,
                        links JSONB,
                        metadata JSONB,
                        version INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                    ),
                )

                # RAG embeddings table
                conn.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS embeddings (
                        id SERIAL PRIMARY KEY,
                        document_id INTEGER REFERENCES documents(id),
                        chunk_text TEXT,
                        embedding VECTOR(384),
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                    ),
                )

                # Service logs table
                conn.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS service_logs (
                        id SERIAL PRIMARY KEY,
                        service_name VARCHAR(100),
                        action VARCHAR(100),
                        status VARCHAR(50),
                        request_data JSONB,
                        response_data JSONB,
                        error_message TEXT,
                        duration_ms INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                    ),
                )

                conn.commit()

            logger.info("✓ Database schema initialized")

        except Exception as e:
            logger.error(f"✗ Failed to initialize database schema: {e}")
            raise

    async def create_elasticsearch_indices(self):
        """Create Elasticsearch indices."""
        logger.info("Creating Elasticsearch indices...")

        try:
            from elasticsearch import Elasticsearch

            es = Elasticsearch(
                [
                    f"{self.config['database']['elasticsearch']['host']}:"
                    f"{self.config['database']['elasticsearch']['port']}",
                ],
            )

            # Documents index
            if not es.indices.exists(index="noteparser-documents"):
                es.indices.create(
                    index="noteparser-documents",
                    body={
                        "mappings": {
                            "properties": {
                                "title": {"type": "text"},
                                "content": {"type": "text"},
                                "file_path": {"type": "keyword"},
                                "file_type": {"type": "keyword"},
                                "concepts": {"type": "keyword"},
                                "created_at": {"type": "date"},
                            },
                        },
                    },
                )
                logger.info("✓ Created documents index")

            # Wiki index
            if not es.indices.exists(index="noteparser-wiki"):
                es.indices.create(
                    index="noteparser-wiki",
                    body={
                        "mappings": {
                            "properties": {
                                "article_id": {"type": "keyword"},
                                "title": {"type": "text"},
                                "content": {"type": "text"},
                                "concepts": {"type": "keyword"},
                                "created_at": {"type": "date"},
                            },
                        },
                    },
                )
                logger.info("✓ Created wiki index")

        except Exception as e:
            logger.error(f"✗ Failed to create Elasticsearch indices: {e}")
            raise

    async def initialize_ai_services(self):
        """Initialize AI service integrations."""
        logger.info("Initializing AI services...")

        try:
            # Create AI services integration
            ai_integration = AIServicesIntegration(self.config["services"])

            # Initialize services
            await ai_integration.initialize()

            logger.info("✓ AI services initialized")

            return ai_integration

        except Exception as e:
            logger.error(f"✗ Failed to initialize AI services: {e}")
            raise

    async def load_sample_data(self):
        """Load sample data for testing."""
        logger.info("Loading sample data...")

        sample_documents = [
            {
                "title": "Introduction to Machine Learning",
                "content": "Machine learning is a subset of artificial intelligence...",
                "file_type": "markdown",
            },
            {
                "title": "Python Programming Basics",
                "content": "Python is a high-level programming language...",
                "file_type": "markdown",
            },
        ]

        # Process sample documents
        ai_integration = await self.initialize_ai_services()

        for doc in sample_documents:
            result = await ai_integration.process_document(doc)
            logger.info(f"Processed sample document: {doc['title']}")

        logger.info("✓ Sample data loaded")

    async def run(self):
        """Run the initialization process."""
        logger.info("Starting service initialization...")

        try:
            # Check database connections
            if not await self.check_database_connections():
                logger.error("Database connections failed. Please ensure all services are running.")
                return False

            # Initialize database schema
            await self.initialize_database_schema()

            # Create Elasticsearch indices
            await self.create_elasticsearch_indices()

            # Initialize AI services
            await self.initialize_ai_services()

            # Optionally load sample data
            if os.getenv("LOAD_SAMPLE_DATA", "false").lower() == "true":
                await self.load_sample_data()

            logger.info("✓ Service initialization completed successfully!")
            return True

        except Exception as e:
            logger.error(f"✗ Service initialization failed: {e}")
            return False


async def main():
    """Main entry point."""
    initializer = ServiceInitializer()
    success = await initializer.run()

    if success:
        logger.info("\n" + "=" * 50)
        logger.info("NoteParser AI Services are ready!")
        logger.info("=" * 50)
        logger.info("\nYou can now:")
        logger.info("  • Access the web interface at http://localhost:5000")
        logger.info("  • Use the API at http://localhost:8000/api/v1")
        logger.info("  • View monitoring at http://localhost:3000 (Grafana)")
        logger.info("  • Check traces at http://localhost:16686 (Jaeger)")
    else:
        logger.error("\nInitialization failed. Please check the logs and try again.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
