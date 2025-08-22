"""
Pytest configuration and fixtures for NoteParser AI integration tests.
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import yaml


@pytest.fixture(scope="session")
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_documents(temp_dir):
    """Create sample documents for testing."""
    documents = {}

    # Text document
    text_doc = temp_dir / "sample.txt"
    text_doc.write_text(
        """
    This is a sample text document for testing the NoteParser AI integration.
    It contains information about machine learning, neural networks, and
    artificial intelligence that should be processed by the AI services.
    
    Key concepts:
    - Machine Learning: Computer systems that learn from data
    - Neural Networks: Computing systems inspired by biological neural networks
    - Deep Learning: Machine learning using deep neural networks
    """,
    )
    documents["text"] = text_doc

    # Markdown document
    md_doc = temp_dir / "sample.md"
    md_doc.write_text(
        """# AI Research Notes

## Introduction
This document contains research notes on artificial intelligence.

### Topics Covered
- **Natural Language Processing**: Understanding human language
- **Computer Vision**: Teaching machines to see
- **Reinforcement Learning**: Learning through interaction

## Mathematical Concepts
The fundamental equation for neural network forward pass:
$$y = f(Wx + b)$$

Where:
- W is the weight matrix
- x is the input vector
- b is the bias vector
- f is the activation function

## Code Example
```python
import numpy as np

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def neural_network_forward(X, W, b):
    return sigmoid(np.dot(X, W) + b)
```

## References
[1] Goodfellow, I., Bengio, Y., & Courville, A. (2016). Deep Learning.
[2] Russell, S., & Norvig, P. (2020). Artificial Intelligence: A Modern Approach.
    """,
    )
    documents["markdown"] = md_doc

    # Large document for performance testing
    large_doc = temp_dir / "large_document.txt"
    large_content = (
        """
    This is a large document created for performance testing.
    It contains repeated content to simulate real-world document processing.
    """
        * 5000
    )  # Create ~500KB document
    large_doc.write_text(large_content)
    documents["large"] = large_doc

    return documents


@pytest.fixture
def mock_ai_config():
    """Mock configuration for AI services."""
    return {
        "services": {
            "ragflow": {
                "host": "localhost",
                "port": 8010,
                "enabled": True,
                "base_url": "http://localhost:8010",
                "config": {
                    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                    "vector_db_type": "faiss",
                    "chunk_size": 512,
                    "top_k": 5,
                    "temperature": 0.7,
                },
            },
            "deepwiki": {
                "host": "localhost",
                "port": 8011,
                "enabled": True,
                "base_url": "http://localhost:8011",
                "config": {
                    "ai_model": "gpt-3.5-turbo",
                    "max_article_length": 10000,
                    "auto_link": True,
                    "similarity_threshold": 0.7,
                },
            },
        },
        "features": {"enable_rag": True, "enable_wiki": True, "enable_ai_suggestions": True},
    }


@pytest.fixture
def mock_service_responses():
    """Mock responses from AI services."""
    return {
        "ragflow": {
            "health": {
                "status": "healthy",
                "uptime": 3600,
                "memory_usage": "512MB",
                "cpu_usage": "15%",
                "documents_indexed": 1000,
            },
            "index_document": {
                "status": "success",
                "document_id": "doc_123",
                "chunks_created": 5,
                "embedding_time": 0.25,
            },
            "query": {
                "documents": [
                    {
                        "title": "Machine Learning Basics",
                        "content": "Introduction to machine learning concepts...",
                        "score": 0.92,
                        "metadata": {"course": "CS101", "topic": "ML", "author": "Test Author"},
                    },
                    {
                        "title": "Neural Networks",
                        "content": "Deep dive into neural network architectures...",
                        "score": 0.87,
                        "metadata": {"course": "CS201", "topic": "Deep Learning"},
                    },
                ],
                "answer": "Based on the documents, machine learning is a subset of AI that enables computers to learn from data.",
                "confidence": 0.89,
                "processing_time": 0.45,
            },
            "insights": {
                "summary": "This document covers fundamental concepts in artificial intelligence and machine learning.",
                "keywords": [
                    "machine learning",
                    "neural networks",
                    "AI",
                    "deep learning",
                    "algorithms",
                ],
                "topics": ["artificial intelligence", "computer science", "technology"],
                "sentiment": "neutral",
                "complexity_score": 0.7,
                "confidence": 0.85,
            },
        },
        "deepwiki": {
            "health": {
                "status": "healthy",
                "uptime": 2400,
                "articles_count": 250,
                "links_count": 500,
                "last_update": "2024-01-15T10:30:00Z",
            },
            "create_article": {
                "status": "success",
                "article_id": "wiki_456",
                "title": "AI Fundamentals",
                "url": "/wiki/ai-fundamentals",
                "links_created": 3,
                "categories": ["AI", "Education"],
            },
            "search": {
                "articles": [
                    {
                        "id": "wiki_123",
                        "title": "Machine Learning Overview",
                        "summary": "Comprehensive overview of ML techniques",
                        "score": 0.94,
                    },
                    {
                        "id": "wiki_124",
                        "title": "Deep Learning Fundamentals",
                        "summary": "Introduction to deep neural networks",
                        "score": 0.89,
                    },
                ],
                "total_results": 15,
                "page": 1,
                "per_page": 10,
            },
            "ask_assistant": {
                "answer": "Neural networks are computing systems inspired by biological neural networks.",
                "sources": ["wiki_123", "wiki_124"],
                "confidence": 0.91,
                "related_topics": ["machine learning", "deep learning", "AI"],
            },
        },
    }


@pytest.fixture
def mock_healthy_services(mock_service_responses):
    """Create mock services that return healthy responses."""

    class MockServiceClient:
        def __init__(self, service_name, responses):
            self.service_name = service_name
            self.responses = responses

        async def health_check(self):
            return self.responses["health"]

        async def post(self, endpoint, data):
            if endpoint in self.responses:
                return self.responses[endpoint]
            return {"status": "success", "data": data}

        async def get(self, endpoint, params=None):
            if endpoint in self.responses:
                return self.responses[endpoint]
            return {"status": "success", "params": params}

    return {
        "ragflow": MockServiceClient("ragflow", mock_service_responses["ragflow"]),
        "deepwiki": MockServiceClient("deepwiki", mock_service_responses["deepwiki"]),
    }


@pytest.fixture
def mock_unhealthy_services():
    """Create mock services that return unhealthy responses."""

    class MockUnhealthyServiceClient:
        def __init__(self, service_name, error_message):
            self.service_name = service_name
            self.error_message = error_message

        async def health_check(self):
            return {"status": "unhealthy", "error": self.error_message}

        async def post(self, endpoint, data):
            raise Exception(self.error_message)

        async def get(self, endpoint, params=None):
            raise Exception(self.error_message)

    return {
        "ragflow": MockUnhealthyServiceClient("ragflow", "Service unavailable"),
        "deepwiki": MockUnhealthyServiceClient("deepwiki", "Connection timeout"),
    }


@pytest.fixture
def ai_test_config(temp_dir, mock_ai_config):
    """Create a test configuration file."""
    config_file = temp_dir / "test_services.yml"
    with open(config_file, "w") as f:
        yaml.dump(mock_ai_config, f)
    return str(config_file)


@pytest.fixture
def mock_parser_with_ai():
    """Create a mock NoteParser with AI integration."""
    from noteparser.core import NoteParser

    # Mock the AI integration
    mock_ai = AsyncMock()
    mock_ai.initialize.return_value = True
    mock_ai.services_initialized = True

    parser = NoteParser(enable_ai=True)
    parser.ai_integration = mock_ai

    return parser, mock_ai


@pytest.fixture
def mock_web_app():
    """Create a mock Flask app for testing web integration."""
    from noteparser.web.app import create_app

    app = create_app({"TESTING": True, "AI_ENABLED": True})
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for testing

    # Mock AI integration
    app.ai_integration = AsyncMock()
    app.ai_integration.initialize.return_value = True

    return app


# Custom pytest markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test requiring real services",
    )
    config.addinivalue_line("markers", "benchmark: mark test as benchmark/performance test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add integration marker to integration tests
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)

        # Add benchmark marker to performance tests
        if "benchmark" in item.nodeid.lower() or "performance" in item.nodeid.lower():
            item.add_marker(pytest.mark.benchmark)

        # Add slow marker to tests that might be slow
        if any(
            keyword in item.nodeid.lower() for keyword in ["large", "batch", "concurrent", "load"]
        ):
            item.add_marker(pytest.mark.slow)


# Environment-based test skipping
def pytest_runtest_setup(item):
    """Skip tests based on environment variables."""
    # Skip integration tests if services are not available
    if "integration" in item.keywords:
        if os.getenv("INTEGRATION_TESTS", "").lower() not in ("1", "true", "yes"):
            pytest.skip("Integration tests disabled. Set INTEGRATION_TESTS=1 to enable.")

    # Skip benchmark tests unless specifically requested
    if "benchmark" in item.keywords:
        if os.getenv("BENCHMARK_TESTS", "").lower() not in ("1", "true", "yes"):
            pytest.skip("Benchmark tests disabled. Set BENCHMARK_TESTS=1 to enable.")


@pytest.fixture(autouse=True)
def clean_environment():
    """Clean environment variables before each test."""
    # Store original values
    original_env = {}
    ai_env_vars = [
        "RAGFLOW_URL",
        "DEEPWIKI_URL",
        "AI_SERVICES_ENABLED",
        "DATABASE_URL",
        "REDIS_URL",
    ]

    for var in ai_env_vars:
        original_env[var] = os.getenv(var)

    yield

    # Restore original values
    for var, value in original_env.items():
        if value is None:
            os.environ.pop(var, None)
        else:
            os.environ[var] = value


# Test data generators
@pytest.fixture
def generate_test_queries():
    """Generate test queries for AI testing."""
    return [
        {
            "query": "What is machine learning?",
            "filters": {},
            "expected_topics": ["machine learning", "AI"],
        },
        {
            "query": "Explain neural networks",
            "filters": {"course": "CS101"},
            "expected_topics": ["neural networks", "deep learning"],
        },
        {
            "query": "How does backpropagation work?",
            "filters": {"topic": "deep learning"},
            "expected_topics": ["backpropagation", "optimization"],
        },
        {
            "query": "What are the applications of AI?",
            "filters": {},
            "expected_topics": ["AI applications", "technology"],
        },
    ]


@pytest.fixture
def performance_test_data():
    """Generate data for performance testing."""
    return {
        "small_documents": 10,
        "medium_documents": 50,
        "large_documents": 5,
        "concurrent_requests": 20,
        "timeout_threshold": 5.0,
        "memory_limit_mb": 500,
    }
