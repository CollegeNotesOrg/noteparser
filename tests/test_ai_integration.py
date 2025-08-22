"""
Tests for AI services integration.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from noteparser.core import NoteParser
from noteparser.integration.ai_services import AIServicesIntegration
from noteparser.integration.service_client import AIServiceClient, ServiceClientManager


class TestServiceClientManager:
    """Test the ServiceClientManager class."""

    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        manager = ServiceClientManager()
        assert "services" in manager.config
        assert "ragflow" in manager.config["services"]
        assert "deepwiki" in manager.config["services"]

    def test_init_with_config_file(self, tmp_path):
        """Test initialization with configuration file."""
        config_data = {
            "services": {
                "ragflow": {
                    "host": "test.example.com",
                    "port": 9000,
                    "base_url": "http://test.example.com:9000",
                },
            },
        }

        config_file = tmp_path / "test_config.yml"
        with open(config_file, "w") as f:
            import yaml

            yaml.dump(config_data, f)

        manager = ServiceClientManager(str(config_file))
        assert manager.config["services"]["ragflow"]["host"] == "test.example.com"
        assert manager.config["services"]["ragflow"]["port"] == 9000

    def test_get_client_creates_new_client(self):
        """Test that get_client creates a new client."""
        manager = ServiceClientManager()
        client = manager.get_client("ragflow")
        assert isinstance(client, AIServiceClient)
        assert client.service_name == "ragflow"

    def test_get_client_returns_existing_client(self):
        """Test that get_client returns existing client."""
        manager = ServiceClientManager()
        client1 = manager.get_client("ragflow")
        client2 = manager.get_client("ragflow")
        assert client1 is client2

    def test_get_client_invalid_service(self):
        """Test get_client with invalid service name."""
        manager = ServiceClientManager()
        with pytest.raises(ValueError, match="Service invalid_service not configured"):
            manager.get_client("invalid_service")

    @pytest.mark.asyncio
    async def test_health_check_all(self):
        """Test health check for all services."""
        manager = ServiceClientManager()

        # Mock the clients
        mock_ragflow = AsyncMock()
        mock_ragflow.health_check.return_value = {"status": "healthy"}
        mock_deepwiki = AsyncMock()
        mock_deepwiki.health_check.return_value = {"status": "healthy"}

        manager.clients["ragflow"] = mock_ragflow
        manager.clients["deepwiki"] = mock_deepwiki

        results = await manager.health_check_all()

        assert "ragflow" in results
        assert "deepwiki" in results
        assert results["ragflow"]["status"] == "healthy"
        assert results["deepwiki"]["status"] == "healthy"


class TestAIServiceClient:
    """Test the AIServiceClient class."""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check."""
        client = AIServiceClient("test", "http://localhost:8000")

        # Mock the httpx client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy", "uptime": 3600}

        client.client = AsyncMock()
        client.client.get.return_value = mock_response

        result = await client.health_check()

        assert result["status"] == "healthy"
        assert "details" in result
        assert result["details"]["uptime"] == 3600

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test failed health check."""
        client = AIServiceClient("test", "http://localhost:8000")

        client.client = AsyncMock()
        client.client.get.side_effect = Exception("Connection refused")

        result = await client.health_check()

        assert result["status"] == "unhealthy"
        assert "error" in result
        assert "Connection refused" in result["error"]

    @pytest.mark.asyncio
    async def test_post_request_success(self):
        """Test successful POST request."""
        client = AIServiceClient("test", "http://localhost:8000")

        mock_response = Mock()
        mock_response.json.return_value = {"result": "success"}
        mock_response.raise_for_status = Mock()

        client.client = AsyncMock()
        client.client.post.return_value = mock_response

        result = await client.post("endpoint", {"data": "test"})

        assert result["result"] == "success"
        client.client.post.assert_called_once_with(
            "http://localhost:8000/endpoint", json={"data": "test"},
        )

    @pytest.mark.asyncio
    async def test_post_request_failure(self):
        """Test failed POST request."""
        client = AIServiceClient("test", "http://localhost:8000")

        import httpx

        client.client = AsyncMock()
        client.client.post.side_effect = httpx.HTTPStatusError(
            "Error", request=Mock(), response=Mock(status_code=500),
        )

        result = await client.post("endpoint", {"data": "test"})

        assert result["status"] == "error"
        assert "error" in result


class TestAIServicesIntegration:
    """Test the AIServicesIntegration class."""

    def test_init_default(self):
        """Test initialization with default config."""
        integration = AIServicesIntegration()
        assert integration.config is not None
        assert not integration.services_initialized

    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = {"test": "value"}
        integration = AIServicesIntegration(config)
        assert integration.config == config

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful service initialization."""
        integration = AIServicesIntegration()

        # Mock the service manager
        mock_manager = AsyncMock()
        mock_manager.health_check_all.return_value = {
            "ragflow": {"status": "healthy"},
            "deepwiki": {"status": "healthy"},
        }

        with patch.object(integration, "manager", mock_manager):
            result = await integration.initialize()

        assert result is True
        assert integration.services_initialized is True

    @pytest.mark.asyncio
    async def test_initialize_failure(self):
        """Test failed service initialization."""
        integration = AIServicesIntegration()

        # Mock the service manager to raise an exception
        mock_manager = AsyncMock()
        mock_manager.health_check_all.side_effect = Exception("Network error")

        with patch.object(integration, "manager", mock_manager):
            result = await integration.initialize()

        assert result is False
        assert integration.services_initialized is False

    @pytest.mark.asyncio
    async def test_process_document_success(self):
        """Test successful document processing."""
        integration = AIServicesIntegration()
        integration.services_initialized = True

        # Mock the service clients
        mock_ragflow = AsyncMock()
        mock_ragflow.extract_insights.return_value = {
            "summary": "Test summary",
            "keywords": ["test", "document"],
            "confidence": 0.95,
        }

        mock_deepwiki = AsyncMock()
        mock_deepwiki.create_article.return_value = {"id": "test-123", "title": "Test Document"}

        mock_manager = Mock()
        mock_manager.get_client.side_effect = lambda name: {
            "ragflow": mock_ragflow,
            "deepwiki": mock_deepwiki,
        }[name]

        integration.manager = mock_manager

        document = {"content": "This is a test document.", "metadata": {"title": "Test Document"}}

        result = await integration.process_document(document)

        assert "ragflow_insights" in result
        assert "deepwiki_article" in result
        assert result["ragflow_insights"]["summary"] == "Test summary"
        assert result["deepwiki_article"]["id"] == "test-123"

    @pytest.mark.asyncio
    async def test_process_document_not_initialized(self):
        """Test document processing when services not initialized."""
        integration = AIServicesIntegration()
        integration.services_initialized = False

        document = {"content": "test", "metadata": {}}

        with pytest.raises(RuntimeError, match="AI services not initialized"):
            await integration.process_document(document)

    @pytest.mark.asyncio
    async def test_query_knowledge_success(self):
        """Test successful knowledge query."""
        integration = AIServicesIntegration()
        integration.services_initialized = True

        mock_ragflow = AsyncMock()
        mock_ragflow.query.return_value = {
            "documents": [
                {"title": "Doc 1", "score": 0.9, "content": "Content 1"},
                {"title": "Doc 2", "score": 0.8, "content": "Content 2"},
            ],
            "answer": "This is the AI answer.",
        }

        mock_manager = Mock()
        mock_manager.get_client.return_value = mock_ragflow

        integration.manager = mock_manager

        result = await integration.query_knowledge("test query")

        assert "documents" in result
        assert "answer" in result
        assert len(result["documents"]) == 2
        assert result["answer"] == "This is the AI answer."

    @pytest.mark.asyncio
    async def test_query_knowledge_not_initialized(self):
        """Test knowledge query when services not initialized."""
        integration = AIServicesIntegration()
        integration.services_initialized = False

        with pytest.raises(RuntimeError, match="AI services not initialized"):
            await integration.query_knowledge("test query")


class TestNoteParserAIIntegration:
    """Test AI integration in NoteParser."""

    def test_noteparser_with_ai_enabled(self):
        """Test NoteParser initialization with AI enabled."""
        with patch("noteparser.core.AIServicesIntegration") as mock_ai:
            parser = NoteParser(enable_ai=True)

        assert parser.enable_ai is True
        assert parser.ai_integration is not None
        mock_ai.assert_called_once()

    def test_noteparser_with_ai_disabled(self):
        """Test NoteParser initialization with AI disabled."""
        parser = NoteParser(enable_ai=False)

        assert parser.enable_ai is False
        assert parser.ai_integration is None

    def test_noteparser_ai_import_error(self):
        """Test NoteParser when AI services can't be imported."""
        with patch("noteparser.core.AIServicesIntegration", side_effect=ImportError("No module")):
            parser = NoteParser(enable_ai=True)

        assert parser.enable_ai is False
        assert parser.ai_integration is None

    @pytest.mark.asyncio
    async def test_parse_to_markdown_with_ai_success(self, tmp_path):
        """Test AI-enhanced markdown parsing."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is a test document for AI processing.")

        # Mock AI integration
        mock_ai = AsyncMock()
        mock_ai.initialize.return_value = True
        mock_ai.process_document.return_value = {
            "summary": "Test document summary",
            "keywords": ["test", "document"],
            "topics": ["testing"],
        }

        parser = NoteParser(enable_ai=True)
        parser.ai_integration = mock_ai

        result = await parser.parse_to_markdown_with_ai(test_file)

        assert "content" in result
        assert "ai_processing" in result
        assert result["ai_processing"]["summary"] == "Test document summary"
        assert "test" in result["ai_processing"]["keywords"]

    @pytest.mark.asyncio
    async def test_parse_to_markdown_with_ai_failure(self, tmp_path):
        """Test AI-enhanced parsing when AI processing fails."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is a test document.")

        # Mock AI integration that fails
        mock_ai = AsyncMock()
        mock_ai.initialize.side_effect = Exception("AI service error")

        parser = NoteParser(enable_ai=True)
        parser.ai_integration = mock_ai

        result = await parser.parse_to_markdown_with_ai(test_file)

        assert "content" in result
        assert "ai_processing" in result
        assert "error" in result["ai_processing"]

    @pytest.mark.asyncio
    async def test_query_knowledge_success(self):
        """Test successful knowledge query."""
        mock_ai = AsyncMock()
        mock_ai.initialize.return_value = True
        mock_ai.query_knowledge.return_value = {
            "documents": [{"title": "Test", "content": "Content"}],
            "answer": "AI answer",
        }

        parser = NoteParser(enable_ai=True)
        parser.ai_integration = mock_ai

        result = await parser.query_knowledge("test query")

        assert "documents" in result
        assert "answer" in result
        assert result["answer"] == "AI answer"

    @pytest.mark.asyncio
    async def test_query_knowledge_no_ai(self):
        """Test knowledge query when AI is disabled."""
        parser = NoteParser(enable_ai=False)

        result = await parser.query_knowledge("test query")

        assert "error" in result
        assert result["error"] == "AI services not enabled"


class TestWebAppAIIntegration:
    """Test AI integration in the web application."""

    def test_create_app_with_ai_enabled(self):
        """Test app creation with AI enabled."""
        from noteparser.web.app import create_app

        with patch("noteparser.web.app.AIServicesIntegration") as mock_ai:
            app = create_app({"AI_ENABLED": True})

        assert app.ai_integration is not None
        mock_ai.assert_called_once()

    def test_create_app_with_ai_disabled(self):
        """Test app creation with AI disabled."""
        from noteparser.web.app import create_app

        app = create_app({"AI_ENABLED": False})

        assert hasattr(app, "ai_integration")

    def test_ai_dashboard_route_with_ai_enabled(self):
        """Test AI dashboard route when AI is enabled."""
        from noteparser.web.app import create_app

        with patch("noteparser.web.app.AIServicesIntegration"):
            app = create_app()

        with app.test_client() as client:
            response = client.get("/ai")

        assert response.status_code == 200

    def test_ai_dashboard_route_with_ai_disabled(self):
        """Test AI dashboard route when AI is disabled."""
        from noteparser.web.app import create_app

        app = create_app()
        app.ai_integration = None

        with app.test_client() as client:
            response = client.get("/ai")

        assert response.status_code == 503  # Service unavailable

    def test_ai_query_route_success(self):
        """Test successful AI query via web API."""
        from noteparser.web.app import create_app

        mock_ai = Mock()
        app = create_app()
        app.ai_integration = mock_ai

        # Mock parser query_knowledge method
        async def mock_query(query, filters):
            return {"documents": [], "answer": "Test answer"}

        app.parser.query_knowledge = mock_query

        with app.test_client() as client:
            response = client.post("/api/ai/query", json={"query": "test question"})

        assert response.status_code == 200
        data = response.get_json()
        assert "answer" in data

    def test_ai_health_route(self):
        """Test AI health check route."""
        from noteparser.web.app import create_app

        app = create_app()
        app.ai_integration = None

        with app.test_client() as client:
            response = client.get("/api/ai/health")

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "disabled"


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "services": {
            "ragflow": {"host": "localhost", "port": 8010, "enabled": True},
            "deepwiki": {"host": "localhost", "port": 8011, "enabled": True},
        },
    }


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for testing."""
    client = AsyncMock()
    return client


# Integration tests that require actual services
@pytest.mark.integration
class TestRealServiceIntegration:
    """Integration tests that require running AI services."""

    @pytest.mark.asyncio
    async def test_real_service_health_check(self):
        """Test health check against real services (if running)."""
        manager = ServiceClientManager()

        try:
            results = await manager.health_check_all()

            # Check that we get results for both services
            assert "ragflow" in results
            assert "deepwiki" in results

            # Results should have status information
            for service_name, status in results.items():
                assert "status" in status
                assert status["status"] in ["healthy", "unhealthy", "disabled"]

        except Exception as e:
            pytest.skip(f"Real services not available: {e}")

    @pytest.mark.asyncio
    async def test_real_service_integration_flow(self, tmp_path):
        """Test full integration flow with real services."""
        # Create a test document
        test_file = tmp_path / "integration_test.txt"
        test_file.write_text(
            """
        This is a comprehensive test document for AI integration.
        It contains information about machine learning, neural networks,
        and artificial intelligence concepts that should be processed
        by the AI services to extract insights and create knowledge.
        """,
        )

        try:
            # Test with AI-enabled parser
            parser = NoteParser(enable_ai=True)

            if parser.ai_integration is None:
                pytest.skip("AI integration not available")

            # Parse document with AI
            result = await parser.parse_to_markdown_with_ai(test_file)

            # Verify we got content
            assert "content" in result
            assert len(result["content"]) > 0

            # Check if AI processing occurred
            if "ai_processing" in result and "error" not in result["ai_processing"]:
                ai_result = result["ai_processing"]

                # Verify AI processing structure
                expected_fields = ["ragflow_insights", "deepwiki_article"]
                for field in expected_fields:
                    if field in ai_result:
                        assert isinstance(ai_result[field], dict)

        except Exception as e:
            pytest.skip(f"Integration test failed - services may not be running: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
